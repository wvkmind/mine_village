"""WebSocket API — game server with real-time communication."""
from __future__ import annotations
import json, os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from models.world import WorldState
from models.character import Character, Personality
from engine.tick import advance
from engine.actions import Action
from engine.map_loader import load_map
from engine.events import check_events
from engine.caravan import check_caravan
from engine.memory import mark_for_compression
from ai.decision import get_npc_action
from state import save_world, load_world

app = FastAPI(title="Mine Village")

# Global game state
_world: WorldState | None = None
_connections: list[WebSocket] = []

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
TICKS_PER_DAY = 144


def _init_world() -> WorldState:
    """Initialize a fresh world from data files."""
    w = WorldState()
    load_map(os.path.join(DATA_DIR, "init_map.json"), w)

    # load NPCs
    with open(os.path.join(DATA_DIR, "init_npcs.json"), encoding="utf-8") as f:
        npc_data = json.load(f)

    for nd in npc_data["npcs"]:
        p = Personality(**nd["personality"])
        c = Character(
            id=nd["id"], name=nd["name"], role=nd.get("role", ""),
            x=nd["x"], y=nd["y"], personality=p,
            skills=nd.get("skills", {}),
            hunger=80, energy=80, health=100,
        )
        w.characters[c.id] = c
        # seed memories
        from engine.memory import add_memory
        for mem_text in nd.get("memories", []):
            add_memory(w, c.id, mem_text, mem_type="event", importance=8)

    # load relationships
    from models.relationship import Relationship
    for rd in npc_data.get("relationships", []):
        w.relationships.append(Relationship(
            character_a=rd["a"], character_b=rd["b"],
            value=rd["value"], type=rd["type"],
        ))

    # load item definitions and place initial items
    with open(os.path.join(DATA_DIR, "init_items.json"), encoding="utf-8") as f:
        item_data = json.load(f)

    from models.item import Item
    # stock warehouse with initial supplies
    wr = w.rooms.get("warehouse")
    wt = wr.tiles if wr else []
    import random
    for idef in item_data["items"]:
        for i in range(3):  # 3 of each to start
            iid = f"{idef['id']}_{i}"
            w.items[iid] = Item(**{**idef, "id": iid})
            if wt:
                tx, ty = random.choice(wt)
                tile = w.get_tile(tx, ty)
                if tile:
                    tile.items.append(iid)

    # give NPCs some starting items
    for char in w.characters.values():
        if char.role == "矿工":
            pid = f"pickaxe_{char.id}"
            w.items[pid] = Item(id=pid, name="矿镐", type="tool", weight=3.0, durability=50)
            char.inventory.append(pid)
        # everyone gets a ration
        rid = f"ration_{char.id}"
        w.items[rid] = Item(id=rid, name="口粮", type="food", weight=0.5, durability=0, effects={"hunger": 20})
        char.inventory.append(rid)

    w.add_event("世界初始化完成")
    save_world(w)
    return w


def _get_world() -> WorldState:
    global _world
    if _world is None:
        try:
            _world = load_world()
        except FileNotFoundError:
            _world = _init_world()
    return _world


def _build_state_for_player(w: WorldState) -> dict:
    """Build the per-tick state push for the player."""
    player = w.characters.get(w.player_id) if w.player_id else None
    if not player:
        return {"tick": w.tick, "status": "no_player", "events": w.events}

    # visible map: tiles in same room + adjacent rooms through doors
    room = w.get_room_at(player.x, player.y)
    visible_tiles = []
    if room:
        for tx, ty in room.tiles:
            t = w.get_tile(tx, ty)
            if t:
                visible_tiles.append({"x": tx, "y": ty, "type": t.type,
                                       "room": t.room_id, "items": t.items,
                                       "occupants": t.occupants})

    # visible characters
    chars_visible = []
    if room:
        for c in w.characters_in_room(room.id):
            if c.alive:
                chars_visible.append({
                    "id": c.id, "name": c.name, "x": c.x, "y": c.y,
                    "role": c.role, "action": c.current_action,
                })

    # player status (descriptive, not numeric)
    def _desc(val, thresholds):
        for t, d in thresholds:
            if val < t:
                return d
        return thresholds[-1][1]

    status = {
        "hunger": _desc(player.hunger, [(10, "快饿死了"), (30, "很饿"), (60, "有点饿"), (100, "不饿")]),
        "energy": _desc(player.energy, [(5, "快晕了"), (20, "很累"), (50, "有点累"), (100, "精力充沛")]),
        "health": _desc(player.health, [(20, "伤势严重"), (50, "身体不适"), (80, "还行"), (100, "健康")]),
    }

    return {
        "tick": w.tick,
        "map_view": visible_tiles,
        "characters_visible": chars_visible,
        "player_status": status,
        "player_pos": {"x": player.x, "y": player.y},
        "events": w.events,
    }


async def _broadcast(data: dict):
    for ws in _connections[:]:
        try:
            await ws.send_json(data)
        except Exception:
            _connections.remove(ws)


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    _connections.append(ws)
    w = _get_world()

    # create player character if needed
    if not w.player_id:
        player = Character(id="player", name="旅人", is_player=True, x=14, y=3)
        w.characters["player"] = player
        w.player_id = "player"
        w.add_event("一个陌生人跟着车队到达了村子")

    # send initial state
    await ws.send_json(_build_state_for_player(w))

    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)

            # parse player action
            player_action = None
            action_type = msg.get("action", "wait")
            if action_type == "move":
                player_action = Action.move("player", msg.get("direction", "north"))
            elif action_type == "talk":
                player_action = Action.talk("player", msg.get("target", ""), msg.get("message", ""))
            elif action_type == "pickup":
                player_action = Action.pickup("player", msg.get("target", ""))
            elif action_type == "eat":
                player_action = Action.eat("player", msg.get("target", ""))
            elif action_type == "attack":
                player_action = Action.attack("player", msg.get("target", ""))
            elif action_type == "wait":
                player_action = Action.wait("player")
            else:
                player_action = Action.wait("player")

            # gather NPC AI decisions
            ai_decisions = {}
            for char in w.characters.values():
                if not char.is_player and not char.is_dead and not char.is_busy:
                    ai_decisions[char.id] = get_npc_action(w, char)

            # advance one tick
            advance(w, player_action=player_action, ai_decisions=ai_decisions)
            check_events(w)
            check_caravan(w)

            # day boundary: compress memories
            if w.tick % TICKS_PER_DAY == 0:
                mark_for_compression(w)

            # autosave
            if w.tick % 100 == 0:
                save_world(w)

            # broadcast state
            state = _build_state_for_player(w)
            await _broadcast(state)

    except WebSocketDisconnect:
        _connections.remove(ws)


@app.get("/api/init")
async def init_world():
    """Force re-initialize world."""
    global _world
    _world = _init_world()
    return {"status": "ok", "tick": _world.tick}


@app.get("/api/state")
async def get_state():
    """Get current world state summary."""
    w = _get_world()
    return {
        "tick": w.tick,
        "characters": len(w.characters),
        "items": len(w.items),
        "events": w.events[-10:],
    }
