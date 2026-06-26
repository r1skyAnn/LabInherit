<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { projectsApi, type ProjectOut } from '@/api/projects'
import ProjectCard from '@/components/projects/ProjectCard.vue'
import ProjectForm from '@/components/projects/ProjectForm.vue'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const auth = useAuthStore()
const projects = ref<ProjectOut[]>([])
const total = ref(0)
const loading = ref(false)
const filterStatus = ref<string>('')
const showForm = ref(false)
const editingProject = ref<ProjectOut | null>(null)

async function load() {
  loading.value = true
  try {
    const resp = await projectsApi.list({
      status: filterStatus.value || undefined,
      page: 1,
      page_size: 100,
    })
    projects.value = resp.data.items
    total.value = resp.data.total
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingProject.value = null
  showForm.value = true
}

function openEdit(project: ProjectOut) {
  editingProject.value = project
  showForm.value = true
}

async function handleSaved() {
  showForm.value = false
  editingProject.value = null
  await load()
}

async function handleDelete(project: ProjectOut) {
  try {
    await projectsApi.remove(project.id)
    ElMessage.success('项目已删除')
    await load()
  } catch {
    // handled by interceptor
  }
}

onMounted(load)
</script>

<template>
  <div class="projects-page">
    <div class="page-header">
      <h2>项目列表</h2>
      <div class="header-actions">
        <el-select v-model="filterStatus" @change="load" clearable placeholder="全部状态" style="width:150px">
          <el-option label="全部状态" value="" />
          <el-option label="规划中" value="planning" />
          <el-option label="进行中" value="active" />
          <el-option label="已暂停" value="paused" />
          <el-option label="已完成" value="completed" />
          <el-option label="已废弃" value="abandoned" />
        </el-select>
        <el-button v-if="auth.user?.status !== 'graduated'" type="primary" @click="openCreate">+ 新建项目</el-button>
      </div>
    </div>

    <el-empty v-if="!loading && projects.length === 0" description="暂无项目" style="margin-top:4rem" />

    <div v-else class="projects-grid">
      <ProjectCard
        v-for="project in projects"
        :key="project.id"
        :project="project"
        :is-owner="auth.user?.id === project.created_by"
        @edit="openEdit"
        @delete="handleDelete"
      />
    </div>

    <div class="summary">共 {{ total }} 个项目</div>

    <el-dialog v-model="showForm" :title="editingProject ? '编辑项目' : '新建项目'" width="600px">
      <ProjectForm :project="editingProject" @saved="handleSaved" @cancel="showForm = false" />
    </el-dialog>
  </div>
</template>

<style scoped>
.projects-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
}

.page-header h2 {
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1rem;
}

.summary {
  margin-top: 1rem;
  color: var(--lab-muted);
  font-size: 0.85rem;
}
</style>
