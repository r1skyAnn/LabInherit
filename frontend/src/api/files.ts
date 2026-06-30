import type { AxiosPromise } from 'axios'
import apiClient from './client'

export type FileCategory = 'image' | 'document' | 'video' | 'audio' | 'archive' | 'mindmap' | 'other'
export type AttachmentRole = 'inline' | 'attachment'

export interface FileOut {
  id: number
  owner_id: number
  project_id: number | null
  original_name: string
  mime_type: string
  size: number
  category: FileCategory
  url: string
  created_at: string
}

export interface NoteAttachmentOut {
  id: number
  note_id: number
  file_id: number
  role: AttachmentRole
  position: number
  created_at: string
  file: FileOut
}

export interface GuideAttachmentOut {
  id: number
  guide_id: number
  file_id: number
  role: AttachmentRole
  position: number
  created_at: string
  file: FileOut
}

export interface AttachmentCreate {
  file_id: number
  role?: AttachmentRole
  position?: number
}

export const filesApi = {
  /**
   * Upload a file via multipart/form-data.
   * No timeout — large files (up to 100 MB) need time to transfer.
   */
  upload(
    file: File,
    projectId?: number,
    onUploadProgress?: (percent: number) => void,
  ): AxiosPromise<FileOut> {
    const fd = new FormData()
    fd.append('file', file)
    if (projectId != null) fd.append('project_id', String(projectId))
    return apiClient.post('/files/upload', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 0,  // disable timeout for uploads
      onUploadProgress: (e) => {
        if (onUploadProgress && e.total) {
          onUploadProgress(Math.round((e.loaded / e.total) * 100))
        }
      },
    })
  },

  getMeta(id: number): AxiosPromise<FileOut> {
    return apiClient.get(`/files/${id}`)
  },

  /** Direct browser download via temporary anchor. */
  downloadUrl(id: number): string {
    return `/api/v1/files/${id}/download`
  },

  remove(id: number): AxiosPromise<{ detail: string }> {
    return apiClient.delete(`/files/${id}`)
  },
}

export const noteAttachmentsApi = {
  list(noteId: number): AxiosPromise<NoteAttachmentOut[]> {
    return apiClient.get(`/files/notes/${noteId}/attachments`)
  },

  attach(noteId: number, payload: AttachmentCreate): AxiosPromise<NoteAttachmentOut> {
    return apiClient.post(`/files/notes/${noteId}/attachments`, payload)
  },

  update(
    noteId: number,
    attachmentId: number,
    payload: Partial<AttachmentCreate>,
  ): AxiosPromise<NoteAttachmentOut> {
    return apiClient.patch(`/files/notes/${noteId}/attachments/${attachmentId}`, payload)
  },

  detach(noteId: number, attachmentId: number): AxiosPromise<{ detail: string }> {
    return apiClient.delete(`/files/notes/${noteId}/attachments/${attachmentId}`)
  },
}

export const guideAttachmentsApi = {
  list(guideId: number): AxiosPromise<GuideAttachmentOut[]> {
    return apiClient.get(`/guides/${guideId}/attachments`)
  },

  attach(guideId: number, payload: AttachmentCreate): AxiosPromise<GuideAttachmentOut> {
    return apiClient.post(`/guides/${guideId}/attachments`, payload)
  },

  update(
    guideId: number,
    attachmentId: number,
    payload: Partial<AttachmentCreate>,
  ): AxiosPromise<GuideAttachmentOut> {
    return apiClient.patch(`/guides/${guideId}/attachments/${attachmentId}`, payload)
  },

  detach(guideId: number, attachmentId: number): AxiosPromise<{ detail: string }> {
    return apiClient.delete(`/guides/${guideId}/attachments/${attachmentId}`)
  },
}

/** Format byte size as human-readable string. */
export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`
}

/** Map a file extension to an emoji icon. */
export function iconForFile(filename: string, category?: FileCategory): string {
  const ext = filename.split('.').pop()?.toLowerCase() ?? ''
  if (category === 'image' || ['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'].includes(ext)) return '🖼️'
  if (category === 'video' || ['mp4', 'webm', 'mov', 'avi'].includes(ext)) return '🎬'
  if (category === 'audio' || ['mp3', 'wav', 'ogg', 'm4a'].includes(ext)) return '🎵'
  if (ext === 'pdf') return '📕'
  if (['doc', 'docx'].includes(ext)) return '📘'
  if (['xls', 'xlsx'].includes(ext)) return '📗'
  if (['ppt', 'pptx'].includes(ext)) return '📙'
  if (category === 'mindmap' || ['mm', 'km', 'xmind'].includes(ext)) return '🧠'
  if (category === 'archive' || ['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) return '📦'
  if (['md', 'txt'].includes(ext)) return '📝'
  return '📄'
}