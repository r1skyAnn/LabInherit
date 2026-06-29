<script setup lang="ts">
import { ref, onMounted, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { notesApi, type NoteOut } from '@/api/notes'
import { commentsApi, type CommentOut } from '@/api/comments'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import MarkdownRenderer from '@/components/notes/MarkdownRenderer.vue'
import NoteForm from '@/components/notes/NoteForm.vue'
import AttachmentList from '@/components/notes/AttachmentList.vue'
import { exportMarkdown, exportHTML, exportDocx, exportPDF, exportMindmapSVG } from '@/utils/exportNote'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const noteId = Number(route.params.noteId)
const projectId = Number(route.params.projectId)

const note = ref<NoteOut | null>(null)
const loading = ref(true)
const showEdit = ref(false)
const exporting = ref(false)
const showMindmap = ref(false)
const mindmapContainer = ref<HTMLElement | null>(null)

// ── Export handlers ──────────────────────────────
async function doExport(kind: 'md' | 'html' | 'docx' | 'pdf' | 'svg') {
  if (!note.value) return
  const { title, content } = note.value
  exporting.value = true
  try {
    if (kind === 'md') {
      exportMarkdown(title, content)
    } else if (kind === 'html') {
      exportHTML(title, content)
    } else if (kind === 'docx') {
      await exportDocx(title, content)
    } else if (kind === 'pdf') {
      await exportPDF(title, content)
    } else if (kind === 'svg') {
      await exportMindmapSVG(content, title)
    }
    ElMessage.success('已开始下载')
  } catch (err: any) {
    console.error(err)
    ElMessage.error(`导出失败: ${err?.message || '未知错误'}`)
  } finally {
    exporting.value = false
  }
}

async function openMindmap() {
  if (!note.value) return
  showMindmap.value = true
  await nextTick()
  if (mindmapContainer.value) {
    const { renderMindmap } = await import('@/utils/exportNote')
    await renderMindmap(note.value.content, mindmapContainer.value)
  }
}

// Comments
const comments = ref<CommentOut[]>([])
const commentsLoading = ref(false)
const newComment = ref('')
const submitting = ref(false)
const editingCommentId = ref<number | null>(null)
const editContent = ref('')
const replyTo = ref<CommentOut | null>(null)
const commentFilter = ref<'all' | 'asks' | 'mine'>('all')

const filteredComments = computed(() => {
  // Only show top-level comments in main list; replies render nested
  const top = comments.value.filter(c => c.parent_id === null)
  switch (commentFilter.value) {
    case 'asks':
      return top.filter(c => c.is_ask)
    case 'mine':
      return top.filter(c => c.author_id === auth.user?.id)
    default:
      return top
  }
})

function repliesOf(parentId: number) {
  return comments.value.filter(r => r.parent_id === parentId)
}

const replyLabel = computed(() => {
  return replyTo.value
    ? `回复 @${replyTo.value.author_name}...`
    : '写下你的评论或建议...'
})

function isAuthor() {
  return note.value?.author_id === auth.user?.id
}

function isCommentAuthor(c: CommentOut) {
  return c.author_id === auth.user?.id
}

function canModifyStatus() {
  return isAuthor() || auth.isOwner
}

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

function statusTag(status: string) {
  switch (status) {
    case 'open': return { type: 'warning', text: '待回复' }
    case 'answered': return { type: 'success', text: '已回复' }
    case 'closed': return { type: 'info', text: '已关闭' }
    default: return { type: '', text: status }
  }
}

async function load() {
  loading.value = true
  try {
    note.value = (await notesApi.get(noteId)).data
  } finally {
    loading.value = false
  }
}

async function loadComments() {
  commentsLoading.value = true
  try {
    comments.value = (await commentsApi.list(noteId)).data.items
  } finally {
    commentsLoading.value = false
  }
}

async function handleLike() {
  if (!note.value) return
  if (note.value.liked) {
    await notesApi.unlike(noteId)
  } else {
    await notesApi.like(noteId)
  }
  await load()
}

function handleSaved() {
  showEdit.value = false
  load()
}

async function handleDelete() {
  try {
    await ElMessageBox.confirm('确定删除这条笔记吗？', '确认删除', {
      confirmButtonText: '删除',
      type: 'warning',
    })
  } catch {
    return
  }
  await notesApi.remove(noteId)
  ElMessage.success('已删除')
  router.push(`/projects/${projectId}/notes`)
}

async function handleTogglePin() {
  if (!note.value) return
  await notesApi.update(noteId, { is_pinned: !note.value.is_pinned })
  ElMessage.success(note.value.is_pinned ? '已取消置顶' : '已置顶')
  await load()
}

// (nextTick already imported above)

// ── Comment actions ──────────────────────────────

async function handleAddComment() {
  if (!newComment.value.trim()) return
  submitting.value = true
  try {
    const payload: any = { content: newComment.value }
    if (replyTo.value) {
      payload.parent_id = replyTo.value.id
    }
    await commentsApi.create(noteId, payload)
    newComment.value = ''
    replyTo.value = null
    ElMessage.success(replyTo.value ? '回复已发布' : '评论已发布')
    await loadComments()
    await load()
  } finally {
    submitting.value = false
  }
}

async function handleAskFollowUp() {
  if (!newComment.value.trim()) return
  submitting.value = true
  try {
    await commentsApi.create(noteId, {
      content: newComment.value,
      is_ask: true,
      parent_id: replyTo.value?.id ?? undefined,
    })
    newComment.value = ''
    replyTo.value = null
    ElMessage.success('追问已提交，作者将收到邮件通知')
    await loadComments()
    await load()
  } finally {
    submitting.value = false
  }
}

function handleReply(c: CommentOut) {
  replyTo.value = c
  // Focus works after next tick when placeholder changes
}

function cancelReply() {
  replyTo.value = null
}

function startEditComment(c: CommentOut) {
  editingCommentId.value = c.id
  editContent.value = c.content
}

function cancelEditComment() {
  editingCommentId.value = null
  editContent.value = ''
}

async function handleUpdateComment(c: CommentOut) {
  if (!editContent.value.trim()) return
  await commentsApi.update(c.id, { content: editContent.value })
  editingCommentId.value = null
  editContent.value = ''
  ElMessage.success('已更新')
  await loadComments()
}

async function handleUpgradeToAsk(c: CommentOut) {
  try {
    await ElMessageBox.confirm(
      '将这条评论升级为追问后，笔记作者会收到邮件通知。确定升级吗？',
      '升级为追问',
      { confirmButtonText: '确定升级', type: 'warning' },
    )
  } catch {
    return
  }
  await commentsApi.update(c.id, { is_ask: true })
  ElMessage.success('已升级为追问，作者将收到邮件通知')
  await loadComments()
}

async function handleChangeStatus(c: CommentOut, newStatus: string) {
  try {
    await commentsApi.update(c.id, { status: newStatus })
    ElMessage.success(`状态已改为 ${statusTag(newStatus).text}`)
    await loadComments()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.error?.message || '状态变更失败')
  }
}

