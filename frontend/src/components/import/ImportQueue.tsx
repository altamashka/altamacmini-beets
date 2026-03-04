import styles from './ImportQueue.module.css'

interface Props {
  selectedPaths: string[]
  onStart: () => void
  onClear: () => void
  loading: boolean
}

function basename(path: string): string {
  return path.replace(/\/$/, '').split('/').slice(-2).join('/')
}

export function ImportQueue({ selectedPaths, onStart, onClear, loading }: Props) {
  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>Import Queue</h2>
        {selectedPaths.length > 0 && (
          <button className={styles.clearBtn} onClick={onClear} disabled={loading}>
            Clear
          </button>
        )}
      </div>

      {selectedPaths.length === 0 ? (
        <p className={styles.empty}>
          Select folders from the downloads panel to queue them for import.
        </p>
      ) : (
        <ul className={styles.list}>
          {selectedPaths.map(p => (
            <li key={p} className={styles.item}>
              <span className={styles.folderIcon}>📁</span>
              <span className={styles.path} title={p}>{basename(p)}</span>
            </li>
          ))}
        </ul>
      )}

      <button
        className={styles.startBtn}
        disabled={selectedPaths.length === 0 || loading}
        onClick={onStart}
      >
        {loading ? (
          <><span className={styles.spinner} /> Starting…</>
        ) : (
          `Start Import${selectedPaths.length > 0 ? ` (${selectedPaths.length})` : ''}`
        )}
      </button>
    </div>
  )
}
