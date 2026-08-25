<template>
  <div class="whiterisk-theme">
    <header class="page-header">
      <nav class="breadcrumb">预警中心 / 洪水</nav>
      <h1>洪水预警</h1>
    </header>
    <main class="dashboard-content">
      <div class="card" style="padding: 60px 40px; text-align: center;">
        <div style="font-size: 64px; margin-bottom: 24px;">⚠️</div>
        <h2 style="font-size: 20px; color: #0f172a; margin-bottom: 12px; font-weight: 600;">洪水预警监测模块</h2>
        <p style="color: #64748b; font-size: 14px; line-height: 1.8; max-width: 500px; margin: 0 auto;">
          该模块用于监控流域洪水风险，基于实时降雨、水位及融雪数据，提供洪水预警等级评估与预警信息发布。
        </p>
        <div style="margin-top: 32px; display: flex; justify-content: center; gap: 16px;">
          <div style="padding: 16px 24px; background: #fef3c7; border-radius: 8px; min-width: 140px; border: 1px solid #fde68a;">
            <div style="font-size: 24px; font-weight: 700; color: #d97706;">--</div>
            <div style="font-size: 12px; color: #92400e; margin-top: 4px;">当前预警等级</div>
          </div>
          <div style="padding: 16px 24px; background: #f1f5f9; border-radius: 8px; min-width: 140px;">
            <div style="font-size: 24px; font-weight: 700; color: #0b4f7c;">--</div>
            <div style="font-size: 12px; color: #64748b; margin-top: 4px;">监测站点</div>
          </div>
          <div style="padding: 16px 24px; background: #f1f5f9; border-radius: 8px; min-width: 140px;">
            <div style="font-size: 24px; font-weight: 700; color: #0b4f7c;">--</div>
            <div style="font-size: 12px; color: #64748b; margin-top: 4px;">预警记录</div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
export default {
  name: 'FloodWarning'
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