async function handleDeleteComment(c: CommentOut) {
  try {
    await ElMessageBox.confirm('确定删除这条评论吗？', '确认删除', {
      confirmButtonText: '删除',
      type: 'warning',
    })
  } catch {
    return
  }
  await commentsApi.remove(c.id)
  ElMessage.success('已删除')
  await loadComments()
  await load()
}

onMounted(() => {
  load()
  loadComments()
})
</script>

<template>
  <div class="note-detail" v-loading="loading">
    <div class="page-header">
      <el-button text @click="router.push(`/projects/${projectId}/notes`)">
        <el-icon><ArrowLeft /></el-icon>
        返回笔记列表
      </el-button>
    </div>

    <template v-if="note">
      <article class="note-article">
        <header class="article-header">
          <div class="header-top">
            <h1>{{ note.title }}</h1>
            <el-tag v-if="note.is_pinned" type="warning" effect="plain">置顶</el-tag>
          </div>
          <div class="header-meta">
            <span class="meta-author">
              {{ note.author_display_name }}
              <a :href="`mailto:${note.author_email}`" class="meta-email">{{ note.author_email }}</a>
            </span>
            <span v-if="note.author_enrollment_year" class="meta-year">
              {{ note.author_enrollment_year }}级
              <template v-if="note.author_graduation_year">入学，{{ note.author_graduation_year }}年毕业</template>
              <template v-else>入学</template>
            </span>
            <span class="meta-date">{{ formatDate(note.created_at) }}</span>
            <span v-if="note.category_name" class="meta-cat">
              <el-tag size="small" type="info">{{ note.category_name }}</el-tag>
            </span>
          </div>
        </header>

        <div class="article-content">
          <MarkdownRenderer :content="note.content" />
        </div>

        <AttachmentList
          :note-id="note.id"
          :can-edit="isAuthor() || auth.isOwner"
          @changed="load"
        />

        <footer class="article-footer">
          <div class="footer-left">
            <el-button @click="handleLike">👍 {{ note.like_count }}</el-button>
            <span class="comment-count-badge">💬 {{ note.comment_count }}</span>
          </div>
          <div class="footer-right" v-if="isAuthor() || auth.isOwner">
            <el-button @click="handleTogglePin">
              {{ note.is_pinned ? '取消置顶' : '置顶' }}
            </el-button>
            <el-dropdown @command="(c: string) => doExport(c as any)" trigger="click">
              <el-button :loading="exporting">
                导出 ⌄
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="md">📄 Markdown (.md)</el-dropdown-item>
                  <el-dropdown-item command="html">🌐 HTML (.html)</el-dropdown-item>
                  <el-dropdown-item command="docx">📘 Word (.docx)</el-dropdown-item>
                  <el-dropdown-item command="pdf">📕 PDF (.pdf)</el-dropdown-item>
                  <el-dropdown-item divided command="svg" @click="openMindmap">🧠 脑图 (SVG)</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-button @click="openMindmap">🧠 预览脑图</el-button>
            <el-button @click="showEdit = true">编辑</el-button>
            <el-button type="danger" plain @click="handleDelete">删除</el-button>
          </div>
        </footer>
      </article>

      <!-- Comments Section -->
      <section class="comments-section">
        <div class="comments-header">
          <h3 class="comments-title">评论 & 追问 ({{ note.comment_count }})</h3>
          <el-radio-group v-model="commentFilter" size="small">
            <el-radio-button value="all">全部</el-radio-button>
            <el-radio-button value="asks">追问</el-radio-button>
            <el-radio-button value="mine">我的</el-radio-button>
          </el-radio-group>
        </div>

        <div class="comment-list" v-loading="commentsLoading">
          <div v-if="filteredComments.length === 0" class="no-comments">
            {{ commentFilter === 'mine' ? '你没有发表过评论' : commentFilter === 'asks' ? '暂无追问' : '暂无评论，欢迎留言或追问' }}
          </div>

          <div
            v-for="c in filteredComments"
            :key="c.id"
            class="comment-card"
            :class="{
              'is-ask': c.is_ask && c.parent_id === null,
              'is-reply': c.parent_id !== null
            }"
          >
            <div class="comment-header">
              <span class="comment-type-badge" v-if="c.is_ask && c.parent_id === null">
                <el-tag :type="statusTag(c.status).type as any" size="small" effect="dark">
                  🔔 {{ statusTag(c.status).text }}
                </el-tag>
              </span>
              <span class="comment-author">{{ c.author_name }}</span>
              <span class="comment-email">{{ c.author_email }}</span>
              <span class="comment-time">{{ formatDate(c.created_at) }}</span>
            </div>

            <div class="comment-body" v-if="editingCommentId !== c.id">
              {{ c.content }}
            </div>
            <div class="comment-edit" v-else>
              <el-input
                v-model="editContent"
                type="textarea"
                :rows="3"
                placeholder="编辑评论..."
              />
              <div class="comment-edit-actions">
                <el-button size="small" @click="handleUpdateComment(c)">保存</el-button>
                <el-button size="small" @click="cancelEditComment()">取消</el-button>
              </div>
            </div>

            <div class="comment-actions" v-if="editingCommentId !== c.id">
              <!-- 回复按钮：追问只有笔记作者能回；所有人不能回复自己 -->
              <el-button
                v-if="(!c.is_ask || isAuthor()) && !isCommentAuthor(c)"
                text size="small"
                @click="handleReply(c)"
              >回复</el-button>
              <!-- 自己的普通评论可以升级为追问（触发邮件通知作者） -->
              <el-button
                v-if="isCommentAuthor(c) && !c.is_ask && c.parent_id === null"
                text size="small"
                type="warning"
                @click="handleUpgradeToAsk(c)"
              >升级为追问</el-button>
              <template v-if="isCommentAuthor(c)">
                <el-button text size="small" @click="startEditComment(c)">编辑</el-button>
                <el-button text size="small" type="danger" @click="handleDeleteComment(c)">删除</el-button>
              </template>
              <template v-if="c.is_ask && canModifyStatus()">
                <el-dropdown @command="(s: string) => handleChangeStatus(c, s)">
                  <el-button text size="small">变更状态</el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item
                        v-for="s in (c.status === 'open'
                          ? ['answered', 'closed']
                          : c.status === 'answered' ? ['closed'] : [])"
                        :key="s"
                        :command="s"
                      >
                        {{ statusTag(s).text }}
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </template>
              <template v-if="auth.isOwner && !isCommentAuthor(c)">
                <el-button text size="small" type="danger" @click="handleDeleteComment(c)">删除</el-button>
              </template>
            </div>

            <!-- Nested replies -->
            <div v-if="repliesOf(c.id).length > 0" class="replies">
              <div v-for="r in repliesOf(c.id)" :key="r.id" class="reply-card">
                <div class="comment-header">
                  <span class="comment-author">{{ r.author_name }}</span>
                  <span class="comment-time">{{ formatDate(r.created_at) }}</span>
                </div>
                <div class="comment-body">{{ r.content }}</div>
                <div class="comment-actions">
                  <el-button
                    v-if="(!c.is_ask || isAuthor()) && !isCommentAuthor(r)"
                    text size="small"
                    @click="handleReply(c)"
                  >回复</el-button>
                  <el-button v-if="isCommentAuthor(r) || auth.isOwner" text size="small" type="danger" @click="handleDeleteComment(r)">删除</el-button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Comment input -->
        <div class="comment-input-area" v-if="auth.isLoggedIn">
          <div class="reply-context" v-if="replyTo">
            <span>回复 @{{ replyTo.author_name }}</span>
            <el-button text size="small" @click="cancelReply()">取消</el-button>
          </div>
          <el-input
            v-model="newComment"
            type="textarea"
            :rows="3"
            :placeholder="replyLabel"
            :disabled="submitting"
          />
          <div class="comment-input-actions">
            <el-button type="primary" :loading="submitting" @click="handleAddComment">
              发表评论
            </el-button>
            <el-popover trigger="hover" placement="top" :width="280">
              <template #reference>
                <el-button type="warning" plain :loading="submitting" @click="handleAskFollowUp">
                  🔔 追问作者
                </el-button>
              </template>
              <div style="font-size:0.85rem; line-height:1.6;">
                <p style="margin:0 0 4px;"><strong>追问会邮件通知笔记作者</strong></p>
                <p style="margin:0; color:#909399;">非紧急问题建议先发普通评论，作者上线就能看到</p>
              </div>
            </el-popover>
          </div>
        </div>
      </section>

      <el-dialog v-model="showEdit" title="编辑笔记" width="720px" destroy-on-close>
        <NoteForm
          :project-id="projectId"
          :note="note"
          @saved="handleSaved"
          @cancel="showEdit = false"
        />
      </el-dialog>

      <el-dialog v-model="showMindmap" title="🧠 笔记脑图（基于标题层级自动生成）" width="900px" destroy-on-close>
        <div ref="mindmapContainer" class="mindmap-container"></div>
        <template #footer>
          <el-button type="primary" @click="doExport('svg')">导出 SVG</el-button>
        </template>
      </el-dialog>
    </template>
  </div>
