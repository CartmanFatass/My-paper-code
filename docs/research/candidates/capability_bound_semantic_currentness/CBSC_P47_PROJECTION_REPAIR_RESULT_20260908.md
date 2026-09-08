# CBSC P47 projection repair technical evidence

Status: prospective minimal-prefix diagnostic; no production correction supported.
Authority: [P47 card](CBSC_P47_PROJECTION_REPAIR_CARD_20260908.md), question and preserved-semantics sections.

The retained dirty test was preserved without edits in
`temp/directions/capability_bound_semantic_currentness/test/p47_projection_20260908_control/initial_dirty_variant.py`,
SHA256 `c6cbbab72a427d9df06460487cc533f349caf565e66da7937c2bad0912f82cab`.
The selected source is that retained variant: omit public-byte export and the
indexed build_observations wrapper before the original projection; compare the
saved public bytes only after projection returns, then stop by PrefixComplete.
No scope-spec section 4 machinery or production edit is added.

## Source boundary and focused checks

Direct inspection follows opportunity_credit_b04/run.py:106–132 through
omrc_b01/engine.py:82–115, RawHistoryAdapter.process and the actual relative
omrc_b01/token.py codec. The run creates the original 384 training tapes and
32 evaluation tapes, computes input/action digests, initializes model/trainer,
then enters the initial projection. Each tape owns a fresh adapter per replay;
immutable public bytes expand to NumPy FP32 rows, torch.from_numpy retains the
array storage, and torch.stack returns [32,152,168]. RAW FIFO updates use four
Python integers; the codec uses immutable bytes and ordinary NumPy bit expansion.
No concrete buffer lifetime, shape, or codec defect was found in this inspection.
Both production directories have zero diff against historical P32 d2753be86.

The test's exception prevents return to run_arm after initial projection,
before fixed rules, held-out evaluation, rollouts, Adam steps, checkpoints or
scientific publication. Zero scores/learning are source-bound, not inferred
from a successful process exit. Post-projection JSON is the diagnostic's affected
publication path. Wrapper frames, entry argparse, startup output and allocation
history still differ from historical P32; this is not process-state identity.
AST parsing and git diff --check passed before the diagnostic. No learner smoke.

## Frozen diagnostic

Node wsl_4070; original lexical interpreter
`/home/wu/.venvs/hmasd-cbsc-system312-local-acquisition-p16-20260907/bin/python`;
CPU FP32, Torch1 and existing numeric-library limits. One detached agent-task,
outer GNU time and timeout TERM115s/KILL5s, adjacent original memory admission
requiring physical/effective availability >=4 GiB. Fresh exact-source cwd
`/home/wu/hmasd-worktrees/cbsc-p47-minimal-prefix-20260908`;
handle `cbsc-p47-minimal-prefix-20260908`.
Argv after admission: selected Python -X faulthandler
`tests/experiments/candidates/capability_bound_semantic_currentness/omrc_b01/test_initial_projection_prefix.py`
`<cwd>/temp/directions/capability_bound_semantic_currentness/test/p47_minimal_20260908/TEST_ONLY_prefix`
`--minimal-reference /home/wu/hmasd-inputs/cbsc-p47-20260908/TEST_ONLY_initial_public_tokens.bin`.

The retained reference is 82,688 bytes; SHA256
`ee4df377990ed9d40b7bcec0241a92268f1b78037cfbbcee90b57c113eae7ccb`, bound before staging.
It is the prior indexed diagnostic input, not retained P32 state.
Cost: one original 416-tape setup and 32 x 2 x 152 = 9,728 adapter calls;
82,688-byte post-projection comparison. No sweep. Prior complete-path wall7.23s
is context; normal time remains uncertain, complete cap120s. Aggregate CPU is
unmeasured; one invocation makes its summed wall equal its critical path.
Post-learner publication is outside this zero-learning diagnostic.
Raw launch/status/admission/log/results will be collected in the preservation
root above. No historical RAW/STRUCT retry or scientific exposure is allocated.
