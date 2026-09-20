# 导入所需的库
import re
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
DATA_MAIN_FILE = Path(r"C:\Users\Administrator\Documents\kimi\Workspaces\RAG数据库\import_data\两河源北斗接收_Data_Receive.dat")
DATA_BACKUP_FILE = Path(r"C:\Users\Administrator\Documents\kimi\Workspaces\RAG数据库\import_data\两河源北斗接收_Data_Receive.dat.backup")

# ---------------------------------------------------------------------------
# 已知站点清单
# ---------------------------------------------------------------------------
# 站点列块不再靠「首列/末列」硬编码圈定，而是按列名前缀（如 KW_、HSZ_）
# 动态识别——新增站点（如 HSZ、HL）无需改代码即可自动导入。
# 本清单的用途是「缺失标记」：已知站点在文件中缺席时仅标记、不报错，
# 站点记录保留在数据库中（历史数据不删除）。
KNOWN_STATIONS = [
    'HXC', 'KW', 'JG', 'KYE', 'KKSLS', 'KKSLM', 'AKSL', 'SDHZ', 'HSZ', 'HL',
]

# 站点列名前缀：一个或多个大写字母 + 下划线（如 KW_Batt_volt → KW）。
# 混合大小写的非站点列（Batt_volt_Self_Avg、PTemp_Self_Avg、Send_TimeStamp(n)）
# 不会匹配，安全。
STATION_PREFIX_RE = re.compile(r'^([A-Z]+)_')


# ---------------------------------------------------------------------------
# 站点列块识别
# ---------------------------------------------------------------------------
def _group_station_columns(all_columns: list[str]) -> dict[str, list[int]]:
    """
    按列名前缀把列分组为站点块，返回 {站点前缀: [起始列索引, 结束列索引]}。

    站点块在 TOA5 文件中是连续的（站点自己的 Header 列开头），
    因此取该前缀出现的最小/最大索引即可圈定范围；块内夹杂的
    ID(n)、Send_TimeStamp(n) 等公共列会在字段映射阶段被自然丢弃。
    """
    blocks: dict[str, list[int]] = {}
    for idx, col in enumerate(all_columns):
        m = STATION_PREFIX_RE.match(col)
        if not m:
            continue
        prefix = m.group(1)
        if prefix in blocks:
            blocks[prefix][1] = idx
        else:
            blocks[prefix] = [idx, idx]
    return blocks


# ---------------------------------------------------------------------------
# 解析 TOA5 文件（单文件）
# ---------------------------------------------------------------------------
def _parse_toa5_dynamically(file_path: Path) -> tuple[pd.DataFrame | None, dict]:
    """
    动态解析 TOA5 宽格式文件，返回 (长格式 DataFrame, 解析报告 dict)。
    如果文件不存在或为空，返回 (None, {})。

    解析报告包含：
      - stations_found:   文件中实际出现的站点前缀
      - new_stations:     不在 KNOWN_STATIONS 中的新站点（会自动导入）
      - missing_stations: 已知但本次文件缺席的站点（标缺失，不报错）
      - dropped_columns:  无法映射到模型字段而被丢弃的列名
    """
    if not file_path.exists():
        return None, {}

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

    station_blocks = _group_station_columns(all_columns)
    stations_found = sorted(station_blocks.keys())
    report = {
        'stations_found': stations_found,
        'new_stations': [s for s in stations_found if s not in KNOWN_STATIONS],
        'missing_stations': [s for s in KNOWN_STATIONS if s not in station_blocks],
        'dropped_columns': [],
    }

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
    dropped = set()

    for _, row in df_wide.iterrows():
        timestamp = row['TIMESTAMP']
        for station_prefix, (start_idx, end_idx) in station_blocks.items():
            station_data_slice = row[start_idx:end_idx + 1]
            new_row = {'timestamp': timestamp, 'station_name': station_prefix}
            for col_name, value in station_data_slice.items():
                if not col_name.startswith(station_prefix + '_'):
                    continue  # 块内夹杂的 ID(n) / Send_TimeStamp(n) 等公共列
                base_name = col_name.replace(station_prefix + '_', '', 1).lower()
                if base_name in model_field_names:
                    new_row[base_name] = value
                else:
                    dropped.add(col_name)
            processed_rows.append(new_row)

    report['dropped_columns'] = sorted(dropped)
    return (pd.DataFrame(processed_rows) if processed_rows else None), report


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
    stations = {}
    created_stations = []
    for name in station_names:
        station_obj, created = Station.objects.get_or_create(name=name)
        stations[name] = station_obj
        if created:
            created_stations.append(name)

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
        'created_stations': created_stations,
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
        all_new_stations: set[str] = set()
        all_missing_stations: set[str] = set()
        all_dropped_columns: set[str] = set()
        for f in files:
            df, report = _parse_toa5_dynamically(f)
            if df is not None and not df.empty:
                dfs.append(df)
                self.stdout.write(f"  {f.name}: {len(df)} 行")
            else:
                self.stdout.write(f"  {f.name}: 无数据或文件为空")
            if report:
                self.stdout.write(f"    站点: {', '.join(report['stations_found']) or '无'}")
                if report['new_stations']:
                    all_new_stations.update(report['new_stations'])
                    self.stdout.write(self.style.WARNING(
                        f"    新增站点（自动导入）: {', '.join(report['new_stations'])}"
                    ))
                if report['missing_stations']:
                    all_missing_stations.update(report['missing_stations'])
                    self.stdout.write(self.style.WARNING(
                        f"    缺失站点（本次无数据，已标记）: {', '.join(report['missing_stations'])}"
                    ))
                if report['dropped_columns']:
                    all_dropped_columns.update(report['dropped_columns'])

        if not dfs:
            self.stdout.write(self.style.WARNING("[Parse] 所有文件均无有效数据，退出。"))
            return

        if all_dropped_columns:
            self.stdout.write(self.style.WARNING(
                f"  以下列无法映射到模型字段，已丢弃: {', '.join(sorted(all_dropped_columns))}"
            ))

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
        if stats['created_stations']:
            self.stdout.write(self.style.WARNING(
                f"  新建站点:     {', '.join(stats['created_stations'])}"
            ))
        if all_missing_stations:
            self.stdout.write(self.style.WARNING(
                f"  缺失站点:     {', '.join(sorted(all_missing_stations))}（本次文件无数据，站点保留）"
            ))

        # ---------------------------------------------------------------
        # 聚合阶段：导入后重算涉及时间范围的日/小时聚合，保证下游
        # （AI 问答、预测流水线、聚合 API）读到最新数据
        # ---------------------------------------------------------------
        if stats['records_created'] > 0:
            from data.aggregation import aggregate_range

            self.stdout.write("[Aggregate] 重算日/小时聚合...")
            agg_stats = aggregate_range(df['timestamp'].min(), df['timestamp'].max())
            self.stdout.write(
                f"  日聚合 {agg_stats['daily_rows']} 行, 小时聚合 {agg_stats['hourly_rows']} 行"
            )
