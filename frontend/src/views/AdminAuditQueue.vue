<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { adminApi, type AuditEntryOut } from '@/api/admin'
import { ElMessage, ElMessageBox } from 'element-plus'

const entries = ref<AuditEntryOut[]>([])
const total = ref(0)
const loading = ref(false)
const filterStatus = ref<string>('pending')
const page = ref(1)
const pageSize = ref(20)

async function load() {
  loading.value = true
  try {
    const resp = await adminApi.listAuditQueue({
      status: filterStatus.value || undefined,
      page: page.value,
      page_size: pageSize.value,
    })
    entries.value = resp.data.items
    total.value = resp.data.total
  } finally {
    loading.value = false
  }
}

async function decide(entry: AuditEntryOut, action: 'approve' | 'reject') {
  const label = action === 'approve' ? '批准' : '拒绝'
  try {
    await ElMessageBox.confirm(`确定${label}该申请吗？`, '确认', {
      confirmButtonText: label,
      type: action === 'approve' ? 'success' : 'warning',
    })
  } catch {
    return
  }
  try {
    await adminApi.decide(entry.id, { action })
    ElMessage.success(`已${label}`)
    await load()
  } catch {
    // handled by interceptor
  }
}

onMounted(load)
</script>

<template>
  <div class="audit-page">
    <h2>审核队列</h2>

    <el-radio-group v-model="filterStatus" @change="page=1;load()" style="margin-bottom:1rem">
      <el-radio-button value="pending">待审核</el-radio-button>
      <el-radio-button value="approved">已批准</el-radio-button>
      <el-radio-button value="rejected">已拒绝</el-radio-button>
      <el-radio-button value="">全部</el-radio-button>
    </el-radio-group>

    <el-table :data="entries" v-loading="loading" border stripe style="width:100%">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="user_display_name" label="姓名" width="120" />
      <el-table-column prop="user_email" label="邮箱" width="200" />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag v-if="row.status === 'pending'" type="warning" size="small">待审核</el-tag>
          <el-tag v-else-if="row.status === 'approved'" type="success" size="small">已批准</el-tag>
          <el-tag v-else type="danger" size="small">已拒绝</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="decision_note" label="备注" min-width="150" />
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <template v-if="row.status === 'pending'">
            <el-button type="success" size="small" @click="decide(row, 'approve')">批准</el-button>
            <el-button type="danger" size="small" @click="decide(row, 'reject')">拒绝</el-button>
          </template>
          <span v-else class="muted">已处理</span>
        </template>
      </el-table-column>
    </el-table>
    <div class="summary">共 {{ total }} 条记录</div>
  </div>
</template>

<style scoped>
.audit-page h2 {
  margin: 0 0 1rem;
}
.muted {
  color: var(--lab-muted);
  font-size: 0.85rem;
}
.summary {
  margin-top: 0.5rem;
  color: var(--lab-muted);
  font-size: 0.85rem;
}
</style>
