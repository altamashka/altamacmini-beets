import { useState } from 'react'
import { triggerNavidromeScan } from '../../api'
import type { ImportJob, WsMessage, AlbumMatchPayload } from '../../types'
import styles from './ImportSummary.module.css'

interface Props {
  job: ImportJob
  events: WsMessage[]
  onReset: () => void
}

interface ConfidenceCounts {
  green: number
  yellow: number
  red: number
}

export function ImportSummary({ job, events, onReset }: Props) {
  const [scanState, setScanState] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [scanError, setScanError] = useState<string | null>(null)

  const matchEvents = events.filter(e =>
    e.event === 'album_match' || e.event === 'album_decision_needed'
  )

  const artFound = matchEvents.filter(e => {
    const p = e.payload as Partial<AlbumMatchPayload>
    return p.artwork?.found === true
  }).length

  const artPct = matchEvents.length > 0
    ? Math.round((artFound / matchEvents.length) * 100)
    : 0

  const confidence: ConfidenceCounts = matchEvents.reduce(
    (acc, e) => {
      const p = e.payload as Partial<AlbumMatchPayload>
      const c = typeof p.confidence === 'number' ? p.confidence * 100 : null
      if (c === null) return acc
      if (c >= 90) acc.green++
      else if (c >= 70) acc.yellow++
      else acc.red++
      return acc
    },
    { green: 0, yellow: 0, red: 0 } as ConfidenceCounts
  )

  async function handleNavidromeScan() {
    setScanState('loading')
    setScanError(null)
    try {
      await triggerNavidromeScan()
      setScanState('success')
    } catch (err) {
      setScanState('error')
      setScanError(err instanceof Error ? err.message : 'Scan trigger failed')
    }
  }

  const isError = job.status === 'error'

  return (
    <div className={styles.summary}>
      <div className={styles.titleRow}>
        <h2 className={styles.title}>{isError ? 'Import Failed' : 'Import Complete'}</h2>
        <span className={isError ? styles.errorBadge : styles.completedBadge}>
          {isError ? 'Error' : 'Done'}
        </span>
      </div>

      <div className={styles.statsGrid}>
        <div className={styles.statCard}>
          <span className={styles.statValue}>{job.albums_total}</span>
          <span className={styles.statLabel}>Albums total</span>
        </div>
        <div className={styles.statCard}>
          <span className={`${styles.statValue} ${styles.green}`}>{job.albums_done}</span>
          <span className={styles.statLabel}>Imported</span>
        </div>
        <div className={styles.statCard}>
          <span className={`${styles.statValue} ${styles.muted}`}>{job.albums_skipped}</span>
          <span className={styles.statLabel}>Skipped</span>
        </div>
        <div className={styles.statCard}>
          <span className={`${styles.statValue} ${styles.purple}`}>{artPct}%</span>
          <span className={styles.statLabel}>Art found</span>
        </div>
      </div>

      {matchEvents.length > 0 && (
        <div className={styles.confidenceSection}>
          <p className={styles.sectionLabel}>Confidence distribution</p>
          <div className={styles.confidenceBars}>
            <div className={styles.confRow}>
              <span className={styles.confDot} style={{ background: '#22c55e' }} />
              <span className={styles.confLabel}>High (&ge;90%)</span>
              <span className={`${styles.confCount} ${styles.green}`}>{confidence.green}</span>
            </div>
            <div className={styles.confRow}>
              <span className={styles.confDot} style={{ background: '#f59e0b' }} />
              <span className={styles.confLabel}>Medium (70–89%)</span>
              <span className={`${styles.confCount} ${styles.yellow}`}>{confidence.yellow}</span>
            </div>
            <div className={styles.confRow}>
              <span className={styles.confDot} style={{ background: '#ef4444' }} />
              <span className={styles.confLabel}>Low (&lt;70%)</span>
              <span className={`${styles.confCount} ${styles.red}`}>{confidence.red}</span>
            </div>
          </div>
        </div>
      )}

      <div className={styles.scanSection}>
        <p className={styles.scanHint}>
          Trigger a Navidrome library scan to make new music available in your media server.
        </p>
        {scanState === 'success' ? (
          <div className={styles.scanSuccess}>✓ Navidrome scan triggered successfully</div>
        ) : (
          <button
            className={styles.scanBtn}
            onClick={handleNavidromeScan}
            disabled={scanState === 'loading'}
          >
            {scanState === 'loading' ? (
              <><span className={styles.spinner} /> Triggering scan…</>
            ) : (
              'Trigger Navidrome Scan'
            )}
          </button>
        )}
        {scanState === 'error' && (
          <div className={styles.scanError}>{scanError}</div>
        )}
      </div>

      {job.error && (
        <div className={styles.errorNote}>
          <span className={styles.errorLabel}>Error:</span> {job.error}
        </div>
      )}

      <button className={styles.resetBtn} onClick={onReset}>
        Import Again
      </button>
    </div>
  )
}
