# GPT-5.6 Pro Convergent Implementation-Plan Disposition

You are the convergent reviewer in the existing HMASD Algorithm Consultation
conversation. Two blind divergent reviews are complete. Adjudicate them against
the repository and issue one final implementation-plan disposition.

## Repository files to inspect

Read all of the following at the pinned commit:

- `docs/external-review/rounds/20260717_variable_n_lifetime_implementation/00_REVIEW_BRIEF.md`
- `docs/external-review/rounds/20260717_variable_n_lifetime_implementation/01_SHARED_SOURCE_MANIFEST.md`
- `docs/external-review/rounds/20260717_variable_n_lifetime_implementation/11_GEMINI_DIVERGENT_RAW.md`
- `docs/external-review/rounds/20260717_variable_n_lifetime_implementation/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260717_variable_n_lifetime_implementation/30_CODEX_SYNTHESIS.md`
- `docs/research/designs/VARIABLE_N_LIFETIME_EVENT_ARCHITECTURE_CONTRACT.md`
- `docs/research/designs/VARIABLE_N_LIFETIME_EVENT_IMPLEMENTATION_PLAN.md`
- `ha_ctse_process/standalone_agent.py`
- `ha_ctse_process/train.py`
- `ha_ctse_process/collectors.py`

Inspect only enough surrounding code to decide the disputed interfaces. No raw
experiment result is being promoted in this round; R49 remains interface-only.

## Requested decision

Return these exact sections:

1. **Final verdict** — exactly one of `ACCEPT_PLAN`, `MODIFY_PLAN`,
   `RETURN_TO_ARCHITECTURE` or `STOP_AT_F0`, with one sentence.
2. **Claim adjudication** — explicitly decide:
   - dedicated trainable event low policy versus frozen wrapper or legacy-class
     modification;
   - the single authoritative lifecycle owner;
   - the two-snapshot temporary-leave transaction;
   - whether exact live resume requires simulator/collector snapshots;
   - exact pre-token critic context;
   - same data-generation contract versus identical realized on-policy data;
   - common-support relative-score evidence versus raw prefix gradient;
   - whether a second tracked acceptance JSON is necessary.
3. **Binding plan corrections** — give the finite exact corrections that must
   be applied before code. Separate correctness requirements from deferred
   ideas.
4. **File/interface boundary** — accept or modify the Codex file list. Do not
   add a module unless it replaces a demonstrated necessity.
5. **Implementation order and stop point** — state the smallest authorized
   sequence and the precise pre-environment/pre-training stop.
6. **Authorization** — state whether applying the document corrections is
   authorized now, and whether production implementation is authorized after
   those corrections. Training is not authorized in this round.

Do not reopen retired R53/R55 lines, add environment-specific intrinsic reward,
design a new experiment, tune a threshold, expand seeds or require a unique
permanent research route. F0 remains the fully matched ordinary-MARL baseline;
F1's only candidate increment is applied-prefix common-support mark coupling.
