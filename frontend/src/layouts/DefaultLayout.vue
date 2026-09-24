<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { RouterView, useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { notificationsApi, type NotificationOut } from '@/api/notifications'
import { notesApi, type NoteOut } from '@/api/notes'
import { ElMessage } from 'element-plus'
import { Bell, Search, Document, ArrowRight, HomeFilled, FolderOpened, Reading, PictureFilled, BellFilled, Medal, User, Grid, TrendCharts, Checked, Key } from '@element-plus/icons-vue'
import EmberLogo from '@/components/EmberLogo.vue'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const sidebarCollapsed = ref(false)

const iconMap: Record<string, any> = {
  HomeFilled, FolderOpened, Reading, PictureFilled, BellFilled, Medal, User, Grid, TrendCharts, Checked, Key,
}

// ── Search ──────────────────────────────
const searchQuery = ref('')
const searchResults = ref<NoteOut[]>([])
const searchVisible = ref(false)
const searchLoading = ref(false)
let searchTimer: ReturnType<typeof setTimeout> | null = null

function handleSearchInput() {
  if (searchTimer) clearTimeout(searchTimer)
  if (!searchQuery.value.trim()) {
    searchResults.value = []
    searchVisible.value = false
    return
  }
  searchTimer = setTimeout(async () => {
    searchLoading.value = true
    try {
      const resp = await notesApi.list({ q: searchQuery.value, page_size: 8 })
      searchResults.value = resp.data.items
      searchVisible.value = true
    } catch { searchResults.value = [] }
    finally { searchLoading.value = false }
  }, 300)
}

function goToResult(note: NoteOut) {
  searchVisible.value = false
  searchQuery.value = ''
  router.push(`/projects/${note.project_id}/notes/${note.id}`)
}

// ── Notifications ────────────────────────
const unreadCount = ref(0)
const notifList = ref<NotificationOut[]>([])
const notifVisible = ref(false)
const notifLoading = ref(false)
let pollTimer: ReturnType<typeof setInterval> | null = null

function loadTypeLabel(type: string): string {
  const map: Record<string, string> = {
    ask_opened: '追问', comment: '评论', system: '系统',
    announcement: '公告', role_changed: '角色变更', status_changed: '状态变更',
  }
  return map[type] || type
}

function loadPayloadSnippet(n: NotificationOut): string {
  try {
    if (n.payload_json) {
      const p = JSON.parse(n.payload_json)
      return p.content || p.note_title || p.title || ''
    }
  } catch {}
  return ''
}

async function fetchUnreadCount() {
  try {
    const resp = await notificationsApi.unreadCount()
    unreadCount.value = resp.data.unread_count
  } catch {}
}

async function loadNotifications() {
  notifLoading.value = true
  try {
    const resp = await notificationsApi.list({ unread_only: false, page_size: 10 })
    notifList.value = resp.data.items
    unreadCount.value = resp.data.unread_count
  } finally {
    notifLoading.value = false
  }
}

async function handleMarkRead(n: NotificationOut) {
  if (n.read_at) return
  await notificationsApi.markRead(n.id)
  n.read_at = new Date().toISOString()
  unreadCount.value = Math.max(0, unreadCount.value - 1)
}

async function handleReadAll() {
  await notificationsApi.readAll()
  notifList.value.forEach(n => { n.read_at = n.read_at || new Date().toISOString() })
  unreadCount.value = 0
  ElMessage.success('已全部标记为已读')
}

function handleNotifClick(n: NotificationOut) {
  handleMarkRead(n)
  notifVisible.value = false
  try {
    if (n.payload_json) {
      const p = JSON.parse(n.payload_json)
      if (p.note_id && p.project_id) {
        router.push(`/projects/${p.project_id}/notes/${p.note_id}`)
      }
    }
  } catch {}
}

function toggleNotif() {
  notifVisible.value = !notifVisible.value
  if (notifVisible.value) loadNotifications()
}

// ── Navigation ───────────────────────────
interface NavItem { path: string; title: string; icon: string; roles?: string[] }

const navItems = computed<NavItem[]>(() => {
  const items: NavItem[] = [
    { path: '/home', title: '首页', icon: 'HomeFilled' },
    { path: '/projects', title: '项目列表', icon: 'FolderOpened' },
    { path: '/guides', title: '新人指南', icon: 'Reading' },
    { path: '/showcase', title: '成果展示墙', icon: 'PictureFilled' },
    { path: '/announcements', title: '公告中心', icon: 'BellFilled' },
    { path: '/alumni', title: '毕业人员专区', icon: 'Medal' },
  ]
  if (auth.isOwner) {
    items.push(
      { path: '/members', title: '成员列表', icon: 'User' },
      { path: '/categories', title: '分类管理', icon: 'Grid' },
      { path: '/admin/dashboard', title: '管理看板', icon: 'TrendCharts' },
      { path: '/admin/audit-queue', title: '审核队列', icon: 'Checked' },
      { path: '/admin/invites', title: '邀请码管理', icon: 'Key' },
    )
  }
  return items
})

function handleLogout() { auth.logout() }
function isActive(path: string) { return route.path === path || route.path.startsWith(path + '/') }

onMounted(() => {
  fetchUnreadCount()
  pollTimer = setInterval(fetchUnreadCount, 30000)
})
onUnmounted(() => { if (pollTimer) clearInterval(pollTimer) })
</script>

<template>
  <el-container class="app-shell">
    <el-aside :width="sidebarCollapsed ? '64px' : '224px'" class="sidebar" :class="{ 'is-collapsed': sidebarCollapsed }">
      <div class="sidebar-brand" @click="sidebarCollapsed = !sidebarCollapsed">
        <div class="brand-inner">
          <EmberLogo :collapsed="sidebarCollapsed" />
          <span v-if="!sidebarCollapsed" class="brand-text">薪火相传</span>
        </div>
      </div>

      <nav class="sidebar-nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-link"
          :class="{ 'is-active': isActive(item.path) }"
          :title="sidebarCollapsed ? item.title : undefined"
        >
          <el-icon class="nav-icon"><component :is="iconMap[item.icon]" /></el-icon>
          <span v-if="!sidebarCollapsed" class="nav-label">{{ item.title }}</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <router-link v-if="!sidebarCollapsed" to="/profile" class="user-info">
          <span class="user-avatar">{{ auth.user?.display_name?.charAt(0) || '?' }}</span>
          <span class="user-name">{{ auth.user?.display_name }}</span>
          <el-tag size="small" :type="auth.isOwner ? 'warning' : 'info'" class="user-role-tag">
            {{ auth.isOwner ? '导师' : '成员' }}
          </el-tag>
        </router-link>
        <router-link v-else to="/profile" class="user-info user-info--compact" :title="auth.user?.display_name">
          <span class="user-avatar">{{ auth.user?.display_name?.charAt(0) || '?' }}</span>
        </router-link>
      </div>
    </el-aside>

    <el-container>
      <el-header class="topbar">
        <div class="topbar-left">
          <h2 class="page-title">{{ (route.meta?.title as string) || 'LabInherit' }}</h2>
        </div>
        <div class="topbar-center">
          <el-popover
            :visible="searchVisible"
            placement="bottom-start" :width="420" trigger="manual"
            :hide-after="0" :show-arrow="false"
          >
            <div class="search-dropdown" v-loading="searchLoading">
              <div v-if="searchResults.length === 0 && !searchLoading" class="search-empty">
                <el-icon><Search /></el-icon>
                <span>{{ searchQuery ? '未找到相关笔记' : '输入关键词搜索笔记' }}</span>
              </div>
              <div v-for="n in searchResults" :key="n.id" class="search-item" @click="goToResult(n)">
                <div class="search-item-icon"><el-icon><Document /></el-icon></div>
                <div class="search-item-content">
                  <div class="search-item-title">{{ n.title }}</div>
                  <div class="search-item-meta">
                    <el-tag size="small" effect="plain">{{ n.project_title || '通用' }}</el-tag>
                    <span class="meta-sep">&middot;</span>
                    <span>{{ n.author_display_name }}</span>
                  </div>
                </div>
                <div class="search-item-arrow"><el-icon><ArrowRight /></el-icon></div>
              </div>
            </div>
            <template #reference>
              <el-input
                v-model="searchQuery" placeholder="搜索笔记..."
                :prefix-icon="Search" clearable size="default"
                @input="handleSearchInput" @clear="searchVisible = false"
                @focus="searchQuery && searchResults.length > 0 && (searchVisible = true)"
                @blur="setTimeout(() => searchVisible = false, 200)"
                class="search-input"
              />
            </template>
          </el-popover>
        </div>
        <div class="topbar-right">
          <el-popover
            :visible="notifVisible" placement="bottom-end" :width="380"
            trigger="click" @show="loadNotifications"
          >
            <template #reference>
              <el-badge :value="unreadCount" :hidden="unreadCount === 0" :max="99" class="notif-badge">
                <el-button text @click="toggleNotif" class="notif-btn">
                  <el-icon :size="19"><Bell /></el-icon>
                </el-button>
              </el-badge>
            </template>
            <div class="notif-popover" v-loading="notifLoading">
              <div class="notif-header">
                <span class="notif-header-title">消息通知</span>
                <el-button v-if="unreadCount > 0" text size="small" @click="handleReadAll">全部已读</el-button>
              </div>
              <div v-if="notifList.length === 0" class="notif-empty">暂无通知</div>
              <div
                v-for="n in notifList" :key="n.id"
                class="notif-item" :class="{ 'is-unread': !n.read_at }"
                @click="handleNotifClick(n)"
              >
                <div class="notif-item-header">
                  <el-tag size="small" :type="n.type === 'ask_opened' ? 'warning' : 'info'" effect="plain">
                    {{ loadTypeLabel(n.type) }}
                  </el-tag>
                  <span v-if="!n.read_at" class="notif-dot"></span>
                </div>
                <div class="notif-item-text">{{ loadPayloadSnippet(n) }}</div>
                <div class="notif-item-time">{{ new Date(n.created_at).toLocaleString('zh-CN') }}</div>
              </div>
            </div>
          </el-popover>
          <el-button text class="logout-btn" @click="handleLogout">退出</el-button>
        </div>
      </el-header>

      <el-main class="main-content">
        <RouterView />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
/* ── Shell ──────────────────────────────── */
.app-shell { height: 100vh; }

/* ── Sidebar ────────────────────────────── */
.sidebar {
  background: var(--ink);
  color: rgba(255, 255, 255, 0.75);
  display: flex; flex-direction: column;
  overflow-y: auto; overflow-x: hidden;
  transition: width 0.22s ease;
  border-right: 1px solid rgba(255, 255, 255, 0.06);
}

.sidebar-brand {
  padding: 1.25rem 1rem 1rem;
  cursor: pointer;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.brand-inner {
  display: flex; align-items: center; gap: 0.6rem;
}
.brand-text {
  font-size: 1.2rem; font-weight: 700;
  color: var(--ember);
  letter-spacing: 0.05em;
  white-space: nowrap;
}

/* ── Navigation ──────────────────────────── */
.sidebar-nav {
  flex: 1; padding: 0.6rem 0.5rem;
  display: flex; flex-direction: column; gap: 2px;
}
.nav-link {
  display: flex; align-items: center; gap: 0.65rem;
  padding: 0.55rem 0.75rem;
  border-radius: 6px;
  color: rgba(255, 255, 255, 0.55);
  text-decoration: none;
  font-size: 0.88rem;
  transition: color 0.15s, background 0.15s;
}
.nav-link:hover {
  color: rgba(255, 255, 255, 0.85);
  background: rgba(255, 255, 255, 0.04);
}
.nav-link.is-active {
  color: var(--ember-glow);
  background: rgba(194, 81, 26, 0.12);
  font-weight: 500;
}
.nav-icon { font-size: 1.15rem; flex-shrink: 0; }
.nav-label { white-space: nowrap; }

.sidebar.is-collapsed .nav-link {
  justify-content: center; padding: 0.6rem 0;
}
.sidebar.is-collapsed .sidebar-brand { padding: 1rem 0.5rem; }
.sidebar.is-collapsed .brand-inner { justify-content: center; }

/* ── Sidebar footer ─────────────────────── */
.sidebar-footer {
  padding: 0.7rem 0.75rem;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}
.user-info {
  display: flex; align-items: center; gap: 0.5rem;
  text-decoration: none; border-radius: 6px;
  padding: 0.4rem 0.5rem; transition: background 0.15s;
}
.user-info:hover { background: rgba(255, 255, 255, 0.06); }
.user-info--compact { justify-content: center; }

.user-avatar {
  width: 30px; height: 30px; border-radius: 50%;
  background: var(--ember); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.8rem; font-weight: 600; flex-shrink: 0;
}
.user-name {
  color: rgba(255, 255, 255, 0.75); font-size: 0.82rem;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.user-role-tag { flex-shrink: 0; }

/* ── Topbar ─────────────────────────────── */
.topbar {
  display: flex; align-items: center; justify-content: space-between;
  background: transparent;
  padding: 1.25rem 1.5rem 0.75rem; height: auto;
}
.page-title {
  margin: 0; font-size: 1.15rem; font-weight: 700;
  color: var(--ink);
  padding-left: 0.75rem;
  border-left: 3px solid var(--ember);
  line-height: 1.3;
}
.topbar-center { flex: 1; max-width: 380px; margin: 0 1.5rem; }
.topbar-center .search-input { width: 100%; }
.topbar-right { display: flex; align-items: center; gap: 0.25rem; }

.notif-btn { color: var(--stone); }
.notif-btn:hover { color: var(--ember); }
.logout-btn { color: var(--stone); font-size: 0.82rem; }

/* ── Search dropdown ───────────────────── */
.search-dropdown {
  max-height: 380px; overflow-y: auto; border-radius: 8px;
}
.search-empty {
  display: flex; align-items: center; justify-content: center;
  gap: 0.5rem; padding: 2rem 1rem;
  color: var(--lab-muted); font-size: 0.85rem;
}
.search-item {
  display: flex; align-items: center; gap: 0.75rem;
  padding: 0.7rem 0.75rem; border-radius: 6px;
  cursor: pointer; transition: background 0.15s;
  border-bottom: 1px solid var(--el-border-color-lighter);
}
.search-item:last-child { border-bottom: none; }
.search-item:hover { background: var(--glow); }
.search-item:hover .search-item-arrow {
  opacity: 1; transform: translateX(2px);
}
.search-item-icon {
  flex-shrink: 0; width: 32px; height: 32px;
  display: flex; align-items: center; justify-content: center;
  background: var(--glow); border-radius: 6px; color: var(--ember);
}
.search-item-content { flex: 1; min-width: 0; overflow: hidden; }
.search-item-title {
  font-size: 0.9rem; font-weight: 500; color: var(--ink);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  margin-bottom: 0.2rem;
}
.search-item-meta {
  display: flex; align-items: center; gap: 0.35rem;
  font-size: 0.76rem; color: var(--lab-muted);
}
.meta-sep { color: var(--el-border-color); }
.search-item-arrow {
  flex-shrink: 0; opacity: 0;
  transition: opacity 0.15s, transform 0.15s; color: var(--ember);
}

/* ── Notification popover ──────────────── */
.notif-popover { max-height: 400px; overflow-y: auto; }
.notif-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 0.5rem; padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--el-border-color-lighter);
}
.notif-header-title { font-weight: 600; font-size: 0.95rem; }
.notif-empty { text-align: center; color: var(--lab-muted); padding: 1.5rem; font-size: 0.88rem; }
.notif-item {
  padding: 0.6rem 0; border-bottom: 1px solid var(--el-border-color-lighter);
  cursor: pointer; transition: background 0.15s;
}
.notif-item:hover { background: var(--glow); }
.notif-item.is-unread { background: var(--glow); }
.notif-item-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 0.2rem;
}
.notif-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--ember);
}
.notif-item-text {
  font-size: 0.84rem; color: var(--ink);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.notif-item-time { font-size: 0.72rem; color: var(--lab-muted); margin-top: 0.15rem; }

/* ── Main content ──────────────────────── */
.main-content {
  background: var(--parchment);
  padding: 1.5rem; overflow-y: auto;
}
</style>
