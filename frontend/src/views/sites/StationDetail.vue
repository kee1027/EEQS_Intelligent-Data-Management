<template>
  <div class="whiterisk-theme">
    <header class="page-header">
      <div class="header-main">
        <nav class="breadcrumb">站点详细数据</nav>
        <h1>> {{ stationConfig.name }}</h1>
      </div>
      <div class="header-right">
        <el-button v-if="isSnowRoute" type="primary" plain size="mini" icon="el-icon-download" class="export-button"
          @click="exportStationData">
          导出站点数据
        </el-button>
      </div>
    </header>

    <main class="dashboard-content">
      <section class="top-section">
        <!-- 标准站点数据卡片 -->
        <div v-if="isStandardStation" class="data-grid">
          <div class="card info-card">
            <div class="card-header">站点信息</div>
            <div class="info-body">
              <div class="info-item">
                <span class="label">海拔</span>
                <span class="value">{{ stationConfig.altitude }}m</span>
              </div>
              <div class="info-item">
                <span class="label">类型</span>
                <span class="value">{{ stationConfig.type }}</span>
              </div>
              <div class="info-item">
                <span class="label">经纬度</span>
                <span class="value">{{ stationConfig.longitude }}°E, {{ stationConfig.latitude }}°N</span>
              </div>
            </div>
          </div>

          <div class="card data-card">
            <div class="card-header">积雪</div>
            <div class="data-body main-metric">
              <div class="primary">
                <span class="label">积雪深度</span>
                <div class="big-value">{{ latestData.snow_depth }} <span class="unit">cm</span></div>
              </div>
              <div class="secondary-metrics">
                <div class="sec-item"><span>雪密度</span> <strong>{{ latestData.density }} kg/m³</strong></div>
                <div class="sec-item"><span>雪水当量</span> <strong>{{ latestData.swe }} mm</strong></div>
              </div>
            </div>
          </div>

          <div class="card data-card">
            <div class="card-header">温度</div>
            <div class="data-body">
              <div class="metric-row">
                <i class="icon-temp"></i>
                <div class="flex-col">
                  <span class="label">气温</span>
                  <span class="mid-value" :class="{ cold: latestData.temp < 0 }">{{ latestData.temp }}° C</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- KKS 降雪站数据卡片 -->
        <div v-if="isSnowStation" class="data-grid">
          <div class="card info-card">
            <div class="card-header">站点信息</div>
            <div class="info-body">
              <div class="info-item">
                <span class="label">海拔</span>
                <span class="value">{{ stationConfig.altitude }}m</span>
              </div>
              <div class="info-item">
                <span class="label">类型</span>
                <span class="value">{{ stationConfig.type }}</span>
              </div>
              <div class="info-item">
                <span class="label">经纬度</span>
                <span class="value">{{ stationConfig.longitude }}°E, {{ stationConfig.latitude }}°N</span>
              </div>
            </div>
          </div>

          <div class="card data-card">
            <div class="card-header">USH-9雪深</div>
            <div class="data-body main-metric">
              <div class="primary">
                <span class="label">USH-9雪深</span>
                <div class="big-value">{{ latestData.ush9_snow_depth }} <span class="unit">cm</span></div>
              </div>
            </div>
          </div>

          <div class="card data-card">
            <div class="card-header">斜向观测带</div>
            <div class="data-body">
              <div class="sec-item"><span>冰含量</span> <strong>{{ latestData.oblique_ice_content }} %</strong></div>
              <div class="sec-item"><span>水含量</span> <strong>{{ latestData.oblique_water_content }} %</strong></div>
              <div class="sec-item"><span>雪密度</span> <strong>{{ latestData.oblique_snow_density }} kg/m³</strong></div>
            </div>
          </div>

          <div class="card data-card">
            <div class="card-header">水平观测带</div>
            <div class="data-body">
              <div class="sec-item"><span>冰含量</span> <strong>{{ latestData.horizontal_ice_content }} %</strong></div>
              <div class="sec-item"><span>水含量</span> <strong>{{ latestData.horizontal_water_content }} %</strong></div>
              <div class="sec-item"><span>雪密度</span> <strong>{{ latestData.horizontal_snow_density }} kg/m³</strong></div>
            </div>
          </div>

          <div class="card data-card">
            <div class="card-header">风吹雪平均通量</div>
            <div class="data-body">
              <div class="sec-item"><span>100cm</span> <strong>{{ latestData.snow_drift_flux_100cm }} g/(m²·s)</strong></div>
              <div class="sec-item"><span>200cm</span> <strong>{{ latestData.snow_drift_flux_200cm }} g/(m²·s)</strong></div>
            </div>
          </div>

          <div class="card data-card">
            <div class="card-header">平均风速</div>
            <div class="data-body">
              <div class="sec-item"><span>100cm</span> <strong>{{ latestData.wind_speed_100cm }} m/s</strong></div>
              <div class="sec-item"><span>200cm</span> <strong>{{ latestData.wind_speed_200cm }} m/s</strong></div>
            </div>
          </div>
        </div>

        <div class="card map-card">
          <div class="map-placeholder" :class="{ 'has-photo': stationImage }">
            <img v-if="stationImage" :src="stationImage" :alt="stationConfig.name + '实况图'" class="station-photo" />
            <div class="map-overlay">
              <span>{{ stationConfig.longitude }}°E, {{ stationConfig.latitude }}°N</span>
            </div>
          </div>
        </div>
      </section>

      <section class="chart-filter-section">
        <div class="card filter-card">
          <div class="card-header">图表时间范围</div>
          <div class="filter-body">
            <div class="filter-item">
              <el-date-picker
                v-model="chartRange"
                type="datetimerange"
                format="yyyy-MM-dd HH:mm:ss"
                :picker-options="{ shortcuts: pickerShortcuts }"
                @change="handleRangeChange"
                start-placeholder="开始时间"
                end-placeholder="结束时间"
              />
            </div>
            <el-button size="mini" @click="loadAllData">查看全部</el-button>
          </div>
        </div>
      </section>

      <!-- 标准站点图表 -->
      <section v-if="isStandardStation" class="charts-section">
        <div class="card chart-card">
          <div class="card-header">气温 摄氏度</div>
          <div ref="airTempChart" class="chart-container"></div>
        </div>

        <div class="card chart-card">
          <div class="card-header">空气相对湿度</div>
          <div ref="airHumidityChart" class="chart-container"></div>
        </div>

        <div class="card chart-card">
          <div class="card-header">风速 (m/s)</div>
          <div ref="windSpeedChart" class="chart-container"></div>
        </div>

        <div class="card chart-card">
          <div class="card-header">土壤水分 (%)</div>
          <div ref="soilMoistureChart" class="chart-container"></div>
        </div>

        <div class="card chart-card">
          <div class="card-header">土壤温度℃</div>
          <div ref="soilTempChart" class="chart-container"></div>
        </div>
      </section>

      <!-- KKS 降雪站图表 -->
      <section v-if="isSnowStation" class="charts-section">
        <div class="card chart-card">
          <div class="card-header">USH-9雪深 (cm)</div>
          <div ref="ush9Chart" class="chart-container"></div>
        </div>

        <div class="card chart-card">
          <div class="card-header">斜向观测带冰含量 (%)</div>
          <div ref="obliqueIceChart" class="chart-container"></div>
        </div>

        <div class="card chart-card">
          <div class="card-header">斜向观测带水含量 (%)</div>
          <div ref="obliqueWaterChart" class="chart-container"></div>
        </div>

        <div class="card chart-card">
          <div class="card-header">水平观测带冰含量 (%)</div>
          <div ref="horizontalIceChart" class="chart-container"></div>
        </div>

        <div class="card chart-card">
          <div class="card-header">水平观测带水含量 (%)</div>
          <div ref="horizontalWaterChart" class="chart-container"></div>
        </div>

        <div class="card chart-card">
          <div class="card-header">风吹雪平均通量</div>
          <div ref="snowDriftFluxChart" class="chart-container"></div>
        </div>

        <div class="card chart-card">
          <div class="card-header">平均风速 (m/s)</div>
          <div ref="windSpeedChart" class="chart-container"></div>
        </div>
      </section>
    </main>
  </div>
