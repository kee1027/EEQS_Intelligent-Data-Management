<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <img src="../../assets/truwel_logo.png" alt="logo" class="login-logo">
        <h2>Truwel 云平台</h2>
        <p class="subtitle">额尔齐斯河流域上游水资源预报管理系统</p>
      </div>
      <div class="login-form">
        <h1>用户登录</h1>
        <p class="hint">请输入您的账号信息以继续</p>
      </div>
    </div>
    <div class="login-footer">
      <p>© Truwel Cloud Platform. All rights reserved.</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Login'
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #f8f9fa 0%, #e6f0fa 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", sans-serif;
}

.login-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.08);
  width: 100%;
  max-width: 420px;
  overflow: hidden;
  border: 1px solid #eaedf2;
}

.login-header {
  background: linear-gradient(135deg, #0b4f7c 0%, #0f172a 100%);
  padding: 40px 32px;
  text-align: center;
  color: white;
}

.login-logo {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  margin-bottom: 16px;
  background: white;
  padding: 4px;
}

.login-header h2 {
  margin: 0 0 8px 0;
  font-size: 22px;
  font-weight: 600;
}

.subtitle {
  margin: 0;
  font-size: 13px;
  opacity: 0.8;
}

.login-form {
  padding: 32px;
}

.login-form h1 {
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 600;
  color: #0f172a;
}

.hint {
  margin: 0 0 24px 0;
  font-size: 14px;
  color: #64748b;
}

.login-footer {
  margin-top: 24px;
  text-align: center;
  color: #94a3b8;
  font-size: 12px;
}
</style>
