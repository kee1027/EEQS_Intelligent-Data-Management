<template>
  <div class="left-panel">
    <!-- 监控系统运行状况 -->
    <div class="card-container">
      <h3 class="card-title">监控系统运行状况</h3>
      <div class="status-content">
        <div class="status-left">
          <div class="data-item">
            <span class="data-value" style="color: #FF8A00; font-size: 28px;">50%</span>
            <span class="data-label">运行率</span>
          </div>
          <div class="data-item">
            <span class="data-value">2 个</span>
            <span class="data-label">在线台站</span>
          </div>
          <div class="data-item">
            <span class="data-value">2 个</span>
            <span class="data-label">资源数</span>
          </div>
          <div class="data-item">
            <span class="data-value">23 人</span>
            <span class="data-label">日活用户</span>
          </div>
        </div>
        <div class="status-right">
          <!-- 进度环占位符 -->
          <div class="progress-ring-placeholder"></div>
          <div class="status-indicators">
            <span class="indicator normal"></span>正常
            <span class="indicator warning"></span>警告
            <span class="indicator fault"></span>故障
          </div>
        </div>
      </div>
    </div>

    <!-- 站点快速入口 -->
    <div class="card-container">
      <h3 class="card-title">站点快速入口</h3>
      <div class="site-buttons">
        <div v-for="site in sites" :key="site.name" class="site-button">
          <div class="site-info">
            <span class="site-name">{{ site.name }}</span>
            <span class="site-time">最近观测: {{ site.lastObservation }}</span>
          </div>
          <i class="el-icon-arrow-right"></i>
        </div>
      </div>
    </div>

    <!-- 告警与待办 -->
    <div class="card-container">
      <h3 class="card-title">告警与待办</h3>
      <div class="alarm-list">
        <div v-for="(alarm, index) in alarms" :key="index" class="alarm-item">
          <span :class="['alarm-level', getAlarmLevelClass(alarm.level)]">{{ alarm.level }}</span>
          <div class="alarm-details">
            <span class="alarm-text">{{ alarm.text }}</span>
            <span class="alarm-info">{{ alarm.time }} - {{ alarm.station }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'LeftPanel',
  data() {
    return {
      sites: [
        { name: '阿克沙拉', lastObservation: '2023-10-26 10:30' },
        { name: '喀伊尔', lastObservation: '2023-10-26 10:25' },
        { name: '可可苏里', lastObservation: '2023-10-26 10:20' }
      ],
      alarms: [
        { level: '高', text: '积雪深度传感器离线', time: '10:30', station: '阿克沙拉' },
        { level: '中', text: '流量数据超出阈值', time: '09:15', station: '可可苏里' },
        { level: '低', text: '设备电池电量低', time: '08:50', station: '喀伊尔' }
      ]
    }
  },
  methods: {
    getAlarmLevelClass(level) {
      if (level === '高') return 'high';
      if (level === '中') return 'medium';
      if (level === '低') return 'low';
      return '';
    }
  }
}
</script>

<style scoped>
.left-panel {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.card-container {
  background-color: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.08);
}

.card-title {
  font-size: 16px;
  color: #0F172A;
  margin: 0 0 16px 0;
  font-weight: 600;
}

/* 监控系统运行状况 */
.status-content {
  display: flex;
}

.status-left {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.data-item {
  display: flex;
  flex-direction: column;
}

.data-value {
  font-size: 18px;
  font-weight: bold;
  color: #0F172A;
}

.data-label {
  font-size: 12px;
  color: #64748B;
}

.status-right {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin-left: 16px;
}

.progress-ring-placeholder {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  border: 8px solid #E5E7EB;
  border-top-color: #3B82F6;
  transform: rotate(45deg); /* Placeholder visual */
}

.status-indicators {
  margin-top: 12px;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #64748B;
}

.indicator {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.indicator.normal { background-color: #22C55E; }
.indicator.warning { background-color: #F59E0B; }
.indicator.fault { background-color: #EF4444; }

/* 站点快速入口 */
.site-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.site-button {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 48px;
  padding: 0 16px;
  background-color: #F1F5F9;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.site-button:hover {
  background-color: #E6EEF8;
}

.site-info {
  display: flex;
  flex-direction: column;
}

.site-name {
  font-size: 14px;
  font-weight: 500;
  color: #0F172A;
}

.site-time {
  font-size: 12px;
  color: #64748B;
}

/* 告警与待办 */
.alarm-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.alarm-item {
  display: flex;
  align-items: flex-start;
}

.alarm-level {
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  padding: 2px 6px;
  border-radius: 4px;
  margin-right: 8px;
  flex-shrink: 0;
}

.alarm-level.high { background-color: #EF4444; }
.alarm-level.medium { background-color: #F59E0B; }
.alarm-level.low { background-color: #94A3B8; }

.alarm-details {
  display: flex;
  flex-direction: column;
}

.alarm-text {
  font-size: 14px;
  color: #0F172A;
}

.alarm-info {
  font-size: 12px;
  color: #64748B;
  margin-top: 4px;
}
</style>