import { useRef, useEffect } from 'react'

const TILE_SIZE = 16
const COLORS = {
  wall: '#111118',
  floor: '#1a1a2e',
  door: '#2a2a44',
  passage: '#2e1e1e',
}
const CHAR_COLOR = '#5588cc'
const PLAYER_COLOR = '#44cc88'
const ITEM_DOT = '#ccaa44'

export default function MapCanvas({ mapView, characters, playerPos, width, height }) {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || !mapView) return
    const ctx = canvas.getContext('2d')
    const cw = canvas.width
    const ch = canvas.height

    ctx.fillStyle = '#0a0a0f'
    ctx.fillRect(0, 0, cw, ch)

    // center on player
    const ox = Math.floor(cw / 2) - (playerPos?.x || 0) * TILE_SIZE
    const oy = Math.floor(ch / 2) - (playerPos?.y || 0) * TILE_SIZE

    // draw tiles
    for (const t of mapView) {
      const sx = ox + t.x * TILE_SIZE
      const sy = oy + t.y * TILE_SIZE
      ctx.fillStyle = COLORS[t.type] || COLORS.floor
      ctx.fillRect(sx, sy, TILE_SIZE - 1, TILE_SIZE - 1)

      // items dot
      if (t.items?.length > 0) {
        ctx.fillStyle = ITEM_DOT
        ctx.fillRect(sx + 2, sy + 2, 3, 3)
      }
    }

    // draw characters
    if (characters) {
      for (const c of characters) {
        const sx = ox + c.x * TILE_SIZE + TILE_SIZE / 2
        const sy = oy + c.y * TILE_SIZE + TILE_SIZE / 2
        ctx.fillStyle = c.id === 'player' ? PLAYER_COLOR : CHAR_COLOR
        ctx.beginPath()
        ctx.arc(sx, sy, TILE_SIZE / 3, 0, Math.PI * 2)
        ctx.fill()

        // name label
        if (c.id !== 'player') {
          ctx.fillStyle = '#888'
          ctx.font = '9px monospace'
          ctx.textAlign = 'center'
          ctx.fillText(c.name, sx, sy - TILE_SIZE / 2)
        }
      }
    }
  }, [mapView, characters, playerPos])

  return (
    <canvas
      ref={canvasRef}
      width={width || 800}
      height={height || 600}
      style={{ width: '100%', height: '100%' }}
    />
  )
}
