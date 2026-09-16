# Intake: host headroom card convergence round (PRO_FINAL, 2026-09-16 05:30Z)

Request `2026-09-16-fsd-host-headroom-card-convergence-01` (TASK `fd9502467`, sent once 2026-09-16
04:59:14Z, operation 5655e1ba-6c1e-4d27-a45f-2f476f756986, one click); complete response at codex/fsd
`1462d3954` ([archive](archive/RESPONSE.md), 38,865 B, sha256 0e9f6ca308ef8bd70d68836708a1db71faeae26a1f378f3eff60b1f42ac7fc66); all fourteen references accessed by the node.

## Decision formed

**C**: the host headroom card is rejected as a "private FLAT is a same-information headroom" card; the
node fixes a different first CONFIRM object, `FSD_MATCHED_INFORMATION_BASELINE_B01` (transcribed in
[FSD_MATCHED_INFORMATION_BASELINE_B01_PROSPECTIVE_CARD_20260916.md](../../FSD_MATCHED_INFORMATION_BASELINE_B01_PROSPECTIVE_CARD_20260916.md)): standing D1280 versus a central-input flat (CF) whose actor receives the legal
central snapshot (global state plus the six joint observations, refreshed at reset and at the k = 10
team-decision steps) and an ego one-hot; I1280 dropped; stage 0 tunes CF's learning rate over
λ ∈ {0.5, 1, 2} on two seeds with a fixed selection rule; stage 1 five fresh blocks; 45 rollouts, nine
panels; primary mean over blocks of G_b = J45(D1280) − J45(CF); MEI .05 J fixed; importance labels
D_REFERENCE_ABOVE / SMALL_SIGNED / CF_REFERENCE_ABOVE with independent interval labels; registered
incomplete branches; 16 fits, ordinary plan about 183,500 s native. `headroom_record: not established`.

## Why the node rejected the card (its three reasons, kept verbatim in substance)

1. Same host and a central critic are not the same execution information: the private FLAT actor never
   sees the central information the skill path uses; learning-rate tuning does not change that.
2. Multiples of a pooled arm SD are not the inference the programme adopted: the .079 J figure was the
   paired I1280 − D1280 block SD, not an arm-level SD; a 2s / 1s rule with a 4-of-5 gate mixes in the
   I1280 arm and discards pairing; importance and uncertainty are read separately.
3. Neither standing D1280 nor the review's .67 J is an established upper reference on this host,
   information and budget; the .67 figure leaves the object entirely.
Also corrected: pre-registered branches may not manufacture "the host does not reward skills", a
code-defect verdict or a lifecycle consequence; lifecycle stays with the owner-triggered review.

## Conformance check (AGENTS.md section 2)

Decides the posed question at its declared class (a B card for one direction) and inside the
node's authority (fixing the card is direction-tier). Consistent with the workflow lanes (CONFIRM:
five seeds satisfies "at least two"; one Pro round at freeze; rule reads every covered outcome) and
with Portfolio control (no lifecycle, no Portfolio Send, one object in the standing budget). The CF
adapter is new research code under ENGINEERING_SCOPE_SPEC (disposable research tier) with
independent review required by lanes section 6. No conflict found; applied as **PRO_FINAL**.
The DM's card and its thin entry (`run_fsd_host_headroom_b01.py`, its launch script and tests,
codex/fsd `4357579b9`) are superseded; the entry is replaced by the new runner in the next commit.

## Decisions this intake produces

Direction tier: object fixed by the node (C). Ledger row 43 (selection; alternatives A/B/D on record).
Object tier: none pending. Next: L0 for the CF adapter and the new runner, independent review,
node tests, stage-0 launch through the operator after fresh admission. Approved-set first-object
wording updated (the node states this is within existing authority). Owner items: none (a
confirmatory result, not a lifecycle decision, produces the P1 item at intake).
