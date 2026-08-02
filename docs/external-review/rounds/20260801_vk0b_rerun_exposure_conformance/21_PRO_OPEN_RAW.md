CONFORMANCE
CHANGES_REQUIRED — the identical-contract rerun is the correct route, but three protected definitions are not yet closed

The design correctly follows Outcome B from the exposure-recovery audit:

V-K0A remains accepted standing evidence.

The historical V-K0B checkpoints remain diagnostic references only.

The missing exposure fields are instrumented.

The same six seeds, training budget, optimizer settings, evaluation bank, order split, thresholds, bootstrap, and branch mapping are reused without pooling.

V-K0C and all architecture changes remain held.

That is the correct scientific response to an invalid operational path rather than an adverse-valid result. The project principles expressly permit retrying a failed operational realization while forbidding seed, budget, model, metric, or threshold rescue of a valid result.

The following ledger items require amendment before implementation.

Ledger item	Disposition
W6-D1 shared optimizer	Accept with a mandatory parameter-coverage binding
W6-D1 high-check and batch counters	Modify the event definitions and make the statuses exhaustive
W6-D2 launcher fail-closed behavior	Conforms, subject to carrying the immutable exposure block forward
W6-D3 analyzer row-1 gate	Modify: exact exposure is required; recorded skips do not excuse reduced exposure
W6-D4 target vectors	Conforms
W6-D4 segment-ending authority	Does not conform: one scalar cannot represent the registered events
W6-D5 identical-contract rerun	Conforms
W6-D6 no additional work	Conforms
1. W6-D1/W6-D3 — one shared high optimizer is admissible, but one scalar alone is insufficient

The exposure audit establishes that this architecture has one high_opt, with a uniform optimizer-state step of 3,000, rather than distinct actor and value optimizers.

The prior ruling’s request for:

high actor optimizer steps
high value optimizer steps

does not require splitting the optimizer or changing training behavior. It requires proof that both trainable objects received the registered optimizer exposure.

Freeze the realization as:

high_optimizer_semantics = SHARED_ACTOR_VALUE_OPTIMIZER

high_actor_optimizer_steps = high_optimizer_steps_shared
high_value_optimizer_steps = high_optimizer_steps_shared

but only if the artifact also proves:

every trainable parameter of the R30 high actor is present in high_opt.param_groups;

every trainable parameter of the high value module is present in those groups;

every such parameter has an optimizer-state step entry;

every actor and value entry has the same step count;

that shared count is exactly 3,000.

The current wording—“read every optimizer state dict present and assert uniformity”—can miss a trainable parameter that never acquired optimizer state because it never received a gradient. Uniformity over the entries that happen to exist is therefore not a complete actor/value exposure certificate.

The manifest should durably contain, at minimum:

high_optimizer_steps_shared
high_actor_parameter_count_expected
high_actor_parameter_count_with_step_state
high_value_parameter_count_expected
high_value_parameter_count_with_step_state
high_optimizer_step_min
high_optimizer_step_max
high_optimizer_parameter_coverage_ok

There is no scientific reason to create two optimizer objects or two independently incremented counters.

2. W6-D1 — “high-check sequences” must mean completed autoregressive decisions, not due calls

The proposed phrase:

high_check_events += number of due high checks processed per
maybe_assign_skills call

is too close to a call-site count. A due call can, in principle, exit or fail before a complete autoregressive edit sequence becomes part of the training record.

Freeze:

high_check_sequences_completed

as the number of successful R30 edit-sequence emissions for which:

act_sequence completed;

the complete token vector was produced;

the associated high-check decision row was committed to the high buffer.

Initial-assignment sequences count: they consume the high policy’s skill-selection support and contribute optimizer exposure even though KEEP is unavailable. agent_tokens_keep and agent_tokens_set then describe the token composition within the completed sequences.

For this fixed two-agent toy, require the structural identity:

N
KEEP
	​

+N
SET
	​

=2N
high sequence
	​

.

A due call that returns before emitting or committing a sequence must not increment high_check_sequences_completed; it must appear under an explicit failure or skipped-event counter.

