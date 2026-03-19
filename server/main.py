#!/usr/bin/env python3
"""Mine Village — game server entry point."""
import os, sys, uvicorn

# ensure server/ is on path
sys.path.insert(0, os.path.dirname(__file__))

# load .env
_env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_env_path):
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

from api.routes import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
