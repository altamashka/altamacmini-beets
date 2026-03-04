import { useCallback, useState } from 'react'
import { createImportJob, submitDecision } from '../api'
import type { AlbumMatchPayload, ImportJob, ManualDecision, WsMessage } from '../types'
import { useWebSocket } from './useWebSocket'

export function useImportJob() {
  const [job, setJob] = useState<ImportJob | null>(null)
  const [events, setEvents] = useState<WsMessage[]>([])
  const [loading, setLoading] = useState(false)

  const onMessage = useCallback((msg: WsMessage) => {
    setEvents(prev => [...prev, msg])

    if (msg.event === 'import_complete') {
      setJob(prev => prev ? { ...prev, status: 'complete', pending_decision: undefined } : prev)
    } else if (msg.event === 'import_error') {
      const errPayload = msg.payload as { message?: string }
      setJob(prev =>
        prev
          ? { ...prev, status: 'error', error: errPayload.message, pending_decision: undefined }
          : prev
      )
    } else if (msg.event === 'album_decision_needed') {
      const payload = msg.payload as unknown as AlbumMatchPayload
      setJob(prev =>
        prev ? { ...prev, status: 'waiting_decision', pending_decision: payload } : prev
      )
    } else if (msg.event === 'album_applying') {
      // Decision accepted — clear pending state, resume running
      setJob(prev =>
        prev ? { ...prev, status: 'running', pending_decision: undefined } : prev
      )
    } else if (msg.event === 'album_complete') {
      const p = msg.payload as { albums_done?: number; albums_total?: number }
      setJob(prev =>
        prev
          ? {
              ...prev,
              albums_done: p.albums_done ?? prev.albums_done + 1,
              albums_total: p.albums_total ?? prev.albums_total,
            }
          : prev
      )
    } else if (msg.event === 'album_skipped') {
      const p = msg.payload as { albums_skipped?: number }
      setJob(prev =>
        prev
          ? {
              ...prev,
              albums_skipped: p.albums_skipped ?? prev.albums_skipped + 1,
            }
          : prev
      )
    } else if (msg.event === 'import_started') {
      const p = msg.payload as { albums_total?: number }
      setJob(prev =>
        prev
          ? { ...prev, status: 'running', albums_total: p.albums_total ?? prev.albums_total }
          : prev
      )
    }
  }, [])

  const { connected } = useWebSocket(job ? `/ws/${job.id}` : null, onMessage)

  const startImport = useCallback(async (paths: string[]) => {
    setLoading(true)
    try {
      const newJob = await createImportJob(paths)
      setJob(newJob)
      setEvents([])
    } finally {
      setLoading(false)
    }
  }, [])

  const decide = useCallback(async (decision: ManualDecision, searchQuery?: string) => {
    if (!job) return
    await submitDecision(job.id, decision, searchQuery)
    // Optimistically clear waiting state
    setJob(prev =>
      prev ? { ...prev, status: 'running', pending_decision: undefined } : prev
    )
  }, [job])

  return { job, events, connected, loading, startImport, decide }
}
