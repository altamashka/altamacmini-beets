import { useState } from 'react'
import { useImportJob } from '../../hooks/useImportJob'
import { DownloadsBrowser } from './DownloadsBrowser'
import { ImportQueue } from './ImportQueue'
import { ImportConsole } from './ImportConsole'
import { ImportSummary } from './ImportSummary'
import styles from './ImportPage.module.css'

export function ImportPage() {
  const { job, events, loading, startImport, decide, reset } = useImportJob()
  const [selectedPaths, setSelectedPaths] = useState<string[]>([])

  function handleStart() {
    startImport(selectedPaths)
  }

  function handleClear() {
    setSelectedPaths([])
  }

  function renderMain() {
    if (job === null) {
      return (
        <ImportQueue
          selectedPaths={selectedPaths}
          onStart={handleStart}
          onClear={handleClear}
          loading={loading}
        />
      )
    }
    if (job.status === 'complete' || job.status === 'error') {
      return <ImportSummary job={job} events={events} onReset={reset} />
    }
    return <ImportConsole job={job} events={events} onDecide={decide} />
  }

  return (
    <div className={styles.page}>
      <h1 className={styles.title}>Import</h1>

      <div className={styles.layout}>
        {/* Left: Downloads browser */}
        <aside className={styles.sidebar}>
          <h2>Downloads</h2>
          <DownloadsBrowser onSelectionChange={setSelectedPaths} />
        </aside>

        {/* Right: Import queue / console / summary */}
        <main className={styles.main}>
          {renderMain()}
        </main>
      </div>
    </div>
  )
}
