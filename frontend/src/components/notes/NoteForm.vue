<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { MdEditor } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'
import hljs from 'highlight.js/lib/core'
import 'highlight.js/styles/github-dark.css'

// Register languages for editor preview's code highlighting
import javascript from 'highlight.js/lib/languages/javascript'
import typescript from 'highlight.js/lib/languages/typescript'
import python from 'highlight.js/lib/languages/python'
import java from 'highlight.js/lib/languages/java'
import bash from 'highlight.js/lib/languages/bash'
import json from 'highlight.js/lib/languages/json'
import xml from 'highlight.js/lib/languages/xml'
import css from 'highlight.js/lib/languages/css'
import sql from 'highlight.js/lib/languages/sql'
import markdown from 'highlight.js/lib/languages/markdown'
import go from 'highlight.js/lib/languages/go'
import rust from 'highlight.js/lib/languages/rust'
import yaml from 'highlight.js/lib/languages/yaml'
import shell from 'highlight.js/lib/languages/shell'

hljs.registerLanguage('javascript', javascript)
hljs.registerLanguage('js', javascript)
hljs.registerLanguage('typescript', typescript)
hljs.registerLanguage('ts', typescript)
hljs.registerLanguage('tsx', typescript)
hljs.registerLanguage('jsx', javascript)
hljs.registerLanguage('python', python)
hljs.registerLanguage('py', python)
hljs.registerLanguage('java', java)
hljs.registerLanguage('bash', bash)
hljs.registerLanguage('sh', bash)
hljs.registerLanguage('json', json)
hljs.registerLanguage('html', xml)
hljs.registerLanguage('xml', xml)
hljs.registerLanguage('vue', xml)
hljs.registerLanguage('css', css)
hljs.registerLanguage('sql', sql)
hljs.registerLanguage('markdown', markdown)
hljs.registerLanguage('md', markdown)
hljs.registerLanguage('go', go)
hljs.registerLanguage('rust', rust)
hljs.registerLanguage('rs', rust)
hljs.registerLanguage('yaml', yaml)
hljs.registerLanguage('yml', yaml)
hljs.registerLanguage('shell', shell)

import { notesApi, type NoteOut } from '@/api/notes'
import { categoriesApi, type CategoryOut } from '@/api/categories'
import { noteAttachmentsApi, filesApi, type FileOut, type NoteAttachmentOut, formatFileSize, iconForFile } from '@/api/files'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  saveDraft, loadDraft, clearDraft,
  newNoteScope, editNoteScope,
  formatDraftAge, type NoteDraft,
} from '@/utils/noteDrafts'

const props = defineProps<{
  projectId: number
  note?: NoteOut | null
}>()

const emit = defineEmits<{
  saved: [note: NoteOut]
  cancel: []
}>()

const loading = ref(false)
const categories = ref<CategoryOut[]>([])
const isEdit = computed(() => !!props.note)
const fileInput = ref<HTMLInputElement | null>(null)
const uploading = ref(false)
// Per-file upload progress: filename -> percent
const uploadProgress = ref<Record<string, number>>({})

const totalProgress = computed(() => {
  const vals = Object.values(uploadProgress.value)
  if (!vals.length) return 0
  return Math.round(vals.reduce((a, b) => a + b, 0) / vals.length)
})
const isUploading = computed(() => totalProgress.value > 0 && totalProgress.value < 100)
const attachments = ref<NoteAttachmentOut[]>([])
const pendingFiles = ref<FileOut[]>([])  // file attachments queued for save

const form = ref({
  title: props.note?.title ?? '',
  content: props.note?.content ?? '',
  category_id: props.note?.category_id ?? (null as number | null),
})

// ── Drafts (localStorage autosave) ─────────────────────────────
const draftScope = computed(() =>
  isEdit.value ? editNoteScope(props.note!.id) : newNoteScope(props.projectId),
)
const draftRecovered = ref<NoteDraft | null>(null)
const lastSavedAt = ref<number | null>(null)
let autosaveTimer: number | null = null

