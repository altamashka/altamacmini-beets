import { useCallback, useState } from 'react'
import { startAuditScan, startFix } from '../api'
import type { AuditIssue, WsMessage } from '../types'
import { useWebSocket } from './useWebSocket'

export type FixState = 'idle' | 'pending' | 'done' | 'error'

export function useAuditState() {
  const [scanId, setScanId] = useState<string | null>(null)
  const [issues, setIssues] = useState<AuditIssue[]>([])
  const [status, setStatus] = useState<'idle' | 'running' | 'complete'>('idle')
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [fixing, setFixing] = useState<Record<string, FixState>>({})

  const onMessage = useCallback((msg: WsMessage) => {
    if (msg.event === 'audit_progress' && msg.payload.issue) {
      setIssues(prev => [...prev, msg.payload.issue as AuditIssue])
    }
    if (msg.event === 'audit_complete') {
      setStatus('complete')
    }
  }, [])

  useWebSocket(scanId ? `/api/audit/ws/${scanId}` : null, onMessage)

  const runAudit = useCallback(async () => {
    setIssues([])
    setSelected(new Set())
    setFixing({})
    setStatus('running')
    const { scan_id } = await startAuditScan()
    setScanId(scan_id)
  }, [])

  const toggleSelect = useCallback((id: string) => {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }, [])

  const selectAll = useCallback((ids: string[]) => {
    setSelected(prev => {
      const next = new Set(prev)
      ids.forEach(id => next.add(id))
      return next
    })
  }, [])

  const clearSelection = useCallback(() => setSelected(new Set()), [])

  const fixIssue = useCallback(async (issue: AuditIssue, operation: string) => {
    const albumId = issue.album_id ?? issue.album_ids?.[0]
    if (!albumId) return
    setFixing(prev => ({ ...prev, [issue.id]: 'pending' }))
    try {
      const { fix_id } = await startFix({
        issue_ids: [issue.id],
        operation,
        params: { album_id: albumId },
      })
      const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
      const ws = new WebSocket(`${proto}://${window.location.host}/api/fix/ws/${fix_id}`)
      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data) as WsMessage
          if (msg.event === 'fix_complete') {
            setFixing(prev => ({ ...prev, [issue.id]: 'done' }))
            ws.close()
          } else if (msg.event === 'fix_error') {
            setFixing(prev => ({ ...prev, [issue.id]: 'error' }))
            ws.close()
          }
        } catch { /* ignore */ }
      }
      ws.onerror = () => setFixing(prev => ({ ...prev, [issue.id]: 'error' }))
    } catch {
      setFixing(prev => ({ ...prev, [issue.id]: 'error' }))
    }
  }, [])

  return { scanId, issues, status, selected, fixing, runAudit, toggleSelect, selectAll, clearSelection, fixIssue }
}
