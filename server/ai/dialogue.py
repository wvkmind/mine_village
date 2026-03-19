"""Dialogue generation — NPC-NPC and NPC-player conversations."""
from __future__ import annotations
from models.world import WorldState
from models.character import Character
from engine.memory import add_memory, propagate_info
from engine.map_loader import sound_level
from ai import poe_client

DIALOGUE_SYSTEM = (
    "你正在扮演一个地下小镇的居民进行对话。"
    "根据你的个性和与对方的关系说话。保持简短自然。用中文。"
)


def generate_npc_dialogue(world: WorldState, speaker: Character,
                          listener: Character) -> str | None:
    """Generate what speaker says to listener. Returns dialogue text or None."""
    rel = world.get_relationship(speaker.id, listener.id)
    rel_str = f"关系:{rel.type}({rel.value})" if rel else "陌生人"
    p = speaker.personality

    prompt = (
        f"你是{speaker.name}（{speaker.role}），正在和{listener.name}说话。\n"
        f"你的性格：社交{p.sociability} 诚实{p.honesty} 脾气{p.temper}\n"
        f"你们的关系：{rel_str}\n"
        f"说一句话。"
    )

    result = poe_client.query(prompt, system=DIALOGUE_SYSTEM, task="npc_dialogue")
    if result:
        # record in memories
        add_memory(world, speaker.id, f"我对{listener.name}说：{result}",
                   mem_type="conversation", importance=2, related=[listener.id])
        add_memory(world, listener.id, f"{speaker.name}对我说：{result}",
                   mem_type="conversation", importance=2, related=[speaker.id])

        # eavesdropping: others in same room hear it
        room = world.get_room_at(speaker.x, speaker.y)
        if room:
            for c in world.characters_in_room(room.id):
                if c.id not in (speaker.id, listener.id) and c.alive:
                    level = sound_level(world, speaker.x, speaker.y, c.x, c.y)
                    if level == "full":
                        add_memory(world, c.id, f"听到{speaker.name}对{listener.name}说：{result}",
                                   mem_type="observation", importance=1,
                                   related=[speaker.id, listener.id], source="overheard")
                    elif level == "partial":
                        add_memory(world, c.id, f"隐约听到{speaker.name}在和{listener.name}说话",
                                   mem_type="observation", importance=1,
                                   related=[speaker.id, listener.id], source="overheard")
        return result
    return None


def generate_npc_response_to_player(world: WorldState, npc: Character,
                                    player_message: str) -> str | None:
    """NPC responds to player's free text input."""
    rel = world.get_relationship(npc.id, world.player_id or "")
    rel_str = f"关系:{rel.type}({rel.value})" if rel else "陌生人"
    p = npc.personality

    prompt = (
        f"你是{npc.name}（{npc.role}），一个地下小镇居民。\n"
        f"性格：社交{p.sociability} 诚实{p.honesty} 脾气{p.temper} 慷慨{p.generosity}\n"
        f"对方是新来的人，你们的关系：{rel_str}\n"
        f"对方说：「{player_message}」\n"
        f"你的回应（一两句话）："
    )

    result = poe_client.query(prompt, system=DIALOGUE_SYSTEM, task="npc_dialogue")
    if result:
        add_memory(world, npc.id, f"新来的人对我说：{player_message}，我回答：{result}",
                   mem_type="conversation", importance=3, related=[world.player_id or "player"])
    return result
