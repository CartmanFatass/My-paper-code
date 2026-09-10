# FOLR B02 — implementation-ready CM assignment

**Prepared for later Root dispatch; not dispatched or execution-allocated here.** Reuse the
available CM `/root/dm_folr_p68_reentry/cm_public_lifecycle_b01` for this closely related runner
change. The shared checkout is `C:/Projects/HMASD-worktrees/codex-vap-folr`, branch
`codex/vap-folr`; preparation started clean at `4c1813e4a`. You are not alone in the repository:
preserve unrelated edits and serialize overlapping source/index work with DM.

1. **Deliverable and goal.** Make the existing B01 runner support the frozen B02 training and
   evaluation seeds, demonstrate the changed seed route, and return an inspectable technical
   acceptance plus exact prospective execution commands. The scientific question is repeatability
   of the full trained package, fixed in [B02 card §§1–3](FOLR_PUBLIC_LIFECYCLE_B02_SCIENCE_CARD_20260909.md).
   Root's eventual dispatch must state whether any scientific execution is allocated; this
   preparation supplies none.
2. **Owned paths and entry points.** `scripts/run_folr_public_lifecycle_b01.py` is the narrow
   edit: remove its 7801-only argument restriction, add explicit `--evaluation-seed` with the
   original 107801 default, and replace evaluation seed literals in RNG reset, environment
   construction and summary/RNG description with that value. Preserve the original training
   seed default 7801. B02 uses `--seed 7802 --evaluation-seed 107802`. Extend the affected check
   in `tests/experiments/candidates/vap_folr_core/public_lifecycle_b01/test_boundaries.py` as
   needed. Reuse `experiments/candidates/vap_folr_core/public_lifecycle_b01/{environment,model,
   learner,collection,attention,flex_qmix,native_env}.py` at reference `387a40f3f`; these modules
   are read-only unless DM receives a concrete necessary semantic repair. Technical evidence
   belongs in `FOLR_PUBLIC_LIFECYCLE_B02_ENGINEERING_RESULT_20260909.md` and later, only if
   execution is allocated, B02 `RESULT_EVIDENCE`/`RESULT_SUMMARY` files in this directory.
3. **Preserved semantics.** [B02 card §2](FOLR_PUBLIC_LIFECYCLE_B02_SCIENCE_CARD_20260909.md#2-preserved-package-and-fresh-randomness)
   and its fixed B01 §§2–3 reference define the public E/B/C interface, incoming pre-GRU
   state rules, native reward/RNG, replay, optimizer, training/evaluation and terminal rules.
   No old weights/data/optimizer/state are loaded; both arms freshly seed before identical
   construction. Equal seed labels do not promise identical traffic, and this is not a causal
   memory ablation. Keep B01 defaults and immutable evidence; no duplicate runner or shim.
4. **Acceptance and direct references.** Check the small source diff, actual training/final
   seed routing and published seed metadata, including preserved defaults and selected
   7802/107802. Use one focused controlled fixture for the changed boundary; it must not train
   or evaluate a policy as a check. Reuse B01's independent semantic review/focused results
   for untouched code. The selected outcome is [B02 card §3](FOLR_PUBLIC_LIFECYCLE_B02_SCIENCE_CARD_20260909.md#3-endpoint-reading-rule-and-predictions),
   counts/stops §4 and event/resource acceptance §5. Applicable evidence-spec §§4 and
   11.8–11.10 are current main revision `d89be7656d367ca10f75ca1185797081b5d722fa`; the
   [preparation intake §2](FOLR_PUBLIC_LIFECYCLE_B02_PREPARATION_INTAKE_20260909.md#2-knowledge-applied-and-its-limit)
   states the relevant inference limits. No fresh full-history audit, extra Pro condition or
   full unchanged-suite repetition. Report a genuine coverage gap or scope breach to DM.
5. **Budget and stop.** The current assignment is preparation only: zero target calls,
   scientific invocations, retries and Pro Sends. The card prospectively limits one future
   RETAIN/RESET pair to 1,800s per complete arm, 3,600s total, and 60s supporting checks/readbacks;
   no pilot, extra evaluation or successor. Do not interpret these design limits as execution
   authority. On a later allocation, use remote-first exact committed/pushed source, new B02
   roots such as `temp/directions/vap_folr_core/exp/public_lifecycle_b02_seed7802_<arm>`, fresh
   destination admission before each arm, detached `agent-task` and sole CM observation.
   Bind the actual new SHA and command then; no old B01 handle/worktree survives to resume.