async function maybeRecoverDraft() {
  // Don't overwrite an existing note's actual content with a stale draft
  const draft = loadDraft(draftScope.value)
  if (!draft) return

  // If the form already has content matching the draft, nothing to recover
  if (draft.title === form.value.title && draft.content === form.value.content) {
    lastSavedAt.value = draft.savedAt
    return
  }

  // Compare against current form state; if user already typed something new, still offer recovery
  const isEmpty = !form.value.title && !form.value.content
  if (isEmpty) {
    form.value.title = draft.title
    form.value.content = draft.content
    form.value.category_id = draft.category_id
    inlineFileIdsToAttach.value = [...(draft.inlineFileIds || [])]
    pendingFiles.value = draft.pendingFileIds
      .map(id => uploadedFilesCache[id])
      .filter(Boolean) as FileOut[]
    draftRecovered.value = draft
    lastSavedAt.value = draft.savedAt
    ElMessage.info(`已恢复 ${formatDraftAge(draft.savedAt)} 的草稿`)
  } else {
    // Form has content; ask whether to recover
    try {
      await ElMessageBox.confirm(
        `检测到 ${formatDraftAge(draft.savedAt)} 的未保存草稿。要恢复它吗？\n\n点击「恢复」会用草稿覆盖当前内容；点击「丢弃」会清除草稿。`,
        '发现草稿',
        {
          confirmButtonText: '恢复草稿',
          cancelButtonText: '丢弃',
          distinguishCancelAndClose: true,
          type: 'info',
        },
      )
      form.value.title = draft.title
      form.value.content = draft.content
      form.value.category_id = draft.category_id
      inlineFileIdsToAttach.value = [...(draft.inlineFileIds || [])]
      pendingFiles.value = draft.pendingFileIds
        .map(id => uploadedFilesCache[id])
        .filter(Boolean) as FileOut[]
      draftRecovered.value = draft
      lastSavedAt.value = draft.savedAt
    } catch (action) {
      // 'discard' returns 'cancel'; both 'cancel' and 'close' should clear the draft
      if (action === 'cancel' || action === 'close') {
        clearDraft(draftScope.value)
      }
    }
  }
}

// Cache file metadata so we can restore pendingFiles on draft recovery
const uploadedFilesCache: Record<number, FileOut> = {}

function scheduleAutosave() {
  if (autosaveTimer != null) {
    clearTimeout(autosaveTimer)
  }
  autosaveTimer = window.setTimeout(() => {
    const draft: NoteDraft = {
      scope: draftScope.value,
      title: form.value.title,
      content: form.value.content,
      category_id: form.value.category_id,
      pendingFileIds: pendingFiles.value.map(f => f.id),
      inlineFileIds: [...inlineFileIdsToAttach.value],
      savedAt: Date.now(),
    }
    saveDraft(draft)
    lastSavedAt.value = draft.savedAt
  }, 1200)  // debounce 1.2s
}

// Track changes for autosave
watch(
  () => [form.value.title, form.value.content, form.value.category_id],
  () => scheduleAutosave(),
)
watch(
  () => [pendingFiles.value.length, inlineFileIdsToAttach.value.length],
  () => scheduleAutosave(),
)

// Cache file metadata as they're uploaded (used during draft recovery)
watch(pendingFiles, (newList) => {
  for (const f of newList) {
    uploadedFilesCache[f.id] = f
  }
}, { deep: true })

const lastSavedLabel = computed(() =>
  lastSavedAt.value ? `已自动暂存 · ${formatDraftAge(lastSavedAt.value)}` : '',
)

async function loadCategories() {
  try {
    const resp = await categoriesApi.list()
    categories.value = resp.data.items
  } catch {
    categories.value = []
  }
}

async function loadAttachments() {
  if (!props.note?.id) return
  try {
    attachments.value = (await noteAttachmentsApi.list(props.note.id)).data
  } catch {
    attachments.value = []
  }
}

function flattenCats(cats: CategoryOut[], prefix = ''): { id: number; label: string }[] {
  const result: { id: number; label: string }[] = []
  for (const cat of cats) {
    result.push({ id: cat.id, label: prefix + cat.name })
    if (cat.children.length > 0) {
      result.push(...flattenCats(cat.children, prefix + cat.name + ' / '))
    }
  }
  return result
}

// ── md-editor-v3 image upload hook ──────────────────────────
// Called when user uses the editor's image button / drags / pastes an image.
// We upload to /api/v1/files/upload, then return the URLs to be inserted into
// the markdown body. The file IDs are stashed for post-save attachment linking.
const inlineFileIdsToAttach = ref<number[]>([])

