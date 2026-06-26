<script setup lang="ts">
import { reactive, ref } from 'vue'
import { authApi } from '@/api/auth'
import { ElMessage } from 'element-plus'

const form = reactive({ email: '' })
const loading = ref(false)
const sent = ref(false)

async function handleSubmit() {
  loading.value = true
  try {
    await authApi.forgotPassword({ email: form.email })
    sent.value = true
    ElMessage.success('如果该邮箱已注册，重置链接已发送（开发模式请查看控制台）')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="forgot-page">
    <h2>忘记密码</h2>
    <p v-if="!sent" class="desc">输入注册邮箱，我们将发送重置链接。</p>
    <el-result v-if="sent" icon="success" title="已发送" sub-title="请检查邮箱（开发模式查看控制台输出）" />
    <el-form v-if="!sent" @submit.prevent="handleSubmit" label-position="top" size="large">
      <el-form-item label="邮箱">
        <el-input v-model="form.email" type="email" placeholder="your@email.com" />
      </el-form-item>
      <el-button type="primary" native-type="submit" :loading="loading" style="width:100%">
        发送重置链接
      </el-button>
    </el-form>
    <div class="links">
      <router-link to="/auth/login">返回登录</router-link>
    </div>
  </div>
</template>

<style scoped>
.forgot-page h2 {
  text-align: center;
  margin: 0 0 0.5rem;
}
.desc {
  text-align: center;
  color: var(--lab-muted);
  font-size: 0.85rem;
  margin-bottom: 1.5rem;
}
.links {
  text-align: center;
  margin-top: 1rem;
  font-size: 0.85rem;
}
</style>
