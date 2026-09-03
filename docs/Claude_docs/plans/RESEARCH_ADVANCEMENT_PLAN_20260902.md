# Advancement plan for the flexible-skill-duration direction (2026-09-02)

Written by Claude Code (Fable 5.1) at the owner's request ("可以做一个推进研究的 plan，使用 ask 和我
确认细节后等待实验代码效率优化完后推进"). It sequences what follows E0 and the throughput refactor,
says what each step needs from the owner and what runs without them, and fixes the budget and
launch policy. Decisions confirmed with the owner are in §7. Governing texts:
`FLEXIBLE_SKILL_DURATION_PLAN_20260902.md` §3 (schemes D0 to D8), §5 (ladder E0 to E6), §11
(decisions and predictions); `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md` §5.2, §11.

## 0. Where things stand

| Item | State |
| --- | --- |
| ADR 01 (D2 policy interruption) | implemented on the base route; `off` byte-identical; accepted (review Parts VII, VIII) |
| ADR 02 (relay corridor host) | implemented, references and margins exact, joined to the learner (Parts VI, VIII) |
| E0 (exposure, probe set) | two seeds, four arms complete, probe set frozen (Part IX) |
| Throughput refactor P0–P3 | done and accepted (review Part X, commit `9f4d0e4ba`): collection 240 s → 18 s per rollout, fingerprint unchanged; P4 decided after E1's intake (§7 decision 4) |
| E1 | complete 2026-09-03, six runs, accepted (review Part XI): the owner's prediction stands unrefuted, the age feature is not carried into E2; one contract erratum (accuracy against a foreign labelling) registered (`E1_AGE_INPUT_RESULT_20260902.md`) |
| Open from ADR 02 | the finite `c` grid; the E5 coupling term (designed when E5 is scheduled) |

## 1. The sequence

Each step is one contract in the E0 format, one prediction on record before launch, one intake
part in the review file, and the decisions it produces. Steps are ordered by dependency, not by
calendar.

| # | Step | Depends on | Host | Runs | What it settles |
| --- | --- | --- | --- | --- | --- |
| R0 | Refactor P0–P3 | — | scenario 1 | tests, timing | environment cost; re-frozen fingerprint |
| R1 | Refactor P4 (update phase) | R0 measurement | — | fingerprint | whether the update is worth engineering now |
| E1 | Age input at fixed `k` (D0 vs D1) | R0 | scenario 1 | 6 (2 arms × 3 seeds), `R = 20` | C2 at fixed `k`; whether the age input is used; the reviewer/owner prediction |
| E2 | D2 at `delta = 1`, sweep `c` | E1 intake; corridor driver | homogeneous corridor (`lambda_1 = lambda_2`) first | `c` grid × 2 seeds + D0 `k` sweep, `R = 20` | the finite `c` grid (ADR 02 open question); D2 vs best fixed `k`; segment length monotone in `c`; chattering on the change flag |
| E2b | E2's best `c` on scenario 1 | E2 | scenario 1 | 2 arms × 3 seeds | whether the corridor's `c` transfers to the UAV host |
| E3 | Heterogeneous hazard | E2 | corridor, three proposal rows | D2 at chosen `c` vs best fixed `k`, 3 seeds | positive gap of the order of `m_dur` |
| E4 | Random-duration events | E2 | corridor, three renewal laws at `E[D] = 20` | D2 vs D0 (`k = 20`) vs D8 comparator, 3 seeds | D2 insensitive to the law; D0 and D8 degrade with `Var(D)` |
| C-gate | Promotion decision | E3 or E4 repeated across 3–5 seeds | — | — | frozen C-BENCH contract, oracle-retuned `k*`, failure boundary |
| E5 | Asynchrony | coupling term designed (ADR 02 decision 3) | corridor with coupling on | individual-only vs two-level interruption | team-level switch rate; `Z` semantics on probes |
| E6 | Add-ons D4, D5 | E3/E4 | corridor | — | delay to switch; unobservable events |
| U | UAV transfer of E4 | E4 | scenario 7 failures | — | whether the corridor result survives the UAV host |

E2 is on the corridor first because the corridor gives exact references (the switching oracle and
every fixed-`k` oracle) so "D2 matches the best fixed `k`" is measured against a known number, and
because it runs at 3 × 10^4 steps/s. E2b then checks the chosen `c` on scenario 1, where the only
reference is the D0 sweep itself.

