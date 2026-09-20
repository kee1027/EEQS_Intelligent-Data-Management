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
        <el-form ref="loginForm" :model="form" :rules="rules" @submit.native.prevent>
          <el-form-item prop="username">
            <el-input
              v-model.trim="form.username"
              prefix-icon="el-icon-user"
              placeholder="用户名"
              autocomplete="username"
              @keyup.enter.native="submitForm"
            />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              v-model="form.password"
              prefix-icon="el-icon-lock"
              type="password"
              placeholder="密码"
              autocomplete="current-password"
              show-password
              @keyup.enter.native="submitForm"
            />
          </el-form-item>
          <el-form-item style="margin-bottom: 0;">
            <el-button
              type="primary"
              style="width: 100%;"
              :loading="loading"
              @click="submitForm"
            >
              登 录
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>
    <div class="login-footer">
      <p>© Truwel Cloud Platform. All rights reserved.</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Login',
  data() {
    return {
      loading: false,
      form: {
        username: '',
        password: ''
      },
      rules: {
        username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
        password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
      }
    }
  },
  methods: {
    submitForm() {
      this.$refs.loginForm.validate(async (valid) => {
        if (!valid) return
        this.loading = true
        try {
          await this.$store.dispatch('user/login', this.form)
          this.$message.success('登录成功')
          const redirect = this.$route.query.redirect || '/'
          this.$router.push(redirect)
        } catch (error) {
          const status = error && error.response && error.response.status
          const detail = error && error.response && error.response.data && error.response.data.detail
          if (status === 401) {
            this.$message.error(detail || '用户名或密码错误')
          } else if (status === 403) {
            this.$message.error(detail || '账户已被停用，请联系管理员')
          } else {
            this.$message.error('登录失败，请稍后重试')
          }
        } finally {
          this.loading = false
        }
      })
    }
  }
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
