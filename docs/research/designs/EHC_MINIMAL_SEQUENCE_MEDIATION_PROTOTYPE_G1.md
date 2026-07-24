# EHC minimal sequence-mediation prototype G1

```text
assignment_id=EHC_MINIMAL_SEQUENCE_MEDIATION_PROTOTYPE_G1
design_status=PM_ACCEPTED
action_kind=bounded_nonformal_measurement_prototype
source_family=ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1
formal=false
formal_result_branch=none
conclusion_bearing_iterations_consumed=0
iterations_remaining=4
fitting_duration_support={6,14}
heldout_duration_support={10,18}
registered_roster_sizes={2,3}
horizon=80
sequence_window_active_steps=6
opportunity_rule=every_active_transition
maximum_roster_capacity=4
normalized_active_count_denominator=4
schedule_mapping=cyclic_split_permutation
action_selection=greedy_argmax_lowest_index_tie_break
episode_cutoff=unfinished_segment_censored_and_eligible
splits=2
roster_sizes=2
durations_per_split=2
duty_sign_starts=2
schedule_rotations=2
controller_count=6
episodes_per_controller=32
total_natural_episodes=192
analysis_output=measurement_tuple_only
interpretation_authority=project_manager
```

## Question and disposition

This prototype asks one question: can exact-snapshot paired sequence mediation
distinguish event-held temporal organization from `CE-RANDOM-USE`,
`CE-EXOGENOUS-LIFETIME`, and `CE-LOGIT-WITHOUT-BEHAVIOR` before any learned G1
comparison is funded?

Project Manager selected the exact-snapshot design over two alternatives:

- natural-only longitudinal mediation is cheaper but cannot remove selection
  bias;
- a static factorial null battery is cheaper still but cannot test downstream
  sequence or terminal consequence;
- the selected design combines a small factorial null battery with paired
  continuation branches, adding causal sequence information without training.

The positive mechanism controller is a synthetic measurement control, not
evidence that a policy learned EHC. `RECURRENT_CONTROL` is retained as the
ordinary-recurrence reduction and may match the positive control. No result from
this prototype adopts a mechanism or changes a formal branch.

## Independent G1 source

The prototype uses a new temporal-duty taskbed. G0 source, runner, analyzer, thresholds, seeds and result remain closed. In particular, G0
`formal_path_exercise`, `select_result_branch`, Stage-2 packing, audit rows and
result schemas are forbidden as G1 evidence.

Each anonymous lifecycle has hidden state
`(g, age, remaining, correct_count, terminal_streak)` with `g in {-1,+1}`.
The actor sees only ordered fields `(cue_value, cue_present, new_segment,
join_flag, rejoin_flag, normalized_active_count)`. The cue reveals `g` for
exactly two active transitions. Identity, lifecycle key, duration, remaining
time, progress, reward, success, future duty and future membership are never
actor inputs.

The primitive action space is `{-1,0,+1}` and correctness is `action == g`.
At the start of a global step, membership events are applied; active members
then observe, choose event/mark/action, and transition. Active lifecycle age is
incremented and remaining duration decremented after the action. When remaining
reaches zero, the segment succeeds iff the last two active actions were correct;
the next segment is initialized for the next global step. Temporary LEAVE
freezes physical, recurrent and commitment state. REJOIN restores it. Terminal
LEAVE censors the incomplete segment and gives no completion credit. A segment
unfinished at the horizon-80 cutoff is likewise censored, remains in the
eligible denominator and receives no completion credit.

The horizon is 80. Initial roster sizes `{2,3}` are enumerated equally. Fitting
membership events occur at global steps `12 TEMP_LEAVE`, `16 REJOIN`, `28 JOIN`
and `68 TERMINAL_LEAVE`. Held-out events occur one active opportunity later at
`13,17,29,69`.

For an initial roster of size `n`, logical temporary target is slot `1`, logical
terminal target is slot `0`, and JOIN creates slot `n`; maximum capacity is 4.
For schedule rotation `r in {0,1}`, fitting maps an existing logical slot `j` to
physical slot `(j+r) mod n`; held-out maps it to `(j+r+1) mod n`. REJOIN targets
the same physical lifecycle frozen by TEMP_LEAVE. Actor
`normalized_active_count` is always `active_count / 4`.

Every active transition is an event opportunity; inactive members receive no
opportunity and their opportunity clock freezes. This constant opportunity law
is independent of target, duration, membership schedule and outcomes.
Membership, duty, event, mark and target streams remain independently owned.

Fitting cells use durations `{6,14}` only; held-out cells use `{10,18}` only.
Together they preserve the declared G1 support `{6,10,14,18}` while making
duration transport measurable. Duty signs, roster sizes and schedule rotations
are enumerated, not selected after results.

