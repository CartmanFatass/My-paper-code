# EHC formal CPU result: benchmark access boundary

- Question: Does the frozen `EVENT_HELD_COMMITMENT_LINK_G0` comparison establish access under its registered utility floor?
- Implicated conjectures: event-held commitment may still be useful in a stronger MARL benchmark; this result only tests the frozen comparison's access boundary.
- Evidence type: formal experiment
- Frozen semantics: `G=U_EHC-U_DUM`, OR/DUM/EHC, CPU with one thread, fixed seeds/budget/reward/observation/PPO and the registered first-match selector.
- Observation: The valid formal run completed 5 paired replicates, 1,250/1,250 updates, 60/60 evaluation cells and passed operational validation. The maximum arm utility UCB was `0.6897088859777634`, below the access floor `0.78`.
- Smallest supported or refuted unit: This frozen benchmark-comparator pair is `NO_ACCESS_THIS_BENCHMARK`.
- Retained lemma: Operational validity and scientific disposition are distinct; a valid access failure does not reject stronger-MARL research or the event-held mechanism outside this source.
- Counterexample: None is inferred beyond the measured access boundary; G, K-bin, intervention and C_total diagnostics do not relabel the first-match result.
- Does not imply: It does not imply event-held commitment is useless, that the algorithm family should be retired, or that any gate, budget, seed, reward, observation, model or threshold should change.
- Portfolio delta: Close this frozen comparison; preserve plural explanations and require external GPT-5.6 Pro result review before iteration 2.
- Reactivation conditions: A later benchmark with an externally reviewed, mechanism-matched access question may reopen stronger-MARL or successor explanations without rescuing this result.
- Provenance: source `fb9909711a2ca8628f3d534936b771885e53b26d`; raw run `logs/formal_event_held_cpu_20260722_fb99097_r2`; train manifest SHA-256 `d4ef17e7c55f67752926916de36512094db1df4ef4e185e5bd20628bf43630fc`; evaluation manifest SHA-256 `06d32935b0a3e35b6791a5186b8acfcb5562674e0e7789e977d2576418ba9d01`; analysis SHA-256 `92e1399fed54abbef3e68fb0ef1badd589d9832209c35f3d8343ba15eb1bdf63`; 1,330/1,330 reference closure; no `.tmp`, `.partial` or `.staging` residue.
