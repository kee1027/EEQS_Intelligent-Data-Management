# 导入所需的库
import pandas as pd
import numpy as np
import pytz
from pathlib import Path
from io import StringIO
from django.db import transaction
from django.core.management.base import BaseCommand, CommandError
from data.models import Station, WeatherData

# ---------------------------------------------------------------------------
# 文件路径常量
# ---------------------------------------------------------------------------
DATA_MAIN_FILE = Path(r"F:\CSI_Datai\LoggerNet\两河源北斗接收_Data_Receive.dat")
DATA_BACKUP_FILE = Path(r"F:\CSI_Datai\LoggerNet\两河源北斗接收_Data_Receive.dat.backup")

# ---------------------------------------------------------------------------
# 站点定义（从列名前缀到表名的映射，以及列范围）
# ---------------------------------------------------------------------------
STATION_DEFINITIONS = [
    ('HXC',   'HXC_Header',   'HXC_TRB3_RH'),
    ('KW',    'KW_Header',    'KW_Snow_density'),
    ('JG',    'JG_Header',    'JG_Snow_Depth'),
    ('KYE',   'KYE_Header',   'KYE_Snow_Depth'),
    ('KKSLS', 'KKSLS_Header', 'KKSLS_Snow_density'),
    ('KKSLM', 'KKSLM_Header', 'KKSLM_RainSnow_HalfHour'),
    ('AKSL',  'AKSL_Header',  'AKSL_Snow_Depth'),
    ('SDHZ',  'SDHZ_Header',  'SDHZ_Snow_density'),
]


# ---------------------------------------------------------------------------
# 解析 TOA5 文件（单文件）
# ---------------------------------------------------------------------------
def _parse_toa5_dynamically(file_path: Path) -> pd.DataFrame | None:
    """
    动态解析 TOA5 宽格式文件，返回长格式 DataFrame。
    如果文件不存在或为空，返回 None。
    """
    if not file_path.exists():
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        raise CommandError(f"无法读取文件 {file_path}: {e}")

    header_start_index = -1
    for i, line in enumerate(lines):
        if line.strip().startswith('"TOA5"'):
            header_start_index = i
            break
    if header_start_index == -1:
        raise CommandError(f"在文件中找不到 TOA5 文件头: {file_path}")

    header_lines = [l.strip() for l in lines[header_start_index:header_start_index + 4]]
    data_lines = lines[header_start_index + 4:]
    all_columns = [col.strip('"') for col in header_lines[1].split(',')]

    df_wide = pd.read_csv(
        StringIO("".join(data_lines)),
        header=None,
        names=all_columns,
        na_values=['"NAN"'],
        quotechar='"',
        sep=','
    )

    model_field_names = {f.name for f in WeatherData._meta.get_fields()}
    processed_rows = []

    for _, row in df_wide.iterrows():
        timestamp = row['TIMESTAMP']
        for station_prefix, start_col_name, end_col_name in STATION_DEFINITIONS:
            try:
                start_idx = all_columns.index(start_col_name)
                end_idx = all_columns.index(end_col_name) + 1
            except ValueError as e:
                raise CommandError(
                    f"为站点 '{station_prefix}' 定义的列 '{e.args[0]}' 在文件头中未找到。"
                )

            station_data_slice = row[start_idx:end_idx]
            new_row = {'timestamp': timestamp, 'station_name': station_prefix}
            for col_name, value in station_data_slice.items():
                base_name = col_name.replace(station_prefix + '_', '', 1).lower()
                if base_name in model_field_names:
                    new_row[base_name] = value
            processed_rows.append(new_row)

    return pd.DataFrame(processed_rows) if processed_rows else None


# ---------------------------------------------------------------------------
# 文件发现与排序
# ---------------------------------------------------------------------------
def _discover_files() -> list[Path]:
    """
    发现数据文件并按修改时间升序排序（旧 → 新）。
    先 backup 后主文件，确保主文件数据在合并冲突时优先保留。
    """
    files = []
    if DATA_BACKUP_FILE.exists():
        files.append(DATA_BACKUP_FILE)
    if DATA_MAIN_FILE.exists():
        files.append(DATA_MAIN_FILE)
    files.sort(key=lambda p: p.stat().st_mtime)
    return files


# ---------------------------------------------------------------------------
# 多文件合并 + 清洗
# ---------------------------------------------------------------------------
def _merge_and_clean(dfs: list[pd.DataFrame]) -> pd.DataFrame:
    """
    合并多个 DataFrame，全局去重，时区处理，数值清洗。
    keep='last' 保证主文件（修改时间最新）的数据覆盖 backup 中的重复行。
    """
    merged = pd.concat(dfs, ignore_index=True)

    # 时区转换（使用 pytz 以保持与原始逻辑一致，此处只做 localize）
    shanghai_tz = pytz.timezone('Asia/Shanghai')
    merged['timestamp'] = pd.to_datetime(merged['timestamp']).dt.tz_localize(shanghai_tz)

    # 全局去重：保留最后出现的（主文件优先）
    merged.drop_duplicates(subset=['station_name', 'timestamp'], keep='last', inplace=True)

    # 数值清洗
    data_cols = [f.name for f in WeatherData._meta.get_fields() if f.name not in ('id', 'station', 'timestamp')]
    for col in data_cols:
        if col in merged.columns:
            merged[col] = pd.to_numeric(merged[col], errors='coerce')

    merged.replace([np.inf, -np.inf], np.nan, inplace=True)
    return merged