Utility is `U=0.75A+0.25B`, where `A` is correct active actions divided by
active action opportunities and `B` is successfully completed segments divided
by all started eligible segments. Censored segments remain in the eligible
denominator and receive no success credit. The manifest precomputes action and
eligible-segment denominators from exogenous schedules, so per-step reward
contributions sum exactly to U. No intrinsic reward exists.

## Controllers and null families

All logit-based controllers use the action order `(-1,0,+1)`, identical actor
information, zero shared base logits, and the explicit treatment path

```text
primitive_logits = base_logits + W_z(m*z)
W_z(s) = (-4s, 0, 4s)
```

`m=1` only for an active EHC treatment and `m=0` for DUM/OR controls.
Softmax probabilities are retained for `instantaneous_tv`, but primitive
actions use greedy argmax in fixed action order `(-1,0,+1)` with the lowest
index winning a tie. The registered action RNG therefore consumes zero draws in
this deterministic prototype; both paired branches verify that zero-draw
identity explicitly.

- `MECHANISM_CONTROL`: RENEW with the visible duty mark at a new segment and
  KEEP at later opportunities; the held mark biases every active action.
- `RANDOM_USE`: KEEP/RENEW is a state-independent Bernoulli(0.5) draw; a renewed
  mark is an independent sign and persists.
- `EXOGENOUS_LIFETIME`: RENEW occurs every fourth active opportunity; its mark
  uses a visible cue when available and an independent sign otherwise.
- `LOGIT_WITHOUT_BEHAVIOR`: event and mark are aligned at segment start but the
  mark bias is applied only on that event step and is not held downstream.
- `RECURRENT_CONTROL`: the OR-style base recurrent state remembers the two-step
  cue and chooses the duty action without any event or mark path.
- `DUM_CONTROL`: it receives the same event/mark variables as
  `MECHANISM_CONTROL`, but `m=0`, so its primitive logits remain the shared base
  logits.

These are measurement constructions, not trained policies. Natural event rows
are never replaced by forced rows.

## Snapshot and interventions

An eligible branch point is the first active opportunity with `age=3`, an
expired cue, at least two remaining active opportunities, and no terminal
lifecycle event at the same global step. Selection uses only current state.

The snapshot contains environment state, frozen inactive lifecycle state,
controller recurrent/commitment state, segment counters, and every owned RNG
state. Each branch restores independently from that snapshot. Future draws are
regenerated from cloned authoritative states; no natural future action, reward
or outcome is copied into a branch.

Two contrasts remain separate:

1. event intervention: force KEEP of the current mark versus RENEW to the
   opposite candidate mark;
2. mark intervention: hold event kind fixed and compare current versus opposite
   mark.

Both use common random numbers after the branch point. Downstream sequence
metrics exclude the intervention action and use the next at most six active
actions, pausing through temporary absence and resuming on REJOIN. Terminal
metrics continue to episode end.

## Measurements

The prototype reports, by controller and split:

- `policy_dependence`: `P(RENEW | new_segment) - P(RENEW | mid_segment)` plus
  realized commitment-lifetime support;
- same-state `instantaneous_tv` for the mark contrast;
- `sequence_hamming` and sequence-correctness difference over the downstream
  active-action window;
- `terminal_utility_delta` for the paired KEEP-versus-RENEW continuation;
- `natural_mediation` as the explicit tuple of boundary-renew rate,
  mid-segment-keep rate, hidden post-cue correctness and natural utility;
- `heldout_robustness`: the same tuple and branch metrics on unseen durations,
  shifted membership timing and anonymous roster permutation.

No scalar composite score replaces these measurements. No bootstrap, learned
threshold, p-value, superiority gate or formal first-match branch is defined.

## Validity and completion

The artifact is invalid unless actor information is leak-free, reward identity
is exact, snapshot round-trip is exact, paired branches begin from identical
state/RNG, future RNG consumption remains equal, all values are finite, and all
registered cells/controllers are present.

Valid completion emits only `status=COMPLETE` plus the registered measurement
tuple and controller provenance. The analyzer does not decide whether a null is
scientifically separated, whether recurrence remains sufficient, or which CDC
action follows. Project Manager interprets the tuple against the named
counterexamples after the run. Completion consumes zero conclusion-bearing
iterations.

## Budget, provenance and artifacts

The prototype enumerates two splits, two roster sizes, two durations per split,
two duty-sign starts and two schedule rotations for each of six controllers:
32 episodes per controller, 192 natural episodes total, horizon 80. At most two branch points per
episode are continued under both contrasts. New source-owned seed namespaces
start at `731001` for task, membership, duty, opportunity, event, mark, action,
evaluation and audit; no G0 seed is imported.

Run with `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`, CPU only and one
thread. The runner writes one nonformal JSON manifest and one analysis JSON
under a caller-supplied `logs/<run-id>/` directory. Both carry `formal=false`,
the source commit, design identity, exact seeds and cell inventory. Analyzer and
formal G1 runners must reject these artifacts as conclusion-bearing evidence.
