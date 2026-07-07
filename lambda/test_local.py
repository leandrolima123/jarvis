#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lambda_function import lambda_handler


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python test_local.py <arquivo.json>")
        sys.exit(1)

    event_path = Path(sys.argv[1])
    event = json.loads(event_path.read_text(encoding="utf-8"))
    response = lambda_handler(event, None)
    print(json.dumps(response, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if not os.getenv("GEMINI_API_KEY"):
        print("Defina GEMINI_API_KEY antes de testar IntentRequest.")
    main()
