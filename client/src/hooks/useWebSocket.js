import { useState, useEffect, useCallback, useRef } from 'react'

export default function useWebSocket(url) {
  const [state, setState] = useState(null)
  const [connected, setConnected] = useState(false)
  const wsRef = useRef(null)

  useEffect(() => {
    const ws = new WebSocket(url)
    wsRef.current = ws
    ws.onopen = () => setConnected(true)
    ws.onclose = () => setConnected(false)
    ws.onmessage = (e) => {
      try { setState(JSON.parse(e.data)) } catch {}
    }
    return () => ws.close()
  }, [url])

  const send = useCallback((data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    }
  }, [])

  return { state, connected, send }
}
