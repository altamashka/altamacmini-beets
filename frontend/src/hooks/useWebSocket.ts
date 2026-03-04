import { useCallback, useEffect, useRef, useState } from 'react'
import type { WsMessage } from '../types'

type Handler = (msg: WsMessage) => void

export function useWebSocket(path: string | null, onMessage: Handler) {
  const wsRef = useRef<WebSocket | null>(null)
  const [connected, setConnected] = useState(false)

  const connect = useCallback(() => {
    if (!path || wsRef.current) return
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const url = `${proto}://${window.location.host}${path}`
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => setConnected(true)
    ws.onclose = () => {
      setConnected(false)
      wsRef.current = null
    }
    ws.onmessage = (e) => {
      try {
        const msg: WsMessage = JSON.parse(e.data)
        onMessage(msg)
      } catch {
        // ignore malformed messages
      }
    }
  }, [path, onMessage])

  useEffect(() => {
    connect()
    return () => {
      wsRef.current?.close()
      wsRef.current = null
    }
  }, [connect])

  return { connected }
}
