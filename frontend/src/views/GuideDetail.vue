<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { guidesApi, type GuideOut } from '@/api/guides'
import { projectsApi, type ProjectOut } from '@/api/projects'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, ArrowRight, ArrowDown } from '@element-plus/icons-vue'
import MarkdownRenderer from '@/components/notes/MarkdownRenderer.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const guides = ref<GuideOut[]>([])
const current = ref<GuideOut | null>(null)
const loading = ref(false)
const relatedProjects = ref<ProjectOut[]>([])
const activeTag = ref<string>('')
const showDialog = ref(false)
const editing = ref<GuideOut | null>(null)

interface TagGroup {
  tag: string
  label: string
  guides: GuideOut[]
}

const tagGroups = computed<TagGroup[]>(() => {
  const map = new Map<string, TagGroup>()
  for (const g of guides.value) {
    if (!map.has(g.tag)) {
      map.set(g.tag, { tag: g.tag, label: g.tag, guides: [] })
    }
    map.get(g.tag)!.guides.push(g)
  }
  return Array.from(map.values()).sort((a, b) => {
    if (a.tag === 'intro') return -1
    if (b.tag === 'intro') return 1
    return 0
  })
})

const expandedTags = ref<Set<string>>(new Set(['intro']))

function toggleTag(tag: string) {
  if (expandedTags.value.has(tag)) {
    expandedTags.value.delete(tag)
  } else {
    expandedTags.value.add(tag)
  }
}

function canCreate() {
  const u = auth.user
  if (!u) return false
  if (u.role === 'owner') return true
  if (u.status === 'graduated') return true
  const ey = u.profile?.enrollment_year
  if (ey && new Date().getFullYear() - ey >= 2) return true
  return false
}

function canUpdate() {
  const u = auth.user
  if (!u) return false
  if (u.role === 'owner') return true
  const ey = u.profile?.enrollment_year
  if (ey && new Date().getFullYear() - ey >= 2) return true
  return false
}

const defaultForm = () => ({
  title: editing.value?.title ?? '',
  slug: editing.value?.slug ?? '',
  content: editing.value?.content ?? '',
  tag: editing.value?.tag ?? 'intro',
  related_projects: editing.value?.related_projects ?? null,
  sort_order: editing.value?.sort_order ?? 0,
  is_pinned: editing.value?.is_pinned ?? false,
})
const form = ref(defaultForm())

async function loadGuides() {
  try {
    guides.value = (await guidesApi.list({ tag: activeTag.value || undefined })).data.items
    if (guides.value.length > 0 && !current.value) {
      const slug = route.params.slug as string
      if (slug) {
        current.value = guides.value.find(g => g.slug === slug) ?? guides.value[0]
      } else {
        current.value = guides.value[0]
      }
      // Auto-expand the tag group that contains the current guide
      if (current.value) {
        expandedTags.value.add(current.value.tag)
      }
    }
  } catch { guides.value = [] }
}

async function loadContent(slug?: string) {
  if (!slug) return
  loading.value = true
  try {
    current.value = (await guidesApi.get(slug)).data
    // Load related projects
    if (current.value?.related_projects) {
      try {
        const ids = JSON.parse(current.value.related_projects) as number[]
        const results = await Promise.all(ids.map(id => projectsApi.get(id).catch(() => null)))
        relatedProjects.value = results.filter(r => r !== null).map(r => r!.data)
      } catch { relatedProjects.value = [] }
    } else {
      relatedProjects.value = []
    }
  } finally {
    loading.value = false
  }
}

function selectGuide(g: GuideOut) {
  expandedTags.value.add(g.tag)
  router.replace(`/guides/${g.slug}`)
}

function openCreate() {
  editing.value = null
  form.value = defaultForm()
  showDialog.value = true
}

function openEdit(g: GuideOut) {
  editing.value = g
  form.value = {
    title: g.title, slug: g.slug, content: g.content,
    tag: g.tag, related_projects: g.related_projects,
    sort_order: g.sort_order, is_pinned: g.is_pinned,
  }
  showDialog.value = true
}

async function handleSubmit() {
  if (!form.value.title.trim()) return
  try {
    if (editing.value) {
      await guidesApi.update(editing.value.id, form.value)
      ElMessage.success('已更新')
    } else {
      await guidesApi.create(form.value)
      ElMessage.success('指南已创建')
    }
    showDialog.value = false
    await loadGuides()
    if (!editing.value) {
      selectGuide(guides.value.find(g => g.slug === form.value.slug) ?? guides.value[0])
    } else {
      await loadContent(form.value.slug)
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.error?.message || '操作失败')
  }
}

