"""Map loader — builds tile grid from high-level JSON definition.

JSON format defines rooms and corridors; this module generates the full
Tile grid, Room index, and provides pathfinding + visibility/sound queries.
"""
from __future__ import annotations
import json
from collections import deque
from models.tile import Tile, Room
from models.world import WorldState

DIRECTIONS = [(0, -1), (0, 1), (-1, 0), (1, 0)]  # N S W E


def load_map(path: str, world: WorldState):
    """Load map JSON and populate world.tiles, world.rooms, world.map_width/height."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    w = data["width"]
    h = data["height"]
    world.map_width = w
    world.map_height = h

    # fill everything with walls
    for y in range(h):
        for x in range(w):
            world.tiles[(x, y)] = Tile(x=x, y=y, type="wall")

    # carve rooms
    for rd in data["rooms"]:
        room = Room(
            id=rd["id"], name=rd["name"], type=rd["type"],
            indoor=rd.get("indoor", True), description=rd.get("description", ""),
        )
        rx, ry = rd["x"], rd["y"]
        rw, rh = rd["w"], rd["h"]
        for dy in range(rh):
            for dx in range(rw):
                tx, ty = rx + dx, ry + dy
                if 0 <= tx < w and 0 <= ty < h:
                    world.tiles[(tx, ty)] = Tile(x=tx, y=ty, type="floor", room_id=room.id)
                    room.tiles.append((tx, ty))
        world.rooms[room.id] = room

    # carve corridors
    for cd in data.get("corridors", []):
        _carve_corridor(world, cd, w, h)

    # place doors
    for dd in data.get("doors", []):
        tx, ty = dd["x"], dd["y"]
        t = world.tiles.get((tx, ty))
        if t:
            t.type = "door"
            # door belongs to adjacent room if any
            if not t.room_id:
                for dx, dy in DIRECTIONS:
                    adj = world.tiles.get((tx + dx, ty + dy))
                    if adj and adj.room_id:
                        t.room_id = adj.room_id
                        break

    # mark exits (surface passages)
    for ex in data.get("exits", []):
        tx, ty = ex["x"], ex["y"]
        t = world.tiles.get((tx, ty))
        if t:
            t.type = "passage"


def _carve_corridor(world: WorldState, cd: dict, map_w: int, map_h: int):
    """Carve a corridor defined by a list of waypoints."""
    points = cd["points"]  # [[x,y], [x,y], ...]
    width = cd.get("width", 1)
    corridor_id = cd.get("id")

    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        # horizontal or vertical segment
        if x1 == x2:  # vertical
            for y in range(min(y1, y2), max(y1, y2) + 1):
                for dw in range(width):
                    tx = x1 + dw
                    if 0 <= tx < map_w and 0 <= y < map_h:
                        t = world.tiles.get((tx, y))
                        if t and t.type == "wall":
                            t.type = "floor"
                            if corridor_id:
                                t.room_id = corridor_id
        else:  # horizontal
            for x in range(min(x1, x2), max(x1, x2) + 1):
                for dw in range(width):
                    ty = y1 + dw
                    if 0 <= x < map_w and 0 <= ty < map_h:
                        t = world.tiles.get((x, ty))
                        if t and t.type == "wall":
                            t.type = "floor"
                            if corridor_id:
                                t.room_id = corridor_id

    # register corridor as a room if it has an id
    if corridor_id and corridor_id not in world.rooms:
        tiles = [(x, y) for (x, y), t in world.tiles.items()
                 if t.room_id == corridor_id]
        world.rooms[corridor_id] = Room(
            id=corridor_id, name=cd.get("name", corridor_id),
            type="corridor", tiles=tiles, indoor=True,
        )


# ── Pathfinding ──────────────────────────────────────────────────────

def find_path(world: WorldState, sx: int, sy: int, ex: int, ey: int) -> list[tuple[int, int]] | None:
    """BFS shortest path. Returns list of (x,y) including start and end, or None."""
    if (sx, sy) == (ex, ey):
        return [(sx, sy)]
    start = (sx, sy)
    end = (ex, ey)
    visited = {start}
    queue = deque([(start, [start])])
    while queue:
        (cx, cy), path = queue.popleft()
        for dx, dy in DIRECTIONS:
            nx, ny = cx + dx, cy + dy
            if (nx, ny) == end:
                return path + [end]
            if (nx, ny) in visited:
                continue
            t = world.tiles.get((nx, ny))
            if t and t.type != "wall":
                visited.add((nx, ny))
                queue.append(((nx, ny), path + [(nx, ny)]))
    return None


def distance(world: WorldState, sx: int, sy: int, ex: int, ey: int) -> int:
    """Path distance in tiles. Returns -1 if unreachable."""
    p = find_path(world, sx, sy, ex, ey)
    return len(p) - 1 if p else -1


# ── Visibility & Sound ───────────────────────────────────────────────

def can_see(world: WorldState, ax: int, ay: int, bx: int, by: int) -> bool:
    """Can character at (ax,ay) see (bx,by)?
    Same room: yes. Adjacent room through door: yes. Otherwise: no."""
    ta = world.tiles.get((ax, ay))
    tb = world.tiles.get((bx, by))
    if not ta or not tb:
        return False
    # same room
    if ta.room_id and ta.room_id == tb.room_id:
        return True
    # through a door: check if any door tile is adjacent to both rooms
    if ta.room_id and tb.room_id:
        for (dx, dy), t in world.tiles.items():
            if t.type == "door":
                a_adj = any(world.tiles.get((dx + ox, dy + oy)) and
                            world.tiles[(dx + ox, dy + oy)].room_id == ta.room_id
                            for ox, oy in DIRECTIONS)
                b_adj = any(world.tiles.get((dx + ox, dy + oy)) and
                            world.tiles[(dx + ox, dy + oy)].room_id == tb.room_id
                            for ox, oy in DIRECTIONS)
                if a_adj and b_adj:
                    return True
    return False


def sound_level(world: WorldState, source_x: int, source_y: int,
                listener_x: int, listener_y: int) -> str:
    """How well can listener hear source? Returns 'full', 'partial', 'none'."""
    ts = world.tiles.get((source_x, source_y))
    tl = world.tiles.get((listener_x, listener_y))
    if not ts or not tl:
        return "none"
    if ts.room_id and ts.room_id == tl.room_id:
        return "full"
    if can_see(world, source_x, source_y, listener_x, listener_y):
        return "partial"
    return "none"
