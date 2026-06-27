<script setup lang="ts">
import type { ProjectOut } from '@/api/projects'
import { useAuthStore } from '@/stores/auth'

const props = defineProps<{
  project: ProjectOut
  isOwner: boolean
}>()

const emit = defineEmits<{
  edit: [project: ProjectOut]
  delete: [project: ProjectOut]
}>()

const auth = useAuthStore()

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
</script>

<template>
  <el-card class="project-card" shadow="hover">
    <div class="card-header">
      <router-link :to="`/projects/${project.id}`" class="card-title">{{ project.title }}</router-link>
      <div class="card-tags">
        <el-tag size="small" :type="statusMap[project.status]?.type as any" effect="plain">
          {{ statusMap[project.status]?.label }}
        </el-tag>
        <el-tag size="small" :type="priorityMap[project.priority]?.type as any" effect="plain">
          {{ priorityMap[project.priority]?.label }}优先级
        </el-tag>
        <el-tooltip :content="project.is_public ? '公开项目' : '私有项目'" placement="top">
          <el-tag size="small" :type="project.is_public ? 'success' : 'warning'" effect="plain">
            {{ project.is_public ? '公开' : '私有' }}
          </el-tag>
        </el-tooltip>
      </div>
    </div>

    <p v-if="project.description" class="card-desc">{{ project.description }}</p>
    <p v-else class="card-desc card-desc--empty">暂无描述</p>

    <div class="card-meta">
      <span v-if="project.tech_stack" class="meta-item">
        <span class="meta-label">技术栈</span>
        <span class="meta-value">{{ project.tech_stack }}</span>
      </span>
      <span v-if="project.repo_url || project.demo_url" class="meta-links">
        <a v-if="project.repo_url" :href="project.repo_url" target="_blank" rel="noreferrer">
          <el-icon><Link /></el-icon> 仓库
        </a>
        <a v-if="project.demo_url" :href="project.demo_url" target="_blank" rel="noreferrer">
          <el-icon><Monitor /></el-icon> 演示
        </a>
      </span>
      <span class="meta-item">
        <span class="meta-label">创建人</span>
        <span class="meta-value">{{ project.creator_display_name ?? '—' }}</span>
      </span>
      <span class="meta-item">
        <span class="meta-label">创建时间</span>
        <span class="meta-value">{{ formatDate(project.created_at) }}</span>
      </span>
    </div>

    <div class="card-footer">
      <router-link :to="`/projects/${project.id}/notes`">
        <el-button size="small" type="primary">笔记</el-button>
      </router-link>
      <template v-if="isOwner || auth.isAdmin">
        <el-button size="small" @click="emit('edit', project)">编辑</el-button>
        <el-button size="small" type="danger" plain @click="emit('delete', project)">删除</el-button>
      </template>
    </div>
  </el-card>
</template>

<script lang="ts">
import { Link, Monitor } from '@element-plus/icons-vue'
export default { components: { Link, Monitor } }
</script>

<style scoped>
.project-card {
  border-radius: 8px;
  transition: transform 0.15s, box-shadow 0.15s;
}
.project-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}
.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}
.card-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--el-text-color-primary);
  flex: 1;
  text-decoration: none;
}
.card-title:hover {
  color: var(--el-color-primary);
}
.card-tags {
  display: flex;
  gap: 0.25rem;
  flex-shrink: 0;
}
.card-desc {
  font-size: 0.85rem;
  color: var(--lab-muted);
  margin: 0 0 0.75rem;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.card-desc--empty {
  font-style: italic;
  color: var(--lab-muted);
}
.card-meta {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.8rem;
  color: var(--lab-muted);
  margin-bottom: 0.75rem;
}
.meta-item {
  display: flex;
  gap: 0.5rem;
  align-items: baseline;
}
.meta-label {
  flex-shrink: 0;
  width: 56px;
  color: var(--lab-muted);
}
.meta-value {
  color: var(--el-text-color-regular);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.meta-links {
  display: flex;
  gap: 0.75rem;
}
.meta-links a {
  display: flex;
  align-items: center;
  gap: 0.2rem;
  color: var(--el-color-primary);
  text-decoration: none;
  font-size: 0.8rem;
}
.meta-links a:hover {
  text-decoration: underline;
}
.card-footer {
  display: flex;
  gap: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--el-border-color-lighter);
}
</style>
