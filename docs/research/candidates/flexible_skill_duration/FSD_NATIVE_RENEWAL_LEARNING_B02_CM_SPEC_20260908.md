# FSD native-renewal learning B02 — bounded CM seed/input specification

P40 prepares this complete coding assignment only. No CM dispatch, implementation,
model/host, diagnostic fixture, test execution or scientific runtime occurs in P40.
The next named implementation assignment reuses CM `/root/fsd_cm_baseline_a01` and
its existing reviewer. P40 explicitly ends enrollment after the three CM comparison
batches; this task requests no fourth comparison.

## 1. Deliverable and exact starting code

Make the reviewed B01 learning path runnable as the single B02 independent pair,
with fixed training770303/evaluation770304 and distinct object/card metadata,
while keeping B01's callable/CLI defaults intact. Do not reimplement the learner
or introduce a generic configuration system.

Designated checkout: `C:/Projects/HMASD-worktrees/codex-fsd`, branch `codex/fsd`.
Complete starting revision: **ab6426ef6ca0267d7b5ca7c833401d6348ab07fb**. It reconciles
P40 main6717784f9 and integrated B01 intakebdf9d024b. Shared runner/test bytes match
reviewed **b3f86bb28879db239b07291c39d93a1c494abe50**. At future dispatch, reconcile
this specification's published commit into the same checkout and record its HEAD;
document-only descendants do not change this source binding. No new branch/worktree
is created for B02 authoring. Preserve unrelated writers' edits and serialize
shared index/edit ownership through check/commit/push.

The scientific contract is [B02 card](FSD_NATIVE_RENEWAL_LEARNING_B02_SCIENCE_CARD_20260908.md)
§§2–7. Accepted unchanged semantics and checks are [B01 CM spec](FSD_NATIVE_RENEWAL_LEARNING_B01_CM_SPEC_20260908.md)
§§2–6 and [P34 technical acceptance](FSD_NATIVE_RENEWAL_LEARNING_B01_TECHNICAL_ACCEPTANCE_20260908.md).
Read only the affected seed/input/metadata entry points below. No full historical
review, old runtime replay or new science-contract document is requested.

## 2. Owned paths and frozen change surface

- `scripts/run_fsd_native_renewal_learning_b01.py`: only seed/object/card input
  threading in `base_summary`, `build_learner`, `final_evaluation` and `main`.
- New `scripts/run_fsd_native_renewal_learning_b02.py`: a thin entry point fixing
  the B02 constants and delegating to the shared implementation.
- `tests/experiments/candidates/flexible_skill_duration/native_renewal_learning_b01/test_learning.py`:
  reuse the existing fake Agent/Adapter and extend the changed-boundary coverage.
  No new fixture framework or scientific-model smoke path is needed.
- A concise B02 technical acceptance record under the direction directory, with
  changed source/check/reviewer evidence and the future CLI shape. DM owns science
  cards/intake/owner records; CM does not rewrite them.

Preserve `applied_mask`, `collect_training`, `evaluate`, `paired_statistics`,
`completed_arm`, `summarize_panel`, deadline/publication/finite handling and all
core/environment/E0/E2/E3 implementations. Tests may adapt calls to the added
explicit arguments without deleting existing assertions. No changes to B01/P38
raw evidence, committed launch scripts or old result semantics are permitted.

## 3. Exact seed/metadata contract and propagation

B02 binds the following values in its thin entry point:

| Binding | B02 | Existing B01 default, retained |
| --- | --- | --- |
| training_seed | 770303 | 770203 |
| evaluation_master | 770304 | 770204 |
| object_id | FSD_NATIVE_RENEWAL_LEARNING_B02 | FSD_NATIVE_RENEWAL_LEARNING_B01 |
| card | docs/research/candidates/flexible_skill_duration/FSD_NATIVE_RENEWAL_LEARNING_B02_SCIENCE_CARD_20260908.md | existing B01 CARD path |

Use explicit call arguments through the shared functions, with B01 defaults.
A concrete minimal interface is keyword-only `training_seed`, `evaluation_master`,
`object_id`, `card` on `main`; pass the needed subset to the three helper entry
points. Keep the existing B01 constants and default behavior; do not mutate the
shared module's globals from the B02 wrapper or leave binding state between calls.
Names of internal locals are ordinary implementation choices; the propagation
and public defaults in this table are fixed.

1. **B02 entry point.** Its `main(argv=None)` delegates once to the shared `main`
   with all four fixed B02 values; its `__main__` guard returns that exit code.
   Reuse the shared CLI, timer, construction, training and publication. No copied
   runner body, monkeypatch-based runtime rebinding or new subprocess launcher.
2. **CLI / main.** `--policy`, required `--seed`, `--launch-sha`, `--out` and H's
   existing comparison arguments retain their meaning. The allowed `--seed`
   is the entry point's fixed training seed:770203 for B01,770303 for B02. A
   mismatch is rejected by the existing argparse boundary before output/model
   construction. Do not expose new generic seed/config/card-selection CLI flags.
   The accepted parsed training seed and fixed evaluation master flow explicitly
   to summary, learner construction and final evaluation. G's adapter uses the
   fixed evaluation master; all cardinalities/caps and control flow are unchanged.
