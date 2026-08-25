# GPT-5.6 Pro Convergent Dynamic-Testbed Disposition

You are the convergent adversarial reviewer in the existing
`HMASD Algorithm Consultation` conversation. The blind Gemini and open-Pro
reviews are complete. Adjudicate both against the pinned repository and issue
one final design disposition for the F0/F1 dynamic-roster testbed.

## Repository files to inspect

Read all of the following at the pinned commit:

- `docs/external-review/rounds/20260717_f0_f1_dynamic_testbed_design/00_REVIEW_BRIEF.md`
- `docs/external-review/rounds/20260717_f0_f1_dynamic_testbed_design/01_SHARED_SOURCE_MANIFEST.md`
- `docs/external-review/rounds/20260717_f0_f1_dynamic_testbed_design/11_GEMINI_DIVERGENT_RAW.md`
- `docs/external-review/rounds/20260717_f0_f1_dynamic_testbed_design/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260717_f0_f1_dynamic_testbed_design/30_CODEX_SYNTHESIS.md`
- `docs/research/designs/VARIABLE_N_LIFETIME_EVENT_ARCHITECTURE_CONTRACT.md`
- `docs/research/designs/VARIABLE_N_LIFETIME_EVENT_IMPLEMENTATION_PLAN.md`
- `ha_ctse_process/variable_roster_event.py`
- `ha_ctse_process/train.py`
- `ha_ctse_process/collectors.py`
- `tests/ha_ctse_process_variable_roster_event_test.py`

Inspect only enough surrounding code to verify that the proposed testbed can
exercise the accepted runtime without changing the F0/F1 intervention. No
scientific result is being promoted and no implementation or experiment is
authorized in this round.

## Requested decision

Return these exact sections:

1. **Final verdict** — exactly one of `ACCEPT_TESTBED_CONTRACT`,
   `MODIFY_TESTBED_CONTRACT`, `REPLACE_TESTBED_SUBSTRATE` or `STOP_AT_F0`, with
   one sentence.
2. **Blind-review adjudication** — decide the common claims and the four live
   disagreements:
   - one generic short action versus `SHORT_A/SHORT_B` with `N_t`-scaled work;
   - shared recurrent direct MAPPO versus primitive-action autoregressive
     direct access;
   - Gemini's ambiguous 500K/PPO10/three-seed budget versus Pro's
     320K/PPO4/single-ledger budget;
   - minimal causal attribution versus an excessive stack of hard gates.
3. **Launch-exact environment contract** — freeze horizon, membership events,
   primitive actions, persistent and reactive dynamics, observations, reset,
   independent RNG ledgers and the sole terminal external reward. Explicitly
   state why the reward is a task objective rather than shaping or intrinsic
   reward.
4. **Evidence execution order** — decide whether one registered contract may
   serialize no-learning carrier checks, the direct arm, then paired F0/F1 by
   causal necessity. Give exact environments, steps, PPO exposure, evaluation
   count and seed/ledger logic without broad seed expansion.
5. **Attribution and outcome branches** — retain only the metrics needed to
   distinguish environment no-access, H2 skill failure, H0 sufficiency, H1
   applied-prefix value and conditional H3 timing. Continuous downstream reads
   may remain descriptive after an upstream failure; avoid turning every read
   into a new prerequisite gate.
6. **F0/F1 causal isolation** — verify that all code, data-generation contracts
   and exposure are shared except the initial-summary versus applied-working-
   summary selector. State the exact natural common-support evidence required
   for H1 and exclude episode-start-only symmetry breaking.
7. **Replacement ledger and stop** — give the finite retain/delete/add set and
   the outcome-dependent portfolio update. Do not create a successor toy or
   module merely because one branch fails.
8. **Authorization** — state whether the accepted design may be moved into
   `docs/research/`. Environment implementation, training and promotion remain
   unauthorized regardless of verdict.

Do not reopen R51--R55, add task-specific intrinsic reward or shaping, introduce
identity/hard roles, add graph/attention/slot/team-latent modules, enable learned
event time, tune an old threshold, expand seeds or authorize parallel routes.
