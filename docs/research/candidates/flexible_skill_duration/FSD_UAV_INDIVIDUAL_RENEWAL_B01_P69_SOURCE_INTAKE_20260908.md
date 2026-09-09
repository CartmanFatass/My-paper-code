# FSD UAV individual-renewal B01 — P69 source readiness intake

**Accept source `ca36e2f941d6c4d4e996a9bd919378af44ea0e93` for the selected
B01 implementation.** P69's source/check/independent-review/readiness phase is
complete. No scientific staging, admission, model construction, training,
evaluation or invocation was allocated or performed. This is engineering
acceptance, with no new native UAV performance observation or prediction score.

## 1. Assignment and accepted artifacts

Root explicitly allocated P69 after the conforming P67 direction intake and
prospective card. The [card §7](FSD_UAV_INDIVIDUAL_RENEWAL_B01_SCIENCE_CARD_20260908.md)
and [CM specification §§1–6](FSD_UAV_INDIVIDUAL_RENEWAL_B01_CM_SPEC_20260908.md)
record the exact source-only boundary at `3fa896737cf805ce63da048ddfa8873f2c5cc18b`.
Original scientific input is `b317b1edde00d05a075b5f5ec5a8bb8e18d9cdba`; the
read-only baseline is `335425e92cda16677fd1f4181e2c31730887e911`.

The same CM `/root/dm_fsd_p47_resume/cm_am_fsd_b03_p47` implemented in
`C:/Projects/HMASD-worktrees/codex-fsd` / `codex/fsd`, reused its existing
independent reviewer and returned editing/index ownership with the checkout
clean and pushed at `ca36e2f941d6c4d4e996a9bd919378af44ea0e93`. Exactly three
owned paths were added:

- `scripts/run_fsd_uav_individual_renewal_b01.py` (424 lines).
- `tests/experiments/candidates/flexible_skill_duration/uav_individual_renewal_b01/test_learning.py` (488 lines).
- [CM technical acceptance](FSD_UAV_INDIVIDUAL_RENEWAL_B01_TECHNICAL_ACCEPTANCE_20260908.md)
  (146 lines, including corrections, evidence and future commands).

No core learner/config/E0/environment/corridor source or old tests changed.
The temporary three-batch CM comparison was already complete before this new
assignment; no fourth enrollment, replayed comparison task or scientific run.

## 2. What was checked and rule applied

I read the complete committed runner, the technical acceptance record, relevant
fake-case coverage and the independent review return. I checked the new action,
terminal/reset, model/evaluator and reward-info boundaries against their direct
unchanged E0/agent/scenario1/adapter definitions. I did not repeat CM's test suite
or run real models. The raw retained check log directly shows 33 passing cases;
the follow-up pairing check and successful syntax command are recorded in the
CM return. Source comparison to the declared baseline and AST-only counts were
computed locally, without importing or running the scientific entry.

The evidence-spec §11.8.6 rule applied verbatim is:

> Use existing trustworthy paths and checks where applicable. Add one focused verification for changed behavior and primary output; do not repeat smoke merely because a launch boundary occurred.

The AGENTS acceptance rule applied verbatim is:

> Parent acceptance checks actual artifacts, relevant changed behavior and credible focused check results, not a completion assertion alone.

