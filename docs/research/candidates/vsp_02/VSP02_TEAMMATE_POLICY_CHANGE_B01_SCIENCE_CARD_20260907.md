Claim: Full Adam RESET may change native adaptation-service return relative to CARRY after one active teammate-policy change on the selected fixed-member handoff task.
Binding MARL structure: (d) other-agent non-stationarity or partial observability; N=2, entity identities and roles remain fixed.

# VSP02 teammate-policy-change B01 — prospective science card

**VSP02-TEAMMATE-POLICY-CHANGE-B01 / B/EXPLORE.** This is a prospective object card, not a C freeze;
A/B have no consumption state. P14-VSP02-B-CARD-AND-CM-COMPARISON-01 authorizes this card/spec and
Root's five-arm engineering comparison, with **zero scientific invocations allocated**.
That was the P14 preparation boundary. **P15 now allocates one scientific pair under §8 below**;
all scientific definitions and the complete 1800-second cap remain unchanged.
Reuse `C:/Projects/HMASD-worktrees/dm-vsp02`, `codex/vsp02`. Root binds the committed preparation
return as the common engineering source; the future B uses its later accepted exact launch SHA.

The full scientific source is Convergence RESPONSE.md at
`1eb3b21b61747b21f374d252005fa48c32e4838d`, accepted in
`VSP02_TEAMMATE_POLICY_CHANGE_CONVERGENCE_INTAKE_20260907.md` §§2–6. The explicit recast remains
`recasts: 1`. The complete companion `VSP02_TEAMMATE_POLICY_CHANGE_B01_CODE_SPEC_20260907.md`
fixes the implementation of that design and the disclosed ordinary P14 choices. Evidence-spec
§§4,5.2,11.4,11.8–11.9 and engineering-scope §§4–5 control; no new decision node is requested.

## 1. Question, primary and ceiling

Does a full Adam reset improve or harm actual service delivered during the fixed adaptation
window after the courier changes policy, compared with ordinary carry from the same learned
network and other learner state? Primary per-arm AUC is the sum of the **1024 actual post-change
training-episode native returns divided by1024**; Delta is RESET minus CARRY. Every episode has
48 joint steps. Preserve all raw returns, non-overlapping16-episode means, sampled evaluations
and endpoints. Neither loss, evaluation interpolation nor a selected checkpoint replaces primary.

One complete pair can support only an initial signal/counterexample on this setup and budget,
and a reasoned bounded follow-up. No stable superiority, unique/generic Adam mechanism, novelty,
variable N, member/identity recovery, simultaneous co-adaptation, transfer, UAV entry or deployment.
No outcome-selected host, policy, seed or checkpoint. The old member-age question stays unresolved.

## 2. Population, information and event-to-consequence path

Persistent receiver A and courier B occupy a five-position corridor {-2,-1,0,1,2}. Each episode
has sixteen three-step service rounds; each round resets positions to0 and supplies one package,
without resetting entities or GRU. Both move left/right or wait; A may receive and B may deliver.
Simultaneous actions cannot combine movement and transfer. Only same-endpoint RECEIVE/DELIVER
awards one shared native reward; otherwise0, no shaping. Native episode service is0–16.

Each round has an independent fair midpoint light. The courier moves twice toward the light and
then delivers before the event; afterward it moves twice toward the opposite endpoint and delivers.
Both policies act legally and are fixed within regimes, with no teammate training or policy search.
The single switch follows prefix episode4096 and its final update. Both arms receive the same
persistent public change bit, with no new-policy content.

Both actor and critic use the same local history: own position, clock/round, visible light and
teammate relative position, actually observed prior teammate action, own prior action, realized
reward, missing/visibility markers and notification. No private target/script state, future action
or correctness label. Code spec §2 freezes an18-field raw encoding, lamp/teammate radius1, prior
B-action visibility at the start of the preceding executed step, and retained past signals across
round reset. These are disclosed ordinary P14 concretizations of the selected local information.

B's real endpoint choice changes where A must arrive. Waiting to observe B's first current move
leaves too few actions for two moves plus receipt; legal history and service feedback can improve
later-round choices and learning signals. Adam history may then change finite-budget service.
Fast recurrent inference can instead make reset unnecessary. There is no join/leave/rejoin,
replacement, survivor transfer, entity/slot change, censoring or variable-duration estimand.

## 3. Learner, comparator, fork and independent unit