This interpretation answers flagged point 2: no separate “per-agent high-check sequence” is required. One shared high check produces one ordered autoregressive sequence containing two agent tokens.

3. W6-D1/W6-D3 — the high-update counters must form an exhaustive partition

The current design increments high_batches_attempted only when a PPO epoch/pass is entered. That leaves a potential blind spot if update_high_from_checks returns before entering the epoch loop because its rows are empty, invalid, or otherwise unusable.

Freeze the expected high optimizer opportunities before any early-return guard. Every opportunity must receive exactly one terminal status:

STEPPED
SKIPPED_NORMAL(reason)
ABORTED(reason)

The cumulative identities must be:

N
attempted
	​

=N
stepped
	​

+N
skipped
	​

+N
aborted
	​

,

and, for the identical V-K0B contract,

completed_outer_updates           = 1000
high_epoch_passes_attempted       = 3000
high_epoch_passes_stepped         = 3000
high_epoch_passes_skipped         = 0
high_epoch_passes_aborted         = 0
high_optimizer_steps_shared       = 3000

The existing training path calls update_high_from_checks once per completed outer update after collection and low/process updates; the registered configuration supplies three high PPO epochs. The exposure audit independently recovered 1,000 outer updates and uniform high_opt step 3,000 from the historical checkpoints.

Most importantly, amend W6-D3 from:

compare optimizer steps with updates × epochs when no skip was recorded

to:

any nonzero skipped or aborted high pass is itself an exposure-contract violation.

A run with 2,997 optimizer steps and three honestly recorded skips is well documented, but it is not the identical frozen 3,000-step optimizer exposure. It must emit:

INVALID_VARIABLE_K_URGENCY_AUDIT
reason = TRAINING_OPTIMIZER_EXPOSURE_MISMATCH

Recording a deviation does not make that deviation admissible.

The same applies to:

environment interactions other than 640,000;

completed outer updates other than 1,000;

nonzero low-level optimizer exposure;

incomplete actor/value parameter coverage;

or a mismatch between completed high sequences and token counts.

4. W6-D2/W6-D3 — bind and propagate the actual-exposure evidence

The current launcher records only total_steps and update_idx as available, explicitly listing the other exposure fields as unavailable. The generic training manifest likewise currently writes total_steps, update_idx, configuration, and runtime metadata, but no complete actual-exposure block.

The amended implementation must make the evidence chain explicit:

training run_manifest.json
    contains actual_exposure + source labels

launcher manifest
    records run_manifest SHA-256
    records checkpoint SHA-256
    records exposure_audit = PASSED | FAILED

audit_vk0b_r30_access.py
    copies the exact source-labelled actual_exposure block
    and its source-manifest hash into the per-seed evaluation manifest

analyze_vk0_result.py
    independently validates the complete block before row 2

Use a versioned block such as:

actual_exposure_schema = "vk0b-exposure-1"

Allowed evidence-source labels should be frozen narrowly, for example:

runtime_counter
training_accumulator
optimizer_state
checkpoint_optimizer_absence

config, nominal, expected, or derived_from_budget are not admissible sources for an actual-exposure field.

This is mostly already implied by W6-D2 and W6-D3, but it must become a concrete implementation binding because the current evaluation manifest propagates only checkpoint/config identity and low-optimizer absence. The historical omission was exactly a break in this chain.

5. W6-D4 — one segment_ending_authority field cannot represent the toy’s final check

The target-vector correction conforms. Persist:

current_targets
previous_targets

as the full slow and fast target vectors at the current and preceding offered checks.

The proposed ending-authority correction does not yet conform.

At the final offered check, a focal agent can:

execute a voluntary SET, ending its incumbent segment at the check boundary; and

have its newly started segment ended by episode termination five primitive steps later.

A single scalar field cannot record both events. Giving episode_termination priority would erase the voluntary renewal; giving voluntary_set priority would erase the exogenous termination. This is the same conflation the original trace correction was intended to remove.

Use either a structured event list:

segment_end_events = [
    {
        "offset_from_check": 0,
        "authority": "voluntary_set"
    },
    {
        "offset_from_check": 5,
        "authority": "episode_termination"
    }
]

