<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { membersApi, type MemberOut } from '@/api/members'
import { adminApi } from '@/api/admin'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'

const auth = useAuthStore()
const members = ref<MemberOut[]>([])
const total = ref(0)
const loading = ref(false)
const search = ref('')

async function load() {
  loading.value = true
  try {
    const resp = await membersApi.list({ search: search.value || undefined, page: 1, page_size: 200 })
    members.value = resp.data.items
    total.value = resp.data.total
  } finally {
    loading.value = false
  }
}

function formatYear(y: number | null) {
  return y ?? '—'
}

const roleLabel: Record<string, string> = {
  owner: '导师', member: '成员',
}
const roleType: Record<string, string> = {
  owner: 'warning', member: 'info',
}
const statusLabel: Record<string, string> = {
  active: '在读', graduated: '已毕业', archived: '已归档',
}
const statusType: Record<string, string> = {
  active: 'success', graduated: 'info', archived: '',
}

const roleOptions: Record<string, { label: string; role: string }[]> = {
  owner: [{ label: '导师', role: 'owner' }, { label: '成员', role: 'member' }],
  member: [{ label: '成员', role: 'member' }],
}

const statusOptions = [
  { label: '在读', status: 'active' },
  { label: '已毕业', status: 'graduated' },
  { label: '归档', status: 'archived' },
]

async function handleChangeRole(user: MemberOut, role: string) {
  try {
    await adminApi.changeRole(user.id, role)
    user.role = role
    ElMessage.success(`已将 ${user.display_name} 角色改为 ${roleLabel[role]}`)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.error?.message || '操作失败')
  }
}

async function handleChangeStatus(user: MemberOut, status: string) {
  try {
    await adminApi.changeStatus(user.id, status)
    user.status = status
    ElMessage.success(`已将 ${user.display_name} 状态改为 ${statusLabel[status]}`)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.error?.message || '操作失败')
  }
}

let searchTimer: ReturnType<typeof setTimeout>
function handleSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(load, 350)
}

onMounted(load)
</script>

<template>
  <div class="members-page">
    <div class="page-header">
      <h2>成员列表</h2>
      <div class="header-actions">
        <el-input
          v-model="search"
          placeholder="搜索姓名或邮箱"
          clearable
          style="width: 220px"
          @input="handleSearch"
          @clear="load"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
    </div>

    <el-table :data="members" v-loading="loading" stripe style="width:100%" row-key="id">
      <el-table-column label="姓名" min-width="120">
        <template #default="{ row }">
          <div class="member-name">{{ row.display_name }}</div>
          <div class="member-email">{{ row.email }}</div>
        </template>
      </el-table-column>
      <el-table-column label="角色" width="130" align="center">
        <template #default="{ row }">
          <template v-if="auth.isOwner && row.role !== 'owner'">
            <el-dropdown @command="(r: string) => handleChangeRole(row, r)">
              <el-tag size="small" :type="roleType[row.role] as any" effect="plain" style="cursor:pointer">
                {{ roleLabel[row.role] ?? row.role }} ▾
              </el-tag>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item
                    v-for="opt in roleOptions[row.role] ?? []"
                    :key="opt.role"
                    :command="opt.role"
                  >{{ opt.label }}</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
          <template v-else>
            <el-tag size="small" :type="roleType[row.role] as any" effect="plain">
              {{ roleLabel[row.role] ?? row.role }}
            </el-tag>
          </template>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="130" align="center">
        <template #default="{ row }">
          <template v-if="auth.isOwner && row.role !== 'owner'">
            <el-dropdown @command="(s: string) => handleChangeStatus(row, s)">
              <el-tag size="small" :type="statusType[row.status] as any" effect="plain" style="cursor:pointer">
                {{ statusLabel[row.status] ?? row.status }} ▾
              </el-tag>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item
                    v-for="opt in statusOptions"
                    :key="opt.status"
                    :command="opt.status"
                  >{{ opt.label }}</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
          <template v-else>
            <el-tag size="small" :type="statusType[row.status] as any" effect="plain">
              {{ statusLabel[row.status] ?? row.status }}
            </el-tag>
          </template>
        </template>
      </el-table-column>
      <el-table-column label="研究方向" min-width="140">
        <template #default="{ row }">
          <span class="field-text">{{ row.research_direction ?? '—' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="就读年份" width="130" align="center">
        <template #default="{ row }">
          {{ formatYear(row.enrollment_year) }}
          <template v-if="row.graduation_year"> → {{ formatYear(row.graduation_year) }}</template>
        </template>
      </el-table-column>
      <el-table-column label="所属单位" min-width="160">
        <template #default="{ row }">
          <span class="field-text">{{ row.current_affiliation ?? '—' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="简介" min-width="200">
        <template #default="{ row }">
          <span class="bio-text">{{ row.bio ?? '—' }}</span>
        </template>
      </el-table-column>
    </el-table>

    <div class="summary">共 {{ total }} 位成员</div>
  </div>
</template>


<style scoped>
.members-page { max-width: 1200px; margin: 0 auto; }

.page-header {
  display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem;
}
.page-header h2 { margin: 0; }
.header-actions { display: flex; gap: 0.75rem; align-items: center; }

.member-name { font-weight: 600; font-size: 0.9rem; }
.member-email { font-size: 0.78rem; color: var(--lab-muted); }

.field-text, .bio-text {
  font-size: 0.85rem; color: var(--el-text-color-regular);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; display: block; max-width: 200px;
}

.summary { margin-top: 1rem; color: var(--lab-muted); font-size: 0.85rem; }
</style>