Use the selected shared64-unit tanh encoder and64-unit GRU, categorical actor and scalar critic,
CPU FP32, one joint Adam, no normalization/extra target. Code spec §§3–4 fixes the precise PPO/GAE,
losses, default initialization and ordinary RNG interfaces. Selected values are Adam lr0.0003,
betas(0.9,0.999), epsilon1e-8, no decay/AMSGrad; PPO clip0.2, value/entropy coefficients0.5/0.01,
global gradient clip0.5, gamma1 and GAE lambda0.95. The terminal bootstrap is0 only after H48.
Each16-complete-episode rollout has four epochs × four whole-episode minibatches =16 joint Adam steps.

Master1103 supplies one prefix of P4096 episodes. After its final update and consumed-buffer
removal, fork identical learned parameters and other state: CARRY retains complete Adam state;
RESET clears all moments and per-parameter steps only. Preserve parameter groups, global progress
and constant schedules. Each independent arm object then performs Q1024 episodes on its own real
trajectory, alternating matched batches. GRU resets only at complete-episode boundaries. Pair
exogenous lights, action RNG and minibatch permutations; isolate evaluation RNG as specified.

The independent training unit is **one prefix and its entire pair**. Arms, service rounds, episodes
and repeated evaluations are not extra training seeds. No no-change arm or extra prefix is selected.

## 4. Evaluation, measurements and exposure

Sample E64 complete frozen stochastic-policy episodes at the old-prefix endpoint, once on the
shared post-switch q0 policy, and per arm at q={16,32,64,128,256,512,768,1024}. The shared q0 is64
actual episodes, not128. No greedy conversion, optimizer step or training-RNG consumption during
evaluation. Prefix competence is observed in the same B, not selected with a score/fork gate.

Publish actual environment steps, complete/partial episode counts, actual Adam.step counts,
evaluation and selection exposure, all raw returns and full curves. Record initial parameter RMS,
actual displacement after the first complete PPO rollout, at prefix end and per-arm from fork;
record the numeric model/Adam/global-progress fork state. These protect learner/comparison meaning;
no checkpoint service, hash guard or complete replay is required. Code spec §5 fixes output fields.

Python counts record nominal `lr*4096=1.2288`, versus default component initialization standard
deviations0.1361 (encoder) and0.07217 (GRU/heads): ratios about9.03 and17.03. This is a nominal scale
comparison, not an Adam displacement bound or measured movement. Required actual displacement is
read from the same future run; no extra pre-run learner probe. Current preparation exposure:
`environment_transitions=0; optimizer_steps=0; evaluation_episodes=0; model_selection_trials=0; result_bearing_invocations=0`.

## 5. Work, host/device and stopping

Main factors are `S*(P+2Q)*H`, four PPO data passes, and `(E+E+2*8*E)*H` evaluation, S=1:
6144 training episodes /294912 training joint steps /384 rollout batches /6144 Adam steps;
1152 evaluation episodes /55296 evaluation steps; **350208 total joint steps** and1179648 PPO
transition-passes. Reused passes are not new interaction; N2 does not double joint steps. Courier
execution is included despite zero courier training. No nested candidate/trajectory/solver search.

The future entire prefix-plus-pair invocation has one **1800-second wall cap**, including imports,
initialization, training, evaluation and publication. One process, one CPU compute thread, FP32;
in-process16-episode batching is allowed. It follows `.codex/hmasd-compute.toml` remote_first
(currently wsl_4070), detached at committed/pushed exact source with adjacent admission on that node.
The host is prospectively portable across the declared CPU routes, without cross-platform bitwise
claims. Local fallback retains the existing no-accepted-remote-process/fresh-admission conditions.
No remote workload or affordability check has occurred; actual wall/CPU/memory remain unknown.

Stop at fixed counts or the complete-invocation deadline; no sign-based stopping, extra arm, seed,
retry, resume or budget. Preserve actual partial observations/errors. Incomplete Q has no full-window
primary; if Q is complete but another output is incomplete, retain trustworthy native-window facts
and name the dependent limitation. Missing optional resources are resources_unmeasured. Technical
failure has no scientific polarity; a cap is not a cost prediction or released invocation.

## 6. MEI, headroom, prediction and reading narrative

Absolute MEI is **0.5 deliveries per adaptation episode**, or512 over Q: one extra service every
two episodes, avoiding an unknown baseline denominator and unrelated to old scores. Old-host matched
terminal greedy headroom remains exactly0. New-host headroom and baseline qualification are absent;
old X-memory observation/action/history/task/budget do not match, so its package is not reused.
Missing new headroom does not gate B. Working prediction adopted from Pro: Delta in[-0.5,+0.5].
Owner prediction: not taken (unattended); score any later actual reply at result intake.