async function handleDelete(g: GuideOut) {
  try {
    await ElMessageBox.confirm('确定删除？', '确认', { confirmButtonText: '删除', type: 'warning' })
  } catch { return }
  await guidesApi.remove(g.id)
  ElMessage.success('已删除')
  current.value = null
  await loadGuides()
  if (guides.value.length > 0) selectGuide(guides.value[0])
}

watch(() => activeTag.value, () => {
  current.value = null
  loadGuides()
})

watch(() => route.params.slug, (slug) => {
  if (slug) loadContent(slug as string)
})

onMounted(async () => {
  await loadGuides()
  const slug = route.params.slug as string
  if (slug) await loadContent(slug)
  else if (guides.value.length > 0) selectGuide(guides.value[0])
})
</script>

<template>
  <div class="guide-page">
    <!-- Left sidebar with accordion -->
    <aside class="guide-sidebar">
      <!-- Tag filter tabs -->
      <div class="guide-tags">
        <div
          v-for="t in [{ value: '', label: '全部' }, ...tagGroups.map(g => ({ value: g.tag, label: g.label }))]"
          :key="t.value"
          class="tag-tab"
          :class="{ active: activeTag === t.value }"
          @click="activeTag = t.value"
        >{{ t.label }}</div>
      </div>

      <!-- Accordion groups -->
      <div class="guide-list">
        <div v-if="tagGroups.length === 0" class="g-empty">暂无内容</div>

        <div v-for="group in tagGroups" :key="group.tag" class="accordion-group">
          <!-- Group header -->
          <div
            class="accordion-header"
            :class="{ active: expandedTags.has(group.tag) }"
            @click="toggleTag(group.tag)"
          >
            <el-icon class="accordion-arrow">
              <ArrowDown v-if="expandedTags.has(group.tag)" />
              <ArrowRight v-else />
            </el-icon>
            <span class="accordion-title">{{ group.label }}</span>
            <el-tag size="small" effect="plain" style="margin-left:auto; margin-right:0.5rem">
              {{ group.guides.length }}
            </el-tag>
          </div>

          <!-- Group items (collapsible) -->
          <div v-if="expandedTags.has(group.tag)" class="accordion-items">
            <div
              v-for="g in group.guides" :key="g.id"
              class="guide-item"
              :class="{ active: current?.id === g.id }"
              @click="selectGuide(g)"
            >
              <span class="gi-pin" v-if="g.is_pinned">📌</span>
              <span class="gi-title">{{ g.title }}</span>
            </div>
          </div>
        </div>
      </div>

      <el-button
        v-if="canCreate()"
        type="primary" size="small"
        :icon="Plus" style="margin-top:0.75rem"
        @click="openCreate"
      >新建指南</el-button>
    </aside>

    <!-- Main content -->
    <main class="guide-main" v-loading="loading">
      <template v-if="current">
        <div class="guide-header">
          <h2>{{ current.title }}</h2>
          <div class="guide-actions">
            <el-button v-if="canUpdate()" text size="small" @click="openEdit(current)">编辑</el-button>
            <el-button v-if="auth.isOwner" text size="small" type="danger" @click="handleDelete(current)">删除</el-button>
          </div>
        </div>
        <div class="guide-content">
          <MarkdownRenderer :content="current.content" />
        </div>

        <!-- Related projects -->
        <div v-if="relatedProjects.length > 0" class="related-section">
          <h4>📂 相关项目</h4>
          <div class="related-cards">
            <div
              v-for="p in relatedProjects" :key="p.id"
              class="related-card"
              @click="router.push(`/projects/${p.id}`)"
            >
              <span class="rc-title">{{ p.title }}</span>
              <span class="rc-desc">{{ (p.description || '').slice(0, 60) }}</span>
            </div>
          </div>
        </div>
      </template>
      <div v-else class="guide-empty">选择左侧指南开始阅读</div>
    </main>

    <!-- Edit dialog -->
    <el-dialog
      v-model="showDialog"
      :title="editing ? '编辑指南' : '新建指南'"
      width="600px" destroy-on-close
    >
      <el-form label-position="top">
        <el-form-item label="标题" required>
          <el-input v-model="form.title" maxlength="200" placeholder="如：Python 环境配置" />
        </el-form-item>
        <el-form-item label="分类标签">
          <el-input v-model="form.tag" maxlength="32" placeholder="输入标签名，如：工具、课程、规范" />
        </el-form-item>
        <el-form-item label="正文（Markdown）">
          <el-input v-model="form.content" type="textarea" :rows="12" placeholder="Markdown 格式..." />
        </el-form-item>
        <el-form-item label="关联项目 ID（JSON数组，如 [1,2]）" v-if="form.tag === 'courses'">
          <el-input v-model="form.related_projects" placeholder='[1, 2, 3]' />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="排序">
              <el-input-number v-model="form.sort_order" :min="0" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="置顶">
              <el-switch v-model="form.is_pinned" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">{{ editing ? '保存' : '创建' }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.guide-page {
  display: flex; gap: 1.5rem; max-width: 1200px; margin: 0 auto; height: calc(100vh - 120px);
}

