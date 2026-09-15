# Independent native Reviewer return

Reviewer: /root/dm_mgtap_resume_20260914/review_ah_mgtap_late512, registered hmasd-reviewer (Astra/high), minimal independent context. Baseline5824bf36a. Native final received2026-09-14; no source writes and no empirical invocation.

No material finding found in the reviewed change against baseline `5824bf36a`.

- **State/RNG:** optimizer and training velocity generator persist across midpoint evaluation. Evaluation has its own environment and generators. The unchanged collector resets recurrent state per episode and uses no-grad; model forwards introduce no dropout or mutable normalization state.
- **Endpoint/completeness:** both complete 32-world panels are required; only final512 supplies primary polarity. Exceptions retain observed partial counts; checkpoint or publication failures cannot produce a successful return.
- **Scope:** 230 source lines, including the 159-line runner. No uncarded §4 machinery or concrete source-budget breach found. Existing learner, pair factory and readout dependencies remain unchanged.

**Independent synthetic check: PASS, 4.75 seconds.** Exercised the actual new runner with substituted collection/update operations: uninterrupted 512-draw training streams per arm, repeated evaluation streams, distinct environments, persistent Adam state, checkpoint optimizer steps512/1024, 1152 published episode rows, closed summary, and adverse final polarity despite positive midpoint polarity. Temporary artifacts were removed; no native scientific invocation occurred.

Checked `protocol.py`, `study.py`, card, `COMMAND.sh`, and relevant factory, geometry, collector/update, environment, RNG and serialization dependencies. Scientific reading supports treating checkpoints/worlds as observations within one training pair.

Residual limits: synthetic coverage establishes runner behavior, not native PPO validity, measured internal threads, resource admission, or complete-command wall/RSS. Those execution facts remain for DM collection.

Reviewed SHA256:
- `protocol.py`: `507237fb71d7030ea4fc4d9f361b34fafcdf00d7d1602f6ea653d45e38715d31`
- `study.py`: `439266300eb0807d8ff66948cfd0476a955b90db00de593bad1d19094d07604a`

Read-only technical evidence; DM retains acceptance.
