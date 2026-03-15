#!/usr/bin/env python3

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from local_ai.corpus_builder import build


if __name__ == "__main__":
    summary = build()
    print(summary)
