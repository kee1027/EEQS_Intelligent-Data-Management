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
            <span class="station-id">站点ID: {{ station.stationId }}</span>
          </div>
          <div class="hydrology-body">
            <div class="metric-row-hydro">
              <span class="label">雨量</span>
              <span class="value">{{ getValue(station.id, 'rainfall') }} mm</span>
            </div>
            <div class="metric-row-hydro">
              <span class="label">水位</span>
              <span class="value">{{ getValue(station.id, 'waterLevel') }} m</span>
            </div>
            <div class="metric-row-hydro">
              <span class="label">流量</span>
              <span class="value">{{ getValue(station.id, 'flowRate') }} m³/s</span>
            </div>
            <div class="metric-row-hydro">
              <span class="label">平均流速</span>
              <span class="value">{{ getValue(station.id, 'velocity') }} m/s</span>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import { HYDROLOGY_STATIONS } from './station-config'
import { getHydrologyData } from '@/api/hydrology/hydrology'

export default {
  name: 'HydrologyIndex',
  data() {
    return {
      stations: HYDROLOGY_STATIONS,
      stationData: {},
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
      for (const station of this.stations) {
        try {
          const res = await getHydrologyData({ station: station.apiName })
          const data = Array.isArray(res.data) ? res.data[0] : res.data
          if (data) {
            this.$set(this.stationData, station.id, {
              rainfall: data.rainfall != null ? data.rainfall : '0.0',
              waterLevel: data.water_level != null ? data.water_level : '0.0',
              flowRate: data.flow_rate != null ? data.flow_rate : '0.0',
              velocity: data.velocity != null ? data.velocity : '0.0'
            })
          }
        } catch (e) {
          console.error('获取水文数据失败:', station.name, e)
        }
      }
    },
    getValue(stationId, field) {
      const data = this.stationData[stationId]
      if (!data || data[field] == null) return '0.0'
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