# ---------------------------------------------------------------------------
# 核心导入逻辑（只 INSERT，不更新）
# ---------------------------------------------------------------------------
def _import_new_records(df: pd.DataFrame, stdout, style) -> dict:
    """
    只插入数据库中不存在的新记录。返回统计信息 dict。
    使用 Unix 秒级整数作为比对键，彻底规避时区库格式差异。
    """
    station_names = df['station_name'].unique()
    stations = {name: Station.objects.get_or_create(name=name)[0] for name in station_names}

    min_ts = df['timestamp'].min()
    max_ts = df['timestamp'].max()

    # 1. 一次性拉取数据库中已有记录（按时间范围过滤）
    existing_records = set(
        (station_id, int(ts.timestamp()))
        for station_id, ts in WeatherData.objects.filter(
            timestamp__range=(min_ts, max_ts)
        ).values_list('station_id', 'timestamp')
    )

    weather_objects = []
    skip_existing = 0
    seen_in_batch = set()

    for _, row in df.iterrows():
        station_obj = stations[row['station_name']]
        py_timestamp = row['timestamp'].to_pydatetime()
        lookup_key = (station_obj.id, int(py_timestamp.timestamp()))

        if lookup_key in existing_records or lookup_key in seen_in_batch:
            skip_existing += 1
            continue

        seen_in_batch.add(lookup_key)

        data_defaults = row.to_dict()
        data_defaults.pop('timestamp')
        data_defaults.pop('station_name')
        defaults_cleaned = {k: v for k, v in data_defaults.items() if pd.notna(v)}

        weather_objects.append(
            WeatherData(
                station=station_obj,
                timestamp=py_timestamp,
                **defaults_cleaned
            )
        )

    # 2. 批量写入（ignore_conflicts=True 作为数据库级兜底）
    records_created = len(weather_objects)
    if weather_objects:
        stdout.write(f"  正在向数据库批量写入 {records_created} 条新记录...")
        WeatherData.objects.bulk_create(weather_objects, batch_size=2000, ignore_conflicts=True)
    else:
        stdout.write("  没有新的数据需要写入。")

    return {
        'records_created': records_created,
        'skip_existing': skip_existing,
        'total_unique': len(df),
    }


# ---------------------------------------------------------------------------
# Django 管理命令
# ---------------------------------------------------------------------------
class Command(BaseCommand):
    help = '解析 TOA5 宽格式数据文件（支持主文件+backup合并）并只插入新记录到 PostgreSQL。'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            nargs='+',
            help='手动指定一个或多个数据文件路径（默认自动扫描主文件+backup）。'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='解析和清洗数据，但不保存到数据库。'
        )

    def handle(self, *args, **options):
        if options['dry_run']:
            self._execute_import(*args, **options)
        else:
            with transaction.atomic():
                self._execute_import(*args, **options)

    def _execute_import(self, *args, **options):
        is_dry_run = options['dry_run']
        manual_files = options['file']

        # ---------------------------------------------------------------
        # 文件发现阶段
        # ---------------------------------------------------------------
        if manual_files:
            files = [Path(f) for f in manual_files]
            self.stdout.write(self.style.WARNING("[Manual] 使用手动指定的文件:"))
            for f in files:
                self.stdout.write(f"  - {f}")
        else:
            files = _discover_files()
            self.stdout.write("[Auto] 扫描数据文件...")
            if not files:
                self.stdout.write(self.style.WARNING("  未找到任何数据文件（主文件和 backup 均不存在）。"))
                return
            for f in files:
                self.stdout.write(f"  - {f.name} (mtime: {f.stat().st_mtime:.0f})")

        # ---------------------------------------------------------------
        # 解析阶段
        # ---------------------------------------------------------------
        self.stdout.write("[Parse] 解析文件...")
        dfs = []
        for f in files:
            df = _parse_toa5_dynamically(f)
            if df is not None and not df.empty:
                dfs.append(df)
                self.stdout.write(f"  {f.name}: {len(df)} 行")
            else:
                self.stdout.write(f"  {f.name}: 无数据或文件为空")

        if not dfs:
            self.stdout.write(self.style.WARNING("[Parse] 所有文件均无有效数据，退出。"))
            return

        # ---------------------------------------------------------------
        # 合并与清洗阶段
        # ---------------------------------------------------------------
        self.stdout.write("[Merge] 合并文件并清洗...")
        df = _merge_and_clean(dfs)
        self.stdout.write(f"  合并后唯一记录: {len(df)} 条")

        if is_dry_run:
            self.stdout.write(self.style.WARNING("\n--- Dry-run 模式结束，未写入数据库 ---"))
            return

        # ---------------------------------------------------------------
        # 入库阶段
        # ---------------------------------------------------------------
        self.stdout.write("[DB] 导入新记录到数据库（只插入，不更新现有数据）...")
        stats = _import_new_records(df, self.stdout, self.style)

        self.stdout.write(self.style.SUCCESS(
            f"\n导入完成:\n"
            f"  文件总数:     {len(files)}\n"
            f"  唯一记录:     {stats['total_unique']}\n"
            f"  跳过已有:     {stats['skip_existing']}\n"
            f"  新写入记录:   {stats['records_created']}\n"
        ))
