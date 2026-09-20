<template>
  <!-- 模板部分不变 -->
  <div class="right-panel">
    <div class="card-container">
      <h3 class="card-title">径流观测数据</h3>
      <div ref="runoffChart" class="chart-container"></div>
    </div>
    <div class="card-container">
      <h3 class="card-title">积雪观测数据</h3>
      <div ref="snowChart" class="chart-container"></div>
    </div>
    <div class="card-container">
      <h3 class="card-title">径流预测数据</h3>
      <div ref="forecastChart" class="chart-container"></div>
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts';
import { getWeatherData } from '@/api/dashboard';

export default {
  name: 'RightPanel',
  data() {
    return {
      runoffChart: null,
      snowChart: null,
      forecastChart: null,
      runoffData: [],
      snowData: [],
      forecastData: [],
      dataPollingInterval: null,
      isFetching: false,
      // 固定时间滚动：显示最近7天数据，每半小时一个点
      // 7天 * 24小时 * 2 = 336个数据点
      maxDataPoints: 336,
      // 新增：纵轴最小保底区间（可根据需求调整，比如5、10）
      minAxisRange: 5
    }
  },
  mounted() {
    this.fetchChartData();
    this.dataPollingInterval = setInterval(this.fetchChartData, 5000);
    window.addEventListener('resize', this.resizeCharts);
  },
  beforeDestroy() {
    clearInterval(this.dataPollingInterval);
    window.removeEventListener('resize', this.resizeCharts);
    [this.runoffChart, this.snowChart, this.forecastChart].forEach(chart => chart && chart.dispose());
  },
  methods: {
    // 核心修改：纵轴范围计算（加保底区间）
    getAxisRange(dataList, field) {
      const values = dataList.map(item => item[field]).filter(val => val !== null && val !== undefined);
      if (values.length === 0) return { min: 0, max: this.minAxisRange };

      // 1. 计算数据本身的极值
      const dataMin = Math.min(...values);
      const dataMax = Math.max(...values);
      const dataRange = dataMax - dataMin;

      // 2. 如果数据波动小于保底区间，自动扩大范围（让数据居中）
      let finalMin, finalMax;
      if (dataRange < this.minAxisRange) {
        // 扩大的余量 = 保底区间 - 数据波动
        const extra = (this.minAxisRange - dataRange) / 2;
        finalMin = dataMin - extra;
        finalMax = dataMax + extra;
      } else {
        // 数据波动足够大，保留原有10%余量逻辑
        finalMin = Math.max(0, dataMin - dataRange * 0.1);
        finalMax = dataMax + dataRange * 0.1;
      }

      return { min: finalMin, max: finalMax };
    },

    initChart(ref, option) {
      const chart = echarts.init(this.$refs[ref]);
      chart.resize();
      chart.setOption({
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' },
          textStyle: { fontSize: 12 },
          formatter: (params) => {
            const time = params[0].axisValue;
            const value = Math.round(params[0].value);
            return `${time}<br/>${params[0].seriesName}：${value}`;
          }
        },
        grid: { left: '8%', right: '5%', bottom: '3%', top: '10%', containLabel: true },
        ...option
      });
      return chart;
    },

    // 径流图表（纵轴自动适配）+ dataZoom滚动
    initRunoffChart() {
      const { min, max } = this.getAxisRange(this.runoffData, 'flow');
      this.runoffChart = this.initChart('runoffChart', {
        dataZoom: [
          {
            type: 'inside',
            xAxisIndex: 0,
            start: 0,
            end: 100
          }
        ],
        xAxis: {
          type: 'category',
          data: this.runoffData.map(item => item.time),
          axisLabel: { show: false },
          axisLine: { show: false }
        },
        yAxis: {
          type: 'value',
          name: '流量 (m³/s)',
          nameTextStyle: { fontSize: 11 },
          min: min,
          max: max,
          interval: Math.ceil((max - min) / 5),
          axisLabel: {
            fontSize: 10,
            formatter: (value) => Math.round(value)
          },
          axisLine: { lineStyle: { color: '#e5e7eb' } },
          splitLine: { lineStyle: { type: 'dashed', color: '#f3f4f6' } }
        },
        series: [{
          data: this.runoffData.map(item => item.flow !== null ? Math.round(item.flow) : null),
          type: 'line',
          smooth: true,
          lineStyle: { width: 2 },
          symbol: 'circle',
          symbolSize: 4,
          name: '径流流量',
          connectNulls: false
        }]
      });
    },

    // 积雪图表（纵轴自动适配）+ dataZoom滚动
    initSnowChart() {
      const { min, max } = this.getAxisRange(this.snowData, 'depth');
      this.snowChart = this.initChart('snowChart', {
        dataZoom: [
          {
            type: 'inside',
            xAxisIndex: 0,
            start: 0,
            end: 100
          }
        ],
        xAxis: {
          type: 'category',
          data: this.snowData.map(item => item.time),
          axisLabel: { show: false },
          axisLine: { show: false }
        },
        yAxis: {
          type: 'value',
          name: '积雪深度 (cm)',
          nameTextStyle: { fontSize: 11 },
          min: min,
          max: max,
          interval: Math.ceil((max - min) / 5),
          axisLabel: {
            fontSize: 10,
            formatter: (value) => Math.round(value)
          },
          axisLine: { lineStyle: { color: '#e5e7eb' } },
          splitLine: { lineStyle: { type: 'dashed', color: '#f3f4f6' } }
        },
        series: [{
          data: this.snowData.map(item => item.depth !== null ? Math.round(item.depth) : null),
          type: 'line',
          smooth: true,
          color: '#5470C6',
          lineStyle: { width: 2 },
          symbol: 'circle',
          symbolSize: 4,
          name: '积雪深度',
          connectNulls: false
        }]
      });
    },

    // 预测图表（纵轴自动适配）+ dataZoom滚动
    initForecastChart() {
      const { min, max } = this.getAxisRange(this.forecastData, 'flow');
      this.forecastChart = this.initChart('forecastChart', {
        dataZoom: [
          {
            type: 'inside',
            xAxisIndex: 0,
            start: 0,
            end: 100
          }
        ],
        xAxis: {
          type: 'category',
          data: this.forecastData.map(item => item.time),
          axisLabel: { show: false },
          axisLine: { show: false }
        },
        yAxis: {
          type: 'value',
          name: '预测流量 (m³/s)',
          nameTextStyle: { fontSize: 11 },
          min: min,
          max: max,
          interval: Math.ceil((max - min) / 5),
          axisLabel: {
            fontSize: 10,
            formatter: (value) => Math.round(value)
          },
          axisLine: { lineStyle: { color: '#e5e7eb' } },
          splitLine: { lineStyle: { type: 'dashed', color: '#f3f4f6' } }
        },
        series: [{
          data: this.forecastData.map(item => item.flow !== null ? Math.round(item.flow) : null),
          type: 'line',
          smooth: true,
          color: '#91CC75',
          lineStyle: { width: 2 },
          symbol: 'circle',
          symbolSize: 4,
          name: '预测流量',
          connectNulls: false
        }]
      });
    },

    updateCharts() {
      // 径流图表更新
      if (this.runoffChart) {
        const { min, max } = this.getAxisRange(this.runoffData, 'flow');
        this.runoffChart.setOption({
          xAxis: { data: this.runoffData.map(item => item.time) },
          yAxis: {
            min: min,
            max: max,
            interval: Math.ceil((max - min) / 5),
            axisLabel: { formatter: v => Math.round(v) }
          },
          series: [{ data: this.runoffData.map(item => item.flow !== null ? Math.round(item.flow) : null) }]
        });
      } else {
        this.initRunoffChart();
      }

      // 积雪图表更新
      if (this.snowChart) {
        const { min, max } = this.getAxisRange(this.snowData, 'depth');
        this.snowChart.setOption({
          xAxis: { data: this.snowData.map(item => item.time) },
          yAxis: {
            min: min,
            max: max,
            interval: Math.ceil((max - min) / 5),
            axisLabel: { formatter: v => Math.round(v) }
          },
          series: [{ data: this.snowData.map(item => item.depth !== null ? Math.round(item.depth) : null) }]
        });
      } else {
        this.initSnowChart();
      }

      // 预测图表更新
      if (this.forecastChart) {
        const { min, max } = this.getAxisRange(this.forecastData, 'flow');
        this.forecastChart.setOption({
          xAxis: { data: this.forecastData.map(item => item.time) },
          yAxis: {
            min: min,
            max: max,
            interval: Math.ceil((max - min) / 5),
            axisLabel: { formatter: v => Math.round(v) }
          },
          series: [{ data: this.forecastData.map(item => item.flow !== null ? Math.round(item.flow) : null) }]
        });
      } else {
        this.initForecastChart();
      }
    },

    // 生成固定时间轴：最近3天，每半小时一个点
    generateFixedTimeAxis() {
      const timeAxis = [];
      const now = new Date();
      // 从3天前开始
      const startTime = new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000);
      // 调整为整点或整30分
      startTime.setMinutes(Math.floor(startTime.getMinutes() / 30) * 30, 0, 0);
      
      while (startTime <= now) {
        const dateStr = startTime.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' });
        const timeStr = startTime.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false });
        timeAxis.push(`${dateStr} ${timeStr}`);
        startTime.setTime(startTime.getTime() + 30 * 60 * 1000); // 每30分钟
      }
      return timeAxis;
    },

    async fetchChartData() {
      if (this.isFetching) return;
      this.isFetching = true;
      try {
        // 获取7天的数据，每半小时一个点，共336个
        const response = await getWeatherData({
          station__name: 'HXC',
          ordering: '-timestamp',
          page_size: this.maxDataPoints
        });
        // DRF 分页响应为 {count, next, previous, results}，需取 results；兼容非分页数组
        let data = Array.isArray(response.data)
          ? response.data
          : (response.data && Array.isArray(response.data.results) ? response.data.results : []);
        if (Array.isArray(data)) {
          // 按时间排序，取最新的maxDataPoints条
          data = data.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)).slice(0, this.maxDataPoints);
          
          // 生成固定时间轴
          const fixedTimeAxis = this.generateFixedTimeAxis();
          
          // 创建数据映射，按时间戳索引
          const dataMap = {};
          data.forEach(item => {
            const dateStr = new Date(item.timestamp).toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' });
            const timeStr = new Date(item.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false });
            const key = `${dateStr} ${timeStr}`;
            dataMap[key] = {
              rainsnow: Math.round(item.rainsnow || 0),
              snow_depth: Math.round(item.snow_depth || 0)
            };
          });
          
          // 将数据映射到固定时间轴，没有数据的用null填充
          const processedData = fixedTimeAxis.map(time => {
            const item = dataMap[time];
            return {
              time: time,
              rainsnow: item ? item.rainsnow : null,
              snow_depth: item ? item.snow_depth : null
            };
          });

          this.runoffData = processedData.map(item => ({ time: item.time, flow: item.rainsnow }));
          this.snowData = processedData.map(item => ({ time: item.time, depth: item.snow_depth }));
          this.forecastData = processedData.map(item => ({ time: item.time, flow: item.rainsnow !== null ? Math.round(item.rainsnow * 1.2) : null }));

          this.updateCharts();
        }
      } catch (error) {
        console.error("获取图表数据失败: ", error);
      } finally {
        this.isFetching = false;
      }
    },

    resizeCharts() {
      [this.runoffChart, this.snowChart, this.forecastChart].forEach(chart => chart && chart.resize());
    }
  }
}
</script>

<style lang="scss" scoped>
/* 样式部分不变 */
.right-panel {
  display: flex;
  flex-direction: column;
  gap: 24px;
  height: 100%;
  min-height: 800px;
}

.card-container {
  background-color: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
}

.card-title {
  font-size: 16px;
  color: #0F172A;
  margin: 0 0 16px 0;
  font-weight: 600;
  flex-shrink: 0;
}

.chart-container {
  flex: 1;
  width: 100%;
  min-height: 200px;
}
</style>
