"""Poe API client — reused from world/ project with retry, fallback, logging."""
from __future__ import annotations
import os, json, time, logging

log = logging.getLogger("poe_client")

_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(_LOG_DIR, exist_ok=True)
_LOG_FILE = os.path.join(_LOG_DIR, "ai_calls.log")

API_KEY = os.environ.get("POE_API_KEY", "")
TIMEOUT = int(os.environ.get("POE_API_TIMEOUT_SEC", "60"))
MAX_RETRIES = int(os.environ.get("POE_MAX_RETRIES", "2"))
RETRY_BACKOFF = int(os.environ.get("POE_RETRY_BACKOFF_SEC", "2"))

# Tier -> model mapping
TIER_MODELS = {
    "cheap": os.environ.get("POE_MODEL_CHEAP", "GPT-5.2-Instant"),
    "normal": os.environ.get("POE_MODEL_NORMAL", "GPT-5.4-Mini"),
    "deep": os.environ.get("POE_MODEL_DEEP", "GPT-5.4"),
    "judge": os.environ.get("POE_MODEL_JUDGE", "GPT-5.4-Pro"),
}

# Task -> (primary_tier, fallback_tier)
TASK_ROUTING = {
    "npc_decision": ("cheap", "normal"),
    "npc_critical": ("deep", "normal"),
    "npc_dialogue": ("cheap", "normal"),
    "memory_compress": ("cheap", "normal"),
}


def _write_log(msg: str):
    from datetime import datetime
    with open(_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")


def is_available() -> bool:
    return bool(API_KEY)


def _call_poe(model: str, prompt: str, system: str = "") -> dict:
    import fastapi_poe as fp
    _write_log(f"[REQ] model={model} prompt_len={len(prompt)}")
    messages = []
    if system:
        messages.append(fp.ProtocolMessage(role="system", content=system))
    messages.append(fp.ProtocolMessage(role="user", content=prompt))

    start = time.time()
    try:
        result = ""
        for partial in fp.get_bot_response_sync(messages=messages, bot_name=model, api_key=API_KEY):
            result += partial.text
        latency = int((time.time() - start) * 1000)
        _write_log(f"[OK] model={model} latency={latency}ms len={len(result)}")
        return {"ok": True, "content": result.strip(), "latency_ms": latency}
    except Exception as e:
        latency = int((time.time() - start) * 1000)
        _write_log(f"[ERR] model={model} latency={latency}ms error={e}")
        return {"ok": False, "content": None, "error": str(e), "latency_ms": latency}


def query(prompt: str, system: str = "", task: str = "npc_decision") -> str | None:
    """Query with retry + tier fallback. Returns text or None."""
    if not is_available():
        return None
    primary_tier, fallback_tier = TASK_ROUTING.get(task, ("cheap", "normal"))
    model = TIER_MODELS[primary_tier]
    fallback = TIER_MODELS[fallback_tier]

    for attempt in range(MAX_RETRIES + 1):
        r = _call_poe(model, prompt, system)
        if r["ok"] and r["content"]:
            return r["content"]
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_BACKOFF)

    if fallback != model:
        r = _call_poe(fallback, prompt, system)
        if r["ok"] and r["content"]:
            return r["content"]
    return None


def query_json(prompt: str, system: str = "", task: str = "npc_decision") -> dict | None:
    """Query and parse JSON response."""
    raw = query(prompt, system, task)
    if not raw:
        return None
    try:
        text = raw
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return json.loads(text.strip())
    except (json.JSONDecodeError, IndexError):
        return {"raw": raw}