## 2. What each step needs from the owner

1. **A prediction, one sentence, before launch.** The reviewer drafts the contract with the two
   competing mechanisms written out and the differentiating measurement, then asks the owner to
   choose or write their own. The prediction goes into plan §11. "Unclear" is an allowed answer;
   the step then runs as exploration without a calibration point.
2. **The decisions the intake produces.** After each result the reviewer lists the decisions
   (usually one to three) and asks them one at a time, as in the ADR rounds.
3. Nothing else. Launch, execution, intake and the next contract run without the owner under the
   policy in §3.

## 3. Launch and budget policy (confirmed in §7)

- **Trigger-based launch.** A contracted step launches when its dependency is in (the previous
  intake is committed) and its prediction is on record. The reviewer does not wait for a separate
  "go" once the policy is confirmed.
- **Wall-clock cap per study** and **concurrency** per §7. Runs are paired by seed so that a stop
  at any point leaves matched arms.
- **Execution** by an Opus session in an isolated worktree at the launch commit, pushing its own
  branch; the reviewer integrates after intake. Learner code does not change during a study; a
  refactor waits for the study to finish or the study records the sha it ran on.
- **Intake** is a review part in `ADR_01_02_ADVERSARIAL_REVIEW_20260902.md` (renamed by an index
  entry, not by moving the file), with the result document accepted, quarantined, or sent back.

## 4. Budget estimate

Assuming R0 halves the scenario-1 rollout (E0: 213 s at 16 lanes → ~105 s) and the corridor
rollout is update-bound (~100 s at 16 lanes, `H = 400`):

| Step | Runs × rollouts | Wall (sequential) | Wall (2 concurrent) |
| --- | --- | --- | --- |
| E1 | 6 × 20 | ~3.5 h | ~2 h |
| E2 | (5 `c` + 5 `k`) × 2 seeds × 20 | ~11 h | ~6 h |
| E2b | 6 × 20 | ~3.5 h | ~2 h |
| E3 | 3 rows × 2 arms × 3 seeds × 20 | ~10 h | ~5 h |
| E4 | 3 laws × 3 arms × 3 seeds × 20 | ~15 h | ~8 h |

R1 (P4) would reduce every row by whatever it takes off the update; the decision whether to do it
before E2 is taken from R0's measurement.

## 5. Open design items resolved inside contracts (no owner decision needed)

- The `c` grid for E2: from E0's D0 gap histogram (agent gap median 0.22, q90 0.64, max 1.66 in
  logit units) the grid `{0.25, 0.5, 1.0, 2.0, inf}` spans the distribution; the contract fixes it
  and records the histogram it came from.
- The D0 `k` sweep for E2 on the corridor: `{1, 2, 5, 20, 40}` as the mechanics page proposes.
- Evaluation budget per arm: 4,096 matched episodes on the corridor (ADR 02), 8 deterministic
  episodes per evaluation on scenario 1 (E0), both recorded with the measured spread.
- Exposure line, preflight, quarantine, manifests: as E0.

## 6. Stop conditions for the programme

- E2 finds no `c` at which D2 reaches the best fixed `k` on the homogeneous corridor: D2's policy
  proxy is too noisy; D3 (value-based interruption) becomes the next object per plan §3, and E2 is
  re-run with D3 before E3.
- E3 shows no positive gap at the large row: the direction's claim is not supported on its own
  host; the owner decides between E4 and parking.
- Any study quarantined twice on the same seed: the runner, not the science, is the problem; the
  reviewer fixes the runner before the next launch.

## 7. Decisions confirmed with the owner

Confirmed one by one on 2026-09-02:

| # | Decision |
| --- | --- |
| 1 | Trigger-based launch for E1 to E4: the reviewer launches when the contract is committed, the dependency is in, and the prediction is on record; the owner is asked only for predictions and post-intake decisions |
| 2 | E2 runs on the homogeneous corridor first; E2b checks the chosen `c` on scenario 1 |
| 3 | Wall-clock cap 8 hours per study; two runs may execute concurrently (4 threads each) on this machine; a study that would exceed the cap reduces seeds or lanes and records the deviation |
| 4 | E1 runs before refactor P4; P4 is decided after E1's intake from R0's measurement |

Immediate consequence: when the refactor's P3 is reviewed and integrated, E1 launches without a further prompt.
