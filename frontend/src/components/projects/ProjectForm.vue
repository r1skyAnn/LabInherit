<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { projectsApi, type ProjectOut } from '@/api/projects'
import { categoriesApi, type CategoryOut } from '@/api/categories'
import { membersApi, type MemberOut } from '@/api/members'
import { ElMessage } from 'element-plus'

const props = defineProps<{
  project?: ProjectOut | null
}>()

const emit = defineEmits<{
  saved: []
  cancel: []
}>()

const loading = ref(false)
const formRef = ref()
const categories = ref<CategoryOut[]>([])
const members = ref<MemberOut[]>([])
const membersLoading = ref(false)

const isEdit = computed(() => !!props.project)

const defaultForm = () => ({
  title: props.project?.title ?? '',
  description: props.project?.description ?? '',
  category_id: props.project?.category_id ?? null,
  status: props.project?.status ?? 'active',
  priority: props.project?.priority ?? 'medium',
  tech_stack: props.project?.tech_stack ?? '',
  repo_url: props.project?.repo_url ?? '',
  demo_url: props.project?.demo_url ?? '',
  zip_url: props.project?.zip_url ?? '',
  started_at: props.project?.started_at ?? '',
  ended_at: props.project?.ended_at ?? '',
  is_public: props.project?.is_public ?? true,
  allowed_viewer_ids: [] as number[],
})

const form = ref(defaultForm())

const rules = {
  title: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
}

function flattenTree(nodes: CategoryOut[], depth = 0): { value: number; label: string }[] {
  const result: { value: number; label: string }[] = []
  for (const n of nodes) {
    result.push({ value: n.id, label: '　'.repeat(depth) + n.name })
    if (n.children?.length) result.push(...flattenTree(n.children, depth + 1))
  }
  return result
}

const flatCategories = computed(() => flattenTree(categories.value))

async function loadCategories() {
  try {
    categories.value = (await categoriesApi.list()).data.items
  } catch {}
}

async function loadMembers() {
  membersLoading.value = true
  try {
    const resp = await membersApi.list({ page_size: 500 })
    members.value = resp.data.items.filter(m => m.status === 'active')
  } catch {}
  finally { membersLoading.value = false }
}

async function submit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const payload = {
      ...form.value,
      category_id: form.value.category_id || null,
      started_at: form.value.started_at || null,
      ended_at: form.value.ended_at || null,
    }
    if (isEdit.value) {
      await projectsApi.update(props.project!.id, payload)
      ElMessage.success('项目已更新')
    } else {
      await projectsApi.create(payload)
      ElMessage.success('项目已创建')
    }
    emit('saved')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadCategories()
  loadMembers()
})
</script>

<template>
  <el-form
    ref="formRef"
    :model="form"
    :rules="rules"
    label-width="90px"
    class="project-form"
  >
    <el-form-item label="项目名称" prop="title">
      <el-input v-model="form.title" placeholder="例如：智能问答系统" maxlength="128" show-word-limit />
    </el-form-item>

    <el-form-item label="所属分类">
      <el-select v-model="form.category_id" style="width: 100%" clearable placeholder="选择研究方向（可选）">
        <el-option v-for="c in flatCategories" :key="c.value" :label="c.label" :value="c.value" />
      </el-select>
    </el-form-item>

    <el-form-item label="项目描述" prop="description">
      <el-input
        v-model="form.description"
        type="textarea"
        :rows="3"
        placeholder="简要描述项目目标与背景"
      />
    </el-form-item>

    <el-row :gutter="16">
      <el-col :span="12">
        <el-form-item label="项目状态" prop="status">
          <el-select v-model="form.status" style="width: 100%">
            <el-option label="规划中" value="planning" />
            <el-option label="进行中" value="active" />
            <el-option label="已暂停" value="paused" />
            <el-option label="已完成" value="completed" />
            <el-option label="已废弃" value="abandoned" />
          </el-select>
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="优先级" prop="priority">
          <el-select v-model="form.priority" style="width: 100%">
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>
      </el-col>
    </el-row>

    <el-form-item label="技术栈" prop="tech_stack">
      <el-input v-model="form.tech_stack" placeholder="例如：Vue3 + FastAPI + PostgreSQL" maxlength="512" />
    </el-form-item>

    <el-row :gutter="16">
      <el-col :span="12">
        <el-form-item label="仓库地址" prop="repo_url">
          <el-input v-model="form.repo_url" placeholder="https://github.com/..." maxlength="512" />
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="演示地址" prop="demo_url">
          <el-input v-model="form.demo_url" placeholder="https://..." maxlength="512" />
        </el-form-item>
      </el-col>
    </el-row>

    <el-form-item label="源码压缩包">
      <el-input v-model="form.zip_url" placeholder="上传路径或外链 URL（可选）" maxlength="512" />
    </el-form-item>

    <el-row :gutter="16">
      <el-col :span="12">
        <el-form-item label="开始时间" prop="started_at">
          <el-date-picker
            v-model="form.started_at"
            type="datetime"
            style="width: 100%"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DDTHH:mm:ss"
            placeholder="选择开始时间"
          />
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="结束时间" prop="ended_at">
          <el-date-picker
            v-model="form.ended_at"
            type="datetime"
            style="width: 100%"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DDTHH:mm:ss"
            placeholder="选择结束时间"
          />
        </el-form-item>
      </el-col>
    </el-row>

    <el-form-item label="可见性">
      <div class="visibility-section">
        <el-radio-group v-model="form.is_public">
          <el-radio :value="true">公开</el-radio>
          <el-radio :value="false">私有</el-radio>
        </el-radio-group>
        <p class="visibility-hint">
          公开：所有成员可见<br>
          私有：仅创建人和指定成员可见
        </p>
        <div v-if="!form.is_public" class="viewer-select">
          <el-form-item label="指定可见成员" label-width="100px" style="margin-bottom:0">
            <el-select
              v-model="form.allowed_viewer_ids"
              multiple
              filterable
              placeholder="选择可见成员"
              style="width: 100%"
              :loading="membersLoading"
              collapse-tags
              collapse-tags-tooltip
            >
              <el-option
                v-for="m in members"
                :key="m.id"
                :label="m.display_name"
                :value="m.id"
              />
            </el-select>
          </el-form-item>
        </div>
      </div>
    </el-form-item>

    <el-form-item class="form-actions">
      <el-button @click="emit('cancel')">取消</el-button>
      <el-button type="primary" :loading="loading" @click="submit">
        {{ isEdit ? '保存修改' : '创建项目' }}
      </el-button>
    </el-form-item>
  </el-form>
</template>

<style scoped>
.project-form { padding: 0.5rem 0.5rem 0; }
.form-actions { margin-bottom: 0; display: flex; justify-content: flex-end; gap: 0.75rem; }
.visibility-section {
  background: var(--el-fill-color-light);
  border-radius: 6px;
  padding: 0.75rem 1rem;
  width: 100%;
}
.visibility-hint {
  font-size: 0.75rem;
  color: var(--lab-muted);
  margin: 0.4rem 0 0;
  line-height: 1.5;
}
.viewer-select {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--el-border-color-lighter);
}
</style>
