<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { showcaseApi, type ShowcaseOut, type ShowcaseCreate } from '@/api/showcase'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Download, Edit } from '@element-plus/icons-vue'

const auth = useAuthStore()
const items = ref<ShowcaseOut[]>([])
const loading = ref(false)
const activeTab = ref<'achievement' | 'blessing'>('achievement')
const showDialog = ref(false)
const isEditing = ref(false)
const editingId = ref<number | null>(null)
const showBlessingHint = ref(false)
const fileUploading = ref(false)
const pdfUploading = ref(false)
const detailItem = ref<ShowcaseOut | null>(null)
const showDetail = ref(false)
const imgInput = ref<HTMLInputElement | null>(null)
const pdfInput = ref<HTMLInputElement | null>(null)

const stickyColors = ['#fff9e6','#fef5e7','#fdebd0','#fef9f0','#fdf2e9','#fdece0','#fef8dd','#fcf3d9']

function stickyBg(index: number) {
  return stickyColors[index % stickyColors.length]
}

const defaultForm = (): ShowcaseCreate => ({
  type: activeTab.value,
  title: '',
  description: '',
  image_url: null,
  pdf_url: null,
  contact_info: null,
  experience: null,
})
const form = ref<ShowcaseCreate>(defaultForm())

const filteredItems = computed(() => items.value.filter(i => i.type === activeTab.value))

function canAddBlessing() {
  const u = auth.user
  if (!u) return false
  if (u.role === 'owner') return true
  if (u.status === 'graduated') return true
  const ey = u.profile?.enrollment_year
  if (ey && new Date().getFullYear() - ey >= 2) return true
  return false
}

const page = ref(1)
const pageSize = ref(12)
const total = ref(0)

async function load() {
  loading.value = true
  try {
    const resp = await showcaseApi.list({ page: page.value, page_size: pageSize.value })
    items.value = resp.data.items
    total.value = resp.data.total
  } finally {
    loading.value = false
  }
}

function handleTabChange(tab: string) {
  activeTab.value = tab as 'achievement' | 'blessing'
  page.value = 1
  load()
}

function openAdd() {
  if (activeTab.value === 'blessing' && !canAddBlessing()) {
    showBlessingHint.value = true
    return
  }
  isEditing.value = false
  editingId.value = null
  form.value = defaultForm()
  showDialog.value = true
}

function openEdit(item: ShowcaseOut) {
  isEditing.value = true
  editingId.value = item.id
  form.value = {
    type: item.type,
    title: item.title,
    description: item.description,
    image_url: item.image_url,
    pdf_url: item.pdf_url,
    contact_info: item.contact_info,
    experience: item.experience,
  }
  showDialog.value = true
  showDetail.value = false
}

function openDetail(item: ShowcaseOut) {
  detailItem.value = item
  showDetail.value = true
}

function getImageUrl(url: string | null) {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return `${import.meta.env.VITE_BACKEND_URL ?? ''}${url}`
}

function getDownloadUrl(url: string | null) {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return `${import.meta.env.VITE_BACKEND_URL ?? ''}${url}`
}

const apiBase = import.meta.env.VITE_API_BASE ?? '/api/v1'

function triggerImage() { imgInput.value?.click() }
function triggerPdf() { pdfInput.value?.click() }

async function handleImageUpload(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  if (!file.type.startsWith('image/')) { ElMessage.error('仅支持图片文件'); return }
  fileUploading.value = true
  try {
    const fd = new FormData(); fd.append('file', file)
    const resp = await fetch(`${apiBase}/upload`, {
      method: 'POST', headers: { Authorization: `Bearer ${auth.token}` }, body: fd,
    })
    if (!resp.ok) throw new Error('upload failed')
    const data = await resp.json()
    form.value.image_url = data.url
    ElMessage.success('图片上传成功')
  } catch { ElMessage.error('上传失败') }
  finally { fileUploading.value = false }
}

async function handlePdfUpload(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  if (file.type !== 'application/pdf') { ElMessage.error('仅支持 PDF 文件'); return }
  pdfUploading.value = true
  try {
    const fd = new FormData(); fd.append('file', file)
    const resp = await fetch(`${apiBase}/upload`, {
      method: 'POST', headers: { Authorization: `Bearer ${auth.token}` }, body: fd,
    })
    if (!resp.ok) throw new Error('upload failed')
    const data = await resp.json()
    form.value.pdf_url = data.url
    ElMessage.success('PDF 上传成功')
  } catch { ElMessage.error('上传失败') }
  finally { pdfUploading.value = false }
}

