# VSP03 B01 technical contract

CM baseline: `24dad2b63aea7f825dcc4ac3002a5d955f153eec`; isolated branch
`codex/cm-vsp03-b01-20260905`. This implements the science card and complete Pro archive
SHA-256 `068a9b6e123183ca9fda857a3874b35b91daed3e213e47eb61c7a97992b542f6`.
No result has been observed at contract writing. Current main AGENTS sections 5–8,
evidence specification 11.8/11.9, engineering/runtime specifications and nearest directory
instructions were read. Older repeated-smoke/ratio wording does not add a requirement.

## Acceptance and ownership

Produce the actual seed-1 T/G comparison at updates 32, 64 and 128 and fixed F at the main
endpoint, with native per-episode components, training curves, exposure and final parameters.
The engineering question is whether the complete selected chain implements that comparison;
DM judges whether initialization helps, the generic learner matches it, or the prior hurts.
No upper, search, new seed, scientific interpretation, old event-source certification, FSD
repair, historical reconstruction, core changes or successor is included.

Owned new source is `experiments/candidates/vsp_03/vsp03_b01/`, thin
`scripts/run_vsp03_b01.py`, optional mirrored tests, and `VSP03_B01_*TECHNICAL*.md`.
Semantic implementer uses its own worktree. CM integrates and inspects the complete diff;
independent reviewer checks scientific semantics and publication. Unrelated changes stay intact.
Scope specification section 4 additions: **none**. No new service, retries, provenance guard,
resume layer, framework, configuration registry, or resource instrumentation platform.

## State and numerical contract

The one process owns both learners sequentially. Each arm independently owns model, joint Adam,
action generator and its current 128-episode batch. CPU NumPy arrays carry independent episode
states and 40 uniforms per episode; time transitions remain sequential. Active policy input is
at most `[128,6]`, and a complete batch has at most 1,152 valid decision rows. No replay,
recurrence, worker, target network, clipping, GAE or discarded training batch is introduced.

Environment identity persists through all 40 transitions. Occupancy starts at one, age at zero;
leave probability is `1/(d+4)`, re-entry probability `1/2`. Events occur between integer states.
At t=0,4,...,32, read `(t/40,y,d/40,a,e,b)` with `b=a*y*(1-e)` before updating history.
CONTINUE sets a=y,e=0; the armed negative-event latch survives re-entry; submission clears bits.
Submission service samples t+1 through t+8; service failure and completion never truncate tails.
Native integer units are `200*success-10*attempt-waiting_ticks`, divided once by 200.
Return-to-go at a valid decision excludes already incurred waiting: `(final_units+t)/200`.
Final CONTINUE retains eight waiting ticks, and no post-submit state becomes a gradient row.

Each CPU float32 learner has actor 1,314 and critic 257 parameters. Corresponding PyTorch Linear
hidden/critic initialization is paired; selected residual/direct-b initialization alone differs.
All parameters remain trainable. Actor and entropy use sums over valid decisions divided by
128 episodes, critic uses 0.5 times valid-row mean squared MC error, advantage is detached.
One backward and joint Adam step per full batch; standard betas/epsilon, lr .001, entropy
`0.01*max(0,(64-u)/63)`. Evaluation uses current parameters, no updates, strict logit>0 submission.
Final parameter serialization is for inspection, not a resume promise or checkpoint selection.

Frozen stream constants: PCG64 with `SeedSequence([seed,split,episode])`, 40 uniforms per episode;
train split 100 and evaluation split 200+update. Episode IDs start at zero within each split;
training batch u uses IDs `(u-1)*128` through `u*128-1`. T/G and final F share addressed
environment streams independent of actions. PyTorch initialization seed is `10000+seed`;
separate CPU action generator seeds T=`20000+seed`, G=`30000+seed`. The eight check episodes use
explicit synthetic tapes. No cross-host bit-identity or upstream-library equivalence is claimed.

## Cost, coverage and execution

Per-arm prospective projection: `I_q + 128*C_q(128,40) + 10*E_q(128,40) + O_q`;
all unit seconds are unknown. Shared work is imports, eight complete check episodes, eight F
batches, summary/publication/read-back. Normal full training batches supply measured cost and
remain training exposure; no extra pilot. Sequential study critical path equals the complete
invocation wall; no summed parallel speed assumption or unmeasured aggregate CPU claim.
Total selected work is 36,360 full episodes, 1,454,400 ticks and 256 joint steps.

Post-learner path coverage: the one selected eight-episode check, executed once inside this
invocation before training, exercises native accounting and the actual write/read publication
path. Static and non-rollout loss checks may precede launch; no repeated simulation smoke.
Review checks initial latch, read-before-update, departure/re-entry, final service tick,
deadline, valid MC targets, objective reductions, counts and endpoint consumers.

Configured execution node is `wsl_4070`, SSH `hmasd-wsl-node`, Python
`/home/wu/.venvs/hmasd/bin/python`; CPU, one compute thread, one scientific process.
Set BLAS/OpenMP thread environment to one before imports and Torch intra/inter-op to one.
CPU portability is prospective; no live migration. Frozen committed/pushed bytes go in an
exact-SHA detached worktree under `/home/wu/hmasd-worktrees/`. Existing `agent-task` runs fresh
actual-node `hmasd_resource_preflight.py admit-memory --out <receipt>` joined by `&&` to the
runner. Remote command, launch SHA, cwd, output and receipt are recorded before acceptance.
Output root will be `temp/directions/vsp_03/exp/vsp03_b01_seed1_r01` in that worktree.

The hard whole invocation bound is 1,800 seconds including imports, check, both arms,
evaluation, reference, publication and necessary read-back. Stop on completion, cap or actual
required-path defect. Earlier endpoints stay labelled at their actual budgets; partial output
is never main-endpoint completion. Missing optional resources narrow resource reporting only.
After acceptance the existing root tracker receives the exact durable task handle; CM retains
technical collection. No observer change permits another launch.

## Reference evidence

Applied `.agents/skills/hmasd-scientific-tools/SKILL.md` and only `references/adapters.md`.
Pinned EPyMARL `cbc38c09588064eab978501d0f12c2cf58fa7fc2` source lines 84–106 show detached
advantages and masking but use valid-row actor normalization, clipping and a separate actor
step; critic is separately stepped. Those differences are deliberately not imported.
Pinned on-policy `de66d7a4b23fac2513f56f96f73b3f5cb96695ac` shared buffer and archived report
show explicit time/environment/agent axes and flattened valid samples. This design uses the
layout lesson only, with no PPO epochs, GAE, subprocess wrapper or framework dependency.
These read-only sources establish implementation patterns, not measured speed or competence.
