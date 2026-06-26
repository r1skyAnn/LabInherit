<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const form = reactive({ email: '', password: '' })
const loading = ref(false)

async function handleLogin() {
  loading.value = true
  try {
    await auth.login(form.email, form.password)
    const redirect = (route.query.redirect as string) || '/home'
    router.push(redirect)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <h2>登录</h2>
    <el-form @submit.prevent="handleLogin" label-position="top" size="large">
      <el-form-item label="邮箱">
        <el-input v-model="form.email" type="email" placeholder="your@email.com" />
      </el-form-item>
      <el-form-item label="密码">
        <el-input v-model="form.password" type="password" show-password placeholder="输入密码" />
      </el-form-item>
      <el-button type="primary" native-type="submit" :loading="loading" style="width:100%">
        登录
      </el-button>
    </el-form>
    <div class="links">
      <router-link to="/auth/register">使用邀请码注册</router-link>
      <router-link to="/auth/forgot-password">忘记密码？</router-link>
    </div>
  </div>
</template>

<style scoped>
.login-page h2 {
  text-align: center;
  margin: 0 0 1.5rem;
}
.links {
  display: flex;
  justify-content: space-between;
  margin-top: 1rem;
  font-size: 0.85rem;
}
</style>