async function handleSubmit() {
  if (activeTab.value === 'achievement' && !form.value.title.trim()) return
  try {
    if (isEditing.value && editingId.value !== null) {
      await showcaseApi.update(editingId.value, {
        title: form.value.title,
        description: form.value.description,
        image_url: form.value.image_url,
        pdf_url: form.value.pdf_url,
        contact_info: form.value.contact_info,
        experience: form.value.experience,
      })
      ElMessage.success('已更新')
    } else {
      form.value.type = activeTab.value
      await showcaseApi.create(form.value)
      ElMessage.success(activeTab.value === 'achievement' ? '成果已发布' : '寄语已发布')
    }
    showDialog.value = false
    await load()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.error?.message || '发布失败')
  }
}

async function handleDelete(item: ShowcaseOut) {
  try {
    await ElMessageBox.confirm('确定删除这条记录吗？', '确认删除', { confirmButtonText: '删除', type: 'warning' })
  } catch { return }
  await showcaseApi.remove(item.id)
  ElMessage.success('已删除')
  showDetail.value = false
  await load()
}

onMounted(load)
</script>

<template>
  <div class="showcase-page">
    <div class="page-header">
      <div class="header-tabs">
        <el-radio-group v-model="activeTab" size="default" @change="handleTabChange">
          <el-radio-button value="achievement">🏆 成果展示</el-radio-button>
          <el-radio-button value="blessing">💌 寄语墙</el-radio-button>
        </el-radio-group>
      </div>
      <el-button type="primary" :icon="Plus" @click="openAdd" v-if="auth.isLoggedIn">
        {{ activeTab === 'achievement' ? '添加成果' : '留下寄语' }}
      </el-button>
    </div>

    <el-alert
      v-if="showBlessingHint"
      title="只有导师、入学2年以上的师兄或已毕业成员可以留下寄语"
      type="info" :closable="true" show-icon
      @close="showBlessingHint = false"
      style="margin-bottom:1rem"
    />

    <!-- Achievement Grid -->
    <div v-if="activeTab === 'achievement'" class="wall-grid" v-loading="loading">
      <div v-if="filteredItems.length === 0" class="wall-empty">还没有人分享成果，快来发第一篇吧</div>
      <div v-for="item in filteredItems" :key="item.id" class="achieve-card" @click="openDetail(item)">
        <div class="achieve-image" v-if="item.image_url">
          <img :src="getImageUrl(item.image_url)" :alt="item.title" loading="lazy" />
        </div>
        <div class="achieve-placeholder" v-else>📄</div>
        <div class="achieve-body">
          <h4 class="achieve-title">{{ item.title }}</h4>
          <p class="achieve-desc" v-if="item.description">{{ item.description.slice(0, 80) }}{{ item.description.length > 80 ? '...' : '' }}</p>
          <a v-if="item.pdf_url" :href="getDownloadUrl(item.pdf_url)" target="_blank" class="achieve-download" @click.stop>
            <el-icon><Download /></el-icon> PDF
          </a>
        </div>
        <div class="achieve-footer">
          <span class="af-author">{{ item.author_name }}</span>
          <el-button v-if="item.author_id === auth.user?.id || auth.isOwner" text size="small" type="danger" @click.stop="handleDelete(item)">删除</el-button>
        </div>
      </div>
    </div>

    <!-- Blessing Sticky Notes -->
    <div v-if="activeTab === 'blessing'" class="sticky-wall" v-loading="loading">
      <div v-if="filteredItems.length === 0" class="wall-empty">还没有人留下寄语</div>
      <div
        v-for="(item, idx) in filteredItems"
        :key="item.id"
        class="sticky-note"
        :style="{ background: stickyBg(idx), transform: `rotate(${(idx % 3) - 1}deg)` }"
        @click="openDetail(item)"
      >
        <h4 class="sticky-title">{{ item.title }}</h4>
        <p class="sticky-body">{{ (item.description || '').slice(0, 80) }}{{ (item.description || '').length > 80 ? '...' : '' }}</p>
        <div class="sticky-footer">
          <span>{{ item.author_name }}</span>
          <span v-if="item.author_graduation_year" class="sticky-year">{{ item.author_graduation_year }}届</span>
        </div>
      </div>
    </div>

    <!-- Detail Dialog -->
    <el-dialog v-model="showDetail" :title="detailItem?.type === 'blessing' ? '寄语详情' : '成果详情'" width="620px" destroy-on-close>
      <template v-if="detailItem">
        <div class="detail-image" v-if="detailItem.image_url">
          <img :src="getImageUrl(detailItem.image_url)" :alt="detailItem.title" style="max-width:100%; border-radius:8px" />
        </div>
        <h3 style="margin:0.75rem 0 0.5rem">{{ detailItem.title }}</h3>
        <div class="detail-meta">
          <span>{{ detailItem.author_name }}</span>
          <span v-if="detailItem.author_enrollment_year">{{ detailItem.author_enrollment_year }}级</span>
          <span v-if="detailItem.author_graduation_year">{{ detailItem.author_graduation_year }}年毕业</span>
        </div>
        <p class="detail-desc" v-if="detailItem.description">{{ detailItem.description }}</p>

        <!-- Achievement extras -->
        <div class="detail-experience" v-if="detailItem.type === 'achievement' && detailItem.experience">
          <h4>💡 经验分享</h4>
          <p>{{ detailItem.experience }}</p>
        </div>

        <div class="detail-actions" v-if="detailItem.type === 'achievement' && detailItem.pdf_url">
          <el-button type="primary" @click="() => { const u = getDownloadUrl(detailItem!.pdf_url); window.open(u, '_blank') }">
            <el-icon><Download /></el-icon> 下载PDF
          </el-button>
        </div>
        <div class="detail-contact" v-if="detailItem.type === 'blessing' && detailItem.contact_info">
          <span>📬 联系方式：{{ detailItem.contact_info }}</span>
        </div>
        <div class="detail-action-bar" v-if="detailItem.author_id === auth.user?.id || auth.isOwner">
          <el-button type="primary" plain size="small" :icon="Edit" @click="openEdit(detailItem)">编辑</el-button>
          <el-button type="danger" plain size="small" @click="handleDelete(detailItem)">删除</el-button>
        </div>
      </template>
    </el-dialog>

    <div class="summary" v-if="total > 0">
      共 {{ total }} 条
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

    <!-- Add Dialog -->
    <el-dialog
      v-model="showDialog"
      :title="isEditing ? '编辑' : (activeTab === 'achievement' ? '添加成果' : '留下寄语')"
      width="550px" destroy-on-close
    >
      <el-form label-position="top">
        <el-form-item label="标题" required v-if="activeTab === 'achievement' || isEditing">
          <el-input v-model="form.title" maxlength="200" placeholder="论文/专利/软著名称" />
        </el-form-item>
        <el-form-item label="小标题（可选）" v-if="activeTab === 'blessing' && !isEditing">
          <el-input v-model="form.title" maxlength="200" placeholder="如：给师弟师妹的话" />
        </el-form-item>
        <el-form-item :label="activeTab === 'achievement' ? '描述' : '寄语'" required>
          <el-input
            v-model="form.description" type="textarea"
            :rows="activeTab === 'achievement' ? 3 : 5"
            :placeholder="activeTab === 'achievement' ? '简要描述这个成果...' : '想对师弟师妹说的话...'"
          />
        </el-form-item>
        <el-form-item label="封面图片">
          <div class="upload-row">
            <el-button :loading="fileUploading" @click="triggerImage">选择图片</el-button>
            <span v-if="form.image_url" class="upload-ok">✓ 已上传</span>
            <input ref="imgInput" type="file" accept="image/*" style="display:none" @change="handleImageUpload" />
          </div>
        </el-form-item>
        <el-form-item label="PDF 附件" v-if="activeTab === 'achievement' || isEditing">
          <div class="upload-row">
            <el-button :loading="pdfUploading" @click="triggerPdf">选择PDF</el-button>
            <span v-if="form.pdf_url" class="upload-ok">✓ 已上传</span>
            <input ref="pdfInput" type="file" accept=".pdf" style="display:none" @change="handlePdfUpload" />
          </div>
        </el-form-item>
        <el-form-item label="经验分享" v-if="activeTab === 'achievement' || isEditing">
          <el-input
            v-model="form.experience" type="textarea" :rows="3"
            placeholder="分享你做这个成果过程中的经验、踩过的坑、给后来人的建议..."
          />
        </el-form-item>
        <el-form-item label="联系方式" v-if="activeTab === 'blessing' || isEditing">
          <el-input v-model="form.contact_info" maxlength="256" placeholder="微信 / 邮箱 / 手机，方便师弟师妹联系你" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">{{ isEditing ? '保存' : '发布' }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.showcase-page { max-width: 1300px; margin: 0 auto; }

