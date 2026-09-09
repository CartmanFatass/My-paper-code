# RCLE B03 S20 CM implementation and launch preparation — 2026-09-09

Root allocation: main fb4f3e0ae9058675162bcb183f34182a969a935f final RCLE section.
Scientific freeze2da8ec66be12da255e69721d0bdc672ce07edc33, current bound card877a1aa072fe37079f0fa3c0a89c0142b9d8084c.
Owned checkout `C:/Projects/HMASD-worktrees/dm-rcle-a02-20260906`, `codex/rcle`, started clean.
[Card §§2–7](RCLE_B03_S20_SCIENCE_CARD_20260909.md) and
[accepted feasibility](RCLE_B03_S20_FEASIBILITY_20260909.md) supply the contract.

## Implementation and protected boundaries

`make_rng(seed=SEED)` and trailing keyword `run(...,seed=SEED,reporting_object=OBJECT_ID)`
carry the actual seed through root construction and summary. CLI accepts19/20, defaults19,
and passes both parameters; reporting object defaults to original namespace and is used
only by summary `object`. Existing old positional calls and wrappers remain intact.
Namespace/block0/true FLEX remain fixed. Seed20 root is
065798a1a4115ac244accada16fc267f814deb622cfd05b9657418892c656e3b.
Shared initialization/model/weighted loss/gradient/optimizer/native/RNG address inventory,
200×64 training, FP64 CPU thread1, panels and primary arithmetic are unchanged.

New11-line `scripts/run_rcle_tbcfv_b03_s20.sh` is the fixed W1→W100→reference list,
with fresh same-node admission&&runner and exit on any failure. W100 receives only the
new `$root/W1/summary.json`; no external or historical fitted input is accepted by this
wrapper. Per-interpreter timeout600/600/30; reference passes internal wall-cap30.
No retry, resume, extra scientific call, guard or scope§4 machinery; scope:none.
Existing recovery test's fake make_rng signature was adapted to accept the explicit seed;
its unchanged model/loss test was not repeated.

## Focused acceptance evidence

One selected supplied-fixture check: `test_s20.py::test_seed_and_new_control_publication`.
Actual CLI/main/run/make_rng/root derivation and summary publication are exercised.
Default19 and explicit19 match the frozen root;20 matches the declared root. Changing
report label/SHA leaves the block digest unchanged. Fake initializer/training/evaluation
consumers see the actual20 key, both weights and fixed FLEX; baselines start zero.
Real primary publication from distinguishable new-W1 data gives Delta_U .4, whereas the
old supplied control would give .7. Wrapper source asserts exact new-W1 path, order,
admissions, limits and stop-on-failure. These synthetic values are not scientific output.
Zero model constructors, native calls, real episodes or backward calls;400 supplied
update records exercise publication but are not actual optimizer steps.

Command: configured local Python `-m pytest -q -p no:cacheprovider --basetemp
<checkout>/temp/directions/roster_consistent_latent_exploration/test/b03-s20-focused-20260909
tests/experiments/candidates/roster_consistent_latent_exploration_tbcfv_b03/test_s20.py`.
Result:1 passed in7.61s; complete subprocess wall8.591198500005703s, exit0.
Existing pytest warning: unknown cache_dir option, no test failure.
Creator removed the resolved owned scratch; absence confirmed. Old blocked scratch untouched.
Prior directory usage19.4703507s +8.5911985s =28.0615492s, leaving271.9384508s of300;
S20 uses8.5911985s of its30s cap. No further test or smoke is planned.
Raw check stdout/receipt retained in `temp/directions/roster_consistent_latent_exploration/s20-preparation/`.

Coverage limit: supplied-output check verifies changed plumbing and primary source;
it does not execute native learning or prove seed20 performance. Unchanged native/loss
checks are reused. Collection must inspect actual initial tensors, roots, counts,
all four panels, full curves and primary before technical acceptance.

## Frozen execution proposal and charged budget

