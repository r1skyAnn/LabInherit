<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { announcementsApi, type AnnouncementOut } from '@/api/announcements'
import { projectsApi } from '@/api/projects'
import { notesApi } from '@/api/notes'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()
const announcements = ref<AnnouncementOut[]>([])
const annLoading = ref(true)
const projectCount = ref(0)
const noteCount = ref(0)
const greeting = ref('')

function getGreeting() {
  const h = new Date().getHours()
  if (h < 8) return '早上好'
  if (h < 12) return '上午好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
}

async function load() {
  greeting.value = getGreeting()
  annLoading.value = true
  try {
    const [anns, projs, notes] = await Promise.all([
      announcementsApi.list({ page: 1, page_size: 5 }),
      projectsApi.list({ page_size: 1 }),
      notesApi.list({ page_size: 1 }),
    ])
    announcements.value = anns.data.items
    projectCount.value = projs.data.total
    noteCount.value = notes.data.total
  } finally {
    annLoading.value = false
  }
}

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

onMounted(load)
</script>

<template>
  <div class="home">
    <!-- Hero -->
    <section class="hero">
      <div class="hero-content">
        <p class="greeting">{{ greeting }}{{ auth.user?.display_name ? '，' + auth.user.display_name : '' }}</p>
        <h1 class="hero-title">LabInherit</h1>
        <p class="hero-sub">实验室薪火传舵平台 · 让每一代经验都有迹可循</p>
      </div>
    </section>

    <!-- Stats -->
    <section class="stats-row">
      <div class="stat-card" @click="router.push('/projects')">
        <div class="stat-icon">📂</div>
        <div class="stat-num">{{ projectCount }}</div>
        <div class="stat-label">课题项目</div>
      </div>
      <div class="stat-card" @click="router.push('/projects')">
        <div class="stat-icon">📝</div>
        <div class="stat-num">{{ noteCount }}</div>
        <div class="stat-label">沉淀笔记</div>
      </div>
    </section>

    <!-- Main content -->
    <div class="home-grid">
      <!-- Announcements -->
      <section class="ann-section">
        <div class="section-header">
          <h3>📢 最新公告</h3>
          <el-button text size="small" @click="router.push('/announcements')">查看全部</el-button>
        </div>
        <div class="ann-list" v-loading="annLoading">
          <el-empty v-if="announcements.length === 0" description="暂无公告" :image-size="50" />
          <div v-for="ann in announcements" :key="ann.id" class="ann-item" @click="router.push('/announcements')">
            <div class="ann-left">
              <span v-if="ann.is_pinned" class="pin-icon">📌</span>
              <span class="ann-title">{{ ann.title }}</span>
            </div>
            <div class="ann-right">
              <span class="ann-author">{{ ann.author_display_name }}</span>
              <span class="ann-time">{{ formatDate(ann.created_at) }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Quick links -->
      <section class="quick-section">
        <div class="section-header">
          <h3>快捷入口</h3>
        </div>
        <div class="quick-cards">
          <div class="quick-card" @click="router.push('/projects')">
            <span class="qc-icon">🔬</span>
            <span class="qc-title">课题项目</span>
            <span class="qc-desc">浏览和创建研究课题</span>
          </div>
          <div class="quick-card" @click="router.push('/showcase')">
            <span class="qc-icon">🏆</span>
            <span class="qc-title">成果展示墙</span>
            <span class="qc-desc">论文专利与师兄寄语</span>
          </div>
          <div class="quick-card" @click="router.push('/announcements')">
            <span class="qc-icon">📢</span>
            <span class="qc-title">公告中心</span>
            <span class="qc-desc">实验室最新通知</span>
          </div>
          <div class="quick-card" v-if="!auth.user || auth.user.status !== 'graduated'" @click="router.push('/members')">
            <span class="qc-icon">👥</span>
            <span class="qc-title">成员列表</span>
            <span class="qc-desc">查看实验室成员</span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.home { max-width: 960px; margin: 0 auto; }

/* Hero */
.hero {
  background: #fff;
  border-radius: 16px;
  padding: 2.5rem 2rem;
  margin-bottom: 1.5rem;
  border: 1px solid var(--el-border-color-lighter);
}
.greeting { margin: 0 0 0.25rem; font-size: 0.9rem; color: var(--lab-muted); }
.hero-title { margin: 0 0 0.5rem; font-size: 2rem; font-weight: 700; color: #1a1a2e; }
.hero-sub { margin: 0; font-size: 0.9rem; color: var(--lab-muted); }

/* Stats */
.stats-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}
.stat-card {
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 1.25rem;
  text-align: center;
  cursor: pointer;
  transition: box-shadow 0.2s;
  border: 1px solid var(--el-border-color-lighter);
}
.stat-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
.stat-icon { font-size: 1.5rem; margin-bottom: 0.25rem; }
.stat-num { font-size: 1.8rem; font-weight: 700; color: var(--el-color-primary); }
.stat-label { font-size: 0.8rem; color: var(--lab-muted); margin-top: 0.1rem; }

/* Grid */
.home-grid {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 1.25rem;
}

.section-header {
  display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem;
}
.section-header h3 { margin: 0; font-size: 0.95rem; font-weight: 600; }

/* Announcements */
.ann-list {
  background: var(--el-bg-color);
  border-radius: 12px;
  border: 1px solid var(--el-border-color-lighter);
  padding: 0 1rem;
  min-height: 120px;
}
.ann-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 0.75rem 0; border-bottom: 1px solid var(--el-border-color-lighter);
  cursor: pointer; transition: color 0.15s;
}
.ann-item:last-child { border-bottom: none; }
.ann-item:hover .ann-title { color: var(--el-color-primary); }
.ann-left { display: flex; align-items: center; gap: 0.4rem; min-width: 0; }
.ann-title { font-size: 0.88rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pin-icon { flex-shrink: 0; font-size: 0.8rem; }
.ann-right { display: flex; gap: 0.75rem; flex-shrink: 0; margin-left: 0.5rem; }
.ann-author { font-size: 0.78rem; color: var(--lab-muted); }
.ann-time { font-size: 0.76rem; color: var(--lab-muted); }

/* Quick links */
.quick-cards {
  display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;
}
.quick-card {
  background: var(--el-bg-color);
  border-radius: 10px;
  border: 1px solid var(--el-border-color-lighter);
  padding: 1rem;
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s;
  display: flex; flex-direction: column; gap: 0.25rem;
}
.quick-card:hover { border-color: var(--el-color-primary-light-3); box-shadow: 0 2px 10px rgba(64,158,255,0.08); }
.qc-icon { font-size: 1.3rem; }
.qc-title { font-size: 0.88rem; font-weight: 600; }
.qc-desc { font-size: 0.74rem; color: var(--lab-muted); }
</style>