async function onUploadImg(files: File[], callback: (urls: string[]) => void) {
  const urls: string[] = []
  for (const f of files) {
    uploadProgress.value[f.name] = 0
    try {
      const resp = await filesApi.upload(f, props.projectId, (pct) => {
        uploadProgress.value[f.name] = pct
      })
      urls.push(resp.data.url)
      inlineFileIdsToAttach.value.push(resp.data.id)
      uploadedFilesCache[resp.data.id] = resp.data
      uploadProgress.value[f.name] = 100
    } catch (err: any) {
      ElMessage.error(`${f.name}: ${err?.response?.data?.error?.message || '上传失败'}`)
      delete uploadProgress.value[f.name]
    }
  }
  callback(urls)
}

function onBeforeUpload(file: File): boolean {
  if (file.size > 100 * 1024 * 1024) {
    ElMessage.error(`${file.name} 超过 100 MB`)
    return false
  }
  return true
}

// ── Generic file attachment (non-image) ─────────────────────
function openFilePicker() { fileInput.value?.click() }

async function handleFilePick(e: Event) {
  const target = e.target as HTMLInputElement
  const files = Array.from(target.files ?? [])
  if (!files.length) return
  uploading.value = true
  for (const f of files) {
    uploadProgress.value[f.name] = 0
    try {
      const resp = await filesApi.upload(f, props.projectId, (pct) => {
        uploadProgress.value[f.name] = pct
      })
      pendingFiles.value.push(resp.data)
      uploadedFilesCache[resp.data.id] = resp.data
      uploadProgress.value[f.name] = 100
    } catch (err: any) {
      ElMessage.error(`${f.name}: ${err?.response?.data?.error?.message || '上传失败'}`)
      delete uploadProgress.value[f.name]
    }
  }
  uploading.value = false
  if (target) target.value = ''
  // Clean up progress map after a short delay so the user sees the 100% briefly
  setTimeout(() => {
    for (const f of files) delete uploadProgress.value[f.name]
  }, 1500)
  ElMessage.success(`已暂存 ${pendingFiles.value.length} 个文件（保存笔记后挂载）`)
}

function removePending(file: FileOut) {
  pendingFiles.value = pendingFiles.value.filter(f => f.id !== file.id)
}

async function removeAttachment(a: NoteAttachmentOut) {
  await noteAttachmentsApi.detach(props.note!.id, a.id)
  ElMessage.success('已移除')
  await loadAttachments()
}

function downloadFile(file: FileOut) {
  const a = document.createElement('a')
  a.href = filesApi.downloadUrl(file.id)
  a.rel = 'noopener'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

async function submit() {
  if (!form.value.title.trim()) {
    ElMessage.warning('请输入标题')
    return
  }
  loading.value = true
  try {
    let note: NoteOut
    if (isEdit.value) {
      note = (await notesApi.update(props.note!.id, form.value)).data
    } else {
      note = (await notesApi.create({ ...form.value, project_id: props.projectId })).data
    }

    // Attach inline-uploaded images
    for (const id of inlineFileIdsToAttach.value) {
      try {
        await noteAttachmentsApi.attach(note.id, { file_id: id, role: 'inline' })
      } catch {
        // best-effort
      }
    }

    // Attach queued file attachments
    for (let i = 0; i < pendingFiles.value.length; i++) {
      try {
        await noteAttachmentsApi.attach(note.id, {
          file_id: pendingFiles.value[i].id,
          role: 'attachment',
          position: i,
        })
      } catch {
        // best-effort
      }
    }

    inlineFileIdsToAttach.value = []
    pendingFiles.value = []

    // Clear the draft after a successful save
    clearDraft(draftScope.value)
    lastSavedAt.value = null

    ElMessage.success(isEdit.value ? '笔记已更新' : '笔记已创建')
    emit('saved', note)
  } finally {
    loading.value = false
  }
}

// Reset inline tracking when editing an existing note (we only track new uploads)
watch(() => props.note?.id, () => {
  inlineFileIdsToAttach.value = []
  pendingFiles.value = []
})

onMounted(() => {
  loadCategories()
  loadAttachments()
  // Defer draft recovery to after initial data load
  setTimeout(() => maybeRecoverDraft(), 100)
})
</script>

<template>
  <el-form :model="form" label-position="top" @submit.prevent="submit">
    <el-form-item label="标题" required>
      <el-input v-model="form.title" placeholder="笔记标题" maxlength="200" />
    </el-form-item>

    <el-form-item label="分类">
      <el-select v-model="form.category_id" placeholder="选择分类（可选）" clearable style="width:100%">
        <el-option
          v-for="cat in flattenCats(categories)"
          :key="cat.id"
          :label="cat.label"
          :value="cat.id"
        />
      </el-select>
    </el-form-item>

    <el-form-item label="内容（Markdown 编辑器）">
      <MdEditor
        v-model="form.content"
        :theme="'light'"
        :preview="true"
        :show-code-row-number="true"
        language="zh-CN"
        :max-length="50000"
        style="height: 480px;"
        :on-upload-img="onUploadImg"
        :on-before-upload="onBeforeUpload"
        :toolbars-exclude="['github']"
      />
      <input
        ref="fileInput"
        type="file"
        multiple
        style="display:none"
        @change="handleFilePick"
      />
    </el-form-item>

    <!-- Pending file attachments -->
    <div v-if="pendingFiles.length" class="pending-block">
      <h5>📎 待挂载文件（{{ pendingFiles.length }}）</h5>
      <div
        v-for="f in pendingFiles"
        :key="f.id"
        class="pending-file"
      >
        <span>{{ iconForFile(f.original_name, f.category) }}</span>
        <span class="filename" :title="f.original_name">{{ f.original_name }}</span>
        <span class="filemeta">{{ formatFileSize(f.size) }}</span>
        <el-button size="small" text type="danger" @click="removePending(f)">移除</el-button>
      </div>
    </div>

    <!-- Existing attachments (edit mode only) -->
    <div v-if="isEdit && attachments.length" class="pending-block">
      <h5>已关联附件（{{ attachments.length }}）</h5>
      <div
        v-for="a in attachments"
        :key="a.id"
        class="pending-file"
      >
        <span>{{ iconForFile(a.file.original_name, a.file.category) }}</span>
        <span class="filename" :title="a.file.original_name">{{ a.file.original_name }}</span>
        <span class="filemeta">{{ formatFileSize(a.file.size) }}</span>
        <el-button size="small" text @click="downloadFile(a.file)">下载</el-button>
        <el-button size="small" text type="danger" @click="removeAttachment(a)">移除</el-button>
      </div>
    </div>

    <!-- Upload progress overlay -->
    <div v-if="isUploading" class="upload-progress-bar">
      <div class="upload-progress-info">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>上传中… {{ totalProgress }}%</span>
      </div>
      <el-progress
        :percentage="totalProgress"
        :stroke-width="6"
        :show-text="false"
        :status="totalProgress >= 100 ? 'success' : ''"
      />
    </div>

    <div class="form-actions">
      <div class="form-actions-left">
        <el-button :loading="uploading" @click="openFilePicker">📎 附加文件</el-button>
        <span v-if="lastSavedLabel" class="hint autosave-hint">{{ lastSavedLabel }}</span>
        <span v-else class="hint">图片可直接拖入编辑器或点击工具栏图片按钮</span>
      </div>
      <div class="form-actions-right">
        <el-button @click="emit('cancel')">取消</el-button>
        <el-button type="primary" :loading="loading" @click="submit">
          {{ isEdit ? '保存' : '创建' }}
        </el-button>
      </div>
    </div>
  </el-form>
</template>

<style scoped>
.form-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 0.5rem;
}
.form-actions-left,
.form-actions-right {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}
.hint {
  font-size: 0.78rem;
  color: var(--el-text-color-secondary);
}
.autosave-hint {
  color: var(--el-color-success);
  font-weight: 500;
}

/* Upload progress bar — sticky at the bottom of the form, above actions */
.upload-progress-bar {
  position: sticky;
  bottom: 0;
  background: var(--el-bg-color);
  border: 1px solid var(--el-color-primary-light-5);
  border-radius: 6px;
  padding: 0.5rem 0.75rem;
  margin: 0.75rem 0 0.25rem;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.04);
  z-index: 5;
}
.upload-progress-info {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.85rem;
  color: var(--el-color-primary);
  margin-bottom: 0.35rem;
}
.is-loading {
  animation: rotating 1.5s linear infinite;
}
@keyframes rotating {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.pending-block {
  margin-top: 0.75rem;
  margin-bottom: 0.75rem;
  padding: 0.6rem 0.75rem;
  background: var(--el-fill-color-light);
  border-radius: 8px;
}
.pending-block h5 {
  margin: 0 0 0.5rem;
  font-size: 0.85rem;
  color: var(--el-text-color-secondary);
}
.pending-file {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.5rem;
  font-size: 0.85rem;
  border-radius: 4px;
}
.pending-file:hover {
  background: var(--el-bg-color);
}
.pending-file .filename {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.pending-file .filemeta {
  color: var(--el-text-color-secondary);
  font-size: 0.75rem;
}
</style>