// Note drafts — localStorage autosave
//
// Each in-progress note gets a draft entry keyed by `noteDraft:<scope>`.
// Scope is one of:
//   - "new:project:<projectId>"   for new notes in a project
//   - "edit:<noteId>"             for existing-note edits
//
// Drafts older than `DRAFT_TTL_MS` are treated as stale.

export interface NoteDraft {
  scope: string
  title: string
  content: string
  category_id: number | null
  // Pending file IDs (for new notes) — we don't persist File blobs, only the IDs
  pendingFileIds: number[]
  // Pending inline file IDs from editor uploads
  inlineFileIds: number[]
  savedAt: number  // Date.now()
}

const STORAGE_PREFIX = 'labinherit:noteDraft:'
const DRAFT_TTL_MS = 7 * 24 * 60 * 60 * 1000  // 7 days

function keyFor(scope: string): string {
  return `${STORAGE_PREFIX}${scope}`
}

export function newNoteScope(projectId: number): string {
  return `new:project:${projectId}`
}

export function editNoteScope(noteId: number): string {
  return `edit:${noteId}`
}

export function saveDraft(draft: NoteDraft): void {
  try {
    const payload: NoteDraft = { ...draft, savedAt: Date.now() }
    localStorage.setItem(keyFor(draft.scope), JSON.stringify(payload))
  } catch {
    // ignore quota errors
  }
}

export function loadDraft(scope: string): NoteDraft | null {
  try {
    const raw = localStorage.getItem(keyFor(scope))
    if (!raw) return null
    const parsed = JSON.parse(raw) as NoteDraft
    if (!parsed.savedAt || Date.now() - parsed.savedAt > DRAFT_TTL_MS) {
      localStorage.removeItem(keyFor(scope))
      return null
    }
    return parsed
  } catch {
    return null
  }
}

export function clearDraft(scope: string): void {
  try {
    localStorage.removeItem(keyFor(scope))
  } catch {
    // ignore
  }
}

export function formatDraftAge(savedAt: number): string {
  const ms = Date.now() - savedAt
  const mins = Math.floor(ms / 60000)
  if (mins < 1) return '刚刚'
  if (mins < 60) return `${mins} 分钟前`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours} 小时前`
  const days = Math.floor(hours / 24)
  return `${days} 天前`
}