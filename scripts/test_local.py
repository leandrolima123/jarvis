#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

LAMBDA_DIR = Path(__file__).resolve().parent.parent / "lambda"
sys.path.insert(0, str(LAMBDA_DIR))

from lambda_function import lambda_handler


def load_env_file() -> None:
    for env_path in (
        Path(__file__).resolve().parent.parent / "lambda" / ".env",
        Path(__file__).resolve().parent.parent / ".env",
    ):
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python scripts/test_local.py <arquivo.json>")
        sys.exit(1)

    event_path = Path(sys.argv[1])
    event = json.loads(event_path.read_text(encoding="utf-8"))
    response = lambda_handler(event, None)
    print(json.dumps(response, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    load_env_file()
    if not os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        print("Defina GEMINI_API_KEY no lambda/.env antes de testar IntentRequest.")
    main()