</template>

<script>
import * as echarts from 'echarts';
import { getWeatherData } from '@/api/dashboard';
import {
  STATION_CONFIG,
  STANDARD_FIELDS,
  SNOW_FIELDS,
  STANDARD_CHARTS,
  SNOW_CHARTS
} from '@/views/sites/station-config';

export default {
  name: 'StationDetail',
  data() {
    return {
      latestData: {
        // 标准站点字段
        snow_depth: '-', temp: '-', swe: '-', density: '-',
        // 降雪站字段
        ush9_snow_depth: '-', oblique_ice_content: '-', oblique_water_content: '-',
        oblique_snow_density: '-', horizontal_ice_content: '-', horizontal_water_content: '-',
        horizontal_snow_density: '-', snow_drift_flux_100cm: '-', snow_drift_flux_200cm: '-',
        wind_speed_100cm: '-', wind_speed_200cm: '-',
        timestamp: ''
      },
      // 定时刷新定时器
      refreshTimer: null,
      // 刷新间隔（毫秒）
      refreshInterval: 300000, // 5分钟
      // 图表实例
      charts: {},
      // 图表数据
      chartData: {},
      rawData: [],
      chartRecords: [],
      chartDisplayRecords: [],
      // 时间选择器范围（[Date, Date]）
      chartRange: null,
      // 前端数据缓存
      dataCache: new Map(),
      // 当前缓存范围
      loadedRange: { start: null, end: null },
      // 用于取消之前的请求（AbortController）
      pendingRequest: null,
      // resize 防抖定时器
      resizeTimer: null,
      // 快捷选项
      pickerShortcuts: [
        { text: '最近1天', onClick(picker) { const end = new Date(); const start = new Date(end.getTime() - 86400000); picker.$emit('pick', [start, end]); }},
        { text: '最近7天', onClick(picker) { const end = new Date(); const start = new Date(end.getTime() - 7 * 86400000); picker.$emit('pick', [start, end]); }},
        { text: '最近30天', onClick(picker) { const end = new Date(); const start = new Date(end.getTime() - 30 * 86400000); picker.$emit('pick', [start, end]); }},
        { text: '最近90天', onClick(picker) { const end = new Date(); const start = new Date(end.getTime() - 90 * 86400000); picker.$emit('pick', [start, end]); }},
        { text: '今年', onClick(picker) { const end = new Date(); const start = new Date(end.getFullYear(), 0, 1); picker.$emit('pick', [start, end]); }},
        { text: '全部', onClick(picker) { picker.$emit('pick', [null, null]); }}
      ]
    };
  },
  computed: {
    stationConfig() {
      const stationId = this.$route.meta.stationId;
      return STATION_CONFIG[stationId] || STATION_CONFIG.KW;
    },
    isStandardStation() {
      return this.stationConfig.fields === 'standard';
    },
    isSnowStation() {
      return this.stationConfig.fields === 'snow';
    },
    isSnowRoute() {
      return this.$route && this.$route.path.indexOf('/snow/') === 0;
    },
    stationImage() {
      return this.stationConfig.photo || null;
    }
  },
  mounted() {
    // 使用 requestAnimationFrame 延迟初始化，确保 Vue <transition> 动画完成后 DOM 尺寸已稳定
    this.$nextTick(() => {
      requestAnimationFrame(() => {
        this.initCharts();
        // 默认加载最近7天
        const end = new Date();
        const start = new Date(end.getTime() - 7 * 86400000);
        this.chartRange = [start, end];
        this.fetchDataByRange(start, end);
      });
    });
    window.addEventListener('resize', this.handleResize);
    // 启动定时刷新
    this.refreshTimer = setInterval(() => {
      this.refreshData();
    }, this.refreshInterval);
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.handleResize);
    // 清除 resize 防抖定时器
    if (this.resizeTimer) {
      clearTimeout(this.resizeTimer);
      this.resizeTimer = null;
    }
    // 清除定时器
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
      this.refreshTimer = null;
    }
    // 取消未完成的请求
    if (this.pendingRequest) {
      this.pendingRequest.abort();
      this.pendingRequest = null;
    }
    // 销毁所有图表
    Object.values(this.charts).forEach(chart => {
      if (chart) chart.dispose();
    });
  },
  methods: {
    // 将 Date 转为 ISO 8601 字符串（UTC）
    toISOString(date) {
      if (!date) return null;
      return date.toISOString();
    },

    getFieldDisplayName(field) {
      if (field.startsWith('vwc_soil_') || field.startsWith('t_soil_')) {
        return field.replace(/^(vwc_soil_|t_soil_)/, '');
      }
      if (field.endsWith('_100cm')) return '100cm';
      if (field.endsWith('_200cm')) return '200cm';
      return field;
    },

    // 计算动态的 axisLabel interval，确保显示约20个标签
    calculateAxisInterval(chart, dataZoomStart, dataZoomEnd) {
      const totalPoints = this.chartDisplayRecords.length;
      if (!totalPoints) return 0;
      const visibleRatio = Math.max(0.05, (dataZoomEnd - dataZoomStart) / 100);
      const visiblePoints = Math.max(1, Math.round(totalPoints * visibleRatio));
      const chartWidth = chart && chart.getWidth ? chart.getWidth() : 1200;
      const targetLabels = Math.max(6, Math.floor(chartWidth / 120));
      const interval = Math.max(0, Math.ceil(visiblePoints / targetLabels) - 1);
      return interval;
    },

    // 更新图表的横轴标签间隔
    updateAxisInterval(chart, dataZoomStart, dataZoomEnd) {
      if (chart) {
        const interval = this.calculateAxisInterval(chart, dataZoomStart, dataZoomEnd);
        chart.setOption({
          xAxis: {
            axisLabel: {
              fontSize: 10,
              interval: interval,
              hideOverlap: true,
              rotate: interval > 5 ? 45 : 0
            }
          }
        });
      }
    },

    // 格式化图表横轴时间戳（纯字符串拼接，避免昂贵的 Intl API 调用）
    formatChartAxisTimestamp(date) {
      const pad = value => String(value).padStart(2, '0');
      return `${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
    },

    // 初始化所有图表（不预生成时间轴，只初始化图表骨架）
    initCharts() {
      const chartConfigs = this.isStandardStation ? STANDARD_CHARTS : SNOW_CHARTS;
      chartConfigs.forEach(config => {
        if (config.multi) {
          const seriesConfig = config.fields.map((field, index) => ({
            name: this.getFieldDisplayName(field),
            color: config.colors[index]
          }));
          this.charts[config.ref] = this.createMultiSeriesChart(config.ref, config.title, seriesConfig);
        } else {
          this.charts[config.ref] = this.createChart(config.ref, config.title, config.color);
        }
      });
    },

    // 创建单系列图表 —— 添加 DOM 存在性检查，初始化后自动 resize 确保尺寸正确
    createChart(ref, yAxisName, color) {
      const dom = this.$refs[ref];
      if (!dom) {
        console.warn(`[StationDetail] Chart DOM ref "${ref}" not found, skipping initialization`);
        return null;
      }
      const chart = echarts.init(dom);
      const initialInterval = this.calculateAxisInterval(chart, 0, 100);
      chart.setOption({
        tooltip: {
          trigger: 'axis',
          textStyle: { fontSize: 12 }
        },
        grid: { left: '8%', right: '5%', bottom: '15%', top: '10%', containLabel: true },
        dataZoom: [
          {
            type: 'slider',
            show: true,
            xAxisIndex: 0,
            start: 0,
            end: 100,
            height: 20,
            bottom: 5
          },
          {
            type: 'inside',
            xAxisIndex: 0,
            start: 0,
            end: 100
          }
        ],
        xAxis: {
          type: 'category',
          data: [],
          axisLabel: { fontSize: 10, interval: initialInterval, hideOverlap: true, rotate: initialInterval > 5 ? 45 : 0 },
          axisLine: { lineStyle: { color: '#e5e7eb' } }
        },
        yAxis: {
          type: 'value',
          name: yAxisName,
          nameTextStyle: { fontSize: 11 },
          axisLabel: {
            fontSize: 10,
            formatter: (value) => value.toFixed(3)
          },
          axisLine: { lineStyle: { color: '#e5e7eb' } },
          splitLine: { lineStyle: { type: 'dashed', color: '#f3f4f6' } },
          scale: true
        },
        series: [{
          data: [],
          type: 'line',
          smooth: true,
          color: color,
          lineStyle: { width: 2 },
          symbol: 'circle',
          symbolSize: 4,
          connectNulls: false
        }]
      });

      // 初始化后立即 resize，确保 transition 后容器尺寸正确
      this.$nextTick(() => chart.resize());

      // 监听 dataZoom 变化，动态调整横轴标签
      chart.on('dataZoom', (params) => {
        let start = 0, end = 100;
        if (params.batch && params.batch[0]) {
          start = params.batch[0].start;
          end = params.batch[0].end;
        } else if (params.start !== undefined) {
          start = params.start;
          end = params.end;
        }
        this.updateAxisInterval(chart, start, end);
      });

      return chart;
    },

    // 创建多系列图表 —— 同样添加 DOM 检查与 resize
    createMultiSeriesChart(ref, yAxisName, seriesConfig) {
      const dom = this.$refs[ref];
      if (!dom) {
        console.warn(`[StationDetail] Chart DOM ref "${ref}" not found, skipping initialization`);
        return null;
      }
      const chart = echarts.init(dom);
      const initialInterval = this.calculateAxisInterval(chart, 0, 100);
      chart.setOption({
        tooltip: {
          trigger: 'axis',
          textStyle: { fontSize: 12 }
        },
        legend: {
          data: seriesConfig.map(s => s.name),
          top: 0,
          textStyle: { fontSize: 10 }
        },
        grid: { left: '8%', right: '5%', bottom: '20%', top: '18%', containLabel: true },
        dataZoom: [
          {
            type: 'slider',
            show: true,
            xAxisIndex: 0,
            start: 0,
            end: 100,
            height: 20,
            bottom: 5
          },
          {
            type: 'inside',
            xAxisIndex: 0,
            start: 0,
            end: 100
          }
        ],
        xAxis: {
          type: 'category',
          data: [],
          axisLabel: { fontSize: 10, interval: initialInterval, hideOverlap: true, rotate: initialInterval > 5 ? 45 : 0 },
          axisLine: { lineStyle: { color: '#e5e7eb' } }
        },
        yAxis: {
          type: 'value',
          name: yAxisName,
          nameTextStyle: { fontSize: 11 },
          axisLabel: {
            fontSize: 10,
            formatter: (value) => value.toFixed(3)
          },
          axisLine: { lineStyle: { color: '#e5e7eb' } },
          splitLine: { lineStyle: { type: 'dashed', color: '#f3f4f6' } },
          scale: true
        },
        series: seriesConfig.map(s => ({
          name: s.name,
          data: [],
          type: 'line',
          smooth: true,
          color: s.color,
          lineStyle: { width: 2 },
          symbol: 'circle',
          symbolSize: 4,
          connectNulls: false
        }))
      });

      // 初始化后立即 resize
      this.$nextTick(() => chart.resize());

      // 监听 dataZoom 变化，动态调整横轴标签
      chart.on('dataZoom', (params) => {
        let start = 0, end = 100;
        if (params.batch && params.batch[0]) {
          start = params.batch[0].start;
          end = params.batch[0].end;
        } else if (params.start !== undefined) {
          start = params.start;
          end = params.end;
        }
        this.updateAxisInterval(chart, start, end);
      });

      return chart;
    },

    // 根据时间范围获取数据（带缓存）
    async fetchDataByRange(start, end) {
      // 取消之前的请求
      if (this.pendingRequest) {
        this.pendingRequest.abort();
        this.pendingRequest = null;
      }

      const reqStart = start ? start.getTime() : null;
      const reqEnd = end ? end.getTime() : null;

      // 检查缓存是否完全覆盖请求范围
      if (this.loadedRange.start && this.loadedRange.end && reqStart && reqEnd) {
        const cacheStart = this.loadedRange.start.getTime();
        const cacheEnd = this.loadedRange.end.getTime();
        if (reqStart >= cacheStart && reqEnd <= cacheEnd) {
          // 完全覆盖，直接前端过滤
          this.filterAndRenderFromCache(reqStart, reqEnd);
          return;
        }
      }

      // 构建请求参数
      const params = {
        station__name: this.stationConfig.apiName,
        ordering: 'timestamp'
      };
      if (reqStart) {
        params.timestamp__gte = this.toISOString(new Date(reqStart));
      }
      if (reqEnd) {
        params.timestamp__lte = this.toISOString(new Date(reqEnd));
      }

      const controller = new AbortController();
      this.pendingRequest = controller;

      try {
        const res = await getWeatherData(params, { signal: controller.signal });
        const data = Array.isArray(res.data) ? res.data : [];

        // 按时间排序并处理
        const sortedData = data
          .map(item => {
            const timestampDate = new Date(item.timestamp);
            return Object.assign({}, item, { timestampDate });
          })
          .filter(item => !isNaN(item.timestampDate.getTime()))
          .sort((a, b) => a.timestampDate - b.timestampDate);

        this.rawData = sortedData;
        this.chartRecords = sortedData;

        // 更新缓存
        if (sortedData.length > 0) {
          const newStart = sortedData[0].timestampDate;
          const newEnd = sortedData[sortedData.length - 1].timestampDate;
          if (this.loadedRange.start && this.loadedRange.end) {
            // 扩展缓存范围
            this.loadedRange.start = new Date(Math.min(this.loadedRange.start.getTime(), newStart.getTime()));
            this.loadedRange.end = new Date(Math.max(this.loadedRange.end.getTime(), newEnd.getTime()));
          } else {
            this.loadedRange.start = newStart;
            this.loadedRange.end = newEnd;
          }
          // 存入缓存
          sortedData.forEach(item => {
            this.dataCache.set(item.timestamp, item);
          });
        }

        // 提取最新数据更新 latestData
        if (sortedData.length > 0) {
          const latest = sortedData[sortedData.length - 1];
          this.latestData = this.buildLatestData(latest, latest.timestampDate);
        }

        // 更新图表
        this.updateChartsWithData(sortedData);

        // 数据加载完成后，统一 resize 所有图表（确保 transition 后尺寸正确）
        this.$nextTick(() => {
          Object.values(this.charts).forEach(chart => {
            if (chart) chart.resize();
          });
        });
      } catch (e) {
        if (e.name === 'AbortError') {
          console.log('请求已取消');
          return;
        }
        console.error('获取数据失败:', e);
      } finally {
        if (this.pendingRequest === controller) {
          this.pendingRequest = null;
        }
      }
    },

    // 从缓存中过滤并渲染
    filterAndRenderFromCache(startTime, endTime) {
      const filtered = this.chartRecords.filter(item => {
        const time = item.timestampDate.getTime();
        return time >= startTime && time <= endTime;
      });
      this.updateChartsWithData(filtered);
    },

    // 用数据更新图表（动态构建时间轴）
    updateChartsWithData(records) {
      this.chartDisplayRecords = records;
      const timeAxis = records.map(item => this.formatChartAxisTimestamp(item.timestampDate));

      const chartConfigs = this.isStandardStation ? STANDARD_CHARTS : SNOW_CHARTS;
      const seriesData = {};

      chartConfigs.forEach(config => {
        if (config.multi) {
          seriesData[config.ref] = config.fields.map(field =>
            records.map(item => item[field] != null ? Math.round(item[field] * 1000) / 1000 : null)
          );
        } else {
          seriesData[config.ref] = records.map(item => item[config.field] != null ? Math.round(item[config.field] * 1000) / 1000 : null);
        }
      });

      chartConfigs.forEach(config => {
        const chart = this.charts[config.ref];
        if (!chart) return;
        const interval = this.calculateAxisInterval(chart, 0, 100);
        if (config.multi) {
          chart.setOption({
            xAxis: {
              data: timeAxis,
              axisLabel: {
                fontSize: 10,
                interval: interval,
                hideOverlap: true,
                rotate: interval > 5 ? 45 : 0
              }
            },
            series: seriesData[config.ref].map(data => ({ data: data }))
          });
        } else {
          chart.setOption({
            xAxis: {
              data: timeAxis,
              axisLabel: {
                fontSize: 10,
                interval: interval,
                hideOverlap: true,
                rotate: interval > 5 ? 45 : 0
              }
            },
            series: [{ data: seriesData[config.ref] }]
          });
        }
      });
    },

    // 处理时间范围变化
    async handleRangeChange() {
      if (!this.chartRange || !this.chartRange[0] || !this.chartRange[1]) {
        await this.loadAllData();
        return;
      }
      const [start, end] = this.chartRange;
      await this.fetchDataByRange(start, end);
    },

    // 加载全部数据
    async loadAllData() {
      this.chartRange = [null, null];
      await this.fetchDataByRange(null, null);
    },

    // 刷新数据（定时器调用）
    async refreshData() {
      if (this.chartRange && this.chartRange[0] && this.chartRange[1]) {
        await this.fetchDataByRange(this.chartRange[0], this.chartRange[1]);
      } else {
        await this.loadAllData();
      }
    },

    buildLatestData(latest, latestDate) {
      const base = {
        timestamp: latestDate.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false })
      };
      if (this.isStandardStation) {
        return {
          ...base,
          snow_depth: latest.snow_depth != null ? latest.snow_depth : '-',
          temp: latest.ta != null ? Math.round(latest.ta * 1000) / 1000 : '-',
          swe: latest.swe != null ? latest.swe : '-',
          density: latest.snow_density != null ? latest.snow_density : '-',
          ush9_snow_depth: '-', oblique_ice_content: '-', oblique_water_content: '-',
          oblique_snow_density: '-', horizontal_ice_content: '-', horizontal_water_content: '-',
          horizontal_snow_density: '-', snow_drift_flux_100cm: '-', snow_drift_flux_200cm: '-',
          wind_speed_100cm: '-', wind_speed_200cm: '-'
        };
      } else {
        return {
          ...base,
          ush9_snow_depth: latest.ush9_snow_depth != null ? latest.ush9_snow_depth : '-',
          oblique_ice_content: latest.oblique_ice_content != null ? latest.oblique_ice_content : '-',
          oblique_water_content: latest.oblique_water_content != null ? latest.oblique_water_content : '-',
          oblique_snow_density: latest.oblique_snow_density != null ? latest.oblique_snow_density : '-',
          horizontal_ice_content: latest.horizontal_ice_content != null ? latest.horizontal_ice_content : '-',
          horizontal_water_content: latest.horizontal_water_content != null ? latest.horizontal_water_content : '-',
          horizontal_snow_density: latest.horizontal_snow_density != null ? latest.horizontal_snow_density : '-',
          snow_drift_flux_100cm: latest.snow_drift_flux_100cm != null ? latest.snow_drift_flux_100cm : '-',
          snow_drift_flux_200cm: latest.snow_drift_flux_200cm != null ? latest.snow_drift_flux_200cm : '-',
          wind_speed_100cm: latest.wind_speed_100cm != null ? latest.wind_speed_100cm : '-',
          wind_speed_200cm: latest.wind_speed_200cm != null ? latest.wind_speed_200cm : '-',
          snow_depth: '-', temp: '-', swe: '-', density: '-'
        };
      }
    },

    // 更新单系列图表
    updateChart(chart, data) {
      if (chart) {
        const interval = this.calculateAxisInterval(chart, 0, 100);
        chart.setOption({
          xAxis: {
            data: this.timeAxis,
            axisLabel: {
              fontSize: 10,
              interval: interval,
              hideOverlap: true,
              rotate: interval > 5 ? 45 : 0
            }
          },
          series: [{ data: data }]
        });
      }
    },

    // 更新多系列图表
    updateMultiSeriesChart(chart, dataArray) {
      if (chart) {
        const interval = this.calculateAxisInterval(chart, 0, 100);
        chart.setOption({
          xAxis: {
            data: this.timeAxis,
            axisLabel: {
              fontSize: 10,
              interval: interval,
              hideOverlap: true,
              rotate: interval > 5 ? 45 : 0
            }
          },
          series: dataArray.map(data => ({ data: data }))
        });
      }
    },

    formatExportValue(value) {
      if (value == null || value === '') return '-';
      if (typeof value === 'number') return Number.isFinite(value) ? value.toFixed(3).replace(/\.?0+$/, '') : '-';
      if (value instanceof Date) return value.toLocaleString('zh-CN');
      return String(value);
    },

    async exportStationData() {
      let exportData = [];

      // 优先使用缓存数据
      if (this.rawData && this.rawData.length > 0) {
        exportData = this.rawData;
      } else {
        try {
          const res = await getWeatherData({
            station__name: this.stationConfig.apiName,
            ordering: '-timestamp',
            limit: 10000
          });
          exportData = Array.isArray(res.data) ? res.data : [];
        } catch (error) {
          console.error('导出站点数据失败:', error);
          this.$message.error('导出站点数据失败');
          return;
        }
      }

      if (!exportData.length) {
        this.$message.warning('暂无可导出的站点数据');
        return;
      }

      let preferredFields;
      let fieldLabels;

      if (this.isStandardStation) {
        preferredFields = [
          'timestamp',
          'station__name',
          'snow_depth',
          'swe',
          'ta',
          'rh',
          'ws',
          'snow_density',
          'vwc_soil_10cm',
          'vwc_soil_20cm',
          'vwc_soil_40cm',
          'vwc_soil_60cm',
          'vwc_soil_100cm',
          't_soil_10cm',
          't_soil_20cm',
          't_soil_40cm',
          't_soil_60cm',
          't_soil_100cm'
        ];
        fieldLabels = {
          timestamp: '时间',
          station__name: '站点',
          snow_depth: '积雪深度(cm)',
          swe: '雪水当量(mm)',
          ta: '气温(°C)',
          rh: '相对湿度(%)',
          ws: '风速(m/s)',
          snow_density: '雪密度(kg/m³)',
          vwc_soil_10cm: '土壤水分10cm(%)',
          vwc_soil_20cm: '土壤水分20cm(%)',
          vwc_soil_40cm: '土壤水分40cm(%)',
          vwc_soil_60cm: '土壤水分60cm(%)',
          vwc_soil_100cm: '土壤水分100cm(%)',
          t_soil_10cm: '土壤温度10cm(°C)',
          t_soil_20cm: '土壤温度20cm(°C)',
          t_soil_40cm: '土壤温度40cm(°C)',
          t_soil_60cm: '土壤温度60cm(°C)',
          t_soil_100cm: '土壤温度100cm(°C)'
        };
      } else {
        preferredFields = [
          'timestamp',
          'station__name',
          'ush9_snow_depth',
          'oblique_ice_content',
          'oblique_water_content',
          'oblique_snow_density',
          'horizontal_ice_content',
          'horizontal_water_content',
          'horizontal_snow_density',
          'snow_drift_flux_100cm',
          'snow_drift_flux_200cm',
          'wind_speed_100cm',
          'wind_speed_200cm'
        ];
        fieldLabels = {
          timestamp: '时间',
          station__name: '站点',
          ush9_snow_depth: 'USH-9雪深(cm)',
          oblique_ice_content: '斜向观测带冰含量(%)',
          oblique_water_content: '斜向观测带水含量(%)',
          oblique_snow_density: '斜向观测带雪密度(kg/m³)',
          horizontal_ice_content: '水平观测带冰含量(%)',
          horizontal_water_content: '水平观测带水含量(%)',
          horizontal_snow_density: '水平观测带雪密度(kg/m³)',
          snow_drift_flux_100cm: '100cm风吹雪平均通量(g/(m²·s))',
          snow_drift_flux_200cm: '200cm风吹雪平均通量(g/(m²·s))',
          wind_speed_100cm: '100cm平均风速(m/s)',
          wind_speed_200cm: '200cm平均风速(m/s)'
        };
      }

      const allFields = Array.from(
        new Set([
          ...preferredFields,
          ...exportData.reduce((keys, row) => keys.concat(Object.keys(row || {})), [])
        ])
      );

      const rows = exportData.map(row => allFields.map(field => this.formatExportValue(row[field])));
      const summaryRows = [
        ['站点名称', this.stationConfig.name],
        ['导出时间', new Date().toLocaleString('zh-CN')],
        ['数据条数', String(exportData.length)],
        ['数据来源', '后端站点数据接口']
      ];

      const escapeHtml = value => String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
      const toRow = cells => `<tr>${cells.map(cell => `<td>${escapeHtml(cell)}</td>`).join('')}</tr>`;
      const headerRow = allFields.map(field => `<th>${escapeHtml(fieldLabels[field] || field)}</th>`).join('');
      const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <style>
    body { font-family: "Microsoft YaHei", Arial, sans-serif; }
    .title { font-size: 18px; font-weight: 700; margin: 0 0 12px; }
    table { border-collapse: collapse; width: 100%; margin-bottom: 16px; }
    th, td { border: 1px solid #d9e2ec; padding: 8px 10px; text-align: left; }
    th { background: #eef4fb; }
  </style>
</head>
<body>
  <div class="title">${this.stationConfig.name}站点数据导出</div>
  <table>
    <tr><th>字段</th><th>值</th></tr>
    ${summaryRows.map(row => toRow(row)).join('')}
  </table>
  <table>
    <tr>${headerRow}</tr>
    ${rows.map(row => toRow(row)).join('')}
  </table>
</body>
</html>`;

      const blob = new Blob(['\ufeff', html], {
        type: 'application/vnd.ms-excel;charset=utf-8'
      });
      const link = document.createElement('a');
      const url = window.URL.createObjectURL(blob);
      link.href = url;
      link.download = `${this.stationConfig.name}_站点数据.xls`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    },

    // 处理窗口大小变化 —— 添加 200ms 防抖，避免频繁触发 resize
    handleResize() {
      if (this.resizeTimer) clearTimeout(this.resizeTimer);
      this.resizeTimer = setTimeout(() => {
        Object.values(this.charts).forEach(chart => {
          if (chart) chart.resize();
        });
        this.refreshChartAxisLabels();
      }, 200);
    },

    refreshChartAxisLabels() {
      Object.values(this.charts).forEach(chart => {
        if (chart) this.updateAxisInterval(chart, 0, 100);
      });
    }
  }
};
</script>

<style scoped>
@import '~@/styles/station-page.scss';
</style>
