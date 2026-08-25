# External Review Request: R30 Fixed-Clock Autoregressive Skill Editing

You are reviewing both an algorithm decision and the concrete repository that
must implement it. Work from private repository
`CartmanFatass/My-paper-code`, branch `aggressive`, target commit
`f62baf626f6f37903b3929c4732952f95d2bc2ab`, or from the supplied ZIP.

## Status You Must Preserve

- R30 is accepted as a design but is **not implemented** at the target commit.
- The current code still samples independent `(skill, duration)` heads, invokes
  the autoregressive loop only for expired agents, and trains high PPO from
  completed variable-length segments.
- R29 actor-density-ratio rewards are retired. Do not rescue, retune, or rename
  that family.
- The first R30 implementation is reward-pure: no new semantic reward, team
  reward, communication-specific intrinsic signal, DADS objective, `q_d/q_D`,
  edit penalty, switch penalty, lifetime bonus, duration entropy floor, or
  forced maximum lifetime.
- The low actor remains `pi_l(a_i | o_i, z_i)`.

## Single Review Decision

Return exactly one top-level verdict:

```text
APPROVE R30
MODIFY R30
REJECT R30
```

The decision is whether the proposed R30 algorithm can be implemented as the
next core HA-CTSE controller after the specific corrections you identify. This
is not a request for a general code-quality review.

## Required Technical Review

Read `R30_FIXED_CLOCK_AR_EDIT_DESIGN_20260714.md` and inspect every primary code
location in `CODE_MAP.md`. Then decide the following rather than merely listing
options.

### 1. Action factorization and pruning

Check the proposed normal-check action:

```text
E_i(current) = {KEEP} union {SET(z): z != current}
P(KEEP)      = p_keep
P(SET(z))    = (1-p_keep) * pi_z(z | SWITCH, applied roster prefix)
```

Verify masks, initial assignment, executed log-probability, entropy semantics,
and whether the design really removes the damaging `K*D` and
short-segment-frequency biases without losing asynchronous realized lifetimes.
Distinguish reduction of per-agent branches from the still-combinatorial
`K**N` joint roster set.

### 2. MAT-style sequential benefit

Determine which high-policy surrogate should actually be implemented for a
stored all-agent edit sequence:

1. one joint PPO ratio `exp(sum_i delta_logp_i)` with one block advantage;
2. token-wise clipped ratios with the same block advantage, averaged over
   agents;
3. sequential/conditional agent advantages in the HAPPO/MAT theorem style;
4. another precisely specified minimal alternative.

Choose one for R30 and justify it mathematically. State exactly which MAT
benefits survive and which theorem claims do not. Do not answer with “all are
possible.”

### 3. Critic and advantage semantics

The current `SkillDurationPolicy.value_head` is evaluated from token features
that include the autoregressive prefix. Decide whether R30 needs:

- one pre-action centralized check value `V_H(x_tau)` independent of sampled
  token prefixes;
- per-agent/token values;
- conditional prefix values;
- or another construction.

Specify high reward aggregation, `Gamma=gamma**L`, per-environment GAE,
terminal blocks shorter than `k0`, incomplete blocks at policy-update
boundaries, normalization, and the exact tensor shapes. Prevent action leakage
into the baseline.

### 4. Clock and collector correctness

The current training loop passes an interleaved global `rollout_idx` into
`maybe_assign_skills`, while the agent also tracks per-environment episode
steps. Specify the only correct R30 check clock and how it behaves across:

- `num_envs > 1`;
- episode reset;
- rollout/update reset while the simulator continues;
- terminal partial blocks;
- initial skill assignment.

### 5. Working-roster teacher forcing

Verify that execution and training can reconstruct the same prefix: earlier
agents' applied `KEEP/SET` results, later agents' old active skills, ages, agent
order, and masks. State what must be stored versus deterministically rebuilt.
Identify any mismatch in the current `_build_roster_ar_prefix` and segment
reconstruction paths.

### 6. Process-segment decoupling

Specify how fixed-check high transitions coexist with variable low-level skill
segments:

```text
KEEP   -> continue the existing semantic/process segment
SET(z) -> close old segment and open z segment
episode/update boundary -> on-policy flush
```

Check whether current `Segment`, `SegmentManager`, `process_update`, reward
injection, and `update_high_from_segments` contain hidden assumptions that
would double-update, omit, or contaminate the new high policy.

### 7. Long-lifetime learning and collapse

Review `p_keep_init=0.6`, derived from the retired uniform
`{1,2,3,4}`-block mean. Decide whether this is the correct no-sweep migration.
Explain whether delayed task GAE is sufficient to make long useful skills
learnable and what prevents `always KEEP` or `always SWITCH` without adding a
lifetime reward or keep entropy.

### 8. Skill differentiation boundary

Review the proposal that switch-skill entropy is isolated to the skill branch:

```text
-lambda_z * stopgrad(p_switch)
          * H(pi_z(. | SWITCH, stopgrad(shared_features)))
```

Decide whether this is needed and implementable without disabling useful PPO
gradients. Confirm or correct the fixed `W=k0`, duration-blind, low-GAE-only
interface reserved for a later realized-effect semantic target. Do not invent
that target in this review unless R30 is invalid without it.

### 9. Checkpoint migration and exact code cut

Decide which parameters can be reused from the pre-R30 checkpoint and which
must be reinitialized. Address the old duration head, high optimizer state,
shared trunk, skill head, value path, compact/OPT encoder, low actor/critic, and
recurrent states.

Give an exact implementation map by repository file and function/class. Name
code that should be replaced, code that should remain as a frozen legacy
comparator, and any code that must fail closed in R30 mode.

## Required Output Format

Use these sections:

1. **Verdict** — one of the three allowed verdicts.
2. **Fatal issues first** — only issues that would make the current design or
   implementation scientifically wrong.
3. **Corrected R30 algorithm** — final equations and pseudocode, not a menu.
4. **Exact code change map** — file, class/function, and required change.
5. **Tensor / gradient / clock contract** — concise but complete.
6. **Checkpoint migration** — reusable and reinitialized state.
7. **Smallest evidence-bearing check** — at most four decision metrics and
   explicit abandon/revise outcomes.
8. **Claims allowed and prohibited** — especially MAT, long lifetime, HMASD
   semantics, and task improvement.

Do not spend space restating the project history. Do not propose a sweep,
another review round, a broad test suite, or more than one implementation route.
If you modify R30, provide the single corrected route Codex should implement.
