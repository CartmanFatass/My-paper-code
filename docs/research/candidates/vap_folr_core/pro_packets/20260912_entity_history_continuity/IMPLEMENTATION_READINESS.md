# FOLR entity-history implementation and resource readiness

**Decision input only: the OPEN family is specified, but no implementation, fit,
test invocation, seed, resource reservation or new cap is allocated here.** FOLR
remains ACTIVE. The selected comparison is one observer-owned GRU16 entity bank
against fresh same-public-information GRU64 Generic RETAIN. Preserve the scalar
LEARNED_EVENT package H and every B01–B04 observation.

This follows the [accepted intake](INTAKE.md), particularly sections 2–4. Root's
accepted main commits are `2e2549d3c6ea3613d33f856342db9524c4057a10` and
`4049f41caccc0f776280b4072b53ba68ec2066c8`. Their required direction/intake/source
surfaces equal the shared authoring HEAD
`78f0869d318ee79774b717bad1cbe2fbc52222d8`; no merge is needed to obtain them.
[READINESS_FACTS.json](READINESS_FACTS.json) binds the inspected source bytes and
computes the counts below using standard-library arithmetic only.

## Minimal L0 and L1 scope

| L0 field | Proposed implementation batch if funded |
| --- | --- |
| Deliverable | Implement the already selected public-information variant and two actors through real replay learning, final checkpoint and native-return publication; then accept the changed contracts. This packet is not that implementation or acceptance. |
| Ownership | DM uses `C:/Projects/HMASD-worktrees/codex-vap-folr`, branch `codex/vap-folr`. Proposed new code directory `experiments/candidates/vap_folr_core/entity_history_b01/`, runner `scripts/run_folr_entity_history_b01.py`, focused tests under `tests/experiments/candidates/vap_folr_core/entity_history_b01/`. These are layout proposals, not a frozen object or created paths. |
| Protected meaning | Intake section 2 controls information, observer/subject lifetime ownership, GRU16/GRU64 and readout. Preserve native easy Traffic Junction, five slots, twenty actual ticks, five actions, reward/dynamics/RNG, CPU FP32, Torch compute/inter-op 1/1, complete-episode TD/double-Q/FlexQMixer and final non-learning evaluation. |
| Acceptance | Evidence-spec sections 4 and 11.4/11.8; engineering-scope sections 7.1–7.3; the changed-risk checks below. Independent high-risk review is required for the implemented information/recurrent/RNG/checkpoint diff, not commissioned for this document. |
| Budget/stop | One proposed implementation/acceptance batch and one matched training pair. Actual funding/caps and the prospective card remain Portfolio/DM work at their proper tiers. No sweep, timing pilot, exhaustive reconstruction, fourth scalar pair, repeat consultation or automatic successor. Section 4 additions needed: **none**. Reuse existing admission, supervisor and Monitor; create no cache, registry, service or generic framework. |

The future implementation stays within engineering-scope section 5: at most
2,000 new non-test attempt lines and 600 runner lines; orchestration proportion
is a review signal. Keep checks proportional to the actual change. No L2/L3
framework or baseline/dependency migration is needed by the inspected path.

Source root below is `experiments/candidates/vap_folr_core/public_lifecycle_b01/`
at accepted main `4049f41ca`; line numbers refer to those fixed bytes.

