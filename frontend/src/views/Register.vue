<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { invitesApi } from '@/api/invites'
import { ElMessage } from 'element-plus'

const router = useRouter()
const form = reactive({
  code: '',
  email: '',
  password: '',
  display_name: '',
  gender: '' as string,
  enrollment_year: null as number | null,
  research_direction: '',
})
const loading = ref(false)

async function handleRegister() {
  loading.value = true
  try {
    const base = {
      email: form.email,
      password: form.password,
      display_name: form.display_name,
      enrollment_year: form.enrollment_year,
      research_direction: form.research_direction || undefined,
      gender: form.gender || undefined,
    }
    if (form.code.trim()) {
      await invitesApi.redeem({ code: form.code.trim(), ...base })
      ElMessage.success('邀请码注册成功，已自动通过')
    } else {
      await invitesApi.register(base)
      ElMessage.success('注册申请已提交，请等待管理员审核')
    }
    router.push('/auth/login')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="register-page">
    <h2>注册</h2>
    <el-form @submit.prevent="handleRegister" label-position="top" size="large">
      <el-form-item label="邀请码（可选）">
        <el-input v-model="form.code" placeholder="有邀请码可自动通过审核" />
      </el-form-item>
      <el-form-item label="邮箱" required>
        <el-input v-model="form.email" type="email" placeholder="your@email.com" />
      </el-form-item>
      <el-form-item label="显示名" required>
        <el-input v-model="form.display_name" placeholder="你的名字" />
      </el-form-item>
      <el-form-item label="性别">
        <el-select v-model="form.gender" style="width:100%" clearable>
          <el-option label="男" value="男" />
          <el-option label="女" value="女" />
        </el-select>
      </el-form-item>
      <el-form-item label="密码" required>
        <el-input v-model="form.password" type="password" show-password placeholder="至少 8 个字符" />
      </el-form-item>
      <el-form-item label="入学年份">
        <el-input-number v-model="form.enrollment_year" :min="2000" :max="2099" style="width:100%" />
      </el-form-item>
      <el-form-item label="研究方向">
        <el-input v-model="form.research_direction" placeholder="如：计算机视觉" />
      </el-form-item>
      <el-button type="primary" native-type="submit" :loading="loading" style="width:100%">
        提交注册
      </el-button>
    </el-form>
    <div class="links">
      <router-link to="/auth/login">已有账号？去登录</router-link>
    </div>
  </div>
</template>

<style scoped>
.register-page h2 {
  text-align: center;
  margin: 0 0 1.5rem;
}
.links {
  text-align: center;
  margin-top: 1rem;
  font-size: 0.85rem;
}
</style>
