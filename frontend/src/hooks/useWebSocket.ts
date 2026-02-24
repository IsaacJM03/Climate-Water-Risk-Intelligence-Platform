import { useEffect, useRef, useState, useCallback } from 'react'
import type { WsMessage } from '../types'

const MAX_MESSAGES = 50
const PING_INTERVAL_MS = 30_000
const MAX_RETRIES = 5

function buildWsUrl(orgId: number, token: string): string {
  const base =
    import.meta.env.VITE_WS_URL ||
    (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/^http/, 'ws')
  return `${base}/ws/${orgId}?token=${token}`
}

export function useWebSocket(orgId: number | null, token: string | null) {
  const [messages, setMessages] = useState<WsMessage[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WsMessage | null>(null)

  const wsRef = useRef<WebSocket | null>(null)
  const retryCountRef = useRef(0)
  const retryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const pingTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const shouldConnectRef = useRef(false)

  const clearTimers = useCallback(() => {
    if (retryTimerRef.current) {
      clearTimeout(retryTimerRef.current)
      retryTimerRef.current = null
    }
    if (pingTimerRef.current) {
      clearInterval(pingTimerRef.current)
      pingTimerRef.current = null
    }
  }, [])

  const connect = useCallback(() => {
    if (!orgId || !token || !shouldConnectRef.current) return

    const url = buildWsUrl(orgId, token)
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      setIsConnected(true)
      retryCountRef.current = 0
      pingTimerRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping')
        }
      }, PING_INTERVAL_MS)
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data as string) as Omit<WsMessage, 'timestamp'>
        const msg: WsMessage = { ...data, timestamp: new Date().toISOString() }
        setLastMessage(msg)
        setMessages((prev) => [msg, ...prev].slice(0, MAX_MESSAGES))
      } catch {
        // pong or non-JSON frames are ignored
      }
    }

    ws.onclose = () => {
      setIsConnected(false)
      clearTimers()
      if (!shouldConnectRef.current) return
      if (retryCountRef.current < MAX_RETRIES) {
        const delay = Math.min(1000 * 2 ** retryCountRef.current, 30_000)
        retryCountRef.current += 1
        retryTimerRef.current = setTimeout(connect, delay)
      }
    }

    ws.onerror = () => {
      ws.close()
    }
  }, [orgId, token, clearTimers])

  useEffect(() => {
    if (!orgId || !token) return
    shouldConnectRef.current = true
    retryCountRef.current = 0
    connect()

    return () => {
      shouldConnectRef.current = false
      clearTimers()
      wsRef.current?.close()
    }
  }, [orgId, token, connect, clearTimers])

  return { messages, isConnected, lastMessage }
}
