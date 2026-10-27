# Judges' questions and answers

**Who uses this?** A small ecommerce operations team investigating delayed orders across separate systems. This is a target-user hypothesis; user interviews and measured ROI are future work.

**What does the agent actually do?** It scopes an investigation, collects bounded source snapshots, stores observations, builds shared context, produces evidence-linked findings, verifies citation identity and drafts next steps. Sample mode uses rules. Optional live model mode produces a narrative from verified findings.

**What makes the result trustworthy?** Every finding carries exact source observation IDs. An order, stock record and ticket remain inspectable. Historical runs pin their own snapshots. Causes have explicit documented, corroborated, inferred or unknown labels. The app does not treat all delay types as stock shortages.

**Where is Zetaris?** The Python collector implements the documented UI-proxy SQL contract for three configurable virtual tables. A live instance and authorized account are required. No live Zetaris verification has been obtained in the current package, so the public demo does not claim one.

**Where is Meterless?** `traceops/world.py` implements the minimal World Model reference-architecture services. The active path ingests immutable observations and builds shared context for the investigator and verifier. This is our implementation of the sponsor architecture, not a hosted SDK call. Advanced enrichment, H-MEM and Markovian are outside this MVP.

**Where is NVIDIA?** An injected compatible model adapter can use an available NVIDIA model. Live NVIDIA inference remains unverified. No GPU or latency claim is made.

**Can it take action?** It creates draft recommendations and exports briefs. It does not change order systems or send customer messages.

**Does $3,600 mean savings?** No. It is the sum of four delayed sample orders in North. It measures order-value exposure in fictional data, not loss, savings or forecast revenue.

**Why does the public demo work without a server?** It computes the same bounded sample rules in browser JavaScript, using public fictional JSON records and browser-local history. The Python runtime owns live provider access, SQLite snapshots and the Zetaris connector. Both sample runtimes have acceptance coverage.

**What would you build next?** Validate usefulness with operations staff, complete live sponsor verification, support regional inventory keys and freshness checks, then add authenticated hosting and quotas.
