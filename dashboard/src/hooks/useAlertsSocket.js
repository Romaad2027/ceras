import { useEffect, useRef, useState } from 'react'

/**
 * useAlertsSocket
 * - Connects to alerts WebSocket stream
 * - Prepends each incoming alert to the local list
 * - Reconnects after 5s if disconnected unexpectedly
 */
export const useAlertsSocket = (token) => {
  const [alerts, setAlerts] = useState([])
  const [isConnected, setIsConnected] = useState(false)
  const [lastCloseCode, setLastCloseCode] = useState(null)
  const [authError, setAuthError] = useState(false)

  const socketRef = useRef(null)
  const reconnectTimerRef = useRef(null)
  const heartbeatTimerRef = useRef(null)
  const shouldReconnectRef = useRef(true)
  const tokenRef = useRef(token)
  const pathIndexRef = useRef(0)
  const hadMessageRef = useRef(false)

  useEffect(() => {
    tokenRef.current = token
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      try {
        socketRef.current.close()
      } catch (_) {}
    }
  }, [token])

  useEffect(() => {
    const resolveBaseAndPaths = () => {
      const explicitWsBase = import.meta.env?.VITE_WS_BASE_URL
      const apiBase = import.meta.env?.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
      if (explicitWsBase) {
        const base = explicitWsBase.replace(/\/$/, '')
        return { baseURL: base, paths: ['/ws/alerts'] }
      }
      let url
      try {
        url = new URL(apiBase)
      } catch {
        const protocol = typeof window !== 'undefined' && window.location?.protocol === 'https:' ? 'wss:' : 'ws:'
        return { baseURL: `${protocol}//127.0.0.1:8000/api/v1`, paths: ['/ws/alerts'] }
      }
      const wsProtocol = url.protocol === 'https:' ? 'wss:' : url.protocol === 'http:' ? 'ws:' : url.protocol
      const baseNoPath = `${wsProtocol}//${url.host}`
      return { baseURL: baseNoPath, paths: ['/api/v1/ws/alerts', '/v1/ws/alerts'] }
    }

    const { baseURL, paths } = resolveBaseAndPaths()

    const connect = () => {
      if (!tokenRef.current) return

      try {
        const path = paths[Math.max(0, Math.min(paths.length - 1, pathIndexRef.current))]
        const url = `${baseURL}${path}?token=${encodeURIComponent(tokenRef.current)}`
        const ws = new WebSocket(url)
        socketRef.current = ws

        ws.onopen = () => {
          console.log('[WS] Alerts socket connected')
          setIsConnected(true)
          setAuthError(false)
          setLastCloseCode(null)
          hadMessageRef.current = false
          if (heartbeatTimerRef.current) {
            clearInterval(heartbeatTimerRef.current)
          }
          heartbeatTimerRef.current = setInterval(() => {
            if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
              try {
                socketRef.current.send('ping')
              } catch (_) {}
            }
          }, 30000)
        }

        ws.onmessage = (event) => {
          try {
            if (typeof event.data === 'string' && (event.data === 'ping' || event.data === 'pong')) {
              return
            }
            const payload = typeof event.data === 'string' ? JSON.parse(event.data) : event.data

            const mergeUnique = (incomingList, existingList) => {
              const result = []
              const seen = new Set()
              const keyFor = (row) =>
                row?.id ??
                row?.event_id ??
                `${row?.created_at || row?.createdAt || ''}_${row?.rule_code || row?.ruleCode || row?.rule || row?.code || ''}`
              const pushIfNew = (row) => {
                const key = keyFor(row)
                if (!seen.has(key)) {
                  seen.add(key)
                  result.push(row)
                }
              }
              ;(incomingList || []).forEach(pushIfNew)
              ;(existingList || []).forEach(pushIfNew)
              return result
            }

            if (payload && payload.type === 'snapshot' && Array.isArray(payload.items)) {
              setAlerts((prev) => mergeUnique(payload.items, prev))
              hadMessageRef.current = true
              return
            }
            if (Array.isArray(payload)) {
              setAlerts((prev) => mergeUnique(payload, prev))
              hadMessageRef.current = true
              return
            }
            if (payload && typeof payload === 'object') {
              setAlerts((prev) => mergeUnique([payload], prev))
              hadMessageRef.current = true
              return
            }
          } catch (e) {
            console.error('[WS] Failed to parse/handle message', e)
          }
        }

        ws.onerror = () => {
          console.error('[WS] Alerts socket error')
        }

        ws.onclose = (evt) => {
          setLastCloseCode(evt?.code || null)
          setIsConnected(false)
          socketRef.current = null
          if (heartbeatTimerRef.current) {
            clearInterval(heartbeatTimerRef.current)
            heartbeatTimerRef.current = null
          }

          if (evt?.code === 1008) {
            setAuthError(true)
            shouldReconnectRef.current = false
            console.error('[WS] Policy violation (likely auth). Not reconnecting.')
            return
          }

          if (shouldReconnectRef.current) {
            console.log('[WS] Alerts socket closed. Reconnecting in 5s…')
            if (!hadMessageRef.current && pathIndexRef.current === 0 && paths.length > 1) {
              pathIndexRef.current = 1
            }
            if (reconnectTimerRef.current) {
              clearTimeout(reconnectTimerRef.current)
            }
            reconnectTimerRef.current = setTimeout(() => {
              connect()
            }, 5000)
          }
        }
      } catch (e) {
        console.error('[WS] Failed to establish socket', e)
      }
    }

    if (tokenRef.current) {
      connect()
    }

    return () => {
      shouldReconnectRef.current = false
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current)
      }
      if (heartbeatTimerRef.current) {
        clearInterval(heartbeatTimerRef.current)
      }
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        socketRef.current.close()
      }
      socketRef.current = null
    }
  }, [])

  return { alerts, isConnected, lastCloseCode, authError }
}

export default useAlertsSocket


