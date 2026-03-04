import { useEffect, useState } from 'react'
import { fetchHealth } from '../../api'
import styles from './StatusBar.module.css'

export function StatusBar() {
  const [db, setDb] = useState<string>('checking')

  useEffect(() => {
    fetchHealth()
      .then(h => setDb(h.library_db))
      .catch(() => setDb('error'))
  }, [])

  return (
    <div className={styles.bar}>
      <span className={`${styles.dot} ${db === 'connected' ? styles.ok : styles.err}`} />
      beets DB: {db}
    </div>
  )
}
