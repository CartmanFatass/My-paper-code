# V-K0B exposure recovery audit — Outcome B (instrument and rerun)

Date: 2026-08-01. Ordered by the disposition of round
`20260801_vk0_result_disposition` ("artifact-only exposure recovery audit
... else identical-contract operational rerun"). Mechanical audit over all
six training roots `logs/vk0b/2026080101..106` at their recorded checkpoint
hashes; every number below read from durable artifacts, none multiplied
from nominal configuration. PM-executed (scout inventory + PM sweep).

## Per-field recovery status (identical across all six seeds)

| # | Mandatory field | Durable source found | Status |
|---|---|---|---|
| 1 | environment interactions | `run_manifest.json:total_steps` = 640000; checkpoint `total_steps` = 640000; CSV last row = 640000 (three independent records agree) | RECOVERED |
| 2 | completed outer updates | `run_manifest.json:update_idx` = 1000; checkpoint = 1000; CSV rows = 1000 | RECOVERED |
| 3 | high actor optimizer steps | checkpoint `high_opt.state[*].step` = 3000 uniformly (= 1000 updates × 3 PPO epochs; CSV per-update `high_optimizer_steps` = 3.0 consistent) | RECOVERED, with the structural caveat below |
| 4 | high value optimizer steps | no separate high-value optimizer exists — one shared `high_opt` covers the high head(s); a distinct counter is structurally absent | STRUCTURALLY SHARED with 3 |
| 5 | high-check sequences | never accumulated anywhere (preflight `not_available`; no CSV column, no log field, no checkpoint counter) | NOT RECOVERABLE |
| 6 | agent-token counts (KEEP/SET) | token constants exist in code; no accumulator, no durable record | NOT RECOVERABLE |
| 7 | skipped / invalid high batches | no counter exists on the high-update path | NOT RECOVERABLE |
| 8 | aborted batches | never accumulated (preflight `not_available`) | NOT RECOVERABLE |
| 9 | low-level optimizer steps | CSV `low_optimizer_steps` = 0.0 at every update; all low optimizer state dicts ABSENT from the checkpoint (consistent with the contracted low-optimizer absence) | RECOVERED (= 0) |
| 10 | checkpoint SHA-256 + resolved-config hash | launcher manifest, all six seeds | RECOVERED |

Cross-seed sweep: all six roots identical in shape — 1000 CSV rows,
640,000 steps, 1000 updates, `high_opt` step = 3000 uniform across every
parameter, low optimizers absent, return code 0.

## Verdict

Fields 5–8 are **not recoverable from any durable artifact** (they were
never accumulated), so per the disposition this is **Outcome B**: instrument
the missing counters and rerun the identical V-K0B operational contract.
The recovered fields (1–4, 9, 10) are internally consistent at every seed
and carry no sign of skipped or partial updates — recorded as supporting
observation, not as a substitute for the mandatory audit trail.

The six existing checkpoints remain diagnostic references (ruled); the
rerun writes fresh roots and never pools with them.
