<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { alumniPostsApi, type AlumniPostOut } from '@/api/alumniPosts'
import { ElMessage } from 'element-plus'

const props = defineProps<{
  post?: AlumniPostOut | null
}>()

const emit = defineEmits<{
  saved: []
  cancel: []
}>()

const loading = ref(false)
const formRef = ref()

const isEdit = computed(() => !!props.post)

const defaultForm = () => ({
  type: props.post?.type ?? 'referral',
  title: props.post?.title ?? '',
  content: props.post?.content ?? '',
  company: props.post?.company ?? '',
  position: props.post?.position ?? '',
  contact_info: props.post?.contact_info ?? '',
  tags: props.post?.tags ?? '',
})

const form = ref(defaultForm())

const rules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  type: [{ required: true, message: '请选择类型', trigger: 'change' }],
}

const typeOptions = [
  { value: 'referral', label: '内推' },
  { value: 'tech', label: '技术分享' },
  { value: 'resource', label: '资源分享' },
]

const showReferralFields = computed(() => form.value.type === 'referral')

async function submit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const payload = {
      ...form.value,
      content: form.value.content || null,
      company: form.value.company || null,
      position: form.value.position || null,
      contact_info: form.value.contact_info || null,
      tags: form.value.tags || null,
    }
    if (isEdit.value) {
      await alumniPostsApi.update(props.post!.id, payload)
      ElMessage.success('帖子已更新')
    } else {
      await alumniPostsApi.create(payload)
      ElMessage.success('帖子已发布')
    }
    emit('saved')
  } finally {
    loading.value = false
  }
}

onMounted(() => {})
</script>

<template>
  <el-form
    ref="formRef"
    :model="form"
    :rules="rules"
    label-width="90px"
    class="alumni-form"
  >
    <el-form-item label="帖子类型" prop="type">
      <el-radio-group v-model="form.type">
        <el-radio-button v-for="opt in typeOptions" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </el-radio-button>
      </el-radio-group>
    </el-form-item>

    <el-form-item label="标题" prop="title">
      <el-input v-model="form.title" placeholder="请输入标题" maxlength="200" show-word-limit />
    </el-form-item>

    <template v-if="showReferralFields">
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="公司">
            <el-input v-model="form.company" placeholder="公司名称" maxlength="128" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="职位">
            <el-input v-model="form.position" placeholder="岗位名称" maxlength="128" />
          </el-form-item>
        </el-col>
      </el-row>
      <el-form-item label="联系方式">
        <el-input
          v-model="form.contact_info"
          placeholder="微信/邮箱/简历链接等"
          maxlength="256"
        />
      </el-form-item>
    </template>

    <el-form-item label="内容">
      <el-input
        v-model="form.content"
        type="textarea"
        :rows="5"
        placeholder="分享您的经验、资源或内推信息..."
      />
    </el-form-item>

    <el-form-item label="标签">
      <el-input v-model="form.tags" placeholder="用逗号分隔，如：Python,后端,实习" maxlength="256" />
      <div class="form-tip">多个标签用逗号分隔</div>
    </el-form-item>

    <el-form-item class="form-actions">
      <el-button @click="emit('cancel')">取消</el-button>
      <el-button type="primary" :loading="loading" @click="submit">
        {{ isEdit ? '保存修改' : '发布帖子' }}
      </el-button>
    </el-form-item>
  </el-form>
</template>

<style scoped>
.alumni-form { padding: 0.5rem 0.5rem 0; }
.form-actions { margin-bottom: 0; display: flex; justify-content: flex-end; gap: 0.75rem; }
.form-tip {
  font-size: 0.75rem;
  color: var(--lab-muted);
  margin-top: 4px;
}
</style>
