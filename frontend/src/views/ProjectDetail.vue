<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { projectsApi, type ProjectOut } from '@/api/projects'
import { commentsApi, type CommentOut } from '@/api/comments'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import ProjectForm from '@/components/projects/ProjectForm.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const projectId = Number(route.params.projectId)
const project = ref<ProjectOut | null>(null)
const loading = ref(true)
const showEdit = ref(false)
const openAsks = ref<CommentOut[]>([])
const asksLoading = ref(false)

const statusMap: Record<string, { label: string; type: string }> = {
  planning: { label: '规划中', type: 'info' },
  active: { label: '进行中', type: 'success' },
  paused: { label: '已暂停', type: 'warning' },
  completed: { label: '已完成', type: '' },
  abandoned: { label: '已废弃', type: 'danger' },
}
const priorityMap: Record<string, { label: string; type: string }> = {
  high: { label: '高', type: 'danger' },
  medium: { label: '中', type: 'warning' },
  low: { label: '低', type: 'info' },
}

function formatDate(d: string | null) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

const isOwner = () => project.value && project.value.created_by === auth.user?.id

const canEdit = () => isOwner() || auth.isOwner

async function load() {
  loading.value = true
  try {
    project.value = (await projectsApi.get(projectId)).data
  } finally {
    loading.value = false
  }
}

async function loadAsks() {
  asksLoading.value = true
  try {
    openAsks.value = (await commentsApi.listProjectAsks(projectId)).data.items
  } finally {
    asksLoading.value = false
  }
}

function goToNote(noteId: number) {
  router.push(`/projects/${projectId}/notes/${noteId}`)
}

function openEdit() {
  showEdit.value = true
}

function handleSaved() {
  showEdit.value = false
  load()
}

async function handleDelete() {
  try {
    await ElMessageBox.confirm('确定删除该项目吗？所有关联数据将不可恢复。', '确认删除', {
      confirmButtonText: '删除',
      type: 'warning',
    })
  } catch {
    return
  }
  await projectsApi.remove(projectId)
  ElMessage.success('项目已删除')
  router.push('/projects')
}

onMounted(() => { load(); loadAsks() })
</script>

