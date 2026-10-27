#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import load_env
from traceops.agent import run
from traceops.world import WorldStoreService

if __name__ == '__main__':
    load_env()
    parser = argparse.ArgumentParser(description='Headless TraceOps investigation and JSONL evidence export')
    parser.add_argument('question')
    parser.add_argument('--output', type=Path, default=Path('runtime/exports'))
    args = parser.parse_args()
    store = WorldStoreService(Path(__file__).resolve().parents[1] / 'runtime/world.sqlite3')
    try:
        result = run(store, args.question)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
    target = args.output / result['id']
    target.mkdir(parents=True, exist_ok=True)
    (target / 'brief.json').write_text(json.dumps(result, indent=2))
    (target / 'trace.jsonl').write_text('\n'.join(json.dumps(e) for e in store.events(result['id'])) + '\n')
    print(json.dumps({'id': result['id'], 'metrics': result['metrics'], 'artifacts': str(target)}, indent=2))
