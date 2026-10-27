# Demo video transcript

Synthetic narration using the macOS Samantha voice. The video uses captured app views and presentation frames, rather than a continuous screen recording. All scenes show sample mode. Live Zetaris and model verification remain pending.

## Scene 1

Trace Ops is Team Alpha’s order investigation project for The Agent That Can Explain Why. It helps an ecommerce operations team connect orders, warehouse inventory, and support tickets. This walkthrough uses captured views of the working sample application. All customers and records are fictional. The sample runs deterministic rules, with no live model or Zetaris calls.

## Scene 2

We begin by asking why orders in the North region are delayed. The application scopes the question, reads three source datasets, and builds a shared evidence context. Five orders fall within the selected region. Four are delayed, involving thirty units and three thousand six hundred dollars of order value. This is exposure in the sample records. It is not predicted loss, measured savings, or real customer revenue.

## Scene 3

Every finding links to source evidence. Here, the keyboard inventory record shows zero available units at the North warehouse, with an inbound shipment marked supplier delayed. Related order and support records corroborate an allocation problem. Trace Ops labels the stock explanation as an inference, because these records do not prove causation. The exact observation identifier stays attached to the investigation.

## Scene 4

A different order produces a different explanation. Order ten forty five has available inventory, while its support ticket records a missed carrier collection. The system reports a documented carrier blocker instead of applying the stock shortage explanation to every delay. Its next step is a draft for logistics to confirm the collection. It does not send customer messages or change the order system.

## Scene 5

When we request an order that does not exist in the snapshot, the system shows no matching records and states that no conclusion can be drawn. This avoids inventing a cause. Users can return to saved investigations, inspect evidence, and export a Markdown brief or a JSON Lines trace. The public browser sample keeps its history in that browser. The Python version stores durable run snapshots in SQLite.

## Scene 6

The workflow has bounded software stages: planner, collector, shared world context, investigator, and verifier. The Python implementation uses the standard library and SQLite, with a buildless browser interface. Fourteen Python tests pass. Seven additional browser sample checks cover the key scenarios, including missing evidence and citation identity. The optional live generator accepts verified findings, allows one model call, and rejects invalid citation identifiers.

## Scene 7

Meterless contributes the World Model reference architecture. Our minimum implementation provides a World Store Service, an idempotent ingestion pipeline, and a context builder used by the active investigation. The source trace records what is implemented. Zetaris contributes the data layer through a connector for three virtual tables using the documented SQL proxy. A real Zetaris account and instance are still required. Live Zetaris and NVIDIA model usage remain unverified. This video does not claim a completed live sponsor integration.

## Scene 8

The complete source and setup instructions are available in Team Alpha’s public GitHub repository, and the browser sample is hosted on GitHub Pages. Recommendations remain drafts. Next steps are live sponsor verification, evaluation with operations users, and authenticated deployment. The project provides a reproducible explanation workflow with inspectable evidence, while keeping its current limitations visible.