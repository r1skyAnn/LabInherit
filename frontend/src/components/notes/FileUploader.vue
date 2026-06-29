<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { filesApi, type FileOut } from '@/api/files'

const props = defineProps<{
  projectId?: number
  /** File types accepted (e.g. 'image/*' or '.pdf,.docx'). */
  accept?: string
  /** Multiple files at once? */
  multiple?: boolean
}>()

const emit = defineEmits<{
  uploaded: [files: FileOut[]]
  error: [message: string]
}>()

const fileInput = ref<HTMLInputElement | null>(null)
const uploading = ref(false)
const progress = ref(0)

function open() {
  fileInput.value?.click()
}

async function handleChange(e: Event) {
  const target = e.target as HTMLInputElement
  const files = Array.from(target.files ?? [])
  if (!files.length) return
  uploading.value = true
  progress.value = 0
  const results: FileOut[] = []
  for (let i = 0; i < files.length; i++) {
    try {
      const resp = await filesApi.upload(files[i], props.projectId)
      results.push(resp.data)
      progress.value = Math.round(((i + 1) / files.length) * 100)
    } catch (err: any) {
      const msg = err?.response?.data?.error?.message || '上传失败'
      ElMessage.error(`${files[i].name}: ${msg}`)
      emit('error', msg)
    }
  }
  uploading.value = false
  if (target) target.value = ''
  if (results.length) {
    ElMessage.success(`已上传 ${results.length} 个文件`)
    emit('uploaded', results)
  }
}

defineExpose({ open })
</script>

<template>
  <input
    ref="fileInput"
    type="file"
    :accept="accept"
    :multiple="multiple"
    style="display: none"
    @change="handleChange"
  />
  <slot :open="open" :uploading="uploading" :progress="progress" />
</template>