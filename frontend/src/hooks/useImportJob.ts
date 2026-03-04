import { useCallback, useState } from 'react'
import { createImportJob, submitDecision } from '../api'
import type { ImportJob, ManualDecision, WsMessage } from '../types'
import { useWebSocket } from './useWebSocket'

export function useImportJob() {
  const [job, setJob] = useState<ImportJob | null>(null)
  const [events, setEvents] = useState<WsMessage[]>([])

  const onMessage = useCallback((msg: WsMessage) => {
    setEvents(prev => [...prev, msg])
    if (msg.event === 'import_complete' || msg.event === 'import_error') {
      setJob(prev => prev ? { ...prev, status: msg.event === 'import_complete' ? 'complete' : 'error' } : prev)
    }
  }, [])

  const { connected } = useWebSocket(job ? `/ws/${job.id}` : null, onMessage)

  const startImport = useCallback(async (paths: string[]) => {
    const newJob = await createImportJob(paths)
    setJob(newJob)
    setEvents([])
  }, [])

  const decide = useCallback(async (decision: ManualDecision, searchQuery?: string) => {
    if (!job) return
    await submitDecision(job.id, decision, searchQuery)
  }, [job])

  return { job, events, connected, startImport, decide }
}
