import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  // Auth layout (login/register/forgot-password/reset-password)
  {
    path: '/auth',
    component: () => import('@/layouts/AuthLayout.vue'),
    meta: { requiresAuth: false },
    children: [
      {
        path: 'login',
        name: 'login',
        component: () => import('@/views/Login.vue'),
        meta: { title: '登录' },
      },
      {
        path: 'register',
        name: 'register',
        component: () => import('@/views/Register.vue'),
        meta: { title: '注册' },
      },
      {
        path: 'forgot-password',
        name: 'forgot-password',
        component: () => import('@/views/ForgotPassword.vue'),
        meta: { title: '忘记密码' },
      },
      {
        path: 'reset-password',
        name: 'reset-password',
        component: () => import('@/views/ResetPassword.vue'),
        meta: { title: '重置密码' },
      },
    ],
  },

  // Default layout (main app shell with sidebar)
  {
    path: '/',
    component: () => import('@/layouts/DefaultLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/home',
      },
      {
        path: 'home',
        name: 'home',
        component: () => import('@/views/Home.vue'),
        meta: { title: '首页' },
      },
      {
        path: 'profile',
        name: 'profile',
        component: () => import('@/views/Profile.vue'),
        meta: { title: '个人资料' },
      },
      {
        path: 'projects',
        name: 'projects',
        component: () => import('@/views/ProjectsList.vue'),
        meta: { title: '项目列表' },
      },
      {
        path: 'projects/:projectId',
        name: 'project-detail',
        component: () => import('@/views/ProjectDetail.vue'),
        meta: { title: '项目详情' },
      },
      {
        path: 'categories',
        name: 'categories',
        component: () => import('@/views/CategoriesList.vue'),
        meta: { title: '分类管理', requiredRoles: ['owner'] },
      },
      {
        path: 'projects/:projectId/notes',
        name: 'project-notes',
        component: () => import('@/views/NotesList.vue'),
        meta: { title: '笔记' },
      },
      {
        path: 'projects/:projectId/notes/:noteId',
        name: 'note-detail',
        component: () => import('@/views/NoteDetail.vue'),
        meta: { title: '笔记详情' },
      },
      {
        path: 'guides/:slug?',
        name: 'guides',
        component: () => import('@/views/GuideDetail.vue'),
        meta: { title: '新人指南' },
      },
      {
        path: 'showcase',
        name: 'showcase',
        component: () => import('@/views/ShowcaseWall.vue'),
        meta: { title: '成果展示墙' },
      },
      {
        path: 'announcements',
        name: 'announcements',
        component: () => import('@/views/AnnouncementsList.vue'),
        meta: { title: '公告中心' },
      },
      {
        path: 'members',
        name: 'members',
        component: () => import('@/views/MembersList.vue'),
        meta: { title: '成员列表', requiredRoles: ['owner'] },
      },
      {
        path: 'alumni',
        name: 'alumni',
        component: () => import('@/views/AlumniPosts.vue'),
        meta: { title: '毕业人员专区' },
      },
      // Owner routes
      {
        path: 'admin/dashboard',
        name: 'admin-dashboard',
        component: () => import('@/views/AdminDashboard.vue'),
        meta: { title: '管理看板', requiredRoles: ['owner'] },
      },
      {
        path: 'admin/audit-queue',
        name: 'admin-audit-queue',
        component: () => import('@/views/AdminAuditQueue.vue'),
        meta: { title: '审核队列', requiredRoles: ['owner'] },
      },
      {
        path: 'admin/invites',
        name: 'admin-invites',
        component: () => import('@/views/AdminInvites.vue'),
        meta: { title: '邀请码管理', requiredRoles: ['owner'] },
      },
    ],
  },

  // Catch-all → login
  {
    path: '/:pathMatch(.*)*',
    redirect: '/auth/login',
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

// Route guards
router.beforeEach((to, _from, next) => {
  const auth = useAuthStore()
  const requiresAuth = to.matched.some((r) => r.meta.requiresAuth === true)
  const requiredRoles = to.meta.requiredRoles as string[] | undefined

  if (requiresAuth && !auth.isLoggedIn) {
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }

  if (!requiresAuth && auth.isLoggedIn && to.name === 'login') {
    next({ name: 'home' })
    return
  }

  if (requiredRoles && auth.user) {
    if (!requiredRoles.includes(auth.user.role)) {
      next({ name: 'home' })
      return
    }
  }

  next()
})

router.afterEach((to) => {
  const title = (to.meta?.title as string | undefined) ?? ''
  document.title = title ? `${title} · LabInherit` : 'LabInherit'
})

export default router
