/**
 * Library Cleaner Page — Phase 3 will fill in full implementation.
 * Scaffold only: audit trigger + issue list shell.
 */
import { useAuditState } from '../../hooks/useAuditState'
import { ProgressBar } from '../shared/ProgressBar'
import styles from './CleanerPage.module.css'

export function CleanerPage() {
  const { issues, status, runAudit } = useAuditState()

  return (
    <div className={styles.page}>
      <h1 className={styles.title}>Library Cleaner</h1>

      <div className={styles.controls}>
        <button
          className={styles.btn}
          onClick={runAudit}
          disabled={status === 'running'}
        >
          {status === 'running' ? 'Scanning…' : 'Run Audit Scan'}
        </button>
        {status !== 'idle' && (
          <span className={styles.count}>{issues.length} issues found</span>
        )}
      </div>

      {status === 'running' && (
        <ProgressBar value={-1} label="Scanning library…" />
      )}

      <div className={styles.issues}>
        {issues.length === 0 && status === 'complete' && (
          <p className={styles.empty}>No issues found.</p>
        )}
        {issues.map(issue => (
          <div key={issue.id} className={styles.issue}>
            <span className={styles.issueType}>{issue.type}</span>
            <span className={styles.issueDesc}>{issue.description}</span>
            {issue.fixable && (
              <button className={styles.fixBtn}>Fix</button>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
