import { ConfidenceBadge } from '../shared/ConfidenceBadge'
import { MetadataDiff } from '../shared/MetadataDiff'
import type { AlbumMatchPayload, ManualDecision } from '../../types'
import styles from './LowConfidenceAlert.module.css'

interface Candidate {
  artist?: string
  album?: string
  year?: number
  confidence?: number
}

interface Props {
  payload: AlbumMatchPayload & { candidates?: Candidate[] }
  onDecide: (decision: ManualDecision) => void
}

export function LowConfidenceAlert({ payload, onDecide }: Props) {
  const candidates = payload.candidates?.slice(0, 5) ?? []

  return (
    <div className={styles.alert}>
      <div className={styles.alertHeader}>
        <span className={styles.alertIcon}>⚠</span>
        <span className={styles.alertTitle}>Low confidence match — manual decision required</span>
        <ConfidenceBadge confidence={payload.confidence} />
      </div>

      <div className={styles.diffSection}>
        <MetadataDiff before={payload.before} after={payload.after} />
      </div>

      {candidates.length > 0 && (
        <div className={styles.candidates}>
          <p className={styles.candidatesLabel}>Alternative candidates:</p>
          <ul className={styles.candidateList}>
            {candidates.map((c, i) => (
              <li key={i} className={styles.candidateItem}>
                <span className={styles.candidateIdx}>{i + 1}.</span>
                <span className={styles.candidateInfo}>
                  {c.artist ?? '?'} — {c.album ?? '?'}
                  {c.year != null && <span className={styles.candidateYear}> ({c.year})</span>}
                </span>
                {c.confidence != null && (
                  <ConfidenceBadge confidence={c.confidence} />
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className={styles.actions}>
        <button
          className={`${styles.actionBtn} ${styles.applyBtn}`}
          onClick={() => onDecide('apply')}
        >
          Apply
        </button>
        <button
          className={`${styles.actionBtn} ${styles.skipBtn}`}
          onClick={() => onDecide('skip')}
        >
          Skip
        </button>
        <button
          className={`${styles.actionBtn} ${styles.asIsBtn}`}
          onClick={() => onDecide('as_is')}
        >
          Import As-Is
        </button>
        <button
          className={`${styles.actionBtn} ${styles.searchBtn}`}
          disabled
          title="Search — Phase 3"
        >
          Search
        </button>
      </div>
    </div>
  )
}
