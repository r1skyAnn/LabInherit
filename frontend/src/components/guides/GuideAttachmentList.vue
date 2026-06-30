<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  filesApi,
  formatFileSize,
  iconForFile,
  guideAttachmentsApi,
  type GuideAttachmentOut,
} from '@/api/files'

const props = defineProps<{
  guideId: number
  canEdit: boolean
}>()

const emit = defineEmits<{
  changed: []
}>()

const attachments = ref<GuideAttachmentOut[]>([])
const loading = ref(false)

const fileAttachments = computed(() =>
  attachments.value.filter(a => a.role === 'attachment'),
)

async function load() {
  loading.value = true
  try {
    const resp = await guideAttachmentsApi.list(props.guideId)
    attachments.value = resp.data
  } catch {
    // ignore
  } finally {
    loading.value = false
  }
}

async function handleDelete(a: GuideAttachmentOut) {
  try {
    await ElMessageBox.confirm(`确认删除附件「${a.file.original_name}」？`, '删除附件', {
      confirmButtonText: '删除',
      type: 'warning',
    })
  } catch {
    return
  }
  await guideAttachmentsApi.detach(props.guideId, a.id)
  ElMessage.success('已移除')
  await load()
  emit('changed')
}

function handleDownload(a: GuideAttachmentOut) {
  const url = filesApi.downloadUrl(a.file.id)
  const a2 = document.createElement('a')
  a2.href = url
  a2.rel = 'noopener'
  document.body.appendChild(a2)
  a2.click()
  document.body.removeChild(a2)
}

onMounted(load)
defineExpose({ load })
</script>

<template>
  <div class="attachment-list" v-loading="loading">
    <div v-if="fileAttachments.length" class="file-list">
      <h4 class="section-title">📎 附件 ({{ fileAttachments.length }})</h4>
      <div
        v-for="a in fileAttachments"
        :key="a.id"
        class="file-row"
      >
        <span class="file-icon">{{ iconForFile(a.file.original_name, a.file.category) }}</span>
        <div class="file-info">
          <div class="filename" :title="a.file.original_name">{{ a.file.original_name }}</div>
          <div class="filemeta">
            <span>{{ formatFileSize(a.file.size) }}</span>
            <span class="dot">·</span>
            <span>{{ a.file.category }}</span>
          </div>
        </div>
        <div class="file-actions">
          <el-button text size="small" @click="handleDownload(a)">下载</el-button>
          <el-button
            v-if="canEdit"
            text
            size="small"
            type="danger"
            @click="handleDelete(a)"
          >移除</el-button>
        </div>
      </div>
    </div>
    <div v-else-if="!loading" class="empty-hint">暂无附件</div>
  </div>
</template>

<style scoped>
.attachment-list {
  margin-top: 1.25rem;
}
.section-title {
  font-size: 0.95rem;
  margin: 0 0 0.6rem;
  color: var(--el-text-color-regular);
}
.empty-hint {
  font-size: 0.85rem;
  color: var(--el-text-color-placeholder);
  padding: 0.6rem 0;
}
.file-list {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
.file-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 0.75rem;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
  background: var(--el-fill-color-blank);
  transition: background 0.15s;
}
.file-row:hover {
  background: var(--el-fill-color-light);
}
.file-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
  width: 2rem;
  text-align: center;
}
.file-info {
  flex: 1;
  min-width: 0;
}
.file-info .filename {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--el-text-color-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.filemeta {
  font-size: 0.75rem;
  color: var(--el-text-color-secondary);
  display: flex;
  gap: 0.4rem;
}
.dot {
  color: var(--el-text-color-placeholder);
}
.file-actions {
  display: flex;
  gap: 0.25rem;
  flex-shrink: 0;
}
</style>