One supervisor `rcle-b03-s20-20260909`, remote wsl_4070, cwd
`/home/wu/hmasd-worktrees/rcle-b03-s20-20260909`, exact source commit recorded at launch.
Output relative root `temp/directions/roster_consistent_latent_exploration/exp/b03-actor100-s20-20260909`.
Interpreter `/home/wu/.venvs/hmasd/bin/python`, CPU FP64/thread1, no local fallback.
No external input stage: W1 is produced within this root before W100.

Logical command: configured agent-task owns `cd <cwd> && mkdir -p <root> &&
HMASD_PYTHON=<python> /usr/bin/time -f wall_s=%e,peak_rss_kib=%M,exit=%x
-o <root>/chain-time.txt timeout 1300 bash scripts/run_rcle_tbcfv_b03_s20.sh <sha> <absolute-root>`.
Wrapper contains the exact three argv/admission pairs; each admission measures physical
and effective available memory≥4GiB before scientific allocation. Outer timing includes
all admissions/startup/build/initialization/training/evaluation/publication in the list.

Counts:33792 episodes/2162688 ticks/400 backward-step calls/12 models=2fits+10helpers.
Per-arm projection from complete paths:W1 79.24s, W10070.95s, reference2.59s; sum152.78s,
planning only. Future actual timings and aggregate CPU remain unmeasured.

Conservative prelaunch debit75s:15s DM preparation plus60s CM support including the
8.5911985s focused check, reads/edits/review/Git/staging preparation command work.
Outer chain≤1300s leaves125s reserved for collection/arithmetic/final publication within
1500s complete object; actual work is charged once. Agent deliberation and asynchronous
waiting are not claimed as measured machine work; report overall elapsed separately.
If support outgrows its debit/reserve, reconcile within the same cap; never reset it.
Scientific sublimits remain600/600/30, without retry or replaced/extra panel.

After acceptance/push/staging, send MONITOR_ADD directly to live-config Monitor for the
entire shared handle; dispatch is distinct from actual adoption. CM stops routine polling;
Root confirms adoption and resumes CM at terminal. DM owns scientific interpretation.
Cleanup inventory: exact remote checkout and supervisor only; no staged old W1 input.
Keep these and all local artifacts until Root's explicit post-integration closeout.

## Independent review and CM disposition

Existing reviewer `rev_ah_rcle_b03` reviewed the complete diff against877a1aa072 read-only:
no material finding. It traced the CLI root into initialization/native scenario/manager/
actor consumers, preserved19 defaults and metadata-only labels, fixed fresh-W1 control,
600/600/30 admission sequence, supplied fixture and unchanged learner/native/old wrappers.
No reviewer tests or scientific calls. CM accepts the changed source/check boundary;
scientific/native execution and full result acceptance remain pending collection.

## Staging resolution and final prelaunch bound

Remote origin fetch stalled before checkout creation and was terminated. The first
incremental Git bundle triggered a missing delta-base fetch in the partial clone and
was also terminated before checkout creation. These are source-staging operations,
not scientific invocations. A committed-object non-thin pack in a Git bundle then
imported successfully without network dependencies; no source bytes changed.
Source bundle369790 bytes SHA256
9e7c2a63a198cd5a5ad9ea4a90bb1a82de0068d97b282d32d5dd937863dc5308
matched after transfer. Exact detached source4d96a832eeaa875b2e6178bd9014067ce32d0339
checked out successfully; declared source diff is empty and `bash -n` passed.
Remote source-only stage `/home/wu/hmasd-inputs/rcle-b03-s20-20260909` now joins the
later closeout inventory; it contains Git bundles, no historical scientific control.

This supersedes the preliminary75/1300/125 budget split above. Conservatively charge
**250s prelaunch support including15s DM**, all focused checking and stalled Git staging;
use **outer timeout1150s**, reserve **100s collection/publication**, totaling1500s.
Per-invocation600/600/30 sublimits remain; the cumulative bound can stop the sequence
before all maxima are spent, as required by the unchanged whole-object cap. Complete
historical projection152.78s remains well below the remaining allowance. No arm/panel
was removed, no experiment retried and no allowance reset. Actual final charge will
retain this conservative support debit plus measured sequence and collection/publication.
