<template>
  <div class="building-container">
    <div class="building-content">
      <div class="building-icon">
        <span class="icon-emoji">🏗️</span>
      </div>
      <div class="building-text">
        <h1>页面建设中</h1>
        <p>该页面正在紧张开发中，敬请期待...</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Building'
}
</script>

<style lang="scss" scoped>
.building-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 50px);
  background: #f8f9fa;
}

.building-content {
  text-align: center;
  color: #0f172a;
  padding: 40px;
}

.building-icon {
  margin-bottom: 24px;
}

.icon-emoji {
  font-size: 80px;
  display: inline-block;
  animation: bounce 2s infinite;
}

.building-text {
  h1 {
    font-size: 28px;
    margin-bottom: 12px;
    color: #0b4f7c;
    font-weight: 600;
  }

  p {
    font-size: 16px;
    color: #64748b;
  }
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-12px);
  }
}
</style>
