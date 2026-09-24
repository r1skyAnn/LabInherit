<script setup lang="ts">
defineProps<{ collapsed?: boolean }>()
</script>

<template>
  <svg
    class="ember-logo"
    :class="{ 'is-collapsed': collapsed }"
    viewBox="0 0 48 48"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <!-- outer ring — the vessel / tradition -->
    <circle
      cx="24" cy="24" r="21"
      stroke="currentColor"
      stroke-width="1.5"
      stroke-opacity="0.25"
      fill="none"
    />
    <!-- middle ring — knowledge passed down -->
    <circle
      cx="24" cy="24" r="16"
      stroke="currentColor"
      stroke-width="1"
      stroke-opacity="0.35"
      fill="none"
    />
    <!-- flame core — the living ember -->
    <path
      d="M24 8
         C20 14, 16 20, 16 26
         C16 32, 20 36, 24 36
         C28 36, 32 32, 32 26
         C32 20, 28 14, 24 8Z"
      fill="currentColor"
      fill-opacity="0.45"
    />
    <!-- inner flame — the spark -->
    <path
      d="M24 14
         C22 18, 20 22, 20 25
         C20 28, 22 31, 24 31
         C26 31, 28 28, 28 25
         C28 22, 26 18, 24 14Z"
      fill="currentColor"
      fill-opacity="0.9"
    />
    <!-- glow dot — the brightest point -->
    <circle cx="24" cy="20" r="3" fill="currentColor" fill-opacity="0.7" />
  </svg>
</template>

<style scoped>
.ember-logo {
  width: 36px;
  height: 36px;
  color: #c2511a;
  transition: transform 0.3s ease, color 0.3s ease;
  flex-shrink: 0;
}
.ember-logo.is-collapsed {
  width: 28px;
  height: 28px;
}
.ember-logo:hover {
  transform: scale(1.08);
  color: #e56832;
}
</style>
