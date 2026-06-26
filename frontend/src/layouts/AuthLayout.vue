<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<template>
  <div class="auth-container">
    <div class="auth-logo">
      <h1>🔬 LabInherit</h1>
      <p class="auth-subtitle">实验室薪火传舵平台</p>
    </div>
    <div class="auth-card">
      <RouterView />
    </div>
  </div>
</template>

<style scoped>
.auth-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 1rem;
}

.auth-logo {
  text-align: center;
  margin-bottom: 1.5rem;
  color: white;
}

.auth-logo h1 {
  margin: 0;
  font-size: 2rem;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.auth-subtitle {
  margin: 0.25rem 0 0;
  font-size: 0.95rem;
  opacity: 0.85;
}

.auth-card {
  background: white;
  border-radius: 16px;
  padding: 2rem 2.5rem;
  width: 100%;
  max-width: 420px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}
</style>
