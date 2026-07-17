# HA-CTSE Current Work

Updated: 2026-07-17

## Controller

- **Active controller:** Codex on branch `aggressive`, working directly in
  `C:\project\HMASD`.
- **Versioning:** Git only; push with `git push My-paper-code aggressive`.
- **Project boundary:** IMOD is operational reference only, not HMASD evidence.
- **External review:** automatic reviewer communication is enabled under the
  bounded workflow in `AGENTS.md`; reviewer responses never authorize code,
  experiments or scientific promotion by themselves.

## Objective

The blind dual-divergent and convergent design round for an
architecture-matched F0/F1 dynamic-roster testbed is terminal. Its verdict is
`MODIFY_TESTBED_CONTRACT`.

The accepted design asks one question: after ordinary dynamic-roster access and
executable skills are established, does conditioning later skill commitments on
earlier applied commitments improve natural roster composition and terminal
external utility beyond the matched F0 controller?

The generic-`SHORT` environment has passed the Stage A no-learning carrier.
Stage B direct primitive-AR access remains authorized. Its first formal attempt
was scientifically invalid because merged recurrent chunks changed CUDA batch
geometry; an original-batch retry was stopped after strided replay slices still
made joint log-probability error exceed `1e-6`. Contiguous original-batch replay
now gives exact zero on the retained 16-environment checkpoint/ledger
diagnostic; a fresh unchanged rerun is required. F0/F1 remains unauthorized.

## Causal Portfolio

- **H0 / F0 sufficiency:** strongest undefeated ordinary-MARL null.
- **H1 / F1 applied-prefix value:** leading conditional hypothesis, still
  untested.
- **H2 / skill execution failure:** active upstream alternative if direct
  primitive control succeeds but both skill arms fail.
- **H3 / exogenous timing limitation:** conditional diagnostic only; learned
  event time remains deferred.

F0 and F1 must share the complete runtime, model, optimization, ledgers and
exposure. Their sole treatment difference is:

```text
F0 -> initial_summary
F1 -> working_summary
```

## Next Actions

1. Commit and push the isolated Stage B replay-geometry repair, then rerun its
   unchanged local 16-environment, 320,000-transition CUDA gate from zero.
2. Interpret only the terminal Stage B result; do not implement or run F0/F1
   unless direct access is valid.
3. Remove the uncommitted R55 draft only at its separately verified cleanup
   boundary; never execute or repurpose its gate.

## Immediate Constraints

- The accepted testbed uses anonymous `4 -> 2 -> 6 -> 4` membership, one
  generic `SHORT` action, a persistent duty, variable-`N` reactive workload,
  horizon 80 and one terminal external utility.
- Evidence is serialized:
  `carrier -> direct primitive-AR -> paired F0/F1 -> conditional timing read`.
- `ha_ctse_process/dynamic_roster_testbed.py` is an isolated environment state
  machine; it is not wired into `train.py`, collectors or the event controller.
- Stage A result `logs/f0f1_dynamic_roster_stage_a_20260717_143552` is valid:
  all M0 checks pass; constructive `P=S=U=1.0`; random positive-utility fraction
  `1.0` with mean utility `0.331217`; optimizer and intrinsic reads are zero.
- Stage B uses a 14,980-parameter anonymous recurrent primitive actor-critic,
  token-factor PPO with one shared team advantage/value, raw current-step
  action-count prefixes and strict standalone schema-3 checkpoints. Its
  focused test passed; a CUDA fresh-to-resume smoke preserved exact ledger and
  cumulative counters, and replay maxima are below `5e-7`.
- The first 320K attempt met every access threshold but is not scientific
  evidence: joint replay reached `1.77e-6`. An original-batch retry was stopped
  at update 181 when strided slices still reached `1.37e-6`; contiguous slices
  make the retained diagnostic exact zero. Only the fresh rerun counts.
- Each learned arm is frozen at 320,000 transitions, 16 environments, rollout
  80, 250 updates and PPO4. Failure cannot trigger a budget, seed, threshold,
  reward or model rescue.
- Intrinsic reward remains environment-agnostic. Task fields, identities,
  roles, success predicates, progress and external reward cannot enter it.
- The current event-runtime skeleton is interface and wiring evidence only. It
  does not establish environment access, skill learning, F1 usefulness or UAV
  transfer.
- R41B remains the positive fixed-`N` source anchor. R51--R54 exact contracts
  are retired; R55 remains an unexecuted, uncommitted draft and is not active.
- Do not add graph, attention, slots, critical residuals, team latent, a new
  discriminator, learned ordering, learned event time, task-specific intrinsic
  reward or reward shaping to this route.
- Git history and `memory/ExpRecord.md` preserve retired-result detail; do not
  duplicate it here or reopen a retired branch by retuning.

## Pointers

- `memory/ALGORITHM_PRINCIPLES.md` — durable research contract.
- `memory/IMPLEMENTATION_PLAN.md` — latest staged core implementation state.
- `memory/ExpRecord.md` — formal experiment contracts and terminal decisions.
- `docs/research/designs/F0_F1_DYNAMIC_ROSTER_TESTBED_CONTRACT.md` — accepted
  design-only contract and exact evidence branches.
- `docs/research/designs/VARIABLE_N_LIFETIME_EVENT_ARCHITECTURE_CONTRACT.md` —
  retained event-runtime architecture boundary.
- `docs/external-review/rounds/20260717_f0_f1_dynamic_testbed_design/` — blind
  reviews, controller synthesis, convergent raw response and disposition.
- `docs/external-review/rounds/20260717_variable_n_lifetime_architecture/` —
  preceding architecture review.
- `docs/external-review/rounds/20260717_variable_n_lifetime_implementation/` —
  preceding implementation-plan review.
