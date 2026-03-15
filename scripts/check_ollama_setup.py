#!/usr/bin/env python3

from pathlib import Path
import json
import os
import shutil
from urllib import request, error


ROOT = Path(__file__).resolve().parent.parent


def main():
    ollama_path = shutil.which("ollama")
    print(json.dumps({"ollama_binary": ollama_path}, indent=2))
    if not ollama_path:
        return

    url = os.environ.get("WOMENS_AI_OLLAMA_URL", "http://127.0.0.1:11434/api/tags")
    try:
        with request.urlopen(url, timeout=5) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        print(json.dumps({"ollama_server": "reachable", "models": payload.get("models", [])[:10]}, indent=2))
    except error.URLError as exc:
        print(json.dumps({"ollama_server": "unreachable", "error": str(exc)}, indent=2))


if __name__ == "__main__":
    main()