| Exact entry point | Smallest new interface / reuse |
| --- | --- |
| `environment.py:7 LifecycleEnv`, `reset:8`, `step:27`, `observation:37`; native `native_env.py:55 reset`, `step:80` | Extend lifecycle observation with common active/birth/departure table and deterministic observer-local visible/seen/primitive-age data. Advance bookkeeping once at reset/completed transition; observation reads must be idempotent. Retain native add/remove/reward side effects and draws, including same-step replacement. |
| `model.py:16 Actor`, `forward:32` | Implement new concrete Generic and BANK actors. Both receive the full fixed-order public table outside masked peer tokens, including invisible subjects. Sanitize physical inputs by the requesting observer's visibility before learned pointwise operations; neither actor sees another observer's private features or critic-only values. |
| `attention.py:22 EntityAttentionLayer.forward` | Reuse compatible projections/masking where appropriate. Its current query prefix `query[:n_queries]` cannot blindly implement one query for every observer: observer i must use its own query, not slot zero. BANK attends only its own live, previously seen entries; no cross-observer pooling. |
| `model.py` and intake section 2 state equation | BANK has shared GRU16 per observer–subject entry, no pooled input to a cell, no extra pooled GRU. Cut row/column state and temporal gradients at the respective lifetime boundaries; carry unseen continuing entries unchanged with legitimate gradients. Use the selected current-feature bypass, zero while unseen, and feedforward 64-to-five Q readout. Generic retains its GRU64 with own-lifetime cuts. |
| `collection.py:20 collect`, `sample:56`, `epsilon_at:7`, `select_action:11` | Reuse these functions: collection stacks every observation key, and `hs[:, -1]` already permits a bank axis. Preserve 21 controller/RNG calls but only 20 environment steps. Replay stores observations, not acting hidden states. Add only the new BANK-minus-Generic primary helper; old scalar counters/rules are not bank reset evidence. |
| `learner.py:16 Learner`, `update:27`, `save:57` | Current constructor directly imports old Actor. Use a small new concrete learner constructor/import while retaining the TD, double-Q, RMSprop, target-copy and save contract. `update` discards the returned hidden sequence, so unchanged Q shape preserves gather/mixer compatibility. Recompute online/target bank state with their own parameters from complete episodes. |
| `flex_qmix.py:37 FlexQMixer`, `forward:45` | Reuse the centralized training-only mixer and its original nine physical/action features unchanged; no bank or new public table enters its input. Its global features must not enter the actor. |
| `scripts/run_folr_public_lifecycle_b01.py:21 main`, `publish:14` | New thin runner chooses BANK/GENERIC_RETAIN, imports the new environment/learner, and preserves training/evaluation/seeding/checkpoint/publication order. Old arm choices and the hard-coded 1,800-second wording are not usable new allocation inputs. Bind the actual granted cap and committed commands prospectively. |

L1 shapes use batch B, episode positions T=21 and I=J=N=5. Physical entities
`[B,T,N,4]` and previous actions `[B,T,N,5]` remain FP32; actions are
`[B,T-1,N]` int64 and reward/termination `[B,T-1]` FP32. Public activity,
birth/departure and continuation are `[B,T,N]` booleans; local visibility/seen
and primitive age are `[B,T,I,J]` (boolean/finite integer, common deterministic
casting to FP32). Labels are stable public slot labels, not persistent trip IDs.

Generic hidden state is `[B,I,64]`, returned history `[B,T,I,64]`; BANK is
`[B,I,J,16]`, returned history `[B,T,I,J,16]`. Both return Q `[B,T,I,5]`.
Observer birth/replacement clears its entire row; subject departure/replacement
clears its column, seen and age; same-trip reappearance resumes. Only visible
active subjects update cells. New visible observations may initialize new cells
after the cuts in the same call. Never-seen subjects have no history token.
Both actors get the same local visibility/seen/age and full public metadata.
Only same-role, same-shape common tensors/RNG consumers are matched at
initialization; isolate arm-specific constructor draws. Whole actor parameters,
parameter counts and initial policies are not asserted identical.

## One-pair source law and unknown cost

Sizing remains 5,000 training episodes, 128 final episodes, batch 32, twenty
native ticks and 21 controller positions per arm. Updates start at episode 32:
`U = 5000 - 32 + 1 = 4969`. The two-arm work has no search or nested candidates.

| Quantity | Generic RETAIN | BANK | Pair / interpretation |
| --- | ---: | ---: | --- |
| Independent training fits | 1 | 1 | One matched pair; no repeat allowance |
| Native train + final ticks | 100000 + 2560 | 100000 + 2560 | 205120 |
| RMSprop updates | 4969 | 4969 | 9938 |
| Replay recurrent row positions, online + target | 33391680 | at most 166958400 | `U × 32 × 21 × 5 × 2`, BANK adds a subject factor 5; backward and gate widths still matter |
| Acting recurrent row positions, train + final | 538440 | at most 2692200 | `(5000+128) × 21 × 5`; BANK adds a subject factor 5 |
| FP32 current hidden-state payload per episode | 1280 bytes | 1600 bytes | Tensor payload only, not RSS or admission memory |
| FP32 one replay-batch hidden-history payload | 860160 bytes | 1075200 bytes | Excludes gates/autograd, projections, Q/mixer, targets, optimizer, replay and Python overhead |
| Complete invocation wall / peak process memory | UNKNOWN | UNKNOWN | Neither row ratio nor width ratio supplies a speed or memory prediction |

For each arm, the runner's complete logical cost is
`W = admission/initialization + 5000*C_collect_train + 4969*C_update(32,21,online,target)
+ checkpoint + 128*C_collect_final + publication/exit`.
The update term includes backward, mixer, clipping and optimizer; collection
includes environment, information bookkeeping, attention/readout and recurrent
work. The coefficients are **unknown for both new BANK and new-interface
Generic**. Pair invocation wall is `W_BANK + W_GENERIC`; study elapsed critical
path is different if execution overlaps. No old-clock extrapolation, width-based
speed claim or zero-learner cost assumption fills these unknowns.

