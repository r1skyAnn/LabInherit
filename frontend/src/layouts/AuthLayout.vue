<script setup lang="ts">
import { RouterView } from 'vue-router'
import EmberLogo from '@/components/EmberLogo.vue'
</script>

<template>
  <div class="auth-container">
    <div class="auth-logo">
      <EmberLogo />
      <h1>薪火相传</h1>
      <p class="auth-subtitle">实验室知识传承平台</p>
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
  background:
    radial-gradient(ellipse at 30% 20%, rgba(194, 81, 26, 0.06) 0%, transparent 60%),
    radial-gradient(ellipse at 70% 80%, rgba(61, 114, 81, 0.04) 0%, transparent 60%),
    var(--parchment);
  padding: 1rem;
}

.auth-logo {
  text-align: center;
  margin-bottom: 1.75rem;
}

.auth-logo :deep(.ember-logo) {
  width: 52px;
  height: 52px;
  margin-bottom: 0.5rem;
}

.auth-logo h1 {
  margin: 0;
  font-size: 1.7rem;
  font-weight: 700;
  color: var(--ink);
  letter-spacing: 0.05em;
}

.auth-subtitle {
  margin: 0.15rem 0 0;
  font-size: 0.88rem;
  color: var(--stone);
}

.auth-card {
  background: #fff;
  border-radius: 12px;
  padding: 2rem 2.5rem;
  width: 100%;
  max-width: 420px;
  box-shadow:
    0 1px 3px rgba(0, 0, 0, 0.04),
    0 8px 40px rgba(0, 0, 0, 0.06);
  border: 1px solid var(--el-border-color-light);
}
</style>