3. **base_summary.** Set the supplied object_id/card, training_master and
   evaluation_master. Preserve `seed=None` for G, otherwise the supplied training
   seed. All other fields are unchanged, including launch_sha supplied at actual
   future execution. G's training_master field is pair context, not learner exposure.
4. **build_learner.** Use the supplied training seed for all three explicit
   `random.seed`, `np.random.seed`, `torch.manual_seed` calls, the16-lane training
   adapter's master_seed and `build_corridor_learner_config(..., seed=...)`.
   Keep four threads before construction and every old config/override unchanged.
   C and H reseed independently at their own process start and create separate
   real learner/optimizer/normalizer instances; no data/RNG instance is shared.
5. **final_evaluation.** Pass the supplied evaluation master as the32-lane
   CorridorEvaluator master_seed and the supplied training seed as its config seed.
   Keep the entire existing construction/sync/evaluation inside `_preserve_rng`,
   with copied active modules/normalizers, resets and zero evaluator optimizer calls.
   Do not reset learner RNG outside that context or derive a seed from the output
   path/policy name/current time/global environment.
6. **Pair behavior.** Fresh H reads only fresh C/G summaries supplied by its argv.
   Existing object/seed/master/host/endpoint metadata checks already prevent a
   B01 C or G from silently becoming B02's comparator. Preserve their actual
   failure behavior: missing/mismatched C prevents complete pair polarity while
   retaining H's own completed endpoint; a missing/mismatched G limits reference
   claims while preserving a trustworthy fresh C/H pair. No new validators,
   provenance guard, hash manifest, registry or cross-pair aggregation is added.

B02 uses training IDs0–79 in five blocks16 and evaluation IDs0–31 under the new
masters. Training episode advancement, real terminal/reset state, masks, rewards,
internal segment metadata/credit, losses and optimizer exposure are untouched.
The new object/card/master metadata must describe the actual keys passed to the
host and model config; changing only JSON labels would not satisfy this contract.

## 4. Preserved semantics and future invocation shape

Preserve B02 card§§2–6, which reuse the accepted B01 comparison: large N6/K2
Bernoulli host; real fresh C/H learning; C internal D2 applied mask; H public
applied mask after reset with authentic internal D2/actor/storage/credit;
public G; own trajectories/normalizers; CPU4/FP32 learner/FP64 host and reward;
five16×400 rollouts per learned arm; deterministic final32 per C/H/G. Maintain
all full/post primary/reference vectors, own-opportunity counts/rates/loss,
internal/applied renewal, actual optimizer/segment counts, first/final parameter
displacement and partial-publication behavior. No previously observed array is
loaded to train, evaluate or fill a new measurement.

B01 and B02 are reported as separate per-training-pair rows at scientific intake;
this runner produces only B02's fresh pair. Do not implement an episode pool,
best-seed selector or combined result/uncertainty estimator. The existing per-pair
MEI branch values remain above_mei, small_or_resolution_limited, opposite_sign or
incomplete as applicable; the B02 card gives their prospective scientific reading.

Future CLI shape, **not an invocation allocated by P40 or by coding acceptance**:

```text
python scripts/run_fsd_native_renewal_learning_b02.py --policy G --seed 770303 --launch-sha <accepted-implementation-sha> --out temp/directions/flexible_skill_duration/exp/native_renewal_learning_b02_770303/G
python scripts/run_fsd_native_renewal_learning_b02.py --policy C --seed 770303 --launch-sha <accepted-implementation-sha> --out temp/directions/flexible_skill_duration/exp/native_renewal_learning_b02_770303/C
python scripts/run_fsd_native_renewal_learning_b02.py --policy H --seed 770303 --launch-sha <accepted-implementation-sha> --out temp/directions/flexible_skill_duration/exp/native_renewal_learning_b02_770303/H --c-summary temp/directions/flexible_skill_duration/exp/native_renewal_learning_b02_770303/C/summary.json --g-summary temp/directions/flexible_skill_duration/exp/native_renewal_learning_b02_770303/G/summary.json
```

The future source SHA is not b3f by fiat: it must name the accepted implementation
containing B02 and the shared parameter threading. Do not create these output
roots, detached handles, resource receipts or command scripts during the coding
assignment unless a later explicit runtime-binding task supplies that work.

## 5. Focused acceptance checks

Reuse all18 accepted synthetic B01 cases. Extend the same fake-only suite to
exercise the changed inputs; real HMASDAgent and RelayCorridorHost construction
remain forbidden by the existing fixture. Do not execute the real runner merely
to test seed propagation. The current suite's complete4.4069052s is only a timing
anchor; total extended focused checks must remain<=300s for this research directory.

Required changed-boundary evidence:

- **Old defaults.** Existing B01 calls still produce B01 object/card,770203/770204
  metadata and original source-level behavior; all prior mask→storage→update,
  reset, evaluator isolation, pair and failure-publication assertions pass.
