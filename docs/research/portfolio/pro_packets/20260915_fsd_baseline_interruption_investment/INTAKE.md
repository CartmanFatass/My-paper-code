# Intake — FSD baseline × interruption investment (Portfolio, 2026-09-15)

Request `2026-09-15-fsd-baseline-interruption-investment-01`, node
`portfolio:cross_direction`, conversation `6a9c109e-b264-83e8-a78b-f9ea1b767b7b`,
task `ba7eb3fe0`, delivery commit `5c6053f4a` on `codex/fsd`
([RESPONSE.md](archive/RESPONSE.md), Issue #22 comment 5679181425). Transport:
Claude Code hub via Agentify Desktop, one accepted Send, `COMPLETE`, GitHub bytes
sha256 `9beb3dd0cb57de306204acdc66131faec8a8ac0ea915195be4a1e9d0a1aa5f0b`
(13,963 bytes), archive under
`temp/sessions/hmasd-chatgpt-pro-transport/archive/portfolio/2026-09-15-fsd-baseline-interruption-investment-01/`.

## Decision and conformance

**Selected: S with prospective corrections** — FLAT, D1280, I1280 across four
fresh training blocks, twelve original fits, fifteen rollouts each, panels after
rollouts 5, 10 and 15, plus minimum implementation and support. FSD stays
ACTIVE/HIGH, authentic D0 default, limited optional I1280 unchanged.

Conformance check by the author DM (the hub): the decision answers the bound
question at its declared class (B/EXPLORE), within evidence-spec §§4, 7, 8.1,
11.4, 11.7–11.11 and the owner's 2026-09-14 programme; it adds no specification
exception, lifecycle, priority or peer change; its corrections are class-correct
and are all applied below. No concrete conflict found. Label
**`PRO_FINAL / OWNER_DELEGATED`** under AGENTS §4.8; execution proceeds without
Root ratification.

## Corrections applied

| Correction | Application |
| --- | --- |
| FLAT from the ordinary `off` configuration, then the `mappo` switch | `make_config("FLAT")` in the runner; `policy_interruption_mode == "off"`, `n_Z = n_z = 1`, zero coordinator/discriminator updates asserted in tests |
| Switch-selected long `k` | **Deviation recorded:** `k = rollout_length + 1` is not runnable (recurrent chunk length is `config.k`); the runner fixes `k = 10`, identical to the D arms; card §8 |
| Rename `H`/`HI` as untuned cross-information package gaps | `GAP_D`, `GAP_I` with `contrast_meaning` in the readout; not §11.7 headroom |
| Retain 15 rollouts and three panels; isolate panels | one evaluator per fit, environments rebuilt per panel, `_preserve_rng()`, learner untouched (test `test_panel_leaves_learner_state_untouched`) |
| MEI .05 J as cost-sensitive target; split importance and uncertainty | `importance_reading`, `uncertainty_reading`, `interval_inside_mei` in the primary block; compound branch removed |
| Four blocks, bases 772203–772503 / 782203–782503 | `BLOCKS` in the runner; 772603/772703 unpurchased |
| Rollout-5 accumulation: 4 new + 2 historical, separate first | `rollout5_accumulation` with `new_blocks` and `historical_blocks` sub-summaries |
| Own the explicit 15-rollout loop and 3-panel assembly | parametrised copy of the frozen collector, equivalence test against the frozen one |
| Opus independent review before launch | dispatched on `db0b11bd8`; findings resolved before any launch |

## Operational mapping

- Source: `scripts/run_fsd_baseline_interruption_b01.py` and
  `tests/experiments/candidates/flexible_skill_duration/baseline_interruption_b01/`
  on `codex/fsd` (`db0b11bd8`, docs at `d4a87c98d`). 15 synthetic tests and 2
  real tiny-host tests (2 lanes, 20-step episodes, real Scenario 1 and real
  agent) green.
- Execution: remote-first `wsl_4070`, CPU FP32 four threads, detached
  `agent-task` per fit, fresh `admit-memory` joined by `&&`, launches only
  through `hmasd-experiment-operator`, observation through
  `hmasd-experiment-tracker`. Twelve fits: `fit --arm {FLAT,D1280,I1280}
  --seed {772203,772303,772403,772503} --output-root <root>`; then `reduce
  --summaries <12 summary.json> --historical-factorial-summary
  docs/research/candidates/flexible_skill_duration/interruption_batch_b01_20260914/RESULT_SUMMARY.json`.
- Ordinary plan 24,000–30,000 s summed native wall (FLAT unmeasured); not a
  cap. Zero automatic retries, replacements, tuning, extra panels or extensions.
- Completion or a concrete dependent limitation ends this allocation, not FSD.

## Ledger and owner surfaces

Ledger `docs/research/portfolio/audit/2026-09-15.md` (Portfolio application
row); owner item `20260915-fsd-001` updated with `auto_applied = S`. Transport
registry note: the shared archive script fails on this key's record (missing
singular `direction_id`, a pre-existing Codex-side schema mismatch), so the
key `portfolio:cross_direction` rests at `DIRECTION_VERIFIED` for this request
with the response fully archived; reported to the owner, not repaired by the
hub.

## Independent review, deviation return and launch (2026-09-15, appended)

- Independent Opus review of the runner at `db0b11bd8`: **ACCEPT_WITH_CORRECTIONS**.
  The reviewer's real-host probe found the D1280 training trajectory bit-identical
  with and without the three evaluation panels and FLAT learning only actor/critic.
  Corrections applied at `dc4dbdfcd` (M1a–c: the true reason for FLAT `k = 10`, the
  deviation recorded on the card §8 and here; M2: `launch_sha` in the comparability
  view; a mixed-source block now fails the contrast). 16 synthetic + 2 real
  tiny-host tests green.
- **Correction note owed to `portfolio:cross_direction`** (AGENTS §2, concrete
  conflict with the decision's "switch-selected long k"): `config.k` is also the
  truncated-BPTT chunk length of the recurrent actor and critic, so the switch's
  `k = rollout_length + 1` would train FLAT through 500-step chunks against the D
  arms' 10-step chunks and confound the architecture contrast with the
  gradient-truncation law. The runner sets `k = 10` (same optimizer law in every
  arm; the single constant skill makes the ten-step re-assignment degenerate).
  The note cannot be sent yet: the key rests at `DIRECTION_VERIFIED` (archive
  defect above). Until it is returned and answered, the FLAT arm is dependent
  work under AGENTS §3; the D1280/I1280 arms are independent authorized work.
- Launch: eight D1280/I1280 fits (blocks 772203, 772303, 772403, 772503) at
  `dc4dbdfcd` on `hmasd-wsl-node`, three block queues concurrent then the fourth;
  handles and receipts in the evidence folder's `EXECUTION.md`. FLAT queues
  (four fits) follow at the same source bytes after the node's answer.

## Correction confirmed (2026-09-15 12:55Z, appended)

`portfolio:cross_direction` confirmed option 1: FLAT stays at `k = 10`
([decision](../../decisions/2026-09-15-fsd-flat-k-correction.md),
[intake](../20260915_fsd_flat_k_correction/INTAKE.md)). The "headroom record" phrase
above reads "untuned package gap" (GAP_D/GAP_I, no MEI, not §11.7 headroom). The FLAT
arm became independent work at 12:55Z; first FLAT fit launched 13:02:49Z at
`dc4dbdfcd` (`EXECUTION.md`).
