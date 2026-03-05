import { useMemo } from 'react'
import type { AuditIssue } from '../../types'
import { useAuditState } from '../../hooks/useAuditState'
import { ProgressBar } from '../shared/ProgressBar'
import { IssueGroup } from './IssueGroup'
import styles from './CleanerPage.module.css'

const ISSUE_TYPE_ORDER = [
  'missing_artwork',
  'missing_metadata',
  'bad_track_numbers',
  'duplicate_album',
  'split_album',
  'broken_file',
]

export function CleanerPage() {
  const {
    issues, status, selected, fixing,
    runAudit, toggleSelect, selectAll, clearSelection, fixIssue,
  } = useAuditState()

  const grouped = useMemo(() => {
    const map: Record<string, AuditIssue[]> = {}
    for (const issue of issues) {
      if (!map[issue.type]) map[issue.type] = []
      map[issue.type].push(issue)
    }
    return map
  }, [issues])

  const orderedTypes = ISSUE_TYPE_ORDER.filter(t => grouped[t]?.length)

  return (
    <div className={styles.page}>
      <div className={styles.topBar}>
        <h1 className={styles.title}>Library Cleaner</h1>
        <div className={styles.controls}>
          <button
            className={styles.scanBtn}
            onClick={runAudit}
            disabled={status === 'running'}
          >
            {status === 'running' ? 'Scanning…' : 'Run Audit Scan'}
          </button>
          {status !== 'idle' && (
            <span className={styles.summary}>
              {issues.length} issue{issues.length !== 1 ? 's' : ''}
              {selected.size > 0 && ` · ${selected.size} selected`}
            </span>
          )}
          {selected.size > 0 && (
            <button className={styles.clearBtn} onClick={clearSelection}>
              Clear selection
            </button>
          )}
        </div>
      </div>

      {status === 'running' && (
        <ProgressBar value={-1} label="Scanning library…" />
      )}

      {status === 'complete' && issues.length === 0 && (
        <p className={styles.empty}>No issues found — library looks clean!</p>
      )}

      <div className={styles.groups}>
        {orderedTypes.map(type => (
          <IssueGroup
            key={type}
            type={type}
            issues={grouped[type]}
            fixing={fixing}
            selected={selected}
            onToggleSelect={toggleSelect}
            onSelectAll={selectAll}
            onFix={fixIssue}
          />
        ))}
      </div>
    </div>
  )
}