.page-header {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;
}
.header-tabs :deep(.el-radio-button__inner) {
  font-weight: 500;
}

/* ── Achievement cards ──────────────────── */
.wall-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.25rem; min-height: 200px;
}
.wall-empty {
  grid-column: 1 / -1;
  text-align: center; padding: 3rem 0; color: var(--lab-muted); font-size: 0.95rem;
}

.achieve-card {
  background: var(--el-bg-color);
  border-radius: 10px; overflow: hidden;
  border: 1px solid var(--el-border-color-lighter);
  cursor: pointer; transition: box-shadow 0.2s;
}
.achieve-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.1); }
.achieve-image { height: 160px; overflow: hidden; background: #f5f5f5; }
.achieve-image img { width: 100%; height: 100%; object-fit: cover; }
.achieve-placeholder {
  height: 100px; display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #f0f4ff 0%, #e8f0fe 100%);
  font-size: 2.2rem;
}
.achieve-body { padding: 0.75rem 1rem; }
.achieve-title { margin: 0 0 0.25rem; font-size: 0.95rem; line-height: 1.4; }
.achieve-desc { font-size: 0.8rem; color: var(--lab-muted); line-height: 1.5; margin: 0; }
.achieve-download {
  display: inline-flex; align-items: center; gap: 0.2rem;
  margin-top: 0.4rem; font-size: 0.8rem; color: var(--el-color-primary); text-decoration: none;
}
.achieve-footer {
  display: flex; justify-content: space-between; align-items: center;
  padding: 0.5rem 1rem; border-top: 1px solid var(--el-border-color-lighter);
  font-size: 0.78rem;
}
.af-author { font-weight: 600; }

/* ── Sticky notes wall ──────────────────── */
.sticky-wall {
  display: flex; flex-wrap: wrap; gap: 1rem; justify-content: center;
  min-height: 200px; padding: 0.5rem;
}
.sticky-note {
  width: 180px; min-height: 160px; padding: 1rem 1rem 0.75rem;
  border-radius: 2px 12px 12px 12px;
  box-shadow: 2px 3px 8px rgba(0,0,0,0.08);
  cursor: pointer; transition: transform 0.25s, box-shadow 0.25s;
  display: flex; flex-direction: column;
}
.sticky-note:hover {
  transform: scale(1.06) !important;
  box-shadow: 4px 6px 16px rgba(0,0,0,0.14);
  z-index: 2;
}
.sticky-title {
  margin: 0 0 0.4rem; font-size: 0.9rem; font-weight: 700;
  color: #5d4037; line-height: 1.3;
}
.sticky-body {
  flex: 1; font-size: 0.8rem; line-height: 1.5; color: #5d4037; margin: 0;
  overflow: hidden; font-style: italic;
}
.sticky-footer {
  margin-top: 0.5rem; font-size: 0.72rem; color: #8d6e63;
  display: flex; justify-content: space-between;
  border-top: 1px dashed rgba(0,0,0,0.08); padding-top: 0.35rem;
}
.sticky-year { font-weight: 600; }

/* ── Detail dialog ──────────────────────── */
.detail-image { margin-bottom: 0.5rem; }
.detail-meta {
  display: flex; gap: 0.75rem; font-size: 0.8rem; color: var(--lab-muted); margin-bottom: 0.75rem;
}
.detail-desc {
  font-size: 0.92rem; line-height: 1.7; white-space: pre-wrap; color: var(--el-text-color-primary);
}
.detail-experience {
  margin-top: 1rem; padding: 1rem; background: #fef8e7; border-radius: 8px;
  border-left: 3px solid var(--el-color-warning);
}
.detail-experience h4 { margin: 0 0 0.4rem; font-size: 0.9rem; }
.detail-experience p { margin: 0; font-size: 0.88rem; line-height: 1.6; white-space: pre-wrap; }
.detail-contact {
  margin-top: 1rem; padding: 0.75rem; background: #f5f5f5; border-radius: 8px;
  font-size: 0.85rem;
}
.detail-actions { margin-top: 1rem; }
.detail-action-bar { margin-top: 1rem; text-align: right; }

/* ── Summary ─────────────────────────── */
.summary { margin-top: 1rem; color: var(--lab-muted); font-size: 0.85rem; text-align: center; }

/* ── Form ──────────────────────────────── */
.upload-row { display: flex; align-items: center; gap: 0.75rem; }
.upload-ok { color: var(--el-color-success); font-size: 0.85rem; }
</style>
