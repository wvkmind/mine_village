"""Prompt builder — constructs AI prompts for NPC decisions."""
from __future__ import annotations
from models.world import WorldState
from models.character import Character
from engine.memory import get_decision_context
from engine.validation import get_legal_actions


def build_decision_prompt(world: WorldState, npc: Character) -> str:
    """Build the full decision prompt per desc.md section 8.2."""
    p = npc.personality
    room = world.get_room_at(npc.x, npc.y)
    room_name = room.name if room else "未知"

    # nearby characters
    nearby = []
    if room:
        for c in world.characters_in_room(room.id):
            if c.id != npc.id and c.alive:
                rel = world.get_relationship(npc.id, c.id)
                rel_str = f"(关系:{rel.value})" if rel else ""
                nearby.append(f"{c.name}{rel_str}")

    # visible items
    tile = world.get_tile(npc.x, npc.y)
    visible_items = []
    if tile:
        for iid in tile.items:
            item = world.items.get(iid)
            if item:
                visible_items.append(item.name)

    # memories
    memories = get_decision_context(world, npc.id)
    recent = [m for m in memories if m.tick >= world.tick - 12]
    permanent = [m for m in memories if m.permanent]

    # relationships with nearby
    rel_lines = []
    for c in world.characters_in_room(room.id) if room else []:
        if c.id == npc.id:
            continue
        rel = world.get_relationship(npc.id, c.id)
        if rel:
            rel_lines.append(f"  {c.name}: {rel.type}({rel.value})")

    # legal actions
    actions = get_legal_actions(world, npc)
    action_strs = []
    for a in actions:
        s = a["action"]
        if "direction" in a:
            s += f" {a['direction']}"
        if "target" in a:
            target = a["target"]
            # resolve target name
            tc = world.characters.get(target)
            ti = world.items.get(target)
            if tc:
                s += f" {tc.name}"
            elif ti:
                s += f" {ti.name}"
            else:
                s += f" {target}"
        action_strs.append(s)

    return f"""你是{npc.name}，一个生活在地下小镇的人。

【你的个性】
社交性:{p.sociability} 勤劳:{p.diligence} 胆量:{p.courage}
慷慨:{p.generosity} 诚实:{p.honesty} 好奇心:{p.curiosity}
脾气:{p.temper} 野心:{p.ambition}

【你的状态】
饱食度:{npc.hunger:.0f} 精力:{npc.energy:.0f} 健康:{npc.health:.0f}
劳动积分:{npc.labor_points}
技能:{npc.skills or '无'}
携带物品:{', '.join(world.items[i].name for i in npc.inventory if i in world.items) or '无'}

【你的位置】
{room_name}，周围有：{', '.join(nearby) or '无人'}，{', '.join(visible_items) or '无物品'}

【你的记忆】
最近发生的事：
{chr(10).join('  ' + m.content for m in recent[-6:]) or '  无'}

重要的事：
{chr(10).join('  ' + m.content for m in permanent[-6:]) or '  无'}

【你的关系】
{chr(10).join(rel_lines) or '  无特殊关系'}

【当前可选行动】
{chr(10).join('  ' + s for s in action_strs)}

请根据你的个性和当前状态，选择一个行动并简要说明理由。
输出格式：
ACTION: {{行动ID}}
TARGET: {{目标，没有则None}}
REASON: {{一句话理由}}
DIALOGUE: {{如果行动是说话，说什么；否则None}}"""


DECISION_SYSTEM = (
    "你是一个地下小镇的NPC。根据你的个性、状态和记忆做出决策。"
    "只能从可选行动中选择。输出严格按照指定格式。"
)
