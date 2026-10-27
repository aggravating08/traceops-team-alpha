# TraceOps — follow the evidence

Team ALPHA · Open Agent Hackathon 2026 · proposed primary track: **The Agent That Can Explain Why**.

TraceOps helps a small ecommerce operations team investigate delayed orders across orders, warehouse inventory and support tickets. It returns scoped order-value exposure, evidence-linked findings, labelled uncertainty and draft next steps. It never sends customer messages or changes fulfilment systems.

## Source and public sample

Source: https://github.com/aggravating08/traceops-team-alpha

Public browser sample: https://aggravating08.github.io/traceops-team-alpha/. The public demo computes fictional data in the browser and keeps history in browser storage. It makes no Zetaris or model calls. Use the Python app below for server-side snapshots and live adapters.

## Run locally

Requires **Python 3.11+**. No pip, Node, Docker or third-party dependencies are needed for sample mode.

```sh
git clone https://github.com/aggravating08/traceops-team-alpha.git
cd traceops-team-alpha
python3 server.py
```

On Windows use `py -3 server.py`. Open **http://127.0.0.1:8765**. To change the port: `python3 server.py --port 8766`.

Try:

- `Why are orders in the North region delayed?` → 4 delayed orders, 30 units, **$3,600** order value exposure.
- `Investigate all delayed orders and order value at risk` → 6 delayed orders, **$4,350** exposure.
- `Why is order ORD-1045 delayed?` → documented carrier issue.
- `Why is ORD-9999 delayed?` → no matching records; no invented answer.

Click any source chip to inspect the exact record. Export the Markdown brief and JSONL agent trace. Recent investigations survive server restarts in `runtime/world.sqlite3`.

**Default sample mode is real executable analysis over fictional CSV data, using deterministic rules. It does not call an LLM or Zetaris.** Do not present sample mode as live sponsor integration.

## What is implemented

- Responsive, keyboard-accessible investigation UI, source view and team playbook.
- Bounded planner → collector → World Model → investigator → verifier workflow.
- Filters for exact ORD identifiers, North/South/East/West and the sample SKUs.
- Three read-only data adapters through a common snapshot interface.
- Content-addressed, append-only observations and transactionally pinned run snapshots.
- ContextBuilderService used by the investigator and citation verifier.
- Deterministic stock/carrier/address findings, conflicting-blocker warnings and unknown-cause handling.
- Optional provider-injected, citation-checked narrative with a maximum of one model call per run.
- Persistent history, exact evidence drill-down, report export and JSONL trace export.
- Zetaris UI proxy connector using the sponsor's documented request contract.

## Sponsor integration and current verification

### Meterless — implemented locally

The hackathon Meterless README states that its engines are **reference architectures, not an installable SDK**. This project implements the minimum World Model subset: `WorldStoreService`, `IngestPipelineService`, and `ContextBuilderService` in `traceops/world.py`. These services run on the active investigation path. They preserve stable identities, immutable observations, run attribution, source provenance and run-scoped context. The store is SQLite; traces are available as JSONL through the API or CLI.

This is **our minimal implementation of the Meterless reference architecture**, not a claim to use an official package or hosted Meterless service. The full ten-stage lifecycle, enrichment jobs, supervisor agent, H-MEM and Markovian are not implemented. The runtime event manifest records these limits. Reference: hackathon Resources → Meterless README and Meterless WORLD MODEL Agent Engine, read October 26, 2026.

### Zetaris — connector implemented; live tenant verification pending

Register `data/orders.csv`, `data/inventory.csv` and `data/tickets.csv` as virtual tables in your own Zetaris installation. Keep them as three logical sources to demonstrate federation. Map required columns exactly as the CSV headers. Use integer quantities and available_units, numeric order_value, and USD-denominated order values. The MVP assumes USD.

Copy `.env.example` to **`.env.local`** and set:

```dotenv
TRACEOPS_DATA_MODE=zetaris
ZETARIS_BASE_URL=https://YOUR-ZETARIS-UI-ORIGIN
ZETARIS_ORG_ID=YOUR_NUMERIC_ORG_ID
ZETARIS_API_KEY=YOUR_EXISTING_KEY
ZETARIS_ORDERS_TABLE=traceops.orders
ZETARIS_INVENTORY_TABLE=traceops.inventory
ZETARIS_TICKETS_TABLE=traceops.tickets
```

