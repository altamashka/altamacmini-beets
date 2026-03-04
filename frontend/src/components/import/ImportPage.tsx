/**
 * Import Page — Phase 2 will fill in full implementation.
 * Scaffold only: layout shell + basic job trigger.
 */
import { useState } from 'react'
import { useImportJob } from '../../hooks/useImportJob'
import { ConfidenceBadge } from '../shared/ConfidenceBadge'
import type { WsMessage } from '../../types'
import styles from './ImportPage.module.css'

export function ImportPage() {
  const { job, events, startImport } = useImportJob()
  const [selectedPaths] = useState<string[]>([])

  return (
    <div className={styles.page}>
      <h1 className={styles.title}>Import</h1>

      <div className={styles.layout}>
        {/* Left: Downloads browser (Phase 2) */}
        <aside className={styles.sidebar}>
          <h2>Downloads</h2>
          <p style={{ color: '#64748b', fontSize: '0.85rem' }}>
            Downloads browser — Phase 2
          </p>
        </aside>

        {/* Right: Import queue / console */}
        <main className={styles.main}>
          {!job ? (
            <div className={styles.queue}>
              <p style={{ color: '#64748b' }}>Select folders from the downloads panel, then start import.</p>
              <button
                className={styles.btn}
                disabled={selectedPaths.length === 0}
                onClick={() => startImport(selectedPaths)}
              >
                Start Import
              </button>
            </div>
          ) : (
            <div className={styles.console}>
              <div className={styles.consoleHeader}>
                <span>Job {job.id.slice(0, 8)}</span>
                <span className={styles.status}>{job.status}</span>
              </div>
              <div className={styles.events}>
                {events.map((e: WsMessage, i) => (
                  <div key={i} className={styles.event}>
                    <span className={styles.eventType}>{e.event}</span>
                    {e.payload.confidence !== undefined && (
                      <ConfidenceBadge confidence={e.payload.confidence as number} />
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
