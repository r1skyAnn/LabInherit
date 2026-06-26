<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { RouterView, useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { notificationsApi, type NotificationOut } from '@/api/notifications'
import { notesApi, type NoteOut } from '@/api/notes'
import { ElMessage } from 'element-plus'
import { Bell, Search } from '@element-plus/icons-vue'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const sidebarCollapsed = ref(false)

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

// Notifications
const unreadCount = ref(0)
const notifList = ref<NotificationOut[]>([])
const notifVisible = ref(false)
const notifLoading = ref(false)
let pollTimer: ReturnType<typeof setInterval> | null = null

function loadTypeLabel(type: string): string {
  const map: Record<string, string> = {
    ask_opened: '追问',
    comment: '评论',
    system: '系统',
  }
  return map[type] || type
}

function loadPayloadSnippet(n: NotificationOut): string {
  try {
    if (n.payload_json) {
      const p = JSON.parse(n.payload_json)
      return p.content || p.note_title || ''
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

interface NavItem {
  path: string
  title: string
  icon: string
  roles?: string[]
}

const navItems = computed<NavItem[]>(() => {
  const items: NavItem[] = [
    { path: '/home', title: '首页', icon: 'HomeFilled' },
    { path: '/projects', title: '项目列表', icon: 'FolderOpened' },
    { path: '/guides', title: '新人指南', icon: 'Reading' },
    { path: '/showcase', title: '成果展示墙', icon: 'PictureFilled' },
    { path: '/announcements', title: '公告中心', icon: 'BellFilled' },
  ]
  if (auth.isAdmin) {
    items.push(
      { path: '/members', title: '成员列表', icon: 'User' },
    )
  }
  if (auth.isAdmin) {
    items.push(
      { path: '/categories', title: '分类管理', icon: 'Grid' },
    )
  }
  if (auth.isOwner) {
    items.push(
      { path: '/admin/dashboard', title: '管理看板', icon: 'TrendCharts', roles: ['owner'] },
      { path: '/admin/audit-queue', title: '审核队列', icon: 'Checked', roles: ['owner'] },
      { path: '/admin/invites', title: '邀请码管理', icon: 'Key', roles: ['owner'] },
    )
  }
  return items
})

function handleLogout() {
  auth.logout()
}

function isActive(path: string) {
  return route.path === path || route.path.startsWith(path + '/')
}

onMounted(() => {
  fetchUnreadCount()
  pollTimer = setInterval(fetchUnreadCount, 30000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<template>
  <el-container class="app-shell">
    <el-aside :width="sidebarCollapsed ? '64px' : '220px'" class="sidebar" :class="{ 'is-collapsed': sidebarCollapsed }">
      <div class="sidebar-brand">
        <router-link to="/home" class="brand-text">{{ sidebarCollapsed ? 'L' : 'LabInherit' }}</router-link>
        <span class="sidebar-toggle" @click="sidebarCollapsed = !sidebarCollapsed">{{ sidebarCollapsed ? '▶' : '◀' }}</span>
      </div>

      <el-menu
        :default-active="route ? route.path : ''"
        :router="true"
        :collapse="sidebarCollapsed"
        background-color="transparent"
        class="nav-menu"
      >
        <el-menu-item
          v-for="item in navItems"
          :key="item.path"
          :index="item.path"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <template #title>{{ item.title }}</template>
        </el-menu-item>
      </el-menu>

      <div class="sidebar-footer">
        <router-link v-if="!sidebarCollapsed" to="/profile" class="user-info">
          <span class="user-name">{{ auth.user?.display_name }}</span>
          <el-tag size="small" :type="auth.isAdmin ? 'warning' : 'info'">
            {{ auth.user?.role === 'owner' ? '导师' : auth.user?.profile?.gender === '女' ? '师姐' : auth.user?.profile?.gender === '男' ? '师兄' : '成员' }}
          </el-tag>
        </router-link>
      </div>
    </el-aside>

    <el-container>
      <el-header class="topbar">
        <div class="topbar-left">
          <h2>{{ (route.meta?.title as string) || 'LabInherit' }}</h2>
        </div>
        <div class="topbar-center">
          <el-popover
            :visible="searchVisible"
            placement="bottom"
            :width="420"
            trigger="manual"
            :hide-after="0"
          >
            <div class="search-dropdown" v-loading="searchLoading">
              <div v-if="searchResults.length === 0 && !searchLoading" class="search-empty">
                {{ searchQuery ? '无搜索结果' : '输入关键词搜索笔记' }}
              </div>
              <div
                v-for="n in searchResults"
                :key="n.id"
                class="search-item"
                @click="goToResult(n)"
              >
                <div class="search-item-title">{{ n.title }}</div>
                <div class="search-item-meta">
                  <el-tag size="small" effect="plain">{{ n.project_title }}</el-tag>
                  <span>{{ n.author_display_name }}</span>
                </div>
              </div>
            </div>
            <template #reference>
              <el-input
                v-model="searchQuery"
                placeholder="搜索笔记..."
                :prefix-icon="Search"
                clearable
                size="default"
                @input="handleSearchInput"
                @clear="searchVisible = false"
                @focus="searchQuery && searchResults.length > 0 && (searchVisible = true)"
                @blur="setTimeout(() => searchVisible = false, 200)"
                class="search-input"
              />
            </template>
          </el-popover>
        </div>
        <div class="topbar-right">
          <el-popover
            :visible="notifVisible"
            placement="bottom-end"
            :width="380"
            trigger="click"
            @show="loadNotifications"
          >
            <template #reference>
              <el-badge :value="unreadCount" :hidden="unreadCount === 0" :max="99" class="notif-badge">
                <el-button text @click="toggleNotif">
                  <el-icon :size="20"><Bell /></el-icon>
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
                v-for="n in notifList"
                :key="n.id"
                class="notif-item"
                :class="{ 'is-unread': !n.read_at }"
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
          <el-button text @click="handleLogout">退出登录</el-button>
        </div>
      </el-header>

      <el-main class="main-content">
        <RouterView />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.app-shell {
  height: 100vh;
}

.sidebar {
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
  color: #fff;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  transition: width 0.25s ease;
}
.sidebar.is-collapsed {
  overflow-x: hidden;
}
.sidebar.is-collapsed .el-menu-item {
  justify-content: center;
  padding: 0 !important;
}

.sidebar-brand {
  display: flex; align-items: center; justify-content: space-between;
  padding: 1.25rem 1.25rem 0.75rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.brand-text {
  font-size: 1.3rem;
  font-weight: 700;
  color: #409eff;
  text-decoration: none;
  letter-spacing: -0.5px;
}

.sidebar-toggle {
  cursor: pointer; font-size: 0.7rem; color: rgba(255,255,255,0.35);
  padding: 2px 4px; transition: color 0.15s;
}
.sidebar-toggle:hover { color: rgba(255,255,255,0.7); }

.nav-menu {
  border-right: none;
  flex: 1;
}

.nav-menu .el-menu-item {
  color: rgba(255, 255, 255, 0.7);
}

.nav-menu .el-menu-item:hover,
.nav-menu .el-menu-item.is-active {
  color: #409eff;
  background-color: rgba(64, 158, 255, 0.08);
}

.sidebar-footer {
  padding: 0.75rem 1.25rem;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  border-radius: 6px;
  padding: 4px 6px;
  transition: background 0.15s;
}
.user-info:hover { background: rgba(255,255,255,0.08); }

.user-name {
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.85rem;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e8eaed;
  padding: 0 1.5rem;
}

.topbar-left h2 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
}
.topbar-center {
  flex: 1; max-width: 360px; margin: 0 1.5rem;
}
.topbar-center .search-input {
  width: 100%;
}
.search-dropdown { max-height: 380px; overflow-y: auto; }
.search-empty {
  text-align: center; padding: 1.5rem; color: var(--lab-muted); font-size: 0.85rem;
}
.search-item {
  padding: 0.6rem 0.75rem; border-bottom: 1px solid var(--el-border-color-lighter);
  cursor: pointer; transition: background 0.15s;
}
.search-item:hover { background: var(--el-fill-color-light); }
.search-item:last-child { border-bottom: none; }
.search-item-title {
  font-size: 0.9rem; font-weight: 600; margin-bottom: 0.2rem;
}
.search-item-meta {
  display: flex; gap: 0.5rem; align-items: center; font-size: 0.76rem; color: var(--lab-muted);
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.notif-badge {
  margin-right: 0.5rem;
}

.main-content {
  background: var(--lab-bg);
  padding: 1.5rem;
  overflow-y: auto;
}

/* ── Notification popover ──────────────── */
.notif-popover {
  max-height: 400px;
  overflow-y: auto;
}
.notif-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--el-border-color-lighter);
}
.notif-header-title {
  font-weight: 600;
  font-size: 0.95rem;
}
.notif-empty {
  text-align: center;
  color: var(--lab-muted);
  padding: 1.5rem;
  font-size: 0.88rem;
}
.notif-item {
  padding: 0.6rem 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
  cursor: pointer;
  transition: background 0.15s;
}
.notif-item:hover {
  background: var(--el-fill-color-light);
}
.notif-item.is-unread {
  background: #f0f5ff;
}
.notif-item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.2rem;
}
.notif-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--el-color-danger);
}
.notif-item-text {
  font-size: 0.84rem;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.notif-item-time {
  font-size: 0.72rem;
  color: var(--lab-muted);
  margin-top: 0.15rem;
}
</style>
