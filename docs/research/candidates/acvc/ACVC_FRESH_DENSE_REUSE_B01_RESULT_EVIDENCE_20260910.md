# ACVC fresh DENSE reuse B01 — result evidence

Date: 2026-09-10. **Valid complete ordinary B/EXPLORE. Both primaries are UP on the one
prospectively selected fresh fit.** The sole allocated study completed and its remote
execution checkout is closed. The native-task-plus-DM subtotal is **180.0564878 s**:
172 s conservative task charge and 8.0564878 s measured DM support. Independent Monitor
tool wall has a retained lower bound greater than 44.34 s and no exact aggregate; full
support/complete-cost conformance is not established if it is included. No successor is allocated.

## 1. Frozen definition and technical acceptance

The [card](ACVC_FRESH_DENSE_REUSE_B01_SCIENCE_CARD_20260910.md) §§2–5 fixes the native host,
fresh fitting law, final checkpoint, C/F/dwell rules, data/RNG and reading. Its §8 applies
the [Portfolio allocation](../../portfolio/decisions/2026-09-10-acvc-fresh-dense-allocation.md)
from immutable Pro response `caf8cf61d92fb3a669f93439a0e2b9967eca943c`. Root assigned the
complete implementation, independent review, execution and intake. This is an ordinary
B with real new learning; E01's zero-new-training exception supplies no authority or time.

Exact accepted source is **60d42dd739ef125a505772f2b1d698b099b43a16**. The DM retained
engineering ownership in `C:/Projects/HMASD-worktrees/codex-acvc`, branch `codex/acvc`.
The optional Implementer changed only the new runner and focused synthetic test; the
independent Reviewer inspected initialization, optimizer/objective, RNG, recurrent state,
actual-command feedback, checkpoint and primary publication. Two partial-failure defects
were corrected before launch and re-reviewed. All protected scientific helpers are unchanged.
The complete path encountered neither interruption nor a missing measurement needed by its primaries.

One synthetic target passed after a fixture-parent setup failure. Both attempts and their
time are retained. There was no native pilot, repeated smoke, broader suite, profile, extra
seed or panel. New non-test source is 441 lines (432 Python and nine shell); the focused
test is 266 lines. Engineering-scope §4 additions: **none**; no source, runner or focused-test
budget breach was found. The native task passes its own cap; the separate Monitor accounting
deviation is recorded in §4. Passing checks establish conformance, not scientific value.
The [execution record](ACVC_FRESH_DENSE_REUSE_B01_EXECUTION_20260910.md) gives the actual
review/correction and exact command rather than a new implementation contract.

## 2. Rule applied verbatim and all outcomes

> **UP** if mean difference >0.01 J; **DOWN** if <−0.01 J; otherwise **WITHIN**, retaining the sign.

F−C and F−dwell are separate primaries; dwell−C is secondary. Each uses the same 64
prespecified initial-world episode keys and its prescribed private proposal streams.
Conditional SE is sample SD of the 64 differences divided by sqrt(64). There is **one
independent new training fit**, not 64 training seeds. No world or adverse return is excluded.

| Fresh base | C mean J | F mean J | Dwell mean J |
|---|---:|---:|---:|
| DENSE/8921 | 0.1150073729 | 0.2379402289 | 0.1502237603 |

| Contrast | Mean ΔJ | Mean ΔS | Conditional SE(J) | Adverse worlds /64 | Rule |
|---|---:|---:|---:|---:|---|
| F−C | +0.1229328560 | +31.4708111419 | 0.0061216915 | 0 | UP |
| F−dwell | +0.0877164686 | +22.4554159547 | 0.0071186843 | 5 | UP |
| dwell−C | +0.0352163875 | +9.0153951872 | 0.0049383583 | 13 | UP |

F−dwell is negative at zero-based episode IDs 20, 25, 41, 46 and 59; its minimum is
−0.0448863449 J. F−C's minimum is +0.0227195012 J. These are retained descriptions of
this panel, not a requirement that every world or future seed improve.

