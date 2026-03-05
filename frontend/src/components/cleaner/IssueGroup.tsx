import { useState } from 'react'
import type { AuditIssue } from '../../types'
import type { FixState } from '../../hooks/useAuditState'
import { IssueCard } from './IssueCard'
import styles from './IssueGroup.module.css'

const OPERATION_FOR_TYPE: Record<string, string> = {
  missing_artwork: 'fetchart',
  missing_metadata: 'fix_albumartist',
  bad_track_numbers: 'fix_tracknums',
  split_album: 'unify_mbids',
  duplicate_album: 'delete_album',
  broken_file: '',
}

const TYPE_LABELS: Record<string, string> = {
  missing_artwork: 'Missing Artwork',
  missing_metadata: 'Missing Metadata',
  bad_track_numbers: 'Bad Track Numbers',
  duplicate_album: 'Duplicate Albums',
  split_album: 'Split Albums',
  broken_file: 'Broken Files',
}

interface Props {
  type: string
  issues: AuditIssue[]
  fixing: Record<string, FixState>
  selected: Set<string>
  onToggleSelect: (id: string) => void
  onSelectAll: (ids: string[]) => void
  onFix: (issue: AuditIssue, operation: string) => void
}

export function IssueGroup({ type, issues, fixing, selected, onToggleSelect, onSelectAll, onFix }: Props) {
  const [open, setOpen] = useState(true)
  const operation = OPERATION_FOR_TYPE[type] ?? ''
  const fixable = issues.some(i => i.fixable) && operation

  const fixAll = () => {
    issues
      .filter(i => i.fixable && fixing[i.id] !== 'done' && fixing[i.id] !== 'pending')
      .forEach(i => onFix(i, operation))
  }

  return (
    <div className={styles.group}>
      <div className={styles.header} onClick={() => setOpen(o => !o)}>
        <span className={styles.chevron}>{open ? '▾' : '▸'}</span>
        <span className={styles.label}>{TYPE_LABELS[type] ?? type}</span>
        <span className={styles.count}>{issues.length}</span>
        {fixable && open && (
          <button
            className={styles.fixAllBtn}
            onClick={e => { e.stopPropagation(); fixAll() }}
          >
            Fix All
          </button>
        )}
        <button
          className={styles.selectAllBtn}
          onClick={e => { e.stopPropagation(); onSelectAll(issues.map(i => i.id)) }}
        >
          Select All
        </button>
      </div>
      {open && (
        <div className={styles.list}>
          {issues.map(issue => (
            <IssueCard
              key={issue.id}
              issue={issue}
              fixState={fixing[issue.id] ?? 'idle'}
              selected={selected.has(issue.id)}
              onToggleSelect={onToggleSelect}
              onFix={onFix}
            />
          ))}
        </div>
      )}
    </div>
  )
}