Above +0.5, a trustworthy complete pair may support one or two new independent prefixes, retaining
all endpoint losses and comparator-competence limits. Inside the MEI, report the actual sign and
absence of a difference at this scale, not equivalence. Below -0.5, CARRY is the supported local
choice; retain every negative value, including inside the MEI. Poor prefix competence limits claims
against a competent baseline and permits no hidden tuning. No sign automatically grants compute;
these B narratives are not a C success rule or an all-positive-seed requirement.

Generic optimizer transience is the strongest alternative: the scripted teammate can be absorbed
into a changing environment. Recurrent inference, critic adaptation, step-count effects and one-run
noise also survive. Event-specific attribution would need a separately justified no-change
comparison; this first B relinquishes that attribution and does not wait for such a control.

## 7. Engineering scope and comparison boundary

Engineering-scope §4 machinery needed: **none**. In-memory fork state is algorithm work. Use plain
torch, argparse/CSV/JSON and Matplotlib Agg; no core edits, worker pool, registry, hash/currentness
guard, retry/resume, service or additional resource telemetry. Research source <=2000 new lines;
runner <=600. Orchestration30% is a review signal. Unit checks <=300s; runner fixture <=60s.

Root receives one complete code spec and five-item task at the committed starting source before
any CM coding. Common initial engineering cap is3600s per arm. The same small seed17/P16/Q16/E4
fixture preserves H48, model and update rules:48 training episodes,48 updates,16 evaluation episodes,
3072 joint steps per planned run; five arms mean15360 fixture steps, **not five B01 invocations**.
Finite unit fixtures and justified correction accounting are bounded in code spec §6. Keep every
outcome; ENGINEERING_FIXTURE artifacts never establish this card's performance claim.

Companions: `VSP02_TEAMMATE_POLICY_CHANGE_B01_CODE_SPEC_20260907.md`,
`VSP02_TEAMMATE_POLICY_CHANGE_B01_CM_TASK_20260907.md`,
`VSP02_TEAMMATE_POLICY_CHANGE_B01_PREPARATION_COUNTS_20260907.json`, and
`VSP02_TEAMMATE_POLICY_CHANGE_B01_PREPARATION_INTAKE_20260907.md`.

## 8. Current P15 execution allocation — 2026-09-07

P15's VSP02 section at main `25b1a88b162ae137b5071ca2d9acb87007fb3ea9` supersedes only the
P14 zero-invocation boundary. It allocates **one complete same-prefix scientific pair**: seed1103,
P4096, Q1024 per arm and all existing evaluations, with one1800-second whole-chain cap. No extra
seed/comparator, retry, resume or cap increase is allocated. A/B consumption rules are unchanged.

The accepted baseline implementation is `b0c957d9b9a23506dbd0ba8a1b8c729ea50d8cad`, with the
evidence-path clarification at `ef39e40706cb9656a81dfa1dd640bac419cd89a8`. DM's P15 readiness
record verifies its correspondence with this card/code spec and the retained original acceptance
artifacts. Source remains unchanged; no new CM comparison or duplicated fixture is needed.

Root uses the exact committed/pushed preparation revision supplied with
`VSP02_TEAMMATE_POLICY_CHANGE_B01_P15_READINESS_20260907.md`, whose implementation surface matches
the accepted baseline. The planned detached worktree is
`/home/wu/hmasd-worktrees/vsp02-tpc-b01-p15-s1103-a1`, node `wsl_4070`, CPU FP32 with one compute
thread. On-node metadata reports CPython3.10.21, torch2.7.0+cu118, NumPy1.26.3 and Matplotlib3.10.0;
the CUDA-enabled distribution still executes this explicit CPU policy. No cross-platform bitwise
claim is made. Fresh memory admission remains adjacent to the actual runner invocation.

The existing seed17 engineering artifact shows first16-step parameter RMS displacement
0.0021576136350631714 from initial parameter RMS0.07669830322265625, a ratio0.028131178193076693.
This establishes a nonzero update path at fixture scale, not scientific performance or a runtime
projection. The machine-generated P15 facts retain these readings and the planned counts.

Root launches/observes the single accepted handle; existing CM `/root/vsp02_cm_baseline_b01`
collects and technically accepts it in the designated authoring checkout; this DM performs the
result intake, audit and Chinese brief. Current scientific exposure remains zero until that launch.
