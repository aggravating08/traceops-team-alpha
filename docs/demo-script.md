# Three-minute demo recording

Record only after the team has validated live Zetaris. If you show sample mode, say so and separately demonstrate the successful real integration. Never display keys, tokens or private contact details.

## 0:00–0:25 — user and problem

Ansh: “TraceOps helps a small ecommerce operations team answer why orders are delayed. Orders, inventory and support each contain part of the answer. Our agent investigates those sources and gives an explanation you can trace back to a record.”

Show the main investigation screen. State the selected track: The Agent That Can Explain Why.

## 0:25–1:10 — real investigation

Ask: “Why are orders in the North region delayed?”

Show four delayed orders and $3,600 order value exposure in the fictional dataset. Say “exposure,” not “saved revenue” or “predicted loss.”

Open ORD-1041 and KB-01 evidence. Explain that the order is delayed, available stock is zero, and a support ticket corroborates allocation trouble. Point out that the causal connection remains an inference.

## 1:10–1:40 — a different cause and uncertainty

Ask: “Why is order ORD-1045 delayed?” Show the carrier ticket. It should not get the stock-shortage explanation.

Ask: “Why is ORD-9999 delayed?” Show no matching records and the explicit warning. Explain that missing data does not become a confident answer.

## 1:40–2:20 — sponsor integration

Shevchenko: show the same three virtual tables in Zetaris and a successful live-mode run, with credentials hidden. Explain the actual proxy SELECT flow and the role of each source.

PRANAY: export the JSONL trace and show `world.ingested`, `context.selected` and `findings.verified`. Explain the implemented Meterless World Model services: stable observations, snapshot ingestion, shared context and provenance. Say these are the team's implementation of the sponsor reference architecture.

If live NVIDIA inference was verified, show the configured model name and narrative. Otherwise explicitly state that the adapter is prepared but unverified and do not claim a live NVIDIA contribution.

## 2:20–2:50 — product and technical distinction

Show a source modal, a persisted history entry and the exported brief. Explain that all recommendations remain drafts and the tool makes no external fulfilment changes.

Mention the bounded scope and limits: fictional data, selected rows only, one model call maximum, citation checking cannot prove semantic accuracy.

## 2:50–3:00 — close

Ansh: “We built a reproducible investigation workflow that ties every finding to source evidence. Next we want to validate it with operations users and add authenticated deployment.”

Show repository and deck links after they exist. The final video must be between 1 and 4 minutes under the event rules.