The [704 episode rows](fresh_dense_reuse_b01_20260910/raw/episodes.jsonl),
[1,024 update records](fresh_dense_reuse_b01_20260910/raw/updates.jsonl) and
[raw summary including all paired vectors](fresh_dense_reuse_b01_20260910/raw/summary.json)
are preserved. The [DM reduction](fresh_dense_reuse_b01_20260910/dm_analysis.json) independently
reads every raw row, verifies exact training/evaluation/reset/update keys, finite quantities
and S=256J, then recomputes means, sample SEs, signs, adverse IDs and intervention totals.
It matches all published primary vectors and reductions. The small standard-library
calculation uses `statistics.mean` and `statistics.stdev`; it performs no resampling,
model loading, new evaluation or training-population aggregation.

## 3. Actual exposure, learner movement and information boundary

Machine-generated exposure: **scientific_invocations=1; fresh_fits=1; selected_final_checkpoints=1;
training_episodes=512; training_team_steps=131072; rollouts=256; Adam_calls=1024;
backward_calls=1024; update_records=1024; replayed_actor_agent_steps=2621440;
critic_update_rows=524288; evaluation_panels=3; evaluation_episodes=192;
evaluation_team_steps=49152; total_team_steps=180224; collection_actor_agent_forwards=901120;
training_critic_forwards=131072; postfit_loads=3; constructors=4; unscored_constructor_resets=4;
gate_constructions=0; duration_heads=0; selector_updates=0; evaluation_updates=0.**

The dominant actual factors are 512×256×5 training forwards, 256×4 full-rollout updates,
and 3×64×256×5 evaluation forwards. All 69,079 parameters were trainable under the fixed
nonzero-lr optimizer. The measured movement is:

| Parameter group | Count | Initial norm | Final norm | Displacement | Displacement / initial norm |
|---|---:|---:|---:|---:|---:|
| Actor | 34,902 | 12.6233969 | 12.9938717 | 3.1786160 | 0.2518035 |
| Critic | 34,177 | 9.2795334 | 11.3352232 | 6.2899752 | 0.6778331 |
| Combined | 69,079 | 15.6671581 | 17.2431927 | 7.0475082 | 0.4498268 |

These observations establish real learner exposure and parameter mobility, not improvement
over initialization: the card includes no initial-policy evaluation. The private DENSE
branch projection moves from zero norm to 0.6326178908; its relative displacement is
undefined at a zero initial norm and remains null in the raw record.

Training master 8921 and evaluation namespace 8922 were selected before output. All 512
training resets are 892101000–892101511; all arms use final-panel world keys
892202000–892202063. The source preserves the separate proposal streams and required
constructor draw order. The fit uses the final episode-512 checkpoint regardless of
base attractiveness. Evaluation has no critic, optimizer or gate updates.

The native host remains five fixed UAVs and 50 users, 256 primitive steps, CPU FP32,
Torch intra/inter-op threads 1/1. The actor receives only own native observation, private
GRU state and its actual command; the global critic input exists only during fitting.
F and dwell each evolve their own recurrent state, joint trajectory and Binding history,
including on overridden proposals. The preceding unique lowest-SINR anchor, current
1–19-user loss predicate and away-dot remain unchanged; a saturated preceding list may
supply an anchor. Membership, entity identity and primitive timing remain fixed.

| Rule | Eligible opportunities | Executed intervention | Distinguishable commands |
|---|---:|---:|---:|
| F | 7,661 | 7,661 retraces | 7,661 |
| dwell | 4,533 | 4,533 dwells | 4,533 |

C bypasses Binding: its zero cue/apply counters mean unmeasured cue incidence, not no link
loss or no executed proposals. Dwell's predicate is evaluated on its own history; it is
not assigned F's event times or dose. These counts therefore do not isolate retrace
causality. The action path remains joint motion/interference → own link history and
proposal → actual command → changed joint geometry/service → later observations and team return.

## 4. Admission, whole cost and deviations

The exact supervisor handle was `acvc-fresh-dense-b01-8921-60d42dd73` on `wsl_4070`,
in `/home/wu/hmasd-worktrees/acvc-fresh-dense-b01-60d42dd73`. Fresh destination-node
admission and the runner were joined by `&&` within the same outer timer and timeout.
The [admission receipt](fresh_dense_reuse_b01_20260910/raw/fresh_dense_reuse_b01_8921_admission.json)
passed physical and effective availability with 15,633,838,080 bytes against 4,294,967,296.

