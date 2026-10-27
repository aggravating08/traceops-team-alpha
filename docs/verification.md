# Verification record

October 26, 2026. Python 3.12.4 on macOS.

- `python3 -m compileall -q traceops`: passed.
- `python3 -m unittest discover -s tests -v`: 14 tests passed in isolated temporary databases, with no live provider calls. Includes mocked valid and invalid model output checks.
- Browser: local server on port 8766 because an unrelated process already uses 8765. That process was preserved.
- Browser North-region investigation: 5 orders reviewed, 4 delayed, 30 units, $3,600 order value exposure.
- Browser source drill-down: ORD-1041 displays its exact pinned record.

Live Zetaris connectivity and live model inference are unverified. Source connector contract coverage uses mocked JSON responses. No production hosting or final hackathon submission has occurred.

- Browser: carrier order ORD-1045 returns one documented carrier blocker and $450 exposure.
- Browser: Markdown export downloaded and contains source records and the carrier finding.
- Browser: team playbook shows all five actual members.
- JavaScript syntax check passed with the bundled Node runtime.
- Editable seven-slide PPTX passed package, font, layout and re-import checks. All seven slide previews were visually inspected. Native PowerPoint execution was not tested.
- Five named tasks were created and assigned on the real Team ALPHA board (19 total tasks including 14 starters).

## October 27 completion pass

Public source repository published. Public browser sample deployed via GitHub Pages, with a successful hosted North investigation: 5 reviewed, 4 delayed, 30 units and $3,600 exposure. Seven browser-runner acceptance checks pass in addition to 14 Python tests. A 219.403-second H.264/AAC walkthrough uses captured app views and synthetic narration. Its audio has nonzero signal. The revised eight-slide deck passed package/layout/font/re-import checks. Live connection readiness reports missing configuration for Zetaris and model access. No live provider calls were made.

## October 27 local model verification

20 Python tests and seven browser acceptance checks pass. Real local Ollama inference with Qwen2.5:0.5b was exercised against fictional CSV data for ORD-1045 and North. An absent order correctly produced no findings and no model call. Full run records are in `evidence/local-qwen-run.json`. This verifies local model inference, not NVIDIA inference or live Zetaris reads.

Structured output restricts citations to supplied evidence IDs. Truncated, oversized, missing-reference and unknown-reference responses fail validation. Citation validity does not prove semantic faithfulness: the small model echoed a system phrase in one result and omitted some details in its brief regional summary. Human review remains required.

To reproduce with an already installed Ollama model server:

```sh
export TRACEOPS_MODEL_MODE=live
export MODEL_BASE_URL=http://127.0.0.1:11434/v1
export MODEL_API_KEY=ollama-local
export MODEL_NAME=qwen2.5:0.5b
export MODEL_RESPONSE_FORMAT=json_schema
python3 scripts/check_connections.py --live
```

The connection checker still exits nonzero when Zetaris is missing; its separate model result reports successful inference. No credential was published. The public walkthrough and deck still depict the earlier deterministic sample mode.
