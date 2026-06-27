<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { notesApi, type NoteOut } from '@/api/notes'
import { categoriesApi, type CategoryOut } from '@/api/categories'
import { ElMessage } from 'element-plus'

const props = defineProps<{
  projectId: number
  note?: NoteOut | null
}>()

const emit = defineEmits<{
  saved: []
  cancel: []
}>()

const loading = ref(false)
const uploadLoading = ref(false)
const categories = ref<CategoryOut[]>([])
const isEdit = computed(() => !!props.note)
const fileInput = ref<HTMLInputElement | null>(null)

const form = ref({
  title: props.note?.title ?? '',
  content: props.note?.content ?? '',
  category_id: props.note?.category_id ?? (null as number | null),
})

async function loadCategories() {
  try {
    const resp = await categoriesApi.list()
    categories.value = resp.data.items
  } catch {
    categories.value = []
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

function triggerUpload() {
  fileInput.value?.click()
}

async function handleUpload(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  uploadLoading.value = true
  try {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('project_id', String(props.projectId))
    if (props.note?.id) {
      fd.append('note_id', String(props.note.id))
    }
    const token = localStorage.getItem('labinherit_token')
    const resp = await fetch('/api/v1/upload', {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: fd,
    })
    if (!resp.ok) throw new Error('Upload failed')
    const data = await resp.json()
    const url = data.url
    form.value.content += `\n![](${url})\n`
    ElMessage.success('图片已上传')
  } catch {
    // handled by interceptor
  } finally {
    uploadLoading.value = false
    if (target) target.value = ''
  }
}

async function submit() {
  if (!form.value.title.trim()) {
    ElMessage.warning('请输入标题')
    return
  }
  loading.value = true
  try {
    if (isEdit.value) {
      await notesApi.update(props.note!.id, form.value)
      ElMessage.success('笔记已更新')
    } else {
      await notesApi.create({ ...form.value, project_id: props.projectId })
      ElMessage.success('笔记已创建')
    }
    emit('saved')
  } finally {
    loading.value = false
  }
}

onMounted(loadCategories)
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

    <el-form-item label="内容（Markdown）">
      <el-input
        v-model="form.content"
        type="textarea"
        placeholder="支持 Markdown 语法和图片粘贴..."
        :rows="12"
      />
      <input
        ref="fileInput"
        type="file"
        accept="image/png,image/jpeg,image/gif,image/webp"
        style="display:none"
        @change="handleUpload"
      />
    </el-form-item>

    <div class="form-actions">
      <el-button :loading="uploadLoading" @click="triggerUpload">上传图片</el-button>
      <div class="form-actions-right">
        <el-button @click="emit('cancel')">取消</el-button>
        <el-button type="primary" :loading="loading" native-type="submit" @click="submit">
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
}
.form-actions-right {
  display: flex;
  gap: 0.5rem;
}
</style>
