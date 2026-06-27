<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { alumniPostsApi, type AlumniPostOut } from '@/api/alumniPosts'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const auth = useAuthStore()
const posts = ref<AlumniPostOut[]>([])
const total = ref(0)
const loading = ref(false)
const filterType = ref<string>('')
const showForm = ref(false)
const editingPost = ref<AlumniPostOut | null>(null)
const showDetail = ref(false)
const currentPost = ref<AlumniPostOut | null>(null)

const canPost = computed(() =>
  auth.user?.status === 'graduated' || auth.user?.status === 'archived'
)

const typeMap: Record<string, { label: string; type: string }> = {
  referral: { label: '内推', type: 'success' },
  tech: { label: '技术分享', type: 'primary' },
  resource: { label: '资源分享', type: 'warning' },
}

const typeOptions = [
  { value: '', label: '全部' },
  { value: 'referral', label: '内推' },
  { value: 'tech', label: '技术分享' },
  { value: 'resource', label: '资源分享' },
]

async function load() {
  loading.value = true
  try {
    const resp = await alumniPostsApi.list({
      type: filterType.value || undefined,
      page: 1,
      page_size: 100,
    })
    posts.value = resp.data.items
    total.value = resp.data.total
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingPost.value = null
  showForm.value = true
}

function openEdit(post: AlumniPostOut) {
  editingPost.value = post
  showForm.value = true
}

function openPostDetail(post: AlumniPostOut) {
  currentPost.value = post
  showDetail.value = true
}

async function handleSaved() {
  showForm.value = false
  editingPost.value = null
  await load()
}

async function handleDelete(post: AlumniPostOut) {
  try {
    await alumniPostsApi.remove(post.id)
    ElMessage.success('帖子已删除')
    await load()
  } catch {
    // handled by interceptor
  }
}

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
  })
}

onMounted(load)
</script>

<template>
  <div class="alumni-page">
    <div class="page-header">
      <h2>毕业人员专区</h2>
      <div class="header-actions">
        <el-select v-model="filterType" @change="load" clearable style="width:140px">
          <el-option v-for="opt in typeOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
        </el-select>
        <el-button v-if="canPost" type="primary" @click="openCreate">+ 发布帖子</el-button>
      </div>
    </div>

    <p class="page-desc" v-if="!canPost">
      欢迎浏览毕业人员的分享。在读成员如需发布内容，请联系管理员调整身份。
    </p>

    <el-empty v-if="!loading && posts.length === 0" description="暂无帖子" style="margin-top:4rem" />

    <div v-else class="posts-grid">
      <div
        v-for="post in posts"
        :key="post.id"
        class="post-card"
        @click="openPostDetail(post)"
      >
        <div class="post-header">
          <el-tag size="small" :type="typeMap[post.type]?.type as any" effect="plain">
            {{ typeMap[post.type]?.label }}
          </el-tag>
          <span class="post-date">{{ formatDate(post.created_at) }}</span>
        </div>
        <h3 class="post-title">{{ post.title }}</h3>
        <p class="post-content">{{ post.content || '暂无内容' }}</p>
        <div v-if="post.type === 'referral'" class="post-referral-info">
          <span v-if="post.company">{{ post.company }}</span>
          <span v-if="post.position"> · {{ post.position }}</span>
        </div>
        <div class="post-tags" v-if="post.tags">
          <el-tag size="small" effect="plain" v-for="tag in post.tags.split(',')" :key="tag" style="margin-right:4px">
            {{ tag.trim() }}
          </el-tag>
        </div>
        <div class="post-footer">
          <span class="post-author">{{ post.author_display_name }}</span>
          <div class="post-actions" @click.stop>
            <template v-if="auth.user?.id === post.author_id || auth.isAdmin">
              <el-button size="small" @click="openEdit(post)">编辑</el-button>
              <el-button size="small" type="danger" plain @click="handleDelete(post)">删除</el-button>
            </template>
          </div>
        </div>
      </div>
    </div>

    <div class="summary">共 {{ total }} 条帖子</div>

    <!-- Create/Edit Form Dialog -->
    <el-dialog v-model="showForm" :title="editingPost ? '编辑帖子' : '发布帖子'" width="560px">
      <AlumniPostForm :post="editingPost" @saved="handleSaved" @cancel="showForm = false" />
    </el-dialog>

    <!-- Detail Dialog -->
    <el-dialog v-model="showDetail" :title="currentPost?.title" width="600px">
      <div v-if="currentPost" class="post-detail">
        <div class="detail-meta">
          <el-tag :type="typeMap[currentPost.type]?.type as any">{{ typeMap[currentPost.type]?.label }}</el-tag>
          <span>{{ currentPost.author_display_name }}</span>
          <span>{{ formatDate(currentPost.created_at) }}</span>
        </div>
        <div v-if="currentPost.type === 'referral'" class="detail-referral">
          <div v-if="currentPost.company"><strong>公司：</strong>{{ currentPost.company }}</div>
          <div v-if="currentPost.position"><strong>职位：</strong>{{ currentPost.position }}</div>
          <div v-if="currentPost.contact_info"><strong>联系方式：</strong>{{ currentPost.contact_info }}</div>
        </div>
        <div class="detail-content">{{ currentPost.content }}</div>
        <div v-if="currentPost.tags" class="detail-tags">
          <el-tag v-for="tag in currentPost.tags.split(',')" :key="tag" size="small" style="margin-right:4px">
            {{ tag.trim() }}
          </el-tag>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script lang="ts">
import AlumniPostForm from '@/components/alumni/AlumniPostForm.vue'
export default { components: { AlumniPostForm } }
</script>

<style scoped>
.alumni-page {
  max-width: 1200px;
  margin: 0 auto;
}
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}
.page-header h2 { margin: 0; }
.header-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}
.page-desc {
  color: var(--lab-muted);
  font-size: 0.85rem;
  margin-bottom: 1rem;
}
.posts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 1rem;
}
.post-card {
  background: #fff;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  padding: 1rem;
  cursor: pointer;
  transition: box-shadow 0.15s, transform 0.15s;
}
.post-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
  transform: translateY(-2px);
}
.post-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}
.post-date {
  font-size: 0.75rem;
  color: var(--lab-muted);
}
.post-title {
  margin: 0 0 0.5rem;
  font-size: 1rem;
  font-weight: 600;
  color: var(--el-text-color-primary);
}
.post-content {
  font-size: 0.85rem;
  color: var(--lab-muted);
  margin: 0 0 0.5rem;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.post-referral-info {
  font-size: 0.8rem;
  color: var(--el-color-success);
  margin-bottom: 0.5rem;
}
.post-tags {
  margin-bottom: 0.5rem;
}
.post-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 0.5rem;
  border-top: 1px solid var(--el-border-color-lighter);
}
.post-author {
  font-size: 0.8rem;
  color: var(--lab-muted);
}
.post-actions {
  display: flex;
  gap: 0.25rem;
}
.summary {
  margin-top: 1rem;
  color: var(--lab-muted);
  font-size: 0.85rem;
}
.post-detail {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.detail-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.85rem;
  color: var(--lab-muted);
}
.detail-referral {
  background: var(--el-fill-color-light);
  padding: 0.75rem 1rem;
  border-radius: 6px;
  font-size: 0.9rem;
}
.detail-content {
  font-size: 0.95rem;
  line-height: 1.7;
  white-space: pre-wrap;
}
.detail-tags { display: flex; flex-wrap: wrap; gap: 0.25rem; }
</style>