/* Sidebar */
.guide-sidebar {
  width: 260px; flex-shrink: 0; display: flex; flex-direction: column;
  background: var(--el-bg-color); border-radius: 12px; padding: 1rem 0.85rem;
  border: 1px solid var(--el-border-color-lighter); overflow-y: auto;
}
.guide-tags {
  display: flex; flex-wrap: wrap; gap: 0.35rem;
  padding: 0 0.15rem 0.75rem;
  margin-bottom: 0.5rem;
  border-bottom: 1px dashed var(--el-border-color-lighter);
}
.tag-tab {
  display: inline-flex; align-items: center; gap: 0.35rem;
  padding: 0.35rem 0.7rem; border-radius: 14px; cursor: pointer;
  font-size: 0.8rem; transition: background 0.15s, color 0.15s;
  color: var(--el-text-color-regular);
  background: var(--el-fill-color-blank);
  border: 1px solid var(--el-border-color-lighter);
}
.tag-tab:hover { background: var(--el-fill-color-light); }
.tag-tab.active {
  background: var(--el-color-primary);
  color: white;
  border-color: var(--el-color-primary);
  font-weight: 600;
}
.tag-icon { font-size: 1rem; }
.tag-label { white-space: nowrap; }

.guide-list {
  flex: 1; display: flex; flex-direction: column; overflow-y: auto;
  padding: 0 0.15rem;
}
.g-empty { text-align: center; color: var(--lab-muted); padding: 1.5rem 0; font-size: 0.85rem; }

/* Accordion */
.accordion-group {
  margin-bottom: 0.4rem;
}
.accordion-header {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.55rem 0.75rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.86rem;
  font-weight: 600;
  color: var(--el-text-color-primary);
  transition: background 0.15s;
  user-select: none;
  background: var(--el-fill-color-blank);
  border: 1px solid transparent;
}
.accordion-header:hover {
  background: var(--el-fill-color-light);
  border-color: var(--el-border-color-lighter);
}
.accordion-header.active {
  background: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary-light-7);
  color: var(--el-color-primary);
}
.accordion-arrow {
  font-size: 0.78rem;
  transition: transform 0.2s;
  color: var(--lab-muted);
  flex-shrink: 0;
}
.accordion-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.accordion-items {
  padding-left: 1.25rem;
  margin: 0.25rem 0 0.4rem 0.5rem;
  border-left: 2px solid var(--el-border-color-lighter);
}

/* Guide items */
.guide-item {
  padding: 0.45rem 0.75rem;
  margin: 0.15rem 0;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.84rem;
  display: flex;
  align-items: center;
  gap: 0.35rem;
  transition: background 0.15s, color 0.15s;
  color: var(--el-text-color-regular);
  position: relative;
}
.guide-item::before {
  content: '';
  position: absolute;
  left: -1.25rem;
  top: 50%;
  width: 0.65rem;
  height: 1px;
  background: var(--el-border-color-lighter);
  pointer-events: none;
}
.guide-item:hover { background: var(--el-fill-color-light); color: var(--el-text-color-primary); }
.guide-item.active { background: var(--el-color-primary-light-9); color: var(--el-color-primary); font-weight: 600; }
.gi-pin { font-size: 0.7rem; flex-shrink: 0; }
.gi-title { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* Main */
.guide-main {
  flex: 1; overflow-y: auto; background: var(--el-bg-color);
  border-radius: 12px; padding: 1.5rem 2rem;
  border: 1px solid var(--el-border-color-lighter);
  min-height: 400px;
}
.guide-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem; }
.guide-header h2 { margin: 0; font-size: 1.3rem; }
.guide-actions { display: flex; gap: 0.25rem; flex-shrink: 0; }
.guide-content { line-height: 1.7; }
.guide-empty { text-align: center; color: var(--lab-muted); padding: 3rem 0; font-size: 0.95rem; }

/* Related projects */
.related-section { margin-top: 2rem; padding-top: 1.5rem; border-top: 1px solid var(--el-border-color-lighter); }
.related-section h4 { margin: 0 0 0.75rem; font-size: 0.95rem; }
.related-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 0.5rem; }
.related-card {
  padding: 0.75rem; border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px; cursor: pointer; transition: border-color 0.15s;
}
.related-card:hover { border-color: var(--el-color-primary); }
.rc-title { display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.2rem; }
.rc-desc { display: block; font-size: 0.76rem; color: var(--lab-muted); }
</style>