or two explicit fields:

incumbent_end_authority_at_check =
    voluntary_set | none_open

post_window_end_authority =
    episode_termination | active_mask_change |
    team_intent_boundary | forced_renewal | none_open

For this frozen toy:

active_mask_change, team_intent_boundary, and forced_renewal are structurally unreachable but remain legal schema values;

a KEEP row ordinarily has incumbent_end_authority_at_check=none_open;

the final window has post_window_end_authority=episode_termination;

a final-check SET may carry both non-none_open values.

initial_assignment is a segment-origin value, not an ending authority, and should not re-enter the ending-authority vocabulary.

The analyzer may ignore these fields for the current V-K0B statistics, but schema version vk0-trace-2 must validate them correctly so a later natural-hazard or censoring analysis does not inherit another semantic collision. The current audit code explicitly stores segment origin under the ending-authority name, confirming why this correction is necessary.

6. W6-D5 and W6-D6 conform

The identical-contract rerun is correctly frozen:

same six scientific seeds
same configuration
same 640,000 interactions
same 1,000 updates
same high optimizer settings
same held-out episode bank
same 32/32 serialization split
same support and competence floors
same bootstrap
same branch mapping
fresh roots
no pooling

The exposure-recovery audit reached Outcome B because fields 5–8 were never accumulated, while the recoverable fields showed no observed partial-update signal. Reusing the same scientific seeds is therefore an operational rerun of an invalid result, not seed expansion or negative-result rescue.

Holding V-K0C, order randomization, architecture changes, new seeds, and tuning is also correct. V-K0A and its authorization tuple remain untouched.

INTERPRETATIONS
1. Shared high optimizer
Accepted, with parameter coverage

One shared high_opt satisfies the actor/value exposure requirement. Do not split it.

The durable record must show that both the high actor and high value parameter sets are fully covered by that optimizer and that all of their per-parameter state steps equal the shared count. Report the same shared count as the exposure of both modules, with its shared semantics explicit.

2. “High-check sequences”
Corrected definition

It means:

completed shared high-check autoregressive edit sequences committed to the training buffer.

It does not mean:

one separate sequence per agent;

every call to maybe_assign_skills;

every due test;

or every continuation-value refresh.

Each completed sequence contains the two agent tokens counted by the KEEP/SET accumulators.

3. Counters count, never gate training
Accepted

The counters must not:

alter a branch;

suppress or repair a skipped update;

change RNG use;

retry a batch;

stop training early;

or change optimizer execution.

A skipped or aborted update is recorded exactly as it happened. The launcher and analyzer, not the trainer, refuse scientific use afterward.

Gate B should nevertheless include one proof-sized non-scientific noninterference witness: with identical initial state and seed, enabling the counters must preserve the token, action, reward, optimizer, and parameter trajectories byte-for-byte, apart from the new counter/manifest fields. That is implementation conformance, not a new scientific experiment.

CONVERGENCE_DECISION
TOUCHPOINT_2                           CHANGES_REQUIRED

IDENTICAL-CONTRACT RERUN ROUTE         RETAINED
SHARED HIGH OPTIMIZER                  ACCEPTED
HIGH-CHECK EVENT INTERPRETATION        CORRECTED
COUNTERS-NOT-GATES PRINCIPLE           ACCEPTED

BLOCKING AMENDMENTS
    1. actor/value parameter-coverage proof for the shared optimizer
    2. exhaustive high-pass status partition and exact no-skip/no-abort gate
    3. completed-sequence definition and sequence/token consistency
    4. non-lossy segment-ending representation
    5. immutable propagation of the source-labelled exposure block

V-K0A                                  STANDS
HISTORICAL V-K0B                       REMAINS INVALID
V-K0C                                  HELD
V-K1                                   HELD
CONSTRAINED RENEWAL-CLASS MECHANISM    HELD

These amendments do not change the scientific experiment, thresholds, seeds, budget, model, evaluation bank, or result mapping. They close the evidence semantics required to make the identical operational rerun auditable.

After they are entered into the ledger, one convergence turn should confirm the text before implementation. This ruling authorizes neither implementation nor the rerun.