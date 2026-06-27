<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { invitesApi, type InviteOut } from '@/api/invites'
import { ElMessage, ElMessageBox } from 'element-plus'

const invites = ref<InviteOut[]>([])
const loading = ref(false)
const createForm = reactive({ max_uses: 1, note: '' })
const creating = ref(false)

async function load() {
  loading.value = true
  try {
    const resp = await invitesApi.list(true)
    invites.value = resp.data
  } finally {
    loading.value = false
  }
}

async function doCreate() {
  creating.value = true
  try {
    const resp = await invitesApi.create({
      max_uses: createForm.max_uses,
      note: createForm.note || undefined,
    })
    ElMessage.success(`邀请码已生成：${resp.data.code}`)
    createForm.note = ''
    await load()
  } finally {
    creating.value = false
  }
}

async function doRevoke(invite: InviteOut) {
  try {
    await ElMessageBox.confirm(`确定作废邀请码 ${invite.code} 吗？`, '确认作废', {
      confirmButtonText: '作废',
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await invitesApi.revoke(invite.id)
    ElMessage.success('已作废')
    await load()
  } catch {
    // handled by interceptor
  }
}

function copyCode(code: string) {
  try {
    navigator.clipboard.writeText(code)
    ElMessage.success('已复制到剪贴板')
  } catch {
    // Fallback for non-HTTPS
    const ta = document.createElement('textarea')
    ta.value = code
    ta.style.position = 'fixed'; ta.style.opacity = '0'
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
    ElMessage.success('已复制到剪贴板')
  }
}

onMounted(load)
</script>

<template>
  <div class="invites-page">
    <h2>邀请码管理</h2>

    <el-card class="create-card" style="margin-bottom:1.5rem">
      <template #header>生成新邀请码</template>
      <el-form inline @submit.prevent="doCreate">
        <el-form-item label="可用次数">
          <el-input-number v-model="createForm.max_uses" :min="1" :max="1000" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="createForm.note" placeholder="如：给研一新生" style="width:200px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" native-type="submit" :loading="creating">生成</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-table :data="invites" v-loading="loading" border stripe style="width:100%">
      <el-table-column prop="code" label="邀请码" width="150">
        <template #default="{ row }">
          <span class="code" @click="copyCode(row.code)" style="cursor:pointer">
            {{ row.code }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="note" label="备注" min-width="150" />
      <el-table-column label="使用" width="100">
        <template #default="{ row }">{{ row.used_count }} / {{ row.max_uses }}</template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag v-if="row.revoked_at" type="danger" size="small">已作废</el-tag>
          <el-tag v-else-if="row.used_count >= row.max_uses" type="warning" size="small">已用完</el-tag>
          <el-tag v-else type="success" size="small">有效</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="170">
        <template #default="{ row }">{{ new Date(row.created_at).toLocaleString() }}</template>
      </el-table-column>
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="!row.revoked_at && row.used_count < row.max_uses"
            type="danger"
            size="small"
            @click="doRevoke(row)"
          >
            作废
          </el-button>
          <span v-else class="muted">—</span>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<style scoped>
.invites-page h2 {
  margin: 0 0 1rem;
}
.code {
  font-family: monospace;
  font-weight: 600;
  color: var(--lab-primary);
}
.code:hover {
  text-decoration: underline;
}
.muted {
  color: var(--lab-muted);
  font-size: 0.85rem;
}
</style>
