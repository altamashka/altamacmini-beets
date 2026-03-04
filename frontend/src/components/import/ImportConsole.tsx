import { useEffect, useRef } from 'react'
import { LowConfidenceAlert } from './LowConfidenceAlert'
import { AlbumImportCard } from './AlbumImportCard'
import type { ImportJob, WsMessage, ManualDecision, AlbumMatchPayload } from '../../types'
import styles from './ImportConsole.module.css'

interface Props {
  job: ImportJob
  events: WsMessage[]
  onDecide: (d: ManualDecision) => void
}

const ALBUM_CARD_EVENTS = new Set([
  'album_match',
  'album_complete',
  'album_skipped',
  'album_decision_needed',
])

export function ImportConsole({ job, events, onDecide }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [events.length])

  const albumEvents = events.filter(e => ALBUM_CARD_EVENTS.has(e.event))

  const statusLabel: Record<string, string> = {
    pending: 'Pending',
    running: 'Running…',
    waiting_decision: 'Waiting for decision',
    complete: 'Complete',
    error: 'Error',
  }

  const statusClass: Record<string, string> = {
    pending: styles.statusPending,
    running: styles.statusRunning,
    waiting_decision: styles.statusWaiting,
    complete: styles.statusComplete,
    error: styles.statusError,
  }

  return (
    <div className={styles.console}>
      <div className={styles.header}>
        <div className={styles.jobInfo}>
          <span className={styles.jobId}>Job {job.id.slice(0, 8)}</span>
          <span className={`${styles.statusBadge} ${statusClass[job.status] ?? ''}`}>
            {statusLabel[job.status] ?? job.status}
          </span>
        </div>
        <div className={styles.progress}>
          <span className={styles.progressText}>
            {job.albums_done} / {job.albums_total > 0 ? job.albums_total : '?'} albums
          </span>
          {job.albums_skipped > 0 && (
            <span className={styles.skippedText}>{job.albums_skipped} skipped</span>
          )}
        </div>
      </div>

      {job.status === 'waiting_decision' && job.pending_decision && (
        <div className={styles.alertSection}>
          <LowConfidenceAlert
            payload={job.pending_decision as AlbumMatchPayload & { candidates?: Array<{ artist?: string; album?: string; year?: number; confidence?: number }> }}
            onDecide={onDecide}
          />
        </div>
      )}

      <div className={styles.eventStream}>
        {albumEvents.length === 0 ? (
          <div className={styles.emptyStream}>
            {job.status === 'pending' ? 'Starting import…' : 'Waiting for album data…'}
          </div>
        ) : (
          albumEvents.map((e, i) => (
            <AlbumImportCard key={`${e.job_id}-${i}`} event={e} />
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
