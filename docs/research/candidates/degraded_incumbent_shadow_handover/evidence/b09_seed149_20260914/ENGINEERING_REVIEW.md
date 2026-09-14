# B09 independent engineering review and DM acceptance

Independent reviewer: native `/root/rv_ah_dish_b09`, configured Astra/high, read-only.
Initial context was the fixed card/L0 and diff `7a83eba75..3a749256d`, without DM
implementation discussion. The reviewer performed no tests, code edits or scientific runs.

## Independent review returned

No material finding in the fixed diff. Reset applies to all four histories before BYPASS
returns (`production_training_engine.py:93–95`). Both live collection and replay then run
the ordinary GRU; a receipt cannot reset BYPASS history. History gradients remain connected;
snapshot encoder/bridge parameters are unused. Likelihood and post-CAS promotion ordering
are unchanged. Mode loads in both policy and optimizer-update reconstruction and persists
in checkpoint bytes; missing mode remains REPLACE and HALF_RETAIN is unchanged.

B09 supplies the new master family/seed149 to shared initialization and both arms. B04
independently deserializes initial bytes and creates each arm's native state, trainer,
policy and normalizers. Both use STRUCTURED/DIRECT_MEAN and both AdamW groups at3e-5.
The primary requires all four final coordinates, equally weighted BYPASS minus REPLACE;
inherited evaluation retains genuine termination, zero remainder, energy, events and first
transfer. Computed pair totals match131,072 transitions/1,024 optimizer calls/≤9,600 EVAL
ticks. Non-test additions214 lines, runner89; no uncarded §4 machinery was identified.
The runner's pre-write accounting boundary still requires external process-exit closure.

The same reviewer received the exact command and remote check record in a follow-up for
this same batch and found no material launch-integrity/accounting defect. All10 focused
cases passed at source3a749256; test wall6.8644327s is contained in enclosingSSH7.6011197s,
and scratch was removed. Explicit OMP/OpenBLAS/MKL/NumExpr=1 and MAX_JOBS=1 complement
the existing one-thread Torch call. Actual-node memory admission is immediately joined
to the runner by`&&`; external timing covers preflight and runner through process exit.
The180s prelaunch charge is an allocated conservative estimate, not a measured complete
cost; do not add contained pytest or the included preflight again. Add postlaunch
observation/collection once. Provider/agent cost remains separately unknown.

Residual limits: this is source/command/test evidence, not actual supervisor acceptance,
runtime topology observation or completed scientific publication. Recurrent state evolution
is distinct from parameter learning, and four evaluation conditions do not become four
independent learning replications. No scientific effectiveness was inferred.

## DM technical acceptance

Accept the reviewed implementation at `3a749256d2aaf16345308827518283c8d2b91ad7`.
DM self-check parsed all changed Python sources and inspected the two-line mode change
and separate B09 study/runner; source B08 modules/entry remain unchanged. The actual
remote focused check verifies reset/masks/owners, gradients, live/replay likelihood and
promotion, mode/optimizer checkpoint restoration, paired all-outcome primary and publication,
and threshold/shared-cost arithmetic. There is no unresolved engineering finding and no
reason for another smoke or broad suite. The existing pytest cache_dir warning is
configuration-only with cache provider disabled; tests and cleanup succeeded.

New retained records: `focused_checks.json`, `staging.json`, `EXECUTION_PLAN.json`.
The exact source is committed/pushed and present in its detached remote worktree.
The plan has not yet been submitted. Technical acceptance does not substitute for actual
memory admission or create a retry. Launch the sole bound pair; attach the accepted handle
to its new batch-owned Monitor, collect the complete result, then make the scientific
intake. Keep actual acceptance/runtime/cost gaps separate from this engineering conclusion.


## Independent review of submit02 serialization repair

Same native Astra/high Reviewer `/root/rv_ah_dish_b09`, same B09 engineering batch:

> No material finding in the submit02 serialization repair.
> The recorded supervisor collapses arguments with `COMMAND="$*"` and later executes
> `eval ${COMMAND@Q}`. Passing the entire shell command as one argument preserves it;
> the supplied `shlex.join(argv)` quoting correctly protects `$PWD`, `&&`, and the
> timing-format quotes until evaluation. `cd`, environment setup, admission and runner
> now execute in the same shell. SHA, seed, interpreter, intended paths and immediate
> `admission && runner` binding remain unchanged.
> Submit01's retained wrapper/log establishes exit2 because Python could not open the
> admission script under `/home/wu/scripts`. The following runner was blocked by `&&`.
> Absent intended roots and the stray timing-only file corroborate no scientific execution.
> The fresh `-submit02` handle preserves the failed handle's evidence.
> Repair costs remain explicitly included in the unchanged estimated180s prelaunch charge,
> without resetting or double-adding them.
> Limits: this reviews the planned serialization, not actual submit02 acceptance. Reconcile
> its returned handle and generated wrapper/log after submission. The180s remains an
> allocation estimate; complete measured cost still requires closeout accounting.

DM accepts this exact bounded repair. No source change or repeated synthetic test is needed.
Published failed records and the new plan keep the effects distinguishable. Execute only
the corrected plan after this record is committed and pushed; then reconcile actual
acceptance and delegate the exact new handle to the same batch Monitor.
