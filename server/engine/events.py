"""Environment events — storms, creatures, equipment failure, disease."""
from __future__ import annotations
import random
from models.world import WorldState
from models.creature import Creature, Disease

STORM_CHANCE_PER_TICK = 0.005  # ~0.5% per tick
DISEASE_CHANCE_PER_TICK = 0.001  # per character per tick
EQUIPMENT_FAIL_BASE = 0.02  # per use tick


def check_events(world: WorldState):
    """Run all environment event checks for this tick."""
    _check_storm(world)
    _check_creatures(world)
    _check_disease(world)
    _tick_diseases(world)


def _check_storm(world: WorldState):
    if random.random() < STORM_CHANCE_PER_TICK:
        world.add_event("地表风暴来袭！地面出入口暂时危险")
        # mark surface passage tiles as hazardous (simplified: just log)


def _check_creatures(world: WorldState):
    """Occasionally spawn creatures near surface passages."""
    if random.random() < 0.003:
        cid = f"creature_{world.tick}"
        # spawn near a random exit
        exits = [(x, y) for (x, y), t in world.tiles.items() if t.type == "passage"]
        if exits:
            ex, ey = random.choice(exits)
            c = Creature(id=cid, type="地表生物", x=ex, y=ey,
                         attack=4 + random.random() * 4,
                         defense=2 + random.random() * 3,
                         health=30 + random.random() * 20,
                         loot=["bio_material"],
                         medicinal_value="地下病")
            world.creatures[cid] = c
            world.add_event(f"一只地表生物出现在({ex},{ey})附近")


def check_equipment_failure(world: WorldState, char_id: str, skill_level: int) -> bool:
    """Check if equipment fails during use. Returns True if failure."""
    chance = EQUIPMENT_FAIL_BASE * (1 - skill_level / 150)
    if random.random() < chance:
        world.add_event(f"{char_id} 使用的设备发生故障")
        return True
    return False


def _check_disease(world: WorldState):
    for char in world.characters.values():
        if not char.alive or char.is_player:
            continue
        if random.random() < DISEASE_CHANCE_PER_TICK:
            if char.id not in world.active_diseases:
                world.active_diseases[char.id] = []
            d = Disease(
                id=f"disease_{world.tick}_{char.id}",
                name="地下病",
                severity=random.randint(2, 6),
                health_drain_per_tick=0.1 * random.randint(1, 3),
                cure_material="bio_material",
                tick_contracted=world.tick,
            )
            world.active_diseases[char.id].append(d)
            world.add_event(f"{char.name} 感染了{d.name}")


def _tick_diseases(world: WorldState):
    for char_id, diseases in list(world.active_diseases.items()):
        char = world.characters.get(char_id)
        if not char or not char.alive:
            continue
        for d in diseases:
            char.health = max(0, char.health - d.health_drain_per_tick)
        if char.health <= 0:
            char.alive = False
            world.add_event(f"{char.name} 因疾病死亡")
