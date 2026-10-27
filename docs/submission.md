# Submission draft

## Project

**TraceOps — evidence-backed order investigations**

## Primary track

The Agent That Can Explain Why

## Problem and users

Small ecommerce operations teams investigate delivery problems by comparing order systems, warehouse stock and support messages. TraceOps provides a bounded workflow to connect those records and explain the available evidence for a delayed order.

## Solution

A user asks about all delayed orders, a region, a SKU or an order identifier. The collector reads a source snapshot. Our World Model ingestion service stores content-addressed observations and pins them to a run. A shared context builder selects related records. The investigator creates supported findings, labels inferred causes and unknowns, and drafts next steps. The verifier checks exact citation IDs and order provenance. The UI supports record inspection, persistent history and artifact export.

The demonstration data is fictional. The North-region sample contains four delayed orders and $3,600 of order value exposure. These figures demonstrate calculation correctness, not measured customer impact or predicted loss.

## Zetaris

The connector uses the UI proxy SQL request contract from the official Zetaris getting-started repository. It reads three configured virtual tables using bounded fixed SELECTs and retains source record identifiers in each finding.

**Current status: connector implemented and contract-tested, live tenant verification pending.** Replace this status only after a real successful run. Include a successful trace and demo of the live source tables in the final submission.

## Meterless

We implement the minimal World Model reference architecture in `traceops/world.py`: WorldStoreService, IngestPipelineService and ContextBuilderService. The active investigation path writes immutable observations, reconstructs run-scoped context and carries provenance to the verifier. Runtime traces disclose implemented and unimplemented features. This is our implementation of sponsor architecture rather than an official Meterless SDK or hosted API.

The distinctive use is an exact, immutable evidence snapshot shared by the investigator and verifier. A later record update does not rewrite an old investigation's evidence.

## NVIDIA and development tools

An injected OpenAI-compatible generator can use an available NVIDIA Nemotron model through the NVIDIA endpoint. **Current status: adapter prepared, live NVIDIA inference unverified.** State the exact model and contribution only after exercising it. Sample mode uses deterministic rules and makes no model calls.

We used Codex to generate and test the application. Cursor was not used in the work recorded here. No separate AMD project code was reused.

## Technical stack

Python 3.11+ standard library, SQLite, HTML, CSS and browser JavaScript. No package installation is required for sample mode. The app binds locally and requires an authenticated deployment layer before public exposure.

## Limitations

The workflow supports bounded order investigations, not unrestricted chat. Source reads cap at 1,000 rows each and context at 200 orders. Totals apply only to selected rows. Stock shortage is an evidence-based hypothesis, not proof of causation. Model narrative citations are checked but semantic faithfulness needs review. There is no production authentication, auto-remediation or demonstrated customer ROI.

## Future enhancements

Validate usefulness with operations users, deploy with authentication and quotas, add source freshness checks, improve regional inventory allocation, and evaluate model explanations against a labelled investigation set.

## Final submission checklist

- [ ] Confirm the team agrees to TraceOps and Track 02.
- [ ] Validate actual Zetaris access and three source reads.
- [ ] Save successful live integration evidence without secrets.
- [ ] Exercise the chosen model, or accurately disclose its unverified status.
- [ ] Run clean setup and regression suite from the shared repository.
- [ ] Update slides to match live status and use final product screenshots.
- [ ] Record and upload a 1–4 minute video.
- [ ] Publish the source repository and verify judge access.
- [ ] Link repository, video and slides in the team submission form.
- [ ] Read final form terms and have the team lead submit.
- [ ] Verify confirmation before October 27, 2026, 23:45 UTC.

The current bundle is a working local project and submission preparation package. It is not an already submitted or eligibility-verified entry.

## Verified handoff links (October 27)

- Source: https://github.com/aggravating08/traceops-team-alpha
- Browser sample: https://aggravating08.github.io/traceops-team-alpha/demo/
- Walkthrough video: https://aggravating08.github.io/traceops-team-alpha/demo/walkthrough.mp4
- Editable deck: https://github.com/aggravating08/traceops-team-alpha/blob/main/output/TraceOps-Team-ALPHA-v2.pptx

The public demo and narrated video show sample mode only. Neither proves live Zetaris or model usage. A final submission must keep these disclosures and must not describe the outstanding integration as completed.
