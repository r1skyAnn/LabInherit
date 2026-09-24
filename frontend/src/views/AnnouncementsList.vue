<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { StarFilled } from '@element-plus/icons-vue'
import { announcementsApi, type AnnouncementOut } from '@/api/announcements'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const announcements = ref<AnnouncementOut[]>([])
const total = ref(0)
const loading = ref(false)
const showForm = ref(false)
const editingAnn = ref<AnnouncementOut | null>(null)
const formRef = ref<FormInstance>()

const form = ref({ title: '', content: '', is_pinned: false })
const saving = ref(false)
const page = ref(1)
const pageSize = ref(10)

async function load() {
  loading.value = true
  try {
    const resp = await announcementsApi.list({ page: page.value, page_size: pageSize.value })
    announcements.value = resp.data.items
    total.value = resp.data.total
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingAnn.value = null
  form.value = { title: '', content: '', is_pinned: false }
  showForm.value = true
}

function openEdit(ann: AnnouncementOut) {
  editingAnn.value = ann
  form.value = { title: ann.title, content: ann.content, is_pinned: ann.is_pinned }
  showForm.value = true
}

async function handleSaved() {
  showForm.value = false
  editingAnn.value = null
  await load()
}

async function handleDelete(ann: AnnouncementOut) {
  try {
    await ElMessageBox.confirm('确定要删除这条公告吗？', '删除公告', { type: 'warning' })
    await announcementsApi.remove(ann.id)
    ElMessage.success('公告已删除')
    await load()
  } catch {
    // cancelled
  }
}

async function submitForm() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    if (editingAnn.value) {
      await announcementsApi.update(editingAnn.value.id, form.value)
      ElMessage.success('公告已更新')
    } else {
      await announcementsApi.create(form.value)
      ElMessage.success('公告已发布')
    }
    await handleSaved()
  } finally {
    saving.value = false
  }
}

function formatDate(d: string) {
  return new Date(d).toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

onMounted(load)
</script>

<template>
  <div class="ann-page">
    <div class="page-header">
      <h2>公告中心</h2>
      <div class="header-actions">
        <el-button type="primary" @click="openCreate">+ 发布公告</el-button>
      </div>
    </div>

    <el-empty v-if="!loading && announcements.length === 0" description="暂无公告" style="margin-top:4rem" />

    <div v-else class="ann-list">
      <el-card
        v-for="ann in announcements"
        :key="ann.id"
        class="ann-card"
        :class="{ 'ann-card--pinned': ann.is_pinned }"
        shadow="hover"
      >
        <div class="ann-header">
          <div class="ann-title-row">
            <span v-if="ann.is_pinned" class="pin-badge">
              <el-icon><StarFilled /></el-icon>
              置顶
            </span>
            <h3 class="ann-title">{{ ann.title }}</h3>
          </div>
          <div class="ann-meta">
            <span>{{ ann.author_display_name ?? '—' }}</span>
            <span class="meta-dot">·</span>
            <span>{{ formatDate(ann.created_at) }}</span>
          </div>
        </div>

        <div class="ann-content">{{ ann.content }}</div>

        <div class="ann-actions" v-if="auth.user?.id === ann.author_id || auth.isOwner">
          <el-button size="small" @click="openEdit(ann)">编辑</el-button>
          <el-button size="small" type="danger" plain @click="handleDelete(ann)">删除</el-button>
        </div>
      </el-card>
    </div>

    <div class="summary">
      共 {{ total }} 条公告
      <el-pagination
        v-if="total > pageSize"
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="load"
        style="margin-top:1rem; justify-content:center"
      />
    </div>

    <el-dialog v-model="showForm" :title="editingAnn ? '编辑公告' : '发布公告'" width="580px">
      <el-form ref="formRef" :model="form" label-width="80px" class="ann-form">
        <el-form-item label="标题" prop="title" :rules="[{ required: true, message: '请输入标题', trigger: 'blur' }]">
          <el-input v-model="form.title" placeholder="公告标题" maxlength="200" show-word-limit />
        </el-form-item>
        <el-form-item label="内容" prop="content" :rules="[{ required: true, message: '请输入内容', trigger: 'blur' }]">
          <el-input v-model="form.content" type="textarea" :rows="5" placeholder="公告正文内容" />
        </el-form-item>
        <el-form-item label="置顶">
          <el-switch v-model="form.is_pinned" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showForm = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitForm">
          {{ editingAnn ? '保存' : '发布' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>
<style scoped>
.ann-page { max-width: 800px; margin: 0 auto; }

.page-header {
  display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem;
}
.page-header h2 {
  margin: 0; font-size: 1.15rem; font-weight: 700;
  padding-left: 0.65rem; border-left: 3px solid var(--ember);
}
.header-actions { display: flex; gap: 0.75rem; }

.ann-list { display: flex; flex-direction: column; gap: 1rem; }

.ann-card {
  border-radius: 6px !important; transition: transform 0.15s, box-shadow 0.15s, border-left-color 0.2s !important;
  border: 1px solid var(--el-border-color-light) !important;
  border-left: 3px solid transparent !important;
}
.ann-card:hover {
  transform: translateX(2px); box-shadow: 0 2px 12px rgba(0,0,0,0.05) !important;
  border-left-color: var(--ember) !important;
}
.ann-card--pinned { border-left-color: var(--ember) !important; }

.ann-header { margin-bottom: 0.65rem; }
.ann-title-row { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.3rem; }
.pin-badge {
  display: inline-flex; align-items: center; gap: 0.2rem;
  font-size: 0.68rem; color: var(--ember);
  background: var(--glow); padding: 1px 6px; border-radius: 3px; flex-shrink: 0; font-weight: 600;
}
.ann-title { margin: 0; font-size: 1rem; font-weight: 600; }
.ann-meta { font-size: 0.78rem; color: var(--stone); display: flex; gap: 0.35rem; }
.meta-dot { opacity: 0.5; }

.ann-content {
  font-size: 0.88rem; color: var(--ink); line-height: 1.7;
  white-space: pre-wrap; margin-bottom: 0.65rem;
}
.ann-actions {
  display: flex; gap: 0.5rem; padding-top: 0.5rem;
  border-top: 1px solid var(--el-border-color-extra-light);
}

.summary { margin-top: 1rem; color: var(--lab-muted); font-size: 0.85rem; }

.ann-form { padding: 0.5rem 0.5rem 0; }
</style>
