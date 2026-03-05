import type { AuditIssue } from '../../types'
import type { FixState } from '../../hooks/useAuditState'
import styles from './IssueCard.module.css'

const OPERATION_FOR_TYPE: Record<string, string> = {
  missing_artwork: 'fetchart',
  missing_metadata: 'fix_albumartist',
  bad_track_numbers: 'fix_tracknums',
  split_album: 'unify_mbids',
  duplicate_album: 'delete_album',
  broken_file: '',
}

interface Props {
  issue: AuditIssue
  fixState: FixState
  selected: boolean
  onToggleSelect: (id: string) => void
  onFix: (issue: AuditIssue, operation: string) => void
}

export function IssueCard({ issue, fixState, selected, onToggleSelect, onFix }: Props) {
  const operation = OPERATION_FOR_TYPE[issue.type] ?? ''

  return (
    <div className={`${styles.card} ${fixState === 'done' ? styles.done : ''}`}>
      <input
        type="checkbox"
        checked={selected}
        onChange={() => onToggleSelect(issue.id)}
        className={styles.checkbox}
      />
      <div className={styles.body}>
        <span className={`${styles.typeBadge} ${styles[issue.type]}`}>
          {issue.type.replace(/_/g, ' ')}
        </span>
        <span className={styles.description}>{issue.description}</span>
      </div>
      {issue.fixable && operation && fixState !== 'done' && (
        <button
          className={`${styles.fixBtn} ${fixState === 'pending' ? styles.pending : ''} ${fixState === 'error' ? styles.error : ''}`}
          onClick={() => onFix(issue, operation)}
          disabled={fixState === 'pending'}
        >
          {fixState === 'pending' ? 'Fixing…' : fixState === 'error' ? 'Retry' : 'Fix'}
        </button>
      )}
      {fixState === 'done' && <span className={styles.doneLabel}>✓ Fixed</span>}
    </div>
  )
}