| Affected boundary | Source and evidence checked | Bounded acceptance |
| --- | --- | --- |
| I versus authentic D0 | `make_config` wraps the existing D0 config, applying I's real .25 cost before both model constructions; common numeric infinite team cost/k10/caps10 and ordinary 6/6 defaults remain. Constructor tests restore production 16/32 lanes and H500. | Both learner and evaluator receive the intended real configuration; no `off` or public-mask substitution. |
| Native action/storage/reset | `collect_training` passes original action and step-data objects, unscaled reward, and terminal next values to storage; only afterward replaces both policy inputs from reset and clears that lane's state. The direct agent metadata are numeric; unused NaN gap work arrays are not part of returned step_data. | The new loop avoids the known E0 terminal-global-state mismatch without modifying E0. Same-token/no-gap decisions remain valid. |
| Real learning exposure | Five rollout/update stages, subsequent collection uses preceding updates, zero bootstrap at all-terminal edges, existing optimizer wrappers and initialization-relative displacement, ordinary buffer clearing after metrics publication. | Source preserves the planned real learner path. Synthetic optimizer calls in tests verify counting, not empirical learning competence. |
| Independent evaluator | Its arm-aware constructor and inherited E0 `_sync` copy active modules and all enabled normalizers, including ValueNorm. Construction/sync/reset/scoring stay inside `_preserve_rng`, with eval mode and no-grad scoring; no evaluator storage or update. | Training state and RNG are isolated. Evaluation segment/storage counts can be zero because this evaluator does not store learning segments; actual scoring decision/switch metrics remain visible. |
| Primary and completeness | Raw U and reporting-only J=6U/500; all 32 ordered differences, sample SD (ddof 1), conditional SE and inclusive .01 rule. Pair identity/config/count/endpoint checks preserve own-arm output if D0 is missing or damaged. | No training-reward rescaling, endpoint selection or fabricated pair polarity. Launch SHA is reported without becoming a pairing gate. |
| Failure and cap | Finite actual values are checked before JSON conversion; intended infinite costs become metadata strings only. Cooperative clock checks cover closed-file publication and preserve incomplete facts. | Future existing supervisor must enforce the complete outer cap; cooperative checks cannot interrupt a single optimizer update and are not a runtime guarantee. |
| Scope | 424 non-test lines, no protected-source edits, no additional framework/registry/profiler or scientific validation panel. | Engineering-scope §4: none added. 600-line runner, 2000-line research code and 300-second test budgets conform. No §5 breach observed. |

Independent reviewer `/root/dm_fsd_p47_resume/cm_am_fsd_b03_p47/rv_ah_fsd_b03_p47`
found an unnecessary launch-SHA equality condition on pairing. CM removed it
and added coverage that a document-descendant SHA cannot block otherwise equal
scientific inputs. The reviewer directly checked that correction and returned
**no material finding remains**. This is not an overruled critic or scientific
verdict. Actual scientific identity/configuration checks remain in the assembler.

The first suite had 32 pass/1 fail: the optional Windows RSS path imported
unrelated E3 during a fake-only test. CM replaced that import with installed
psutil's current-process RSS read. Two syntax attempts encountered Windows task
cache path handling; the same source files compiled with native path separators
and the extended task-cache prefix. Final suite: **33 passed in 4.26s**. The
post-review targeted pairing regression passed (1 case in 3.23s); syntax and
diff checks passed. Tool-computed complete observed check wall is
`9.140208 + 5.795297 + .1022448 + 4.6118665 = 19.6496163 seconds`, below 300.
No repeated full suite followed the syntax-only or one-predicate correction.

CM attempted task-scratch cleanup. Automatic approval review rejected both
verified PowerShell deletions as **"blocked by policy"**. The ignored
`temp/directions/flexible_skill_duration/test/uav_b01_p69_source_20260908/`
remains, containing check evidence/cache/fixtures. It is not a scientific output
root and no source depends on it. I did not attempt another deletion route.
This cleanup exception limits housekeeping completion, not source acceptance;
no launch, research disposition or owner approval is inferred from the rejection.

## 3. Counts, scientific meaning and remaining uncertainty

Current P69 scientific exposure is zero: no real learner/evaluator/environment
construction, checkpoint load, training start/transition/update, scientific
evaluation, simulation, profile, resource admission or remote staging. Fake
fixtures are test cases and cannot count as independent empirical evidence.
The production scientific root does not exist at source acceptance.

AST readback of the new runner matches the card: seeds 770503/780503; 16 training
lanes/32 evaluation lanes; H500/five rollouts; six UAVs/fifty users; D0/I caps
3600/18000s. If later allocated, algorithm work remains 80000 training transitions,
32000 evaluation steps, 112000 total environment steps/672000 agent observations,
10 update stages, four model constructions/two training starts/zero old loads,
6000 batch control calls. D0 joint rows are 800/rollout and I's maximum is 8000,
with common team rows 800. Real optimizer counts remain to be observed.

