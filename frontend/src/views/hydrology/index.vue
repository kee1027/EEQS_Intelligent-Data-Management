<template>
  <div class="whiterisk-theme">
    <header class="page-header">
      <div class="header-main">
        <nav class="breadcrumb">水文观测 </nav>
        <h1>实时水文数据</h1>
      </div>
    </header>

    <main class="dashboard-content">
      <div class="hydrology-grid">
        <div v-for="station in stations" :key="station.id" class="card hydrology-card">
          <div class="card-header">
            <i class="el-icon-s-flag station-icon"></i>
            <span class="station-name">{{ station.name }}</span>
            <span class="station-id">{{ station.id }}</span>
          </div>
          <div class="hydrology-body">
            <div class="metric-row-hydro">
              <span class="label">降水累计</span>
              <span class="value">{{ getValue(station.id, 'rainfall') }}</span>
            </div>
            <div class="metric-row-hydro">
              <span class="label">预测流量（明日）</span>
              <span class="value">{{ getValue(station.id, 'flowRate') }}</span>
            </div>
            <div class="metric-row-hydro">
              <span class="label">最新观测时间</span>
              <span class="value small">{{ getValue(station.id, 'observedAt') }}</span>
            </div>
          </div>
        </div>
      </div>
      <div v-if="!stations.length && !loading" class="empty-hint">
        暂无站点数据
      </div>
    </main>
  </div>
</template>

<script>
import request from '@/utils/request'

export default {
  name: 'HydrologyIndex',
  data() {
    return {
      stations: [],
      stationData: {},
      loading: false,
      refreshTimer: null,
      refreshInterval: 300000
    }
  },
  mounted() {
    this.fetchAllData()
    this.refreshTimer = setInterval(() => {
      this.fetchAllData()
    }, this.refreshInterval)
  },
  beforeDestroy() {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer)
      this.refreshTimer = null
    }
  },
  methods: {
    async fetchAllData() {
      this.loading = true
      try {
        // 1. 站点清单
        const { data: stations } = await request({ url: '/stations/', method: 'get' })
        const list = Array.isArray(stations) ? stations : (stations.results || [])
        this.stations = list.map(s => ({ id: s.name, name: s.name }))

        // 2. 最近一次成功预测（各站明日流量）
        const forecastMap = {}
        try {
          const { data: latest } = await request({
            url: '/hydrology-forecast-daily/latest/',
            method: 'get'
          })
          for (const s of (latest.stations || [])) {
            if (s.forecasts && s.forecasts.length) {
              forecastMap[s.station] = Number(s.forecasts[0].flow_avg).toFixed(2) + ' m³/s'
            }
          }
        } catch (e) {
          console.warn('获取预测数据失败:', e)
        }

        // 3. 每站最新一条观测（降水累计 + 观测时间）
        for (const station of this.stations) {
          try {
            const { data } = await request({
              url: '/weatherdata/',
              method: 'get',
              params: { station__name: station.id, page_size: 1 }
            })
            const rows = data.results || data || []
            const latestRow = rows[0]
            this.$set(this.stationData, station.id, {
              rainfall: latestRow && latestRow.rainsnow != null
                ? Number(latestRow.rainsnow).toFixed(2) + ' mm'
                : '--',
              flowRate: forecastMap[station.id] || '--',
              observedAt: latestRow && latestRow.timestamp
                ? latestRow.timestamp.replace('T', ' ').slice(0, 16)
                : '--'
            })
          } catch (e) {
            console.error('获取水文数据失败:', station.name, e)
          }
        }
      } catch (e) {
        console.error('获取站点列表失败:', e)
      } finally {
        this.loading = false
      }
    },
    getValue(stationId, field) {
      const data = this.stationData[stationId]
      if (!data || data[field] == null) return '--'
      return data[field]
    }
  }
}
</script>

<style scoped>
@import '~@/styles/page-layout.scss';

.hydrology-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}

.hydrology-card {
  background: white;
  border: 1px solid #eaedf2;
  border-radius: 4px;
  overflow: hidden;
}

.hydrology-card .card-header {
  padding: 16px;
  border-bottom: 1px solid #f0f2f5;
  display: flex;
  align-items: center;
  gap: 8px;
}

.station-icon {
  font-size: 20px;
  color: #2c7be5;
}

.station-name {
  font-weight: 600;
  font-size: 16px;
  color: #333;
}

.station-id {
  margin-left: auto;
  font-size: 12px;
  color: #888;
}

.hydrology-body {
  padding: 16px;
}

.metric-row-hydro {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #f8f9fa;
}

.metric-row-hydro:last-child {
  border-bottom: none;
}

.metric-row-hydro .label {
  font-size: 13px;
  color: #666;
}

.metric-row-hydro .value {
  font-size: 16px;
  font-weight: 600;
  color: #2c7be5;
}

.metric-row-hydro .value.small {
  font-size: 13px;
  font-weight: 400;
  color: #666;
}

.empty-hint {
  text-align: center;
  color: #94a3b8;
  padding: 60px 0;
}

@media (max-width: 1024px) {
  .hydrology-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .hydrology-grid {
    grid-template-columns: 1fr;
  }
}
</style>