<template>
  <div class="project-detail" v-loading="loading">
    <div class="page-header">
      <el-button text @click="router.push('/projects')">
        <el-icon><ArrowLeft /></el-icon>
        返回项目列表
      </el-button>
    </div>

    <template v-if="project">
      <div class="project-hero">
        <div class="hero-top">
          <h2>{{ project.title }}</h2>
          <div class="hero-tags">
            <el-tag size="small" :type="statusMap[project.status]?.type as any" effect="plain">
              {{ statusMap[project.status]?.label }}
            </el-tag>
            <el-tag size="small" :type="priorityMap[project.priority]?.type as any" effect="plain">
              {{ priorityMap[project.priority]?.label }}优先级
            </el-tag>
            <el-tag size="small" :type="project.is_public ? 'success' : 'warning'" effect="plain">
              {{ project.is_public ? '公开' : '私有' }}
            </el-tag>
          </div>
        </div>
        <p v-if="project.description" class="hero-desc">{{ project.description }}</p>
        <p v-else class="hero-desc hero-desc--empty">暂无描述</p>

        <div class="hero-meta">
          <div class="meta-item" v-if="project.category_name">
            <span class="meta-label">所属分类</span>
            <span class="meta-value">{{ project.category_name }}</span>
          </div>
          <div class="meta-item" v-if="project.tech_stack">
            <span class="meta-label">技术栈</span>
            <span class="meta-value">{{ project.tech_stack }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">创建人</span>
            <span class="meta-value">{{ project.creator_display_name ?? '—' }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">创建时间</span>
            <span class="meta-value">{{ formatDate(project.created_at) }}</span>
          </div>
          <div class="meta-item" v-if="project.started_at || project.ended_at">
            <span class="meta-label">起止时间</span>
            <span class="meta-value">
              {{ formatDate(project.started_at) }} — {{ formatDate(project.ended_at) }}
            </span>
          </div>
        </div>

        <div class="hero-links" v-if="project.repo_url || project.demo_url || project.zip_url">
          <a v-if="project.repo_url" :href="project.repo_url" target="_blank" rel="noreferrer" class="link-btn">代码仓库</a>
          <a v-if="project.demo_url" :href="project.demo_url" target="_blank" rel="noreferrer" class="link-btn">在线演示</a>
          <a v-if="project.zip_url" :href="project.zip_url" target="_blank" rel="noreferrer" class="link-btn">📦 源码压缩包</a>
        </div>

        <div class="hero-actions" v-if="canEdit()">
          <el-button @click="openEdit">编辑</el-button>
          <el-button type="danger" plain @click="handleDelete">删除</el-button>
        </div>
      </div>

      <!-- Open Asks -->
      <div class="asks-section" v-if="openAsks.length > 0" v-loading="asksLoading">
        <h3 class="asks-title">⏳ 待处理追问 ({{ openAsks.length }})</h3>
        <div v-for="a in openAsks" :key="a.id" class="ask-item" @click="goToNote(a.target_id)">
          <div class="ask-item-header">
            <span class="ask-badge">{{ a.status === 'open' ? '待回复' : a.status }}</span>
            <span class="ask-author">{{ a.author_name }}</span>
          </div>
          <div class="ask-content">{{ a.content.slice(0, 100) }}{{ a.content.length > 100 ? '...' : '' }}</div>
        </div>
      </div>
      <div class="asks-section" v-else-if="!asksLoading">
        <h3 class="asks-title">⏳ 追问 (0)</h3>
        <p class="asks-empty">暂无待处理追问</p>
      </div>

      <el-divider />

      <el-dialog v-model="showEdit" title="编辑项目" width="640px" destroy-on-close>
        <ProjectForm :project="project" @saved="handleSaved" @cancel="showEdit = false" />
      </el-dialog>
    </template>
  </div>
</template>

<style scoped>
.project-hero {
  background: #fefdf9; border-radius: 6px;
  border: 1px solid var(--el-border-color-light); padding: 1.75rem 2rem;
  max-width: 800px;
}
.page-header { max-width: 800px; margin-bottom: 0.75rem; }
.hero-top {
  display: flex; align-items: center; gap: 1rem; margin-bottom: 0.65rem;
}
.hero-top h2 {
  margin: 0; font-size: 1.3rem; font-weight: 700;
  padding-left: 0.65rem; border-left: 3px solid var(--ember);
}
.hero-tags { display: flex; gap: 0.2rem; }
.hero-desc { color: var(--ink); line-height: 1.65; margin: 0 0 1rem; font-size: 0.9rem; }
.hero-desc--empty { font-style: italic; color: var(--stone); }
.hero-meta { display: flex; flex-wrap: wrap; gap: 1.25rem; font-size: 0.84rem; margin-bottom: 1rem; }
.meta-item { display: flex; flex-direction: column; }
.meta-label { color: var(--stone); font-size: 0.73rem; }
.meta-value { color: var(--ink); }
.hero-links { display: flex; gap: 0.65rem; margin-bottom: 1rem; }
.link-btn {
  display: inline-block; padding: 0.35rem 0.7rem;
  border: 1px solid var(--ember); border-radius: 4px;
  color: var(--ember); text-decoration: none; font-size: 0.83rem;
}
.link-btn:hover { background: var(--glow); }
.hero-actions { display: flex; gap: 0.5rem; }

.asks-section { margin: 1.25rem 0; max-width: 800px; }
.asks-title { font-size: 0.9rem; font-weight: 600; margin: 0 0 0.5rem; color: var(--ink); }
.asks-empty { font-size: 0.84rem; color: var(--stone); }
.ask-item {
  padding: 0.6rem 0.75rem; margin-bottom: 0.3rem;
  background: var(--glow); border-radius: 4px; cursor: pointer;
  border-left: 3px solid var(--ember); transition: background 0.15s;
}
.ask-item:hover { background: #fde9d8; }
.ask-item-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.15rem; }
.ask-badge {
  font-size: 0.68rem; background: var(--ember); color: #fff;
  padding: 1px 6px; border-radius: 3px; font-weight: 600;
}
.ask-author { font-size: 0.78rem; font-weight: 600; }
.ask-content { font-size: 0.8rem; color: var(--ink); }
</style>
