<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { notesApi, type NoteOut } from '@/api/notes'
import { projectsApi, type ProjectOut } from '@/api/projects'
import { categoriesApi, type CategoryOut } from '@/api/categories'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Search } from '@element-plus/icons-vue'
import NoteCard from '@/components/notes/NoteCard.vue'
import NoteForm from '@/components/notes/NoteForm.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const projectId = Number(route.params.projectId)

const project = ref<ProjectOut | null>(null)
const notes = ref<NoteOut[]>([])
const total = ref(0)
const loading = ref(false)
const showForm = ref(false)
const editingNote = ref<NoteOut | null>(null)
const filterCategory = ref<number | null>(null)
const searchQuery = ref('')
const categories = ref<CategoryOut[]>([])

async function loadProject() {
  try {
    project.value = (await projectsApi.get(projectId)).data
  } catch {
    // handled
  }
}

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

const page = ref(1)
const pageSize = ref(12)

async function load() {
  loading.value = true
  try {
    const resp = await notesApi.list({
      project_id: projectId,
      category_id: filterCategory.value ?? undefined,
      q: searchQuery.value || undefined,
      page: page.value,
      page_size: pageSize.value,
    })
    notes.value = resp.data.items
    total.value = resp.data.total
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingNote.value = null
  showForm.value = true
}

function openEdit(note: NoteOut) {
  editingNote.value = note
  showForm.value = true
}

function handleSaved() {
  showForm.value = false
  load()
}

async function handleDelete(note: NoteOut) {
  try {
    await ElMessageBox.confirm(`确定删除笔记「${note.title}」吗？`, '确认删除', {
      confirmButtonText: '删除',
      type: 'warning',
    })
  } catch {
    return
  }
  await notesApi.remove(note.id)
  ElMessage.success('已删除')
  await load()
}

async function handleLike(note: NoteOut) {
  await notesApi.like(note.id)
  await load()
}

async function handleTogglePin(note: NoteOut) {
  await notesApi.update(note.id, { is_pinned: !note.is_pinned })
  ElMessage.success(note.is_pinned ? '已取消置顶' : '已置顶')
  await load()
}

onMounted(async () => {
  await Promise.all([loadProject(), loadCategories()])
  await load()
})
</script>

<template>
  <div class="notes-page" v-loading="loading">
    <div class="page-header">
      <el-button text @click="router.push('/projects')">
        <el-icon><ArrowLeft /></el-icon>
        返回项目列表
      </el-button>
      <h2 v-if="project">{{ project.title }} · 笔记</h2>
    </div>

    <div class="toolbar">
      <div class="toolbar-left">
        <el-input v-model="searchQuery" placeholder="搜索笔记..." clearable @clear="page=1;load()" @keyup.enter="page=1;load()" style="width:240px">
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select v-model="filterCategory" placeholder="全部分类" clearable @change="page=1;load()" style="width:200px">
          <el-option
            v-for="cat in flattenCats(categories)"
            :key="cat.id"
            :label="cat.label"
            :value="cat.id"
          />
        </el-select>
      </div>
      <el-button type="primary" @click="openCreate">写笔记</el-button>
    </div>

    <el-empty v-if="total === 0 && !loading" description="暂无笔记，点击「写笔记」开始记录" />

    <div class="notes-grid">
      <NoteCard
        v-for="note in notes"
        :key="note.id"
        :note="note"
        @edit="openEdit"
        @delete="handleDelete"
        @like="handleLike"
        @toggle-pin="handleTogglePin"
      />
    </div>

    <div class="summary">
      共 {{ total }} 条笔记
      <el-pagination
        v-if="total > pageSize"
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="load"
        style="margin-top:1rem; justify-content:center"
      />
    </div>

    <el-dialog v-model="showForm" :title="editingNote ? '编辑笔记' : '新建笔记'" width="720px" destroy-on-close>
      <NoteForm
        :project-id="projectId"
        :note="editingNote"
        @saved="handleSaved"
        @cancel="showForm = false"
      />
    </el-dialog>
  </div>
</template>

<style scoped>
.page-header {
  margin-bottom: 1rem;
}
.page-header h2 {
  margin: 0.5rem 0 0; font-size: 1.15rem; font-weight: 700;
  padding-left: 0.65rem; border-left: 3px solid var(--ember);
}
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}
.toolbar-left {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}
.notes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 1rem;
}
.summary {
  margin-top: 1rem;
  color: var(--lab-muted);
  font-size: 0.85rem;
}
</style>
