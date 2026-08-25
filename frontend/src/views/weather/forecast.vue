<template>
  <div class="whiterisk-theme">
    <header class="page-header">
      <nav class="breadcrumb">气象服务 / 预报</nav>
      <h1>气象预报</h1>
    </header>
    <main class="dashboard-content">
      <div class="card" style="padding: 60px 40px; text-align: center;">
        <div style="font-size: 64px; margin-bottom: 24px;">🌤️</div>
        <h2 style="font-size: 20px; color: #0f172a; margin-bottom: 12px; font-weight: 600;">气象预报服务</h2>
        <p style="color: #64748b; font-size: 14px; line-height: 1.8; max-width: 500px; margin: 0 auto;">
          提供流域范围内的气象预报数据，包括温度、降水、风速等关键气象要素的中短期预报，为水文模型提供驱动数据。
        </p>
        <div style="margin-top: 32px; display: flex; justify-content: center; gap: 16px;">
          <div style="padding: 16px 24px; background: #f1f5f9; border-radius: 8px; min-width: 140px;">
            <div style="font-size: 24px; font-weight: 700; color: #0b4f7c;">--</div>
            <div style="font-size: 12px; color: #64748b; margin-top: 4px;">预报时长</div>
          </div>
          <div style="padding: 16px 24px; background: #f1f5f9; border-radius: 8px; min-width: 140px;">
            <div style="font-size: 24px; font-weight: 700; color: #0b4f7c;">--</div>
            <div style="font-size: 12px; color: #64748b; margin-top: 4px;">分辨率</div>
          </div>
          <div style="padding: 16px 24px; background: #f1f5f9; border-radius: 8px; min-width: 140px;">
            <div style="font-size: 24px; font-weight: 700; color: #0b4f7c;">--</div>
            <div style="font-size: 12px; color: #64748b; margin-top: 4px;">更新频次</div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
export default {
  name: 'WeatherForecast'
}
</script>

<style scoped>
.whiterisk-theme {
  background-color: #f8f9fa;
  color: #1e2125;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", sans-serif;
  padding-bottom: 50px;
  min-height: 100%;
}
.page-header {
  padding: 32px 5%;
  background: white;
  border-bottom: 1px solid #eaedf2;
}
.page-header h1 {
  font-size: 26px;
  margin: 0;
  font-weight: 600;
  color: #0f172a;
}
.breadcrumb {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 8px;
}
.dashboard-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px 20px;
}
.card {
  background: white;
  border: 1px solid #eaedf2;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
</style>
