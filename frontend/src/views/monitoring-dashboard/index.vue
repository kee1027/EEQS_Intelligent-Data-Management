<template>
  <div class="screen-container">
    <header class="screen-header">
      <span class="title">额尔齐斯河流域上游水资源预报管理系统</span>
      <div class="title-right">
        <span class="datetime">{{ nowTime }}</span>
      </div>
    </header>

    <div class="screen-body">
      <left-panel class="panel left" />
      <center-map class="panel center" />
      <right-panel class="panel right" />
    </div>

    <footer class="screen-footer">
        <!-- 底部可以添加其他信息 -->
    </footer>
  </div>
</template>

<script>
import LeftPanel from './components/LeftPanel.vue'
import CenterMap from './components/CenterMap.vue'
import RightPanel from './components/RightPanel.vue'

export default {
  name: 'MonitoringDashboard',
  components: {
    LeftPanel,
    CenterMap,
    RightPanel
  },
  data() {
    return {
      nowTime: '',
      timer: null
    }
  },
  mounted() {
    this.updateTime()
    this.timer = setInterval(this.updateTime, 1000)
  },
  beforeDestroy() {
    clearInterval(this.timer)
  },
  methods: {
    updateTime() {
      const now = new Date();
      const year = now.getFullYear();
      const month = (now.getMonth() + 1).toString().padStart(2, '0');
      const date = now.getDate().toString().padStart(2, '0');
      const hours = now.getHours().toString().padStart(2, '0');
      const minutes = now.getMinutes().toString().padStart(2, '0');
      const seconds = now.getSeconds().toString().padStart(2, '0');
      this.nowTime = `${year}/${month}/${date} ${hours}:${minutes}:${seconds}`;
    }
  }
}
</script>

<style lang="scss" scoped>
.screen-container {
  min-width: 1200px;
  max-width: 1600px;
  margin: 0 auto;
  height: 100vh;
  width: 100%;
  display: flex;
  flex-direction: column;
  padding: 24px;
  box-sizing: border-box;
  background-color: #F7F8FC; /* A light background color */
}

.screen-header {
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  margin-bottom: 24px;

  .title {
    font-size: 24px;
    font-weight: bold;
    color: #0F172A;
  }

  .title-right {
    position: absolute;
    right: 0;
    top: 50%;
    transform: translateY(-50%);
    .datetime {
      font-size: 16px;
      color: #64748B;
    }
  }
}

.screen-body {
  flex: 1;
  display: flex;
  height: 90%;
}

.panel {
  height: 100%;
}
.left {
  width: 300px;
}
.center {
  flex: 1;
  margin: 0 24px;
}
.right {
  width: 360px;
}
.screen-footer {
    height: 0; /* Removing footer for now */
}
</style>