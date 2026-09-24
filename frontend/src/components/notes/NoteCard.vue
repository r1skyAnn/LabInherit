<script setup lang="ts">
import type { NoteOut } from '@/api/notes'
import { useAuthStore } from '@/stores/auth'

const props = defineProps<{
  note: NoteOut
}>()

const emit = defineEmits<{
  edit: [note: NoteOut]
  delete: [note: NoteOut]
  like: [note: NoteOut]
  togglePin: [note: NoteOut]
}>()

const auth = useAuthStore()

function isAuthor() {
  return props.note.author_id === auth.user?.id
}

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}
</script>

<template>
  <el-card class="note-card" shadow="hover">
    <div class="note-header">
      <router-link :to="`/projects/${note.project_id}/notes/${note.id}`" class="note-title">
        {{ note.title }}
      </router-link>
      <div class="note-tags">
        <el-tag v-if="note.is_pinned" size="small" type="warning" effect="plain">置顶</el-tag>
        <el-tag v-if="note.category_name" size="small" type="info" effect="plain">
          {{ note.category_name }}
        </el-tag>
      </div>
    </div>

    <div class="note-preview">
      {{ note.content.slice(0, 200) }}{{ note.content.length > 200 ? '...' : '' }}
    </div>

    <div class="note-meta">
      <span class="meta-item">
        {{ note.author_display_name }}
        <span class="meta-email">({{ note.author_email }})</span>
      </span>
      <span class="meta-item">{{ formatDate(note.created_at) }}</span>
    </div>

    <div class="note-footer">
      <el-button text size="small" @click="emit('like', note)">
        👍 {{ note.like_count }}
      </el-button>
      <span class="footer-actions" v-if="isAuthor() || auth.isOwner">
        <el-button text size="small" @click="emit('togglePin', note)">
          {{ note.is_pinned ? '📌 取消置顶' : '📌 置顶' }}
        </el-button>
        <el-button text size="small" @click="emit('edit', note)">编辑</el-button>
        <el-button text size="small" type="danger" @click="emit('delete', note)">删除</el-button>
      </span>
    </div>
  </el-card>
</template>

<style scoped>
.note-card {
  border-radius: 6px !important;
  border: 1px solid var(--el-border-color-light) !important;
  border-left: 3px solid transparent !important;
  transition: transform 0.15s, box-shadow 0.15s, border-left-color 0.2s !important;
}
.note-card:hover {
  transform: translateX(2px);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05) !important;
  border-left-color: var(--ember) !important;
}
.note-header {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 0.5rem; margin-bottom: 0.4rem;
}
.note-title {
  font-size: 1rem; font-weight: 600; color: var(--ink);
  text-decoration: none; flex: 1;
}
.note-title:hover { color: var(--ember); }
.note-tags { display: flex; gap: 0.2rem; flex-shrink: 0; }
.note-preview {
  font-size: 0.83rem; color: var(--stone); line-height: 1.5;
  margin-bottom: 0.6rem;
}
.note-meta {
  display: flex; gap: 0.75rem; font-size: 0.76rem;
  color: var(--stone); margin-bottom: 0.4rem;
}
.meta-email { font-size: 0.73rem; opacity: 0.7; }
.note-footer {
  display: flex; justify-content: space-between; align-items: center;
  padding-top: 0.45rem; border-top: 1px solid var(--el-border-color-extra-light);
}
.footer-actions { display: flex; gap: 0.15rem; }
</style>
