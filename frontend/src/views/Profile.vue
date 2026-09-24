<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { usersApi } from '@/api/users'
import { filesApi } from '@/api/files'
import { ElMessage } from 'element-plus'
import { Upload, UserFilled } from '@element-plus/icons-vue'
import type { AxiosResponse } from 'axios'
import type { FileOut } from '@/api/files'

const auth = useAuthStore()

const profileForm = reactive({
  display_name: '',
  gender: '' as string,
  enrollment_year: null as number | null,
  graduation_year: null as number | null,
  research_direction: '',
  current_affiliation: '',
  bio: '',
  avatar_url: null as string | null,
})
const profileLoading = ref(false)
const avatarUploading = ref(false)
const avatarInput = ref<HTMLInputElement | null>(null)

const pwdForm = reactive({ old_password: '', new_password: '' })
const pwdLoading = ref(false)

onMounted(() => {
  const u = auth.user
  if (u) {
    profileForm.display_name = u.display_name
    profileForm.gender = u.profile?.gender ?? ''
    profileForm.enrollment_year = u.profile?.enrollment_year ?? null
    profileForm.graduation_year = u.profile?.graduation_year ?? null
    profileForm.research_direction = u.profile?.research_direction ?? ''
    profileForm.current_affiliation = u.profile?.current_affiliation ?? ''
    profileForm.bio = u.profile?.bio ?? ''
    profileForm.avatar_url = u.profile?.avatar_url ?? null
  }
})

function avatarUrl(url: string | null) {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return `${import.meta.env.VITE_BACKEND_URL ?? ''}${url}`
}

function triggerAvatar() { avatarInput.value?.click() }

async function handleAvatarUpload(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  if (!file.type.startsWith('image/')) { ElMessage.error('仅支持图片格式'); return }
  avatarUploading.value = true
  try {
    const resp: AxiosResponse<FileOut> = await filesApi.upload(file)
    profileForm.avatar_url = resp.data.url
    ElMessage.success('头像上传成功，保存后生效')
  } catch { ElMessage.error('上传失败') }
  finally { avatarUploading.value = false }
}

async function saveProfile() {
  profileLoading.value = true
  try {
    const resp = await usersApi.updateMe({
      display_name: profileForm.display_name,
      gender: profileForm.gender || undefined,
      enrollment_year: profileForm.enrollment_year,
      graduation_year: profileForm.graduation_year,
      research_direction: profileForm.research_direction || undefined,
      current_affiliation: profileForm.current_affiliation || undefined,
      bio: profileForm.bio || undefined,
      avatar_url: profileForm.avatar_url ?? undefined,
    })
    auth.user = resp.data
    localStorage.setItem('labinherit_user', JSON.stringify(resp.data))
    ElMessage.success('个人资料已更新')
  } finally {
    profileLoading.value = false
  }
}

async function changePassword() {
  pwdLoading.value = true
  try {
    await usersApi.changePassword(pwdForm)
    ElMessage.success('密码已修改')
    pwdForm.old_password = ''
    pwdForm.new_password = ''
  } finally {
    pwdLoading.value = false
  }
}
</script>

<template>
  <div class="profile-page">
    <h2>个人资料</h2>

    <el-card class="section">
      <template #header>头像</template>
      <div class="avatar-section">
        <div class="avatar-preview">
          <img v-if="profileForm.avatar_url" :src="avatarUrl(profileForm.avatar_url)" class="avatar-img" />
          <el-icon v-else class="avatar-placeholder"><UserFilled /></el-icon>
        </div>
        <div class="avatar-actions">
          <el-button :loading="avatarUploading" @click="triggerAvatar">
            <el-icon><Upload /></el-icon> 上传头像
          </el-button>
          <input ref="avatarInput" type="file" accept="image/*" style="display:none" @change="handleAvatarUpload" />
          <p class="avatar-hint">支持 JPG / PNG / WebP，保存后生效</p>
        </div>
      </div>
    </el-card>

    <el-card class="section">
      <template #header>基本信息</template>
      <el-form label-position="top" size="large">
        <el-form-item label="邮箱">
          <el-input :model-value="auth.user?.email" disabled />
        </el-form-item>
        <el-form-item label="角色">
          <el-tag>{{ auth.user?.role }}</el-tag>
        </el-form-item>
        <el-form-item label="状态">
          <el-tag :type="auth.user?.status === 'active' ? 'success' : 'warning'">
            {{ auth.user?.status }}
          </el-tag>
        </el-form-item>
        <el-form-item label="显示名">
          <el-input v-model="profileForm.display_name" />
        </el-form-item>
        <el-form-item label="性别">
          <el-select v-model="profileForm.gender" style="width:100%" clearable>
            <el-option label="男" value="男" />
            <el-option label="女" value="女" />
          </el-select>
        </el-form-item>
        <el-form-item label="入学年份">
          <el-input-number v-model="profileForm.enrollment_year" :min="2000" :max="2099" style="width:100%" />
        </el-form-item>
        <el-form-item label="毕业年份">
          <el-input-number v-model="profileForm.graduation_year" :min="2000" :max="2099" style="width:100%" />
        </el-form-item>
        <el-form-item label="研究方向">
          <el-input v-model="profileForm.research_direction" />
        </el-form-item>
        <el-form-item label="当前单位">
          <el-input v-model="profileForm.current_affiliation" />
        </el-form-item>
        <el-form-item label="个人简介">
          <el-input v-model="profileForm.bio" type="textarea" :rows="3" />
        </el-form-item>
        <el-button type="primary" :loading="profileLoading" @click="saveProfile">保存</el-button>
      </el-form>
    </el-card>

    <el-card class="section">
      <template #header>修改密码</template>
      <el-form @submit.prevent="changePassword" label-position="top" size="large">
        <el-form-item label="旧密码">
          <el-input v-model="pwdForm.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="pwdForm.new_password" type="password" show-password placeholder="至少 8 个字符" />
        </el-form-item>
        <el-button type="primary" native-type="submit" :loading="pwdLoading">修改密码</el-button>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.profile-page {
  max-width: 600px;
  margin: 0 auto;
}
.profile-page h2 {
  margin: 0 0 1.5rem;
}
.section {
  margin-bottom: 1.5rem;
}
.avatar-section {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}
.avatar-preview {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  overflow: hidden;
  background: var(--el-fill-color-light);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.avatar-placeholder {
  font-size: 2rem;
  color: var(--el-text-color-placeholder);
}
.avatar-actions {
  flex: 1;
}
.avatar-hint {
  font-size: 0.78rem;
  color: var(--el-text-color-secondary);
  margin: 0.35rem 0 0;
}
</style>
