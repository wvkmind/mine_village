import { useState, useEffect, useRef } from 'react'
import MapCanvas from './canvas/MapCanvas'
import useWebSocket from './hooks/useWebSocket'

const WS_URL = `ws://${location.hostname}:8000/ws`

const KEY_MAP = { ArrowUp: 'north', ArrowDown: 'south', ArrowLeft: 'west', ArrowRight: 'east',
                  w: 'north', s: 'south', a: 'west', d: 'east' }

export default function App() {
  const { state, connected, send } = useWebSocket(WS_URL)
  const [events, setEvents] = useState([])
  const [chatText, setChatText] = useState('')
  const [chatTarget, setChatTarget] = useState(null)
  const eventRef = useRef(null)

  // accumulate events
  useEffect(() => {
    if (state?.events?.length) {
      setEvents(prev => [...prev.slice(-80), ...state.events])
    }
  }, [state])

  // auto-scroll events
  useEffect(() => {
    if (eventRef.current) eventRef.current.scrollTop = eventRef.current.scrollHeight
  }, [events])

  // keyboard movement
  useEffect(() => {
    const handler = (e) => {
      const dir = KEY_MAP[e.key]
      if (dir) { send({ action: 'move', direction: dir }); e.preventDefault() }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [send])

  const doAction = (action, extra = {}) => send({ action, ...extra })

  const sendChat = () => {
    if (chatText.trim() && chatTarget) {
      send({ action: 'talk', target: chatTarget, message: chatText })
      setChatText('')
    }
  }

  const status = state?.player_status || {}
  const chars = state?.characters_visible || []
  const npcsNearby = chars.filter(c => c.id !== 'player')

  const statusClass = (text) => {
    if (!text) return 'ok'
    if (text.includes('死') || text.includes('快')) return 'danger'
    if (text.includes('很') || text.includes('严重')) return 'warn'
    return 'ok'
  }

  return (
    <div className="game-container">
      <div className="map-panel">
        <div className="tick-display">
          {connected ? `Tick ${state?.tick || 0}` : '连接中...'}
        </div>
        <MapCanvas
          mapView={state?.map_view}
          characters={chars}
          playerPos={state?.player_pos}
          width={800}
          height={600}
        />
      </div>

      <div className="side-panel">
        {/* Status */}
        <div className="status-bar">
          <h3>状态</h3>
          <div className={`status-item ${statusClass(status.hunger)}`}>
            饥饿：{status.hunger || '—'}
          </div>
          <div className={`status-item ${statusClass(status.energy)}`}>
            精力：{status.energy || '—'}
          </div>
          <div className={`status-item ${statusClass(status.health)}`}>
            健康：{status.health || '—'}
          </div>
        </div>

        {/* Event log */}
        <div className="event-log" ref={eventRef}>
          <h3>事件</h3>
          {events.map((e, i) => (
            <div key={i} className="event-entry">{e}</div>
          ))}
        </div>

        {/* Actions */}
        <div className="action-bar">
          <h3>行动</h3>
          <div className="action-buttons">
            <button className="action-btn" onClick={() => doAction('move', { direction: 'north' })}>↑北</button>
            <button className="action-btn" onClick={() => doAction('move', { direction: 'south' })}>↓南</button>
            <button className="action-btn" onClick={() => doAction('move', { direction: 'west' })}>←西</button>
            <button className="action-btn" onClick={() => doAction('move', { direction: 'east' })}>→东</button>
            <button className="action-btn" onClick={() => doAction('wait')}>等待</button>
            <button className="action-btn" onClick={() => doAction('eat')}>吃东西</button>
          </div>

          {/* Nearby NPCs for interaction */}
          {npcsNearby.length > 0 && (
            <>
              <h3 style={{ marginTop: 8 }}>附近的人</h3>
              <div className="action-buttons">
                {npcsNearby.map(c => (
                  <button key={c.id} className="action-btn"
                    onClick={() => setChatTarget(c.id)}
                    style={chatTarget === c.id ? { borderColor: '#5588cc' } : {}}>
                    {c.name}{c.role ? `(${c.role})` : ''}
                  </button>
                ))}
              </div>
            </>
          )}

          {/* Chat input */}
          {chatTarget && (
            <div className="chat-input">
              <input
                value={chatText}
                onChange={e => setChatText(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && sendChat()}
                placeholder={`对 ${npcsNearby.find(c => c.id === chatTarget)?.name || chatTarget} 说...`}
              />
              <button onClick={sendChat}>说</button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
