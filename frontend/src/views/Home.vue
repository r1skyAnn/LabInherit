<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { announcementsApi, type AnnouncementOut } from '@/api/announcements'
import { projectsApi } from '@/api/projects'
import { notesApi } from '@/api/notes'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import EmberLogo from '@/components/EmberLogo.vue'

const auth = useAuthStore()
const router = useRouter()
const announcements = ref<AnnouncementOut[]>([])
const annLoading = ref(true)
const projectCount = ref(0)
const noteCount = ref(0)
const memberCount = ref(0)
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
      announcementsApi.list({ page: 1, page_size: 4 }),
      projectsApi.list({ page_size: 1 }),
      notesApi.list({ page_size: 1 }),
    ])
    announcements.value = anns.data.items
    projectCount.value = projs.data.total
    noteCount.value = notes.data.total
    memberCount.value = 0 // fetched by admin only
  } finally {
    annLoading.value = false
  }
}

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}

onMounted(load)
</script>

<template>
  <div class="home">
    <!-- Hero — scholar's greeting -->
    <section class="home-hero">
      <div class="hero-brand">
        <EmberLogo />
        <div class="hero-text">
          <p class="greeting">{{ greeting }}{{ auth.user?.display_name ? '，' + auth.user.display_name : '' }}</p>
          <p class="hero-desc">实验室薪火传舵平台 — 让每一代的经验都有迹可循</p>
        </div>
      </div>
    </section>

    <!-- Stats — three numbers that tell the lab's story -->
    <section class="home-stats">
      <div class="stat-item" @click="router.push('/projects')">
        <span class="stat-num">{{ projectCount }}</span>
        <span class="stat-label">课题项目</span>
      </div>
      <div class="stat-divider"></div>
      <div class="stat-item" @click="router.push('/projects')">
        <span class="stat-num">{{ noteCount }}</span>
        <span class="stat-label">沉淀笔记</span>
      </div>
      <div class="stat-divider"></div>
      <div class="stat-item" @click="router.push('/members')">
        <span class="stat-num">—</span>
        <span class="stat-label">传承成员</span>
      </div>
    </section>

    <!-- Content grid -->
    <div class="home-grid">
      <!-- Announcements — left bar cards -->
      <section class="home-announcements">
        <div class="lab-section-header">
          <h3>最新公告</h3>
          <el-button text size="small" @click="router.push('/announcements')">查看全部 &rarr;</el-button>
        </div>
        <div v-loading="annLoading" class="ann-list">
          <el-empty v-if="announcements.length === 0" description="暂无公告" :image-size="48" />
          <div
            v-for="ann in announcements" :key="ann.id"
            class="ann-item lab-card lab-card--accent"
            @click="router.push('/announcements')"
          >
            <div class="ann-main">
              <span v-if="ann.is_pinned" class="ann-pin">置顶</span>
              <span class="ann-title">{{ ann.title }}</span>
            </div>
            <div class="ann-meta">
              <span>{{ ann.author_display_name }}</span>
              <span>{{ formatDate(ann.created_at) }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Quick links -->
      <section class="home-quick">
        <div class="lab-section-header">
          <h3>快捷入口</h3>
        </div>
        <div class="quick-list">
          <div class="quick-item lab-card" @click="router.push('/showcase')">
            <span class="qi-icon">🏆</span>
            <span class="qi-label">成果展示墙</span>
          </div>
          <div class="quick-item lab-card" @click="router.push('/guides')">
            <span class="qi-icon">📖</span>
            <span class="qi-label">新人指南</span>
          </div>
          <div class="quick-item lab-card" @click="router.push('/alumni')">
            <span class="qi-icon">🎓</span>
            <span class="qi-label">毕业专区</span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.home { max-width: 900px; margin: 0 auto; }

/* ── Hero ────────────────────────────────── */
.home-hero {
  margin-bottom: 1.75rem;
}
.hero-brand {
  display: flex; align-items: center; gap: 1.25rem;
}
.hero-brand :deep(.ember-logo) {
  width: 56px; height: 56px;
}
.hero-text { flex: 1; }
.greeting {
  margin: 0 0 0.15rem; font-size: 1.05rem; font-weight: 600;
  color: var(--ink);
}
.hero-desc {
  margin: 0; font-size: 0.82rem; color: var(--stone);
}

/* ── Stats ───────────────────────────────── */
.home-stats {
  display: flex; align-items: center;
  background: #fefdf9;
  border-radius: 6px;
  border: 1px solid var(--el-border-color-light);
  margin-bottom: 1.75rem;
}
.stat-item {
  flex: 1; text-align: center; padding: 1.1rem 0.75rem;
  display: flex; flex-direction: column; gap: 0.15rem;
  cursor: pointer; transition: background 0.15s;
}
.stat-item:hover { background: var(--glow); }
.stat-item:first-child { border-radius: 6px 0 0 6px; }
.stat-item:last-child { border-radius: 0 6px 6px 0; }
.stat-num {
  font-size: 1.5rem; font-weight: 700; color: var(--ember);
  letter-spacing: -0.02em;
}
.stat-label { font-size: 0.76rem; color: var(--stone); }
.stat-divider {
  width: 1px; height: 32px; background: var(--el-border-color-extra-light);
  flex-shrink: 0;
}

/* ── Grid ────────────────────────────────── */
.home-grid {
  display: grid;
  grid-template-columns: 1fr 260px;
  gap: 1.5rem;
}

/* ── Announcements ───────────────────────── */
.ann-list {
  display: flex; flex-direction: column; gap: 0.5rem;
  min-height: 120px;
}
.ann-item {
  padding: 0.75rem 1rem;
  cursor: pointer;
}
.ann-main {
  display: flex; align-items: center; gap: 0.45rem;
  margin-bottom: 0.25rem;
}
.ann-pin {
  font-size: 0.65rem; padding: 1px 6px;
  background: var(--glow); color: var(--ember);
  border-radius: 3px; flex-shrink: 0;
  font-weight: 600;
}
.ann-title {
  font-size: 0.88rem; overflow: hidden;
  text-overflow: ellipsis; white-space: nowrap;
}
.ann-meta {
  display: flex; gap: 0.6rem; font-size: 0.73rem; color: var(--stone);
  padding-left: 0.5rem;
}

/* ── Quick links ─────────────────────────── */
.quick-list {
  display: flex; flex-direction: column; gap: 0.5rem;
}
.quick-item {
  padding: 0.85rem 1rem;
  display: flex; align-items: center; gap: 0.6rem;
  cursor: pointer;
}
.qi-icon { font-size: 1.1rem; flex-shrink: 0; }
.qi-label { font-size: 0.85rem; font-weight: 500; }
</style>
