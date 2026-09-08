# UCOPE B02 — prepared five-item CM handoff

**Prepared under P33; not dispatched.** Future recipient is the same available
CM `/root/ucope_cm_baseline_b01`, using
`C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906`, branch
`codex/ucope`. It is not alone in the repository: preserve other agents'
edits and retain one editing owner for overlapping paths through commit.

1. **Deliverable and goal:** implement the B02 common per-agent PPO clipping
   amendment for T/G and return an inspectable, checked commit with independent
   credit review. The complete specification is
   [CODE_SPEC §§1–8](UCOPE_UAV_MOTION_PREFIX_B02_CODE_SPEC_20260908.md).
   This handoff itself commissions no coding or UAV invocation.
2. **Owned paths/source:** exact starting source
   `b5607f46fea91379582af8bf87e60b61bc4a269b`, with accepted code surface
   `9c541a8047b8c33e90f09aa65e326180343a23a0`. Own existing
   `experiments/candidates/ucope/uav_motion_prefix_b01/{policy,learner,study}.py`,
   `scripts/run_ucope_uav_motion_prefix_b01.py` and the exact mapped tests in
   CODE_SPEC §1. Main's P33 tree alone lacks some accepted source; retain the
   complete designated checkout. No new checkout, environment edit or framework.
3. **Preserved semantics:** [card §§2–5](UCOPE_UAV_MOTION_PREFIX_B02_SCIENCE_CARD_20260908.md#2-unchanged-host-ownership-and-information)
   and CODE_SPEC §§2–6 fix the same duration{1,4}, t0-only compound action,
   actual masks, all primitive observations/rewards, critic, FP32/RNG,
   counts/final sampling and native primary. New masters 7001/7002 and explicit
   B02 identity are fixed; sum eligible agent losses before the primitive-row
   mean. Preserve historical joint modes and every P21/P24 evidence binding.
4. **Acceptance:** exact original commands and deterministic changed-credit
   cases in CODE_SPEC §8, existing information/reward/count/primary checks,
   and independent review of grouping/normalization/masks/old values/duration
   plus collector/update wiring. One synthetic B02 fixture must report 80
   team steps,8 Adam calls and0 UAV calls. Evidence-spec §11.8.6–7 controls
   proportionate checks and dependent limits; fixture success is no native gain.
5. **Budget/stop:** when separately assigned, source additions≤2,000 lines,
   runner≤600, focused tests≤300 s, one fixture≤60 s plus readback; no new §4
   machinery or real UAV/model-evaluation experiment. Existing in-scope
   corrections stay with the same CM. Return a concrete semantic/scope gap
   rather than widening the algorithm or its budget. P33 allocates no coding
   or checks; all three CM comparison batches are complete and no fourth is
   selected. Prospective scientific caps remain1,800 s/arm,3,600 s/pair,
   7,200 s summed, requiring a later explicit runtime allocation.