Complete study work additionally includes the one implementation batch, focused
checks, required independent review/corrections, exact-source staging/verification,
supervisor launch, monitoring, collection/source-primary
acceptance, archival and assigned cleanup. Their wall/CPU/agent costs are
unknown; no support run was added to price them. Root/Portfolio should account
for support once and name the new per-arm and complete allocation explicitly.
Old caps/references, including the 300-second support reference, are not new
funding. The toy 2,700-second runtime-investigation threshold is not a scientific
polarity, study cap or automatic launch gate.

## Remote prerequisites and actual admission

The live primary-control configuration is the source of future routing.
This read found enabled `hmasd-wsl-node` / `LAPTOP-U9TDKC8A`, repository
`/home/wu/projects/HMASD`, detached execution worktrees under
`/home/wu/hmasd-worktrees`, Python `/home/wu/.venvs/hmasd/bin/python`, and
supervisor `/usr/local/bin/agent-task`. Configured Python 3.10.21, NumPy 1.26.3
and Torch 2.7.0+cu118 are recorded configuration, last verified 2026-09-04;
they are not a new environment or resource measurement. A GPU-equipped node
does not change this selected CPU FP32/Torch 1/1 path. The inspected native
environment is Python/NumPy; no new native extension build was identified.

Before funded execution, publish source and committed exact commands, fetch
the launch SHA, establish its detached worktree and required imports on that
node, and preserve the Linux publication path (`resource` is used by the old
runner). No Windows fallback or CUDA migration is selected here. Portable
heavy verification also uses published exact bytes remotely; no uncommitted
source is copied for execution.

`scripts/hmasd_resource_preflight.py:250 assess_memory_floor` and
`admit-memory --out <receipt>` provide the actual fixed floor: physical and
effective available memory each at least **4 GiB**. Effective availability is
the minimum of physical availability and bounded cgroup headroom; missing
required measurements refuse admission. Put admission adjacent to each exact
invocation in its supervised command, before model/RNG creation. This packet
has no current admission result. Payload examples above are not a substitute
or an extra projected-memory gate.

After any later accepted launch, use the current primary Monitor configuration:
MONITOR_ADD requires `get_goal`, continuation/creation of an unbudgeted matching
unfinished goal, retention through accepted terminal delivery and an actual
goal-state MONITOR_ADOPTED receipt. DM retains collection and acceptance. No
handle exists now; no Monitor or Transport action is requested by this packet.

## Focused acceptance after a real allocation

1. Falsify actor information leaks by perturbing unseen physical values and
   other observers' private values; exercise invisible public notices in both
   policies, never-seen masks, inactive subjects and correct observer-i query.
2. Exercise departure, same-step replacement, observer replacement and unseen
   same-trip reappearance; check row/column cuts, gradient cuts versus valid
   carry, age bookkeeping and idempotent observation reads.
3. Check sequential collection versus complete-episode online/target unroll,
   their own parameters and unchanged Q interface; no acting-state replay cache.
4. Exercise a focused real learner update through bank gradients, mixer,
   RMSprop, target copy and checkpoint serialization, plus compatible-module
   RNG matching. Check the dependent finite primary-array/mean publication.
5. Preserve native reward/RNG/terminal controller behavior; verify new runner
   arm/seed/cap routes and BANK-minus-Generic inclusive ±1 reading. Incomplete
   output has no scientific polarity. A smoke check does not become a pilot.

Reuse relevant existing cases in
`tests/experiments/candidates/vap_folr_core/public_lifecycle_b01/test_boundaries.py`
(native/refill, actor timing, real learner/checkpoint, replay RNG/publication)
as source pointers; do not automatically rerun the whole scalar-specific suite.
Future test scratch belongs to its creator under `temp/`, with retained useful
diagnostics and cleanup. No tests or experiment imports were executed here.

**Technical choice:** publish this source-grounded readiness input (recommended)
instead of inferring timing, funding or runtime acceptance. Owner-delegated
decision (unattended, 2026-09-03 instruction): publish the bounded technical input.
The scientific-reading assumption remains intake section 3: common public facts
must reach both actors, while retained physical history belongs only to its
observer. No new scientific claim or mechanism selection is made. Strongest
support is the untested ownership/action path; B04's competent generic remains
the strongest counterevidence. The next discriminator, if funded, is the one
real native package comparison; its claim ceiling remains exploratory B.
