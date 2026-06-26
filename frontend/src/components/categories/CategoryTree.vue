<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { categoriesApi, type CategoryOut, type CategoryCreate, type CategoryUpdate } from '@/api/categories'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'

const auth = useAuthStore()
const treeData = ref<CategoryOut[]>([])
const total = ref(0)
const loading = ref(false)
const showForm = ref(false)
const editingCategory = ref<CategoryOut | null>(null)
const formParentId = ref<number | null>(null)

const form = ref<CategoryCreate>({ name: '', parent_id: null, sort_order: 0 })
const formLoading = ref(false)

async function load() {
  loading.value = true
  try {
    const resp = await categoriesApi.list()
    treeData.value = resp.data.items
    total.value = resp.data.total
  } finally {
    loading.value = false
  }
}

function openCreate(parentId: number | null = null) {
  editingCategory.value = null
  formParentId.value = parentId
  form.value = { name: '', parent_id: parentId, sort_order: 0 }
  showForm.value = true
}

function openEdit(cat: CategoryOut) {
  editingCategory.value = cat
  form.value = { name: cat.name, parent_id: cat.parent_id, sort_order: cat.sort_order }
  showForm.value = true
}

async function handleSubmit() {
  if (!form.value.name.trim()) return
  formLoading.value = true
  try {
    if (editingCategory.value) {
      const data: CategoryUpdate = { name: form.value.name, sort_order: form.value.sort_order }
      await categoriesApi.update(editingCategory.value.id, data)
      ElMessage.success('分类已更新')
    } else {
      await categoriesApi.create(form.value)
      ElMessage.success('分类已创建')
    }
    showForm.value = false
    await load()
  } finally {
    formLoading.value = false
  }
}

async function handleDelete(cat: CategoryOut) {
  try {
    await ElMessageBox.confirm(
      `确定删除分类「${cat.name}」吗？${cat.children.length > 0 ? '其下所有子分类也会被删除。' : ''}`,
      '确认删除',
      { confirmButtonText: '删除', type: 'warning' },
    )
  } catch {
    return
  }
  await categoriesApi.remove(cat.id)
  ElMessage.success('已删除')
  await load()
}

function renderTree(nodes: CategoryOut[]): any[] {
  return nodes.map((node) => ({
    id: node.id,
    label: node.name,
    children: node.children.length > 0 ? renderTree(node.children) : undefined,
    _raw: node,
  }))
}

function onTreeAction(_data: any, action: string, node: any) {
  const cat = node._raw as CategoryOut
  if (action === 'add') {
    openCreate(cat.id)
  } else if (action === 'edit') {
    openEdit(cat)
  } else if (action === 'delete') {
    handleDelete(cat)
  }
}

function renderLabel(_data: any, node: any) {
  const cat = node._raw as CategoryOut
  return cat.name
}

onMounted(load)
</script>

<template>
  <div class="category-tree" v-loading="loading">
    <div class="tree-header">
      <span class="tree-title">分类管理</span>
      <el-button type="primary" size="small" @click="openCreate(null)">添加根分类</el-button>
    </div>

    <el-empty v-if="total === 0 && !loading" description="暂无分类，点击上方按钮创建" />

    <div v-for="root in treeData" :key="root.id" class="tree-node">
      <div class="node-row">
        <span class="node-name">{{ root.name }}</span>
        <span class="node-slug">/{{ root.slug }}</span>
        <span class="node-actions">
          <el-button text size="small" @click="openCreate(root.id)">+子分类</el-button>
          <el-button text size="small" @click="openEdit(root)">编辑</el-button>
          <el-button text size="small" type="danger" @click="handleDelete(root)">删除</el-button>
        </span>
      </div>
      <div v-if="root.children.length > 0" class="node-children">
        <div v-for="child in root.children" :key="child.id" class="tree-node child-node">
          <div class="node-row">
            <span class="node-name">{{ child.name }}</span>
            <span class="node-slug">/{{ child.slug }}</span>
            <span class="node-actions">
              <el-button text size="small" @click="openCreate(child.id)">+子分类</el-button>
              <el-button text size="small" @click="openEdit(child)">编辑</el-button>
              <el-button text size="small" type="danger" @click="handleDelete(child)">删除</el-button>
            </span>
          </div>
          <div v-if="child.children.length > 0" class="node-children">
            <div v-for="gchild in child.children" :key="gchild.id" class="tree-node child-node">
              <div class="node-row">
                <span class="node-name">{{ gchild.name }}</span>
                <span class="node-slug">/{{ gchild.slug }}</span>
                <span class="node-actions">
                  <el-button text size="small" @click="openCreate(gchild.id)">+子分类</el-button>
                  <el-button text size="small" @click="openEdit(gchild)">编辑</el-button>
                  <el-button text size="small" type="danger" @click="handleDelete(gchild)">删除</el-button>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Form dialog -->
    <el-dialog
      v-model="showForm"
      :title="editingCategory ? '编辑分类' : '新建分类'"
      width="480px"
      destroy-on-close
    >
      <el-form :model="form" label-position="top" @submit.prevent="handleSubmit">
        <el-form-item label="分类名称" required>
          <el-input v-model="form.name" placeholder="例如：目标检测" maxlength="128" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" :max="9999" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showForm = false">取消</el-button>
        <el-button type="primary" :loading="formLoading" @click="handleSubmit">
          {{ editingCategory ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.tree-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}
.tree-title {
  font-weight: 600;
  font-size: 1rem;
}
.tree-node {
  margin-bottom: 2px;
}
.child-node {
  margin-left: 2rem;
}
.node-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: var(--el-fill-color-light);
  border-radius: 6px;
  margin-bottom: 2px;
}
.node-row:hover {
  background: var(--el-fill-color);
}
.node-name {
  font-weight: 500;
}
.node-slug {
  color: var(--el-text-color-placeholder);
  font-size: 0.8rem;
}
.node-actions {
  margin-left: auto;
  display: flex;
  gap: 0.25rem;
  opacity: 0;
  transition: opacity 0.2s;
}
.node-row:hover .node-actions {
  opacity: 1;
}
.node-children {
  margin-top: 2px;
}
</style>
