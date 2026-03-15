#!/usr/bin/env python3

from pathlib import Path
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from local_ai.assistant import LocalWomensHealthAssistant


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("question", help="User question to evaluate")
    parser.add_argument("--corpus", default="artifacts/knowledge_corpus.jsonl")
    parser.add_argument("--top-k", type=int, default=4)
    args = parser.parse_args()

    assistant = LocalWomensHealthAssistant(Path(args.corpus))
    result = assistant.answer(args.question, top_k=args.top_k)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