The old-work 1617.82/16178.2-second scenarios retain their stated limits; no
current remote rate or cap feasibility was measured. The selected complete
D0 3600/I 18000/sum21600-second caps remain binding. No pilot or earlier A was
added. Complete future timing includes admission/imports/initialization through
training, unique evaluation and closed-file paired publication.

Claim ceiling remains the prospective single-pair B question. The strongest
support for readiness is the actual preserved computation path plus focused
checks and independent review; that does not support a UAV gain. The reactive
D0 null, earlier competent E3 losses, B03's corridor gain together with its G
shortfall, and absent tuned scenario1 headroom remain scientifically unchanged.
The selected next discriminator is the new I/D0 native-return comparison, not
more fake cases. DM's within-±.01/low-confidence forecast is **unscored**;
owner prediction is **not taken (unattended)**. No formal UAV-entry registration,
recast or Portfolio lifecycle/priority/capacity change is made by this source intake.

## 4. Decisions this intake produces

**Object / technical.** Options: (a) accept this committed bounded source and
return readiness/exact future argv to Root; (b) require a concrete source correction;
(c) infer staging or experiment authority. Recommendation and selection: (a).
**Owner-delegated decision (unattended, 2026-09-03 instruction): (a)**, within
Root's P69 allocation. No unresolved measurement-changing source finding remains.
The residual runtime boundary is explicit and does not justify another smoke,
profile, automatic retry or scientific launch in this assignment.

Ordinary technical acceptance is recorded in this intake/card/audit; it creates
no additional P1/P2 review item and does not manufacture an owner reply. Existing
P67 direction/new-card items remain. Owner flags: none. At the clean boundary,
`item.py reviews --json` returned `[]` in this checkout and current main
(`b0748a8fa47e6901c61a2315535a981f33051878`); all FSD audit owner cells
were empty. No review needs application or marking answered, and no owner
prediction reply exists. Relative to the source-allocation checkout, current
main's only relevant instruction delta remains the already read/applied Root-wake
relay rule; evidence/engineering specs and compute declaration are unchanged.
The [Chinese source brief](../../portfolio/owner/briefs/flexible_skill_duration/2026-09-08_FSD_UAV_INDIVIDUAL_RENEWAL_B01_P69_SOURCE.md)
reports engineering readiness only.

## 5. Exact future argv and Root return

From a future detached worktree at the accepted source SHA, use the currently
configured remote interpreter (from `.codex/hmasd-compute.toml`):

```text
/home/wu/.venvs/hmasd/bin/python scripts/run_fsd_uav_individual_renewal_b01.py --arm D0 --output-root temp/directions/flexible_skill_duration/exp/uav_individual_renewal_b01_770503/D0
/home/wu/.venvs/hmasd/bin/python scripts/run_fsd_uav_individual_renewal_b01.py --arm I --output-root temp/directions/flexible_skill_duration/exp/uav_individual_renewal_b01_770503/I --d0-summary temp/directions/flexible_skill_duration/exp/uav_individual_renewal_b01_770503/D0/summary.json
```

These are source-readiness argv, not dispatched commands or accepted handles.
Root must explicitly allocate the full technical execution/observation/collection
phase before staging or admission. That later assignment retains the existing
remote-first `wsl_4070` CPU/four-thread route, exact committed source, fresh
on-node admission and complete supervisor caps, with D0 then I once and no
unallocated retry. I consumes the original D0 summary; primary readout and
publication stay inside I's cap. No hardware comparison or extra performance
validation is selected.

Return `3fa896737cf805ce63da048ddfa8873f2c5cc18b` (P69 allocation),
`ca36e2f941d6c4d4e996a9bd919378af44ea0e93` (accepted source), and this intake/card
commit to Root for specified integration, checking already integrated content.
DM sends one new P69 completed Root-action event through the configured relay;
native CM/reviewer results keep their original parent chain. No new Pro request,
scientific result or direction/Portfolio decision is needed by source acceptance.
