// TypeScript mirrors of backend Pydantic models

// --- Library ---

export interface TrackInfo {
  id: number
  title: string
  track?: number
  disc?: number
  length?: number
  path: string
  mb_trackid?: string
  format?: string
  bitrate?: number
}

export interface AlbumInfo {
  id: number
  album: string
  albumartist: string
  year?: number
  genre?: string
  mb_albumid?: string
  artpath?: string
  tracks: TrackInfo[]
}

export type AuditIssueType =
  | 'duplicate_album'
  | 'missing_artwork'
  | 'missing_metadata'
  | 'bad_track_numbers'
  | 'split_album'
  | 'broken_file'

export interface AuditIssue {
  id: string
  type: AuditIssueType
  album_id?: number
  album_ids?: number[]
  description: string
  fixable: boolean
}

export interface FixRequest {
  issue_ids: string[]
  operation: string
  params?: Record<string, unknown>
}

// --- Imports ---

export type ImportJobStatus = 'pending' | 'running' | 'waiting_decision' | 'complete' | 'error'
export type ManualDecision = 'apply' | 'skip' | 'as_is' | 'search'

export interface AlbumMetadata {
  artist?: string
  album?: string
  year?: number
  genre?: string
  albumartist?: string
}

export interface AlbumMatchPayload {
  confidence: number
  before: AlbumMetadata
  after: AlbumMetadata
  artwork: { found: boolean; source?: string; url?: string }
  tracks: TrackInfo[]
}

export interface ImportJob {
  id: string
  status: ImportJobStatus
  paths: string[]
  albums_total: number
  albums_done: number
  albums_skipped: number
  current_album?: string
  pending_decision?: AlbumMatchPayload
  error?: string
}

// --- WebSocket ---

export type WsEventType =
  | 'import_started'
  | 'album_begin'
  | 'album_match'
  | 'album_decision_needed'
  | 'album_applying'
  | 'album_complete'
  | 'album_skipped'
  | 'import_complete'
  | 'import_error'
  | 'fix_started'
  | 'fix_progress'
  | 'fix_complete'
  | 'fix_error'
  | 'audit_started'
  | 'audit_progress'
  | 'audit_complete'

export interface WsMessage {
  event: WsEventType
  job_id: string
  timestamp: string
  payload: Record<string, unknown>
}

// --- Downloads ---

export interface DownloadEntry {
  name: string
  path: string
  is_dir: boolean
  size?: number
}

export interface DownloadBrowseResult {
  path: string
  is_dir: boolean
  entries: DownloadEntry[]
}
