import { Navigate, Route, Routes } from 'react-router-dom'
import { Sidebar } from './components/layout/Sidebar'
import { StatusBar } from './components/layout/StatusBar'
import { ImportPage } from './components/import/ImportPage'
import { CleanerPage } from './components/cleaner/CleanerPage'
import styles from './App.module.css'

export default function App() {
  return (
    <div className={styles.shell}>
      <Sidebar />
      <div className={styles.content}>
        <main className={styles.main}>
          <Routes>
            <Route path="/" element={<Navigate to="/import" replace />} />
            <Route path="/import" element={<ImportPage />} />
            <Route path="/cleaner" element={<CleanerPage />} />
          </Routes>
        </main>
        <StatusBar />
      </div>
    </div>
  )
}
