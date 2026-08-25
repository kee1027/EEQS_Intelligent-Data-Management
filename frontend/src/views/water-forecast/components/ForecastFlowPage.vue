<template>
  <div class="whiterisk-theme">
    <header class="page-header">
      <div class="header-main">
        <nav class="breadcrumb">站点详细数据</nav>
        <h1>> {{ config.pageTitle }}</h1>
      </div>
      <el-button
        type="primary"
        plain
        size="mini"
        icon="el-icon-download"
        class="export-button"
        @click="exportStationData"
      >
        导出站点数据
      </el-button>
    </header>

    <main class="dashboard-content">
      <section class="top-section">
        <div class="data-grid">
          <div class="card info-card">
            <div class="card-header">站点信息</div>
            <div class="info-body">
              <div class="info-item">
                <span class="label">海拔</span>
                <span class="value">1475m</span>
              </div>
              <div class="info-item">
                <span class="label">类型</span>
                <span class="value">综合观测场</span>
              </div>
            </div>
          </div>

          <div class="card data-card">
            <div class="card-header">模型简介</div>
            <div class="data-body main-metric">
              <div class="primary">
                <span class="label">模型名称</span>
                <div class="mid-value">{{ config.modelName }}</div>
              </div>
              <div class="secondary-metrics">
                <div class="model-desc">{{ config.modelDescription }}</div>
              </div>
            </div>
          </div>

          <div class="card data-card">
            <div class="card-header">预测粒度</div>
            <div class="data-body">
              <div class="metric-row">
                <div class="flex-col">
                  <span class="label">时间步长</span>
                  <span class="big-value">{{ config.granularity }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="card map-card">
          <div class="map-placeholder">
            <div class="map-overlay">
              <span>89.39°N, 47.21°E</span>
            </div>
          </div>
        </div>
      </section>

      <section class="charts-section">
        <div class="card chart-card">
          <div class="card-header">
            预测流量
            <el-tag v-if="isMockData" size="mini" type="info">模拟数据</el-tag>
            <el-tag v-else size="mini" type="success">实时数据</el-tag>
          </div>
          <div ref="forecastFlowChart" class="chart-container"></div>
        </div>
      </section>
    </main>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import request from '@/utils/request'

export default {
  name: 'ForecastFlowPage',
  props: {
    period: {
      type: String,
      default: 'ten-days'
    }
  },
  data() {
    return {
      chart: null,
      animationTimer: null,
      labels: [],
      forecastValues: [],
      maxValues: [],
      minValues: [],
      currentStep: 0,
      isMockData: true
    }
  },
  computed: {
    config() {
      if (this.period === 'month') {
        return {
          pageTitle: '库威积雪水文观测场 - 月预测',
          granularity: '30天',
          modelName: '月尺度融雪径流模型',
          modelDescription: '结合气象驱动与流域下垫面参数，进行未来30天流量区间预测。',
          points: 30
        }
      }
      if (this.period === 'year') {
        return {
          pageTitle: '库威积雪水文观测场 - 年预测',
          granularity: '1年',
          modelName: '年尺度水量平衡模型',
          modelDescription: '基于多年降水、温度与融雪贡献率，进行未来12个月趋势研判。',
          points: 12
        }
      }
      return {
        pageTitle: '库威积雪水文观测场 - 天预测',
        granularity: '24小时',
        modelName: '短临融雪-径流耦合模型',
        modelDescription: '融合实时观测与温度响应因子，滚动预测未来1天来水变化。',
        points: 20
      }
    }
  },
  mounted() {
    this.fetchData()
    window.addEventListener('resize', this.handleResize)
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.handleResize)
    this.clearAnimationTimer()
    if (this.chart) {
      this.chart.dispose()
      this.chart = null
    }
  },
  methods: {
    async fetchData() {
      try {
        await this.fetchRealForecastData()
      } catch (e) {
        console.warn('真实预报数据获取失败，使用模拟数据:', e)
        this.prepareForecastData()
        this.isMockData = true
      }
      this.$nextTick(() => {
        this.initChart()
        this.startPlayback()
      })
    },
    async fetchRealForecastData() {
      const res = await request({
        url: `/forecast/${this.period}`,
        method: 'get'
      })
      const data = res.data
      if (!data || !data.labels || !data.forecastValues) {
        throw new Error('后端数据格式无效')
      }
      this.labels = data.labels
      this.forecastValues = data.forecastValues
      this.maxValues = data.maxValues || []
      this.minValues = data.minValues || []
      this.isMockData = false
    },
    prepareForecastData() {
      const pointCount = this.config.points
      const labels = []

      for (let i = 0; i < pointCount; i++) {
        if (this.period === 'month') {
          labels.push(`4月${i + 1}日`)
        } else if (this.period === 'year') {
          labels.push(`${i + 1}月`)
        } else {
          const day = Math.floor(i / 2) + 1
          labels.push(`第${day}天 ${i % 2 === 0 ? '00:00' : '12:00'}`)
        }
      }

      const forecastValues = []
      const maxValues = []
      const minValues = []
      const base = this.period === 'year' ? 62 : this.period === 'month' ? 48 : 42
      const slope = this.period === 'year' ? 1.4 : this.period === 'month' ? 0.4 : 0.7
      const waveAmplitude = this.period === 'year' ? 5 : this.period === 'month' ? 3 : 2.4
      const baseSpread = this.period === 'year' ? 8 : this.period === 'month' ? 6 : 4.5
      const spreadVariance = this.period === 'year' ? 6 : this.period === 'month' ? 4.5 : 3.5

      for (let i = 0; i < pointCount; i++) {
        const predicted = +(base + i * slope + Math.sin(i / 2.5) * waveAmplitude).toFixed(2)
        const spreadFactor = 0.3 + Math.abs(Math.sin(i / 2.4))
        const spread = +(baseSpread + spreadFactor * spreadVariance).toFixed(2)
        forecastValues.push(predicted)
        maxValues.push(+(predicted + spread).toFixed(2))
        minValues.push(+(Math.max(0, predicted - spread)).toFixed(2))
      }

      this.labels = labels
      this.forecastValues = forecastValues
      this.maxValues = maxValues
      this.minValues = minValues
    },
    initChart() {
      this.chart = echarts.init(this.$refs.forecastFlowChart)
      this.chart.setOption({
        tooltip: {
          trigger: 'axis',
          formatter: params => {
            if (!params || !params.length) return ''
            const idx = params[0].dataIndex
            const core = this.forecastValues[idx]
            const min = this.minValues[idx]
            const max = this.maxValues[idx]
            return [
              this.labels[idx],
              `核心预测: ${core} m³/s`,
              `置信区间: ${min} ~ ${max} m³/s`
            ].join('<br/>')
          }
        },
        legend: {
          top: 10,
          data: ['核心预测', '置信区间']
        },
        grid: {
          left: '7%',
          right: '5%',
          top: 48,
          bottom: 58,
          containLabel: true
        },
        dataZoom: [
          {
            type: 'slider',
            show: true,
            xAxisIndex: 0,
            start: this.period === 'year' ? 0 : 45,
            end: 100,
            height: 20,
            bottom: 10
          },
          {
            type: 'inside',
            xAxisIndex: 0,
            start: this.period === 'year' ? 0 : 45,
            end: 100
          }
        ],
        xAxis: {
          type: 'category',
          data: this.labels,
          axisLabel: {
            fontSize: 10,
            interval: this.period === 'year' ? 0 : 1,
            rotate: this.period === 'year' ? 0 : 35
          }
        },
        yAxis: {
          type: 'value',
          name: '流量 (m³/s)',
          axisLabel: {
            formatter: value => Number(value).toFixed(2)
          },
          splitLine: {
            lineStyle: {
              type: 'dashed',
              color: '#edf0f5'
            }
          }
        },
        series: [
          {
            name: '置信区间下界',
            type: 'line',
            smooth: true,
            stack: 'confidence',
            symbol: 'none',
            animation: false,
            animationDuration: 0,
            animationDurationUpdate: 0,
            lineStyle: { width: 0, opacity: 0 },
            areaStyle: { opacity: 0 },
            tooltip: { show: false },
            data: []
          },
          {
            name: '置信区间',
            type: 'line',
            smooth: true,
            stack: 'confidence',
            symbol: 'none',
            animation: false,
            animationDuration: 0,
            animationDurationUpdate: 0,
            lineStyle: { width: 0, opacity: 0 },
            itemStyle: { color: '#8fd19e' },
            areaStyle: {
              color: 'rgba(143, 209, 158, 0.28)'
            },
            data: []
          },
          {
            name: '核心预测',
            type: 'line',
            smooth: true,
            symbol: 'circle',
            symbolSize: 5,
            color: '#2c7be5',
            lineStyle: { width: 2.5 },
            data: []
          }
        ]
      })
    },
    buildProgressiveSeries(source, step) {
      return source.map((value, index) => (index <= step ? value : null))
    },
    buildProgressiveBandWidth(step) {
      return this.maxValues.map((value, index) => {
        if (index > step) return null
        return +(value - this.minValues[index]).toFixed(2)
      })
    },
    updateChartByStep(step) {
      if (!this.chart) return
      this.chart.setOption({
        series: [
          { data: this.buildProgressiveSeries(this.minValues, step) },
          { data: this.buildProgressiveBandWidth(step) },
          { data: this.buildProgressiveSeries(this.forecastValues, step) }
        ]
      })
    },
    startPlayback() {
      this.clearAnimationTimer()
      this.currentStep = 0
      this.updateChartByStep(this.currentStep)
      this.animationTimer = setInterval(() => {
        if (this.currentStep >= this.labels.length - 1) {
          this.clearAnimationTimer()
          return
        }
        this.currentStep += 1
        this.updateChartByStep(this.currentStep)
      }, 500)
    },
    clearAnimationTimer() {
      if (this.animationTimer) {
        clearInterval(this.animationTimer)
        this.animationTimer = null
      }
    },
    exportStationData() {
      const summaryRows = [
        ['站点名称', '库威积雪水文观测场'],
        ['页面标题', this.config.pageTitle],
        ['模型名称', this.config.modelName],
        ['模型简介', this.config.modelDescription],
        ['预测粒度', this.config.granularity],
        ['导出时间', new Date().toLocaleString('zh-CN')]
      ]
      const detailRows = this.labels.map((label, index) => [
        label,
        this.forecastValues[index].toFixed(2),
        this.minValues[index].toFixed(2),
        this.maxValues[index].toFixed(2)
      ])

      const escapeHtml = value =>
        String(value)
          .replace(/&/g, '&amp;')
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;')
          .replace(/"/g, '&quot;')

      const toRow = cells => `<tr>${cells.map(cell => `<td>${escapeHtml(cell)}</td>`).join('')}</tr>`
      const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <style>
    body { font-family: "Microsoft YaHei", Arial, sans-serif; }
    table { border-collapse: collapse; width: 100%; margin-bottom: 16px; }
    th, td { border: 1px solid #d9e2ec; padding: 8px 10px; text-align: left; }
    th { background: #eef4fb; }
    .title { font-size: 18px; font-weight: 700; margin: 0 0 12px; }
  </style>
</head>
<body>
  <div class="title">站点数据导出</div>
  <table>
    <tr><th>字段</th><th>值</th></tr>
    ${summaryRows.map(row => toRow(row)).join('')}
  </table>
  <table>
    <tr><th>时间点</th><th>核心预测 (m³/s)</th><th>置信区间下限</th><th>置信区间上限</th></tr>
    ${detailRows.map(row => toRow(row)).join('')}
  </table>
</body>
</html>`

      const blob = new Blob(['\ufeff', html], {
        type: 'application/vnd.ms-excel;charset=utf-8'
      })
      const link = document.createElement('a')
      const url = window.URL.createObjectURL(blob)
      link.href = url
      link.download = `${this.config.pageTitle.replace(/[\\/:*?"<>|]/g, '_')}_站点数据.xls`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    },
    handleResize() {
      if (this.chart) {
        this.chart.resize()
      }
    }
  }
}
</script>

<style scoped>
@import '~@/styles/station-page.scss';

.forecast-page .card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.model-desc {
  font-size: 13px;
  color: #4b5563;
  line-height: 1.7;
}

.big-value {
  font-size: 30px;
  font-weight: 700;
  color: #2c7be5;
  margin-top: 10px;
}

.mid-value {
  font-size: 22px;
  font-weight: 600;
  margin-top: 8px;
}

.chart-card {
  min-height: 420px;
}

.chart-container {
  height: 380px;
  padding: 12px;
}

@media (max-width: 1024px) {
  .top-section {
    grid-template-columns: 1fr;
  }
}
</style>