Restart the server. The connector posts bounded, fixed SELECTs to `/api/proxy/sql-editor/sqls/run-query` with `sql`, `limit`, optional `engineId`, Bearer authorization, `X-Org-ID` and `X-Request-ID`. It follows the official [Zetaris getting-started HTTP helpers](https://github.com/zetaris/getting-started/tree/main/scripts). The UI origin is required, rather than the raw REST endpoint.

`normalize()` accepts object arrays and column-plus-row arrays. Verify your tenant's actual response shape and update that function if it differs. The connector deliberately rejects unknown schemas, duplicate keys, missing fields and results above 1000 rows per source. Context is capped at 200 orders and clearly marked if truncated. All totals apply to selected rows only.

No authorized Zetaris endpoint or credentials were available during development. **A mocked contract test is not a live integration test.** Before submission, run the app against your real tenant and preserve a successful trace and recording. A failure never falls back to sample data.

### NVIDIA / model — optional live adapter; not yet exercised

Set these in `.env.local`:

```dotenv
TRACEOPS_MODEL_MODE=live
MODEL_BASE_URL=https://integrate.api.nvidia.com/v1
MODEL_API_KEY=YOUR_EXISTING_KEY
MODEL_NAME=EXACT_MODEL_ID_AVAILABLE_IN_YOUR_ACCOUNT
```

Choose a currently available NVIDIA Nemotron model from your sponsor account if appropriate. Alternatively use an authorized OpenAI-compatible provider. No model ID is assumed. The model receives only verified findings and scope. Every narrative must be JSON and cite allowed full evidence IDs. **Citation integrity is validated; semantic faithfulness is not guaranteed.** The UI labels the model narrative for review and keeps deterministic findings separate. Failed calls or invalid output fail the run visibly.

Live model calls transmit the selected verified findings (including customer names in the configured dataset) to the configured provider. Use these fictional fixtures for the hackathon and only supply other data when authorized.

## Tests and headless execution

```sh
python3 -m unittest discover -s tests -v
python3 scripts/investigate.py 'Why are North orders delayed?'
```

Tests cover expected totals, citations, missing evidence, conflicting blockers, duplicate-key transaction rollback, idempotency, restart persistence, run isolation, explicit provider failure, request mapping, HTTP routes and origin guards. They use temporary databases and no external APIs. `docs/verification.md` records validation performed.

The CLI writes `brief.json` and `trace.jsonl` under the selected `--output` directory. The CLI works without a browser, illustrating that the World Model engine is headless.

## Architecture

```text
Browser / CLI
    ↓ question
Planner (bounded scope parser, no arbitrary SQL)
    ↓ fixed source reads
Sample CSV adapter OR Zetaris read-only proxy adapter
    ↓ snapshot, source keys, timestamps
Meterless World Model pattern
  WorldStoreService: SQLite append observations + run snapshots
  IngestPipelineService: stable IDs + idempotent transactional ingestion
  ContextBuilderService: selected orders + related stock + tickets
    ↓ shared grounded context
Investigator: supported blocker rules + optional injected generator
    ↓ claims with citations
Verifier: exact evidence IDs + matching order provenance
    ↓
Brief, draft next steps, source drill-down, persistent history, JSONL trace
```

The "agents" are cooperating software stages in one bounded workflow; sample mode does not pretend they are autonomous model agents. The model performs narrative generation in live mode. The MVP deliberately avoids model-generated SQL, automatic writes and unbounded agent loops.

## Repository map

- `server.py`: loopback HTTP API, safe static serving, env loading.
- `traceops/agent.py`: planning, investigation, verification and generator injection.
- `traceops/world.py`: minimal Meterless World Model implementation.
- `traceops/connectors.py`: sample and Zetaris source readers.
- `web/`: buildless HTML/CSS/JS UI; no CDN dependency.
- `data/`: entirely fictional demonstration datasets.
- `tests/`: isolated, network-free regression suite.
- `web/app.js`: team playbook and proposed work ownership.
- `docs/demo-script.md`: 3-minute recording script.
- `docs/submission.md`: truthful submission draft and remaining checklist.

## Deployment limits

The included server binds to **127.0.0.1** for a local demo. It has no user authentication, authorization or production rate limiting. Do not expose it through a public tunnel as-is. A public demo requires an authenticated hosting layer, HTTPS, a persistent volume for `runtime/`, bounded concurrency and request quotas. Share a recorded demonstration and reproducible repository if public hosting cannot be safely completed before the deadline.

## Provenance and deadline

Created during the October 22–27, 2026 build window using Codex-generated code. No code from the separate AMD project was reused. Python and browser standard libraries are pre-existing components; there are no added package dependencies. Declare AI assistance and any later reused components in the final submission.

Official submission deadline: **October 27, 2026, 23:59 UTC / October 28, 2026, 04:59 PKT**. [Official event and rules](https://hackathon.genai.works/event/open-agent-hackathon-2026). Both Zetaris and Meterless are mandatory. Code readiness alone is not submission readiness: finish live Zetaris validation, video, slides, repository publication and link checks.

## Team handoff files

The editable pitch deck is `output/TraceOps-Team-ALPHA-v2.pptx`. Update its live-verification disclosures after successful sponsor runs. Synthetic example evidence is in `docs/evidence/`. Five named tasks were created on the Team ALPHA board; the app includes the team playbook.

## Public browser sample build

Run `python3 scripts/build_demo.py` to regenerate `docs/demo/` from the UI and fixtures. GitHub Pages serves the `docs/` directory. The browser sample has its own explicitly labelled runtime and no provider credentials. With Node 22+ available, run `node tests/browser-sample.test.mjs` for seven acceptance checks. Python sample and live modes remain the primary runtime.

## Submission materials

- Editable deck: `output/TraceOps-Team-ALPHA-v2.pptx`
- Narrated sample walkthrough: `output/TraceOps-Walkthrough.mp4` (3 minutes 39 seconds)
- Public video: https://aggravating08.github.io/traceops-team-alpha/demo/walkthrough.mp4
- Transcript: `docs/video-transcript.md`
- Connection readiness: `python3 scripts/check_connections.py` (prints missing variable names, never secret values). Add `--live` only when you want real source reads and a model test.

The walkthrough uses captured sample-app views with synthetic narration. Live sponsor verification remains pending, so it is a reviewable demo draft rather than evidence of a live sponsor run.
