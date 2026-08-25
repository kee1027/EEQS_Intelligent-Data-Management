<template>
  <div class="whiterisk-theme">
    <header class="page-header">
      <nav class="breadcrumb">气象服务 / 历史数据</nav>
      <h1>气象历史数据</h1>
    </header>
    <main class="dashboard-content">
      <div class="card" style="padding: 60px 40px; text-align: center;">
        <div style="font-size: 64px; margin-bottom: 24px;">📊</div>
        <h2 style="font-size: 20px; color: #0f172a; margin-bottom: 12px; font-weight: 600;">气象历史数据查询</h2>
        <p style="color: #64748b; font-size: 14px; line-height: 1.8; max-width: 500px; margin: 0 auto;">
          提供流域内各气象观测站点历史数据的检索与可视化，支持温度、湿度、风速、降水等多要素的时间序列分析。
        </p>
        <div style="margin-top: 32px; display: flex; justify-content: center; gap: 16px;">
          <div style="padding: 16px 24px; background: #f1f5f9; border-radius: 8px; min-width: 140px;">
            <div style="font-size: 24px; font-weight: 700; color: #0b4f7c;">--</div>
            <div style="font-size: 12px; color: #64748b; margin-top: 4px;">数据年限</div>
          </div>
          <div style="padding: 16px 24px; background: #f1f5f9; border-radius: 8px; min-width: 140px;">
            <div style="font-size: 24px; font-weight: 700; color: #0b4f7c;">--</div>
            <div style="font-size: 12px; color: #64748b; margin-top: 4px;">站点数量</div>
          </div>
          <div style="padding: 16px 24px; background: #f1f5f9; border-radius: 8px; min-width: 140px;">
            <div style="font-size: 24px; font-weight: 700; color: #0b4f7c;">--</div>
            <div style="font-size: 12px; color: #64748b; margin-top: 4px;">数据总量</div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
export default {
  name: 'WeatherHistory'
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