</template>

<style scoped>
.note-article {
  max-width: 800px;
  margin: 0 auto;
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 2.5rem;
}
.header-top {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}
.header-top h1 {
  margin: 0;
  font-size: 1.6rem;
}
.header-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 1.25rem;
  font-size: 0.82rem;
  color: var(--lab-muted);
  padding-bottom: 1.25rem;
  border-bottom: 1px solid var(--el-border-color-lighter);
  margin-bottom: 1.5rem;
}
.meta-email {
  margin-left: 0.5rem;
  color: var(--el-color-primary);
  text-decoration: none;
  font-size: 0.78rem;
}
.article-content {
  min-height: 200px;
}
.article-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid var(--el-border-color-lighter);
}
.footer-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}
.comment-count-badge {
  font-size: 0.9rem;
  color: var(--lab-muted);
}
.footer-right {
  display: flex;
  gap: 0.5rem;
}

/* ── Comments ────────────────────────────── */
.comments-section {
  max-width: 800px;
  margin: 1.5rem auto 0;
  background: var(--el-bg-color);
  border-radius: 12px;
  padding: 1.5rem 2rem;
}
.comments-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}
.comments-title {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 600;
}
.no-comments {
  text-align: center;
  color: var(--lab-muted);
  padding: 2rem 0;
  font-size: 0.92rem;
}
.comment-card {
  padding: 0.75rem;
  border-bottom: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  margin-bottom: 0.5rem;
  background: var(--el-bg-color);
  border-left: 3px solid transparent;
}
.comment-card.is-ask {
  background: #fef7e8;
  border-left: 3px solid var(--el-color-warning);
}
.comment-card.is-reply {
  padding-left: 1rem;
  background: transparent;
  border-bottom: 1px dashed var(--el-border-color-lighter);
  margin-left: 1.5rem;
  border-left: 2px solid var(--el-color-primary-light-5);
}
.comment-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.35rem;
}
.comment-type-badge {
  margin-right: 0.25rem;
}
.comment-author {
  font-weight: 600;
  font-size: 0.88rem;
}
.comment-email {
  font-size: 0.78rem;
  color: var(--el-color-primary);
}
.comment-time {
  font-size: 0.76rem;
  color: var(--lab-muted);
  margin-left: auto;
}
.comment-body {
  font-size: 0.9rem;
  color: var(--el-text-color-primary);
  line-height: 1.6;
  white-space: pre-wrap;
}
.comment-actions {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  margin-top: 0.35rem;
}
.comment-edit {
  margin: 0.5rem 0;
}
.comment-edit-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.replies {
  margin-top: 0.5rem;
}

/* Input */
.reply-context {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--el-color-primary-light-9);
  padding: 0.35rem 0.75rem;
  border-radius: 6px 6px 0 0;
  font-size: 0.84rem;
  color: var(--el-color-primary);
  border: 1px solid var(--el-color-primary-light-5);
  border-bottom: none;
}
.comment-input-area {
  margin-top: 1.25rem;
}
.comment-input-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.75rem;
  justify-content: flex-end;
}
</style>

.mindmap-container {
  width: 100%;
  height: 600px;
  background: #fafafa;
  border-radius: 8px;
  overflow: hidden;
}
.mindmap-container :deep(svg) {
  display: block;
}
