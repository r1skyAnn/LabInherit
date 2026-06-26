<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { adminApi, type DashboardOut, type UnansweredAsk } from '@/api/admin'

const router = useRouter()
const data = ref<DashboardOut | null>(null)
const loading = ref(true)

const statusLabel: Record<string, string> = {
  planning: '规划中', active: '进行中', paused: '已暂停', completed: '已完成', abandoned: '已放弃',
}
const statusType: Record<string, string> = {
  planning: 'info', active: 'success', paused: 'warning', completed: '', abandoned: 'danger',
}

async function load() {
  loading.value = true
  try {
    data.value = (await adminApi.dashboard()).data
  } finally {
    loading.value = false
  }
}

function goAsk(ask: UnansweredAsk) {
  router.push(`/projects/${ask.project_id}/notes/${ask.note_id}`)
}

onMounted(load)
</script>

<template>
  <div class="dashboard" v-loading="loading">
    <h2 class="page-title">管理看板</h2>

    <template v-if="data">
      <!-- KPI Cards -->
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-value">{{ data.kpis.users.active }}</div>
          <div class="kpi-label">在读</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-value">{{ data.kpis.users.graduated }}</div>
          <div class="kpi-label">已毕业</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-value">{{ data.kpis.users.archived }}</div>
          <div class="kpi-label">已归档</div>
        </div>
        <div class="kpi-card warn">
          <div class="kpi-value">{{ data.kpis.pending_audits }}</div>
          <div class="kpi-label">待审核</div>
        </div>
        <div class="kpi-card warn">
          <div class="kpi-value">{{ data.kpis.open_asks }}</div>
          <div class="kpi-label">待处理追问</div>
        </div>
        <div class="kpi-card danger" v-if="data.kpis.stale_projects > 0">
          <div class="kpi-value">{{ data.kpis.stale_projects }}</div>
          <div class="kpi-label">断代项目 ({{ '>' }}90天)</div>
        </div>
        <div class="kpi-card danger" v-if="data.kpis.failed_emails > 0">
          <div class="kpi-value">{{ data.kpis.failed_emails }}</div>
          <div class="kpi-label">失败邮件</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-value">{{ data.kpis.notes_total }}</div>
          <div class="kpi-label">笔记总数</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-value">{{ data.kpis.comments_total }}</div>
          <div class="kpi-label">评论总数</div>
        </div>
      </div>

      <div class="dash-grid">
        <!-- Unanswered Asks -->
        <el-card class="dash-card" shadow="hover">
          <template #header>
            <span class="card-title">⏳ 待处理追问 ({{ data.unanswered_asks.length }})</span>
          </template>
          <div v-if="data.unanswered_asks.length === 0" class="empty-hint">暂无</div>
          <div v-for="a in data.unanswered_asks" :key="a.id" class="ask-row" @click="goAsk(a)">
            <div class="ask-title">
              <span class="ask-badge">{{ a.days_open }}天</span>
              {{ a.content.slice(0, 60) }}{{ a.content.length > 60 ? '...' : '' }}
            </div>
            <div class="ask-meta">
              <span>{{ a.asker_name }}</span>
              <span>· 笔记《{{ a.note_title }}》</span>
            </div>
          </div>
        </el-card>

        <!-- Stale Projects -->
        <el-card class="dash-card" shadow="hover">
          <template #header>
            <span class="card-title">📦 断代项目 ({{ data.stale_projects.length }})</span>
          </template>
          <div v-if="data.stale_projects.length === 0" class="empty-hint">暂无，保持得好！</div>
          <div v-for="p in data.stale_projects" :key="p.id" class="item-row">
            <div class="item-name">{{ p.title }}</div>
            <div class="item-meta">
              <el-tag size="small" :type="statusType[p.status] as any" effect="plain">
                {{ statusLabel[p.status] ?? p.status }}
              </el-tag>
              <span>{{ p.creator_display_name }}</span>
            </div>
          </div>
        </el-card>

        <!-- Hot Notes -->
        <el-card class="dash-card" shadow="hover">
          <template #header>
            <span class="card-title">🔥 热帖排行</span>
          </template>
          <div v-if="data.hot_notes.length === 0" class="empty-hint">暂无</div>
          <div v-for="(n, i) in data.hot_notes" :key="n.id" class="item-row" @click="goProjectNote(n.project_id, n.id)">
            <div class="item-name">
              <span class="rank-num">{{ i + 1 }}</span>
              {{ n.title }}
            </div>
            <div class="item-meta">
              <span>👍 {{ n.like_count }}</span>
              <span>💬 {{ n.comment_count }}</span>
              <span>· {{ n.project_title }}</span>
            </div>
          </div>
        </el-card>

        <!-- Failed Emails -->
        <el-card class="dash-card" shadow="hover" v-if="data.failed_emails.length > 0">
          <template #header>
            <span class="card-title" style="color:var(--el-color-danger)">📧 失败邮件 ({{ data.failed_emails.length }})</span>
          </template>
          <div v-for="e in data.failed_emails" :key="e.id" class="item-row">
            <div class="item-name">{{ e.subject }}</div>
            <div class="item-meta">
              <span>{{ e.to_email }}</span>
              <el-tag size="small" type="danger" effect="plain">重试{{ e.retry_count }}次</el-tag>
              <span class="error-text" v-if="e.last_error">{{ e.last_error.slice(0, 80) }}</span>
            </div>
          </div>
        </el-card>
      </div>
    </template>
  </div>
</template>

<style scoped>
.dashboard { max-width: 1300px; margin: 0 auto; }
.page-title { margin: 0 0 1.25rem; font-size: 1.2rem; }

/* KPI */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}
.kpi-card {
  background: var(--el-bg-color);
  border-radius: 10px;
  padding: 1rem;
  text-align: center;
  border-left: 3px solid var(--el-color-primary);
}
.kpi-card.warn { border-left-color: var(--el-color-warning); }
.kpi-card.danger { border-left-color: var(--el-color-danger); }
.kpi-value { font-size: 1.6rem; font-weight: 700; color: var(--el-text-color-primary); }
.kpi-label { font-size: 0.78rem; color: var(--lab-muted); margin-top: 0.15rem; }

/* Grid */
.dash-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 1rem;
}
.dash-card { cursor: default; }
.card-title { font-weight: 600; font-size: 0.95rem; }
.empty-hint { text-align: center; padding: 1.5rem 0; color: var(--lab-muted); font-size: 0.85rem; }

/* Items */
.item-row, .ask-row {
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
  cursor: pointer;
}
.item-row:last-child, .ask-row:last-child { border-bottom: none; }
.item-row:hover, .ask-row:hover { background: var(--el-fill-color-light); }
.item-name { font-size: 0.9rem; margin-bottom: 0.15rem; }
.item-meta { font-size: 0.76rem; color: var(--lab-muted); display: flex; gap: 0.5rem; align-items: center; }
.rank-num { display: inline-block; width: 20px; font-weight: 700; color: var(--el-color-primary); }

.ask-row { }
.ask-title { font-size: 0.88rem; margin-bottom: 0.15rem; }
.ask-badge { display: inline-block; background: #fef0c7; color: #b54708; padding: 0 6px; border-radius: 4px; font-size: 0.72rem; margin-right: 0.35rem; font-weight: 600; }
.ask-meta { font-size: 0.74rem; color: var(--lab-muted); display: flex; gap: 0.5rem; }

.error-text { color: var(--el-color-danger); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
</style>
