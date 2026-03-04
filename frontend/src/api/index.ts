import type { AlbumInfo, DownloadBrowseResult, ImportJob, FixRequest } from '../types'
import api from './client'

// --- Library ---

export const fetchAlbums = (q?: string) =>
  api.get<AlbumInfo[]>('/library/albums', { params: q ? { q } : {} }).then(r => r.data)

export const fetchAlbum = (id: number) =>
  api.get<AlbumInfo>(`/library/albums/${id}`).then(r => r.data)

export const fetchLibraryStats = () =>
  api.get<{ album_count: number; track_count: number }>('/library/stats').then(r => r.data)

// --- Downloads ---

export const browseDownloads = (path?: string) =>
  api.get<DownloadBrowseResult>('/downloads/browse', { params: path ? { path } : {} }).then(r => r.data)

// --- Imports ---

export const createImportJob = (paths: string[]) =>
  api.post<ImportJob>('/import/jobs', { paths }).then(r => r.data)

export const fetchImportJob = (id: string) =>
  api.get<ImportJob>(`/import/jobs/${id}`).then(r => r.data)

export const submitDecision = (jobId: string, decision: string, search_query?: string) =>
  api.post(`/import/jobs/${jobId}/decide`, { decision, search_query }).then(r => r.data)

// --- Audit ---

export const startAuditScan = () =>
  api.post<{ scan_id: string }>('/audit/scans').then(r => r.data)

export const fetchAuditScan = (id: string) =>
  api.get(`/audit/scans/${id}`).then(r => r.data)

// --- Fixes ---

export const startFix = (request: FixRequest) =>
  api.post<{ fix_id: string }>('/fix/', request).then(r => r.data)

// --- Navidrome ---

export const triggerNavidromeScan = () =>
  api.post('/navidrome/scan').then(r => r.data)

// --- Health ---

export const fetchHealth = () =>
  api.get<{ status: string; library_db: string }>('/health').then(r => r.data)
