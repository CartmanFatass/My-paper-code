# VSP-C1 K4 B02 budget512 result intake — 2026-09-06

Object `VSPC1-K4-FACTOR-VALUE-B02-BUDGET512`
([card](VSPC1_K4_FACTOR_VALUE_B02_BUDGET512_SCIENCE_CARD_20260906.md),
[CM objective](VSPC1_K4_FACTOR_VALUE_B02_BUDGET512_CM_OBJECTIVE_20260906.md),
[CM record](VSPC1_K4_FACTOR_VALUE_B02_BUDGET512_CM_RECORD_20260906.md)). Direction Manager:
the Claude research hub. Predictions were on record in card section 5 before either arm was
launched; the reading rule in card section 3 is applied below in its written order.

## 1. Provenance (observation)

| Fact | FACTOR | GENERIC |
| --- | --- | --- |
| Node / task | `wsl_4070` / `vspc1_b02_factor_s3_90c730a098d1_01` | `wsl_4070` / `vspc1_b02_generic_s3_90c730a098d1_01` |
| Launch sha / worktree | `90c730a098d1c39d4265684c40afdf881909fa43` / `/home/wu/hmasd-worktrees/vspc1_b02_90c730a098d1` | same |
| Runner | `scripts/run_vspc1_k4_factor_value_b02_budget512.py --arm FACTOR --seed 3` | `--arm GENERIC --seed 3` |
| Exit / status | 0 / `complete`, `primary_dependency_defects: []` | 0 / `complete`, `primary_dependency_defects: []` |
| Outer wall / peak RSS (`/usr/bin/time -v`) | 2.66 s / 508 MB | 2.17 s / 510 MB |
| Inner wall through primary readback / RSS | 2.38 s / 479.0 MB | 1.92 s / 479.5 MB |
| Aggregate CPU through primary readback | 2.24 s | 2.10 s |
| Optimizer steps / parameters | 512 / 188 | 512 / 191 |
| Evidence | `results/k4_b02_budget512_seed3_20260906/factor/` (`summary.json` sha256 `352c0df4…`) | `results/k4_b02_budget512_seed3_20260906/generic/` (`summary.json` sha256 `0389c044…`) |

Memory admission passed on the executing node immediately before each runner (`admission.json`
in each folder). Device `cpu`, dtype `float32`, one compute thread, batch 32 episodes, seed 3
streams as declared (numpy context `[3, 101]`, exploration `[3, 102]`; torch `3201/3202` and
`3301`). Evaluation is greedy and consumes no random draws.

## 2. Dependency check (reading-rule row 1)

Both invocations completed with the required prospective instrumentation. Trajectory checks
over 16,648 episodes per arm report zero held-action, partner-timing, reward, return,
terminal-bootstrap and loss-weight violations. Counts equal the card's expected counts exactly:
training 16,384 episodes / 98,304 joint steps / 32,768 legal decisions / 32,768 renewals
(24,576 at p = 2, 8,192 at p = 6); evaluation 264 / 1,584 / 528 / 528 (396 / 132). All 33
curve points and all eight context strata are present for both arms. No primary dependency is
damaged; row 1 does not apply and the full reading proceeds.

## 3. Measurements (all prespecified in card section 2)

| Quantity | FACTOR | GENERIC | Difference (FACTOR − GENERIC) |
| --- | --- | --- | --- |
| J(0) | 0.458333 | 0.500000 | −0.041667 |
| J(128) (same-instance original-budget read-out) | 0.750000 | 0.666667 | **ΔJ_128 = +0.083333 (+1/12)** |
| J(512) (primary endpoint) | 0.833333 | 0.833333 | **ΔJ_512 = 0** |
| L = J(512) − J(128) | L_F = +0.083333 | L_G = +0.166667 | **D = ΔJ_512 − ΔJ_128 = −0.083333 (−1/12)** |
| J(512) − J(0) | +0.375000 | +0.333333 | |
| AUC(0:128), divisor 8 | 0.643229 | 0.640625 | +0.002604 |
| AUC(0:512), divisor 32 | 0.763672 | 0.718750 | +0.044922 |
| AUC(128:512), divisor 24 (descriptive) | 0.803819 | 0.744792 | +0.059028 |
| ‖θ_0‖ / ‖θ_128‖ / ‖θ_512‖ | 4.020 / 4.545 / 5.430 | 3.877 / 4.118 / 4.490 | |
| ‖θ_128 − θ_0‖ / ‖θ_512 − θ_0‖ / ‖θ_512 − θ_128‖ | 2.364 / 3.557 / 1.928 | 1.935 / 2.531 / 1.334 | |

Curve shape (33 points, u = 0, 16, …, 512). FACTOR first touches 5/6 at u = 208 and holds it
without interruption from u = 400. GENERIC first touches 5/6 at u = 432, dips to 0.791667 at
u = 448, and holds 5/6 from u = 464. Under the ε = 0.1 tail both arms keep learning
(L_F, L_G > 0), with GENERIC's late gain twice FACTOR's.

Final context profile at u = 512 is identical for both arms: the four p = 2 contexts return
1.0 and the four p = 6 contexts return 2/3. 5/6 is the host's declared analytic free-policy
reference (B01 card, B01 result evidence line "the declared analytical free-policy reference
remains 5/6"), so both arms sit exactly at that reference at the endpoint and the remaining
loss is the same long-period profile in both.

Seed-3 0:128 prefix listed beside the B01 seeds, origin stated (a prefix of the B02 seed-3
training path under the B01 exploration schedule, not an extra B01 seed; no pooled mean is
formed and no 512 point enters the old three-seed mean):

| Seed | Endpoint at 128 (FACTOR − GENERIC) | AUC(0:128) difference | Source |
| --- | --- | --- | --- |
| 0 | −1/24 | −0.028646 | B01 |
| 1 | +1/12 | +0.033854 | B01 seed-1/2 card |
| 2 | +1/12 | +0.023438 | B01 seed-1/2 card |
| 3 (prefix) | +1/12 | +0.002604 | this B02 path |

MEI was declared descriptive absolute 1/12. ΔJ_128 equals it exactly; ΔJ_512 is zero; D equals
−1/12. These magnitudes are kept as they are.

## 4. Reading rule applied in order (card section 3)

1. Damaged dependency or incomplete invocation: no (section 2).
2. "Seed 3's positive gap holds or widens at 512 … and FACTOR shows visible late absolute
   improvement": no. FACTOR does improve late (L_F = +1/12), but the gap does not hold; it
   closes to zero.
3. "128 point adverse, 512 point favourable": no. The 128 point is favourable.
4. **"128 point favourable, 512 shrinks to zero or negative, or GENERIC improves more late":
   yes on both clauses** (ΔJ_512 = 0; L_G = 1/6 > L_F = 1/12). This is the first applicable
   row. Bounded reading, in the card's words: *limits the case for extending the early
   advantage; proves neither equivalence nor general negative transfer.* What it changes next:
   *stop extending the unchanged combination for a larger endpoint; keep the short-budget
   evidence; the automatic-extension path for this model ends.*

Two later rows record facts that qualify, but do not replace, the row-4 reading:

- Row 6 fact: both arms reach the host's analytic reference 5/6 with the same final context
  profile. ΔJ_512 = 0 is therefore an equality at the reference ceiling, not GENERIC overtaking
  FACTOR on an open scale. The curves are not without difference (FACTOR reaches and holds the
  reference earlier; AUC(0:512) and AUC(128:512) both favour FACTOR), so row 6's "no useful
  curve difference" clause is not met and its consequence is not invoked here. The ceiling fact
  is recorded because any later comparison of these parameterizations at 512 updates on this
  toy has no endpoint room left.
- Row 7 guard: endpoint (0) and the two AUC windows (positive) do not agree in sign. No metric
  is picked to declare a winner; the positive AUC values stand as measured descriptions of the
  paired path and do not become a cross-period sharing-efficiency narrative.

What this result shows: in one fresh training instance, the parameterization that was ahead at
the original budget (by the declared minimum effect) was caught by the generic comparator when
both were run four times longer, and both arrived at the host's reference. The observed native
consequence is time-to-reference, not endpoint level.

What it does not show: equivalence of the two parameterizations; negative transfer; a
population budget interaction (one instance); anything about the three B01 seeds' own 512
behaviour; a claim about the production host.

## 5. Predictions scored

- **Pro (r02 working prediction)**: "a seed-3 gap at 128 is more likely to shrink than reliably
  widen" — matched (shrank to zero). Refutation condition ("FACTOR's late absolute return and
  the relative gap rise together") not met. Not refuted.
- **DM (hub)**: L_F > 0 and L_G > 0 — right. |ΔJ_512| ≤ 1/12 — right (0). D opposite in sign to
  ΔJ_128 — right (−1/12 vs +1/12). L_G ≥ L_F — right. Late AUC difference smaller in magnitude
  than the AUC(0:128) difference — **wrong** (+0.059 vs +0.0026; the DM predicted regression
  in the late window and instead the late window carries most of the whole-curve difference).
  Most likely branch "fourth row or fifth" — right (fourth).
- **Owner**: not taken (unattended).

## 6. Exposure and cost

Two arm invocations at one fresh seed, as the card authorized; no other exposure. Usage per
valid result: 4.83 s outer wall in total (2.66 + 2.17) against a 2,700 s cap per arm; peak RSS
510 MB. Card cost projection (~30 s per arm from the B01 cost law) was conservative by an order
of magnitude; the measured cost law is retained in each `summary.json`.

## 7. Check against current instructions and specifications

Evidence-spec §11.8 ordinary burdens apply; no exact-replay, bit-identity or exhaustive
diagnostic is claimed or required. The B01 readings, initial values and adverse observation are
unchanged (card section 2). The old AUC divisor and the three-seed mean are untouched. Nothing
in this reading conflicts with the archived r02 Convergence decision, AGENTS.md §2 or the
engineering scope specification; no exception is requested.

## 8. Decisions this intake produces

**Object tier (owner absent; §4).**

1. Accept both invocations as one valid completed B02 result (technical). Options: accept /
   return for a defect. No defect; accepted. `OWNER_DELEGATED (unattended, 2026-09-03
   instruction)`.
2. Apply the card's row-4 consequence (selection): the automatic-extension path for this
   model/optimizer combination ends; no 1,024 or 2,048 extension, no fourth B01 seed, no
   repeat of this instance. Options: apply the prewritten consequence / propose a deviation.
   Applied as written. `OWNER_DELEGATED (unattended, 2026-09-03 instruction)`.

**Direction tier.** What K4 does next after B02 (a named new host question, a comparator
representation question, a tabular control, or ending the public-plan toy family) is an
open-or-close decision for `em:vsp_c1:convergence`. The DM does not select it locally. A
post-B02 Convergence packet is prepared with this intake as its evidence; until the archived
decision arrives, VSP-C1 parks at a clean boundary (everything committed, no run live) and
leaves the hub's working set. The DM's recommendation to the node, for the record: do not
repeat the toy at any budget; if K4 continues, the next object should change the question
(representation of the comparator or a host with room above the current reference), not the
budget.

Owner brief (Chinese): `docs/research/portfolio/owner/briefs/vsp_c1/2026-09-06_K4-B02-budget512-result.md`.

scope: none
