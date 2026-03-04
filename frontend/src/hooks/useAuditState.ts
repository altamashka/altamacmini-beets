import { useCallback, useState } from 'react'
import { startAuditScan } from '../api'
import type { AuditIssue, WsMessage } from '../types'
import { useWebSocket } from './useWebSocket'

export function useAuditState() {
  const [scanId, setScanId] = useState<string | null>(null)
  const [issues, setIssues] = useState<AuditIssue[]>([])
  const [status, setStatus] = useState<'idle' | 'running' | 'complete'>('idle')

  const onMessage = useCallback((msg: WsMessage) => {
    if (msg.event === 'audit_progress' && msg.payload.issue) {
      setIssues(prev => [...prev, msg.payload.issue as AuditIssue])
    }
    if (msg.event === 'audit_complete') {
      setStatus('complete')
    }
  }, [])

  useWebSocket(scanId ? `/ws/${scanId}` : null, onMessage)

  const runAudit = useCallback(async () => {
    setIssues([])
    setStatus('running')
    const { scan_id } = await startAuditScan()
    setScanId(scan_id)
  }, [])

  return { scanId, issues, status, runAudit }
}
