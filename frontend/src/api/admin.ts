import type { AxiosPromise } from 'axios'
import apiClient from './client'

// ── Audit ───────────────────────────────────

export interface AuditEntryOut {
  id: number
  user_id: number
  user_email: string
  user_display_name: string
  submitted_payload: Record<string, unknown>
  reviewer_id: number | null
  reviewer_email: string | null
  status: string
  decision_note: string | null
  decided_at: string | null
  created_at: string
}

export interface AuditListResponse {
  items: AuditEntryOut[]
  total: number
}

export interface DecisionRequest {
  action: 'approve' | 'reject'
  note?: string | null
}

// ── Dashboard ───────────────────────────────

export interface DashboardKPIs {
  users: { active: number; graduated: number; archived: number }
  pending_audits: number
  open_asks: number
  stale_projects: number
  failed_emails: number
  notes_total: number
  comments_total: number
}

export interface StaleProject {
  id: number
  title: string
  status: string
  last_activity_at: string | null
  creator_display_name: string
}

export interface HotNote {
  id: number
  title: string
  project_id: number
  project_title: string
  like_count: number
  comment_count: number
}

export interface UnansweredAsk {
  id: number
  note_id: number
  project_id: number
  note_title: string
  asker_name: string
  content: string
  created_at: string
  days_open: number
}

export interface FailedEmail {
  id: number
  to_email: string
  subject: string
  retry_count: number
  last_error: string | null
}

export interface DashboardOut {
  kpis: DashboardKPIs
  stale_projects: StaleProject[]
  hot_notes: HotNote[]
  unanswered_asks: UnansweredAsk[]
  failed_emails: FailedEmail[]
}

export const adminApi = {
  // ── Audit queue ──
  listAuditQueue(params?: {
    status?: string
    page?: number
    page_size?: number
  }): AxiosPromise<AuditListResponse> {
    return apiClient.get('/admin/audit-queue', { params })
  },

  decide(entryId: number, data: DecisionRequest): AxiosPromise<AuditEntryOut> {
    return apiClient.post(`/admin/audit-queue/${entryId}/decision`, data)
  },

  // ── Dashboard ──
  dashboard(): AxiosPromise<DashboardOut> {
    return apiClient.get('/admin/dashboard')
  },

  // ── User management ──
  changeRole(userId: number, role: string): AxiosPromise<{ detail: string }> {
    return apiClient.post(`/admin/users/${userId}/role`, { role })
  },

  changeStatus(userId: number, status: string): AxiosPromise<{ detail: string }> {
    return apiClient.post(`/admin/users/${userId}/status`, { status })
  },
}
