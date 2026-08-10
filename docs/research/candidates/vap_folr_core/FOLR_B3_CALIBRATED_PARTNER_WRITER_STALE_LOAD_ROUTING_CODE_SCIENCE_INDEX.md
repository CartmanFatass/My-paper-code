# FOLR-B3 calibrated partner-writer stale-load routing: code-science index

This index binds the frozen `CAND-VAP-FOLR-CORE@constructive-revision-v6`
question to one prospective implementation package. It records no result and
does not authorize a run, acceptance, successor, C treatment, formal compute,
or External Pro request.

## Two-phase stop boundary

`partner_writer_stale_load_routing.py` freezes seeds 95031–95038 and the exact
Phase-P/Phase-R manifest. Phase P reward-trains `OrdinaryPartnerWriter` for 32
batches of 64 episodes per seed and evaluates only the final checkpoint on 512
held-out episodes. Its action loss is REINFORCE from ordinary sampled external
reward; no direct-label, auxiliary, critic, recurrence, cached action, or
cached-kernel path exists. Phase R is constructed and trained only when all
four registered calibration gates pass. A failed calibration therefore emits
the natural `B3_PARTNER_WRITE_CALIBRATION_FAILED` stop without a comparison.

The immutable `PartnerWriteDTO` binds every frozen payload to `owner_t@0`,
`inert_partner_q1@0`, a writer-call identity, and its source bit and byte
digest. The final Phase-P writer state is cloned byte-identically into each
Phase-R arm within a seed and all writer parameters are frozen.

## Real lifecycle host and treatment delta

`partner_writer_stale_load_routing_host.py` owns a three-transition physical
host. It records ordinary owner-private and obsolete-partner writes, validates
one typed `TERMINAL_LEAVE(inert_partner_q0@0) + JOIN(inert_partner_q1@0)`
transaction while preserving the exact `owner_t@0` record, accepts the bound
new-partner write, and performs one fresh four-action choice. The departed
record is terminal with empty state; terminal choice clears every record.

`MatchedRoutedActor` gives all three arms identical trainable parameter names,
shapes, counts, initialization, writer/update/readout calls, optimizer, data
order, and budgets. Their only delta is the fixed input mask immediately before
the common learned event updater:

- typed retains the owner channels and zeros obsolete-partner channels;
- generic supplies both channel families;
- reset zeros both pre-event channel families.

`generic_class_nesting_witness` constructs the exact generic mapping by copying
all typed parameters and setting `event_update.weight[:,2:4]` to zero. The
generic formula is then tensor-exact equal to the typed transition for every
input. Validators require the constructive witness in every final Phase-R
checkpoint.

## Frozen data, counts, and RNG isolation

Each Phase-R training batch has 32 CLEAN episodes balanced across `(s,n_new)`
and 32 STALE_LOAD episodes balanced across `(s,n_old,n_new)`. Every arm/seed is
trained for 32 batches and evaluated at its final checkpoint on 512 fresh
episodes per regime. Phase, seed, arm, train/evaluation, episode, initialization,
and action streams use explicit SHA-256-derived namespaces; artifact roots are
supplied once and must begin absent or empty. Phase-R train/evaluation roots use
constructively disjoint integer blocks for every `(phase,arm,seed)` namespace;
manifest validation recomputes every root and separately rejects any cross-arm
or cross-phase overlap.

If Phase R runs, the registered identity is exactly 65,536 training episodes,
28,672 evaluation episodes, 94,208 complete episodes, 282,624 real environment
transitions and policy calls, and 1,024 learner/trainer/Adam updates. There are
32 final-only checkpoints and zero retry, rescue, sweep, checkpoint selection,
hypothetical transition, or additional arm/seed/regime. If calibration fails,
validators require Phase-R counts and checkpoints to remain zero while
retaining the exact Phase-P counts.

## Lossless evidence and independent reconstruction

`phase_p_evaluation.jsonl.gz` retains every final binary kernel, sampled action,
reward, transaction witness, writer binding, `n_new` intervention, identity and
unused-pre-event fields. `phase_r_evaluation.jsonl.gz` retains every complete
four-action kernel as numeric float32 values and exact byte views, action,
reward, component decodes, transaction/write witnesses, paired `do(n_old)`
kernel, total variation, and owner-epoch-key intervention.

`validate_train`, `validate_evaluation`, and `validate_result` independently
check the manifest, final-only checkpoints, writer/schema matching, file
bindings, activity identity, lifecycle witnesses, kernel bytes, metrics,
estimands, and branch. Metrics are reconstructed from the retained sidecars;
the result cannot substitute a summary. `analyze` implements the exact seven
branch precedence and emits no scientific branch in technical-only mode.

The validators census every file under the checkpoint root, hash the actual
writer tensors in every Phase-R checkpoint against its Phase-P final writer,
rederive the constructive generic-class mapping from each loaded final actor,
and reconstruct all Phase-P seed/aggregate accuracies, response gates and the
combined calibration decision from retained rows. A natural Phase-P stop must
have no Phase-R checkpoint or sidecar. Every retained row must carry the full
q0→q1 replacement, bound q1 writer and terminal-clear witnesses.

`B3_INVALID_CONTRACT` is reachable only from ordered structured predicates for
binding, class nesting, arm matching, the real-event/write probe, shortcuts,
caps and root/artifact isolation. Missing or malformed files remain technical
exceptions and are never converted into scientific contract evidence. Train,
evaluate, analyze, sidecar, checkpoint, canonical result and optional external
result outputs are write-once; source commit, run id, stage identity, contract
evidence and upstream bindings are checked across every stage.

The production entry is
`scripts/run_folr_b3_calibrated_partner_writer_stale_load_routing.py`. It exposes
only train, evaluate, analyze, validation, and summary operations—no retry,
rescue, sweep, arm/seed selection, or checkpoint selector.

## Claim boundary

The strongest positive branch supports only host-local, finite-budget typed
routing value after prospective writer calibration. Generic sufficiency is an
equally valid result. Calibration or control failure leaves the comparison
unidentified. No branch establishes general value, generic impossibility,
promotion, retirement, or a successor.
