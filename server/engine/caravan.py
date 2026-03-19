"""Caravan system — periodic arrival, cargo, information, new characters."""
from __future__ import annotations
import random
from models.world import WorldState
from models.caravan import CaravanInfo
from models.item import Item
from engine.memory import add_memory

CARAVAN_INTERVAL = 1000  # ~7 days


def check_caravan(world: WorldState):
    """Check if caravan arrives this tick. Handle arrival sequence."""
    if world.tick < world.next_caravan_tick:
        # signal approaching (a few ticks before)
        if world.tick == world.next_caravan_tick - 5:
            world.add_event("巡逻者报告：车队信号已探测到，预计很快到达")
        return

    if world.tick == world.next_caravan_tick:
        _caravan_arrives(world)


def _caravan_arrives(world: WorldState):
    """Process caravan arrival."""
    world.add_event("车队到达了！")

    info = CaravanInfo(
        news=[_random_news()],
        road_events=[_random_road_event()],
        main_city_changes=[_random_city_change()],
        cargo=_generate_cargo(),
    )
    world.last_caravan = info

    # unload cargo: create items in warehouse
    warehouse_tiles = []
    wr = world.rooms.get("warehouse")
    if wr:
        warehouse_tiles = wr.tiles

    for item_type, qty in info.cargo.items():
        for i in range(qty):
            iid = f"cargo_{world.tick}_{item_type}_{i}"
            world.items[iid] = Item(
                id=iid, name=_CARGO_NAMES.get(item_type, item_type),
                type=item_type, weight=1.0, durability=0 if item_type == "food" else -1,
                effects={"hunger": 25} if item_type == "food" else {},
            )
            if warehouse_tiles:
                tx, ty = random.choice(warehouse_tiles)
                tile = world.get_tile(tx, ty)
                if tile:
                    tile.items.append(iid)

    # distribute news to NPCs as memories
    for char in world.characters.values():
        if char.alive and not char.is_player:
            add_memory(world, char.id, f"车队到达，带来消息：{'; '.join(info.news)}",
                       mem_type="event", importance=7, source="firsthand")

    world.next_caravan_tick = world.tick + CARAVAN_INTERVAL


_CARGO_NAMES = {"food": "口粮", "medicine": "药品", "material": "材料", "tool": "工具"}


def _generate_cargo() -> dict[str, int]:
    return {
        "food": random.randint(30, 50),
        "medicine": random.randint(3, 8),
        "material": random.randint(5, 15),
    }


def _random_news() -> str:
    return random.choice([
        "主城最近扩建了新的居住区",
        "另一个矿村发现了新矿脉",
        "主城和北部中继城之间的路线修好了",
        "听说东边出现了新的生物群落",
        "主城的物资价格最近上涨了",
    ])


def _random_road_event() -> str:
    return random.choice([
        "路上一切顺利",
        "途中遭遇了小型风暴，延误了半天",
        "路上遇到了一群地表生物，绕路了",
        "有一段路面损坏严重，需要维修",
    ])


def _random_city_change() -> str:
    return random.choice([
        "主城人口增长，需要更多矿产",
        "主城新任命了一位调度长",
        "北部中继城的水源出了问题",
        "主城开始研究新的能源提炼技术",
    ])