- **New real call wiring with fakes.** The B02 binding reaches each explicit
  Python/NumPy/Torch seed call, training-adapter master and learner-config seed
  as770303. Spy or record those arguments without constructing a real model/host.
  Four Torch threads precede the fake model and the other accepted config fields
  stay unchanged. Metadata-only substitution cannot pass this check.
- **Evaluation and G wiring.** New G uses770304 and IDs0–31 in production sizing,
  with no learner construction. A fake-sized test may retain the existing two
  lanes/three-step fixture. C/H evaluator construction gets master770304/config
  seed770303 while preserving RNG state, own module/ValueNorm synchronization
  and zero optimizer calls. Reuse/parameterize the actual E2-constructor/sync test.
- **Thin entry point and no residual binding.** Exercise the actual B02 main
  delegation with the same fake-patched shared module, yielding a complete tiny
  G/C/H panel with B02 metadata and fresh comparison inputs. A later B01 call
  in the same test process retains B01 defaults; do not implement runtime global
  rebinding to satisfy the wrapper. An unsupported CLI seed is rejected before
  model/output construction. Tests may bind the imported shared module to the
  existing fixture's module object to prevent an unpatched duplicate import.
- **Paired identity and dependent failure.** Use the existing summary fixture to
  show a B01 C cannot supply a B02 H pair, and a B01/mismatched-master G cannot
  supply its reference. Preserve the already-complete H/companion facts and the
  existing missing-reference behavior; do not construct an extra scientific panel.

Run the one extended file under `tests/AGENTS.md` with the existing local
scientific interpreter and a direction-scoped basetemp. This short focused suite
may run locally; no separate benchmark, calibration, full-history suite or actual
learner smoke is requested. Check the focused diff for unchanged collector,
policy, reward, evaluator internals, pair arithmetic and publication semantics.

Because this diff propagates RNG and result identity, reuse the independent
Reviewer under the CM role's high-impact review requirement. Its bounded question
is whether defaults/new seeds reach the intended actual consumers without global
leakage or changed scientific behavior. Give it this spec/card's current sections,
source diff and focused results; no new Scout/critic or full old learner audit is
needed. Reviewer examines the changed source independently without an extra run.

## 6. Budget, execution constraints and stop

Only the selected seed/metadata propagation, thin wrapper, focused tests and
technical acceptance record are owned. Existing<=600 lines per runner and2000 new
non-test lines per research attempt apply; do not duplicate the445-line runner
or add scope§4 machinery. There is no new orchestration-ratio gate or exception
application. Return a concrete out-of-scope need instead of implementing it.

Implementation/checks are not a scientific execution allocation. Model, host,
learner, training/evaluation, diagnostic fixture/probe, resource admission and
result roots stay uncreated in production. No old checkpoint, fourth comparison,
additional pair/arm/seed, Pro Send or automatic launch follows. Required synthetic
checks construct only the existing fakes and are bounded as above.

For a later separately allocated panel, proposed complete caps remain G60,C900,
H900s (sum1860), including admission through publication. Remote-first/exact-SHA,
CPU4/precision, resource floor and ordered companion/failure rules are card§6.
No source test or preparation result creates a new runtime budget.

Commit changed owned paths explicitly with attribution and scope:none, push
immediately and return the full commit, source/check/review evidence, remaining
concrete issue and exact future argv to DM/Root. Same CM handles focused corrections;
Root integrates accepted code, then DM handles readiness and any separately issued
runtime route. Do not ask CM to select another scientific question or rewrite this card.

## 7. Complete five-item handoff for Root's next named CM command

1. **Deliverable/goal:** implement B02's fixed770303/770304 independent-pair
   entry point by explicit seed/object/card inputs to the reviewed B01 code;
   preserve B01 defaults and return technical acceptance, not a scientific result.
2. **Owned paths/entry points:** the B01 runner's four functions in§2–3, one thin
   B02 script, existing B01 synthetic test file and a B02 technical record. Use
   `C:/Projects/HMASD-worktrees/codex-fsd`, `codex/fsd`, complete starting code
   ab6426ef6ca0267d7b5ca7c833401d6348ab07fb/source-equivalent b3f86bb28; reconcile
   this published spec first. Preserve other writers and serialize edits/index.
3. **Preserved semantics:** B02 card§§2–6; only the four fixed seed/identity bindings
   change. No global rebinding, copied learner, core/collector/evaluator/pair-math
   change, old result rewrite, cross-pair pooling or scientific invocation.
4. **Acceptance:** this spec§3 exact consumer mapping and§5 changed-boundary
   fake checks; retain the18 original test cases and their assertions, plus independent focused RNG/identity
   review. Card§§3–5 and evidence-spec§4,5.2,11.4,11.8.3,11.8.6–7 fix the relevant
   scientific requirements. New metadata must match actual host/config inputs.
5. **Budget/stop:** <=300s synthetic suite, existing600/2000-line budgets, scope§4
   none, zero production model/host/learner/runtime/probe. No fourth comparison or
   launch binding; stop for a concrete owned-surface/semantic gap. Commit/push the
   complete bounded change and return to DM/Root; no further scientific allocation.