| Measured or conservatively charged boundary | Seconds |
|---|---:|
| Runner start before imports through just before summary serialization | 157.5084427830 |
| Outer admission/startup through command publication and exit | 168.37 |
| Integer supervisor start-to-exit duration | 169 |
| Wider conservative whole-task charge | **172** |
| DM runtime support: both checks, collection, numerical intake and closeout | **8.0564878** |
| Native task plus DM support subtotal | **180.0564878** |
| Independent Monitor retained tool wall, separate boundary | **>44.34; exact aggregate unavailable** |

The wider charge is ceil(169 + one second of timestamp granularity + the supervisor's
recorded one-second final sleep + the entire 0.6461753 s submit-client interval).
The monitor directly observed finished/exit0 and no active tmux session. This is a
conservative task charge, not a new precise timer or a cross-host timestamp subtraction.
The native task passes its 330 s limit and the measured DM subset is within 30 s. Every DM
support call, including failed fixture setup, is itemized in the
[collection receipt](ACVC_FRESH_DENSE_REUSE_B01_COLLECTION_20260910.json). New focused
checks total 3.7175557 s; the research directory's prior-plus-new focused total is
27.7442098 s against 300 s. No allowance is reset by correction or borrowed from E01.

**Budget/accounting deviation:** the subsequent Root-forwarded Monitor bookkeeping receipt
reports about 0.8 s for initial status, retained terminal-query tool-wall parts 30.2 s and
14.14 s, and about 0.7 s for bounded logs; an adoption message took about 0.1 s. Its exact
aggregate is unavailable. Root confirmed that this lower-bound tool wall is greater than
44.34 s and must remain separate from both the native task and measured DM support. No
fresh query was made to repair the missing aggregate. The Monitor lower bound alone is
above the 30 s support limit if that surface is included. Consequently **complete≤360 s
and support≤30 s conformance is unestablished if Monitor observation is included**.
This record neither silently charges nor exempts it, and does not call the DM subtotal
the full cost. Root retains any resulting same-Portfolio-node consequence; no local
allocation exception, repetition or changed scientific polarity follows.

Peak RSS is 555,852 KiB (542.82421875 MiB) from the outer command. Aggregate CPU work and
cgroup headroom are unmeasured; the raw `resources_unmeasured` flag is preserved. These
limits do not invalidate the trustworthy native returns or learner counts. The runner
wall excludes some admission/final exit work and is not substituted for the complete bill.
No timeout, damaged primary, missing update record, or scientific-semantic deviation occurred.

## 5. Preservation, prediction receipts and claim ceiling

Raw evidence was committed/pushed at `809ecf104`, with the three otherwise ignored raw
logs added at `236dc02fa`. All 16 native/support/supervisor files were captured in a local
archive whose SHA256 matches the remote archive:
`441de0bda690b1d99c2cfc653c2cd3c088f4bb434062117df755db18942c16a4`.
The 282,957-byte final checkpoint has SHA256
`0e2e2b78b8c37d538d143b9c736e58e4bb0de925fb641c230ba1999a230bf0cb` and remains in
that archive and the extracted local runtime root. Exact locations and per-file hashes
are in the collection receipt and DM reduction. No checkpoint was reloaded during intake.

After verified preservation and terminal/no-live-session checks, scoped closeout removed
only this detached remote execution checkout and its supervisor metadata. At remote
`2026-09-11T02:50:53+08:00`, both paths were confirmed absent and the checkout absent from
`git worktree list`. Exact source remains committed. The shared local authoring checkout
and local scientific archive remain; Root owns integration and any later reclamation.

The prospective UP probabilities .75 (F−C) and .65 (F−dwell) both matched. Brier scores
are .0625 and .1225, mean .0925. Owner prediction: **not taken (unattended)**.
The [scientific intake](ACVC_FRESH_DENSE_REUSE_B01_INTAKE_20260910.md) interprets these
results as preliminary fixed-package support on one newly trained base. They establish
neither training-population stability nor isolated retrace causality, history necessity,
optimality, tuned headroom, transfer or formal UAV-validation entry. No B consumption
state, automatic successor, T/G restart or direction/Portfolio disposition follows.
