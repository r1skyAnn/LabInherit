<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authApi } from '@/api/auth'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const form = reactive({
  token: (route.query.token as string) || '',
  new_password: '',
})
const loading = ref(false)

async function handleReset() {
  loading.value = true
  try {
    await authApi.resetPassword({ token: form.token, new_password: form.new_password })
    ElMessage.success('密码已重置，请重新登录')
    router.push('/auth/login')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="reset-page">
    <h2>重置密码</h2>
    <el-form @submit.prevent="handleReset" label-position="top" size="large">
      <el-form-item label="重置令牌">
        <el-input v-model="form.token" placeholder="从邮件链接中自动获取" />
      </el-form-item>
      <el-form-item label="新密码">
        <el-input v-model="form.new_password" type="password" show-password placeholder="至少 8 个字符" />
      </el-form-item>
      <el-button type="primary" native-type="submit" :loading="loading" style="width:100%">
        重置密码
      </el-button>
    </el-form>
    <div class="links">
      <router-link to="/auth/login">返回登录</router-link>
    </div>
  </div>
</template>

<style scoped>
.reset-page h2 {
  text-align: center;
  margin: 0 0 1.5rem;
}
.links {
  text-align: center;
  margin-top: 1rem;
  font-size: 0.85rem;
}
</style>
