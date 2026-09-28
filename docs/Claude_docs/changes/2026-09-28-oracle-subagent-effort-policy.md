# 2026-09-28 — Oracle subagent at max effort; daily delegation keeps high

Owner instruction (2026-09-27 PDT / 2026-09-28 UTC, Claude WSL session): most work does not need
Fable at max effort. Daily delegation keeps the current default `high` for cost and time; an
**Oracle** subagent runs Fable 5.1 at **max** effort and is used only for research decisions and
planning.

## Change

- New `.claude/agents/hmasd-oracle.md`: `model: fable`, `effort: max`, read-only tools
  (Read, Grep, Glob, Bash, WebSearch, WebFetch). Both values are accepted by the installed CLI
  (2.1.283: model aliases `sonnet/opus/haiku/fable`, effort `low/medium/high/xhigh/max`).
  The body is directly maintained as a Claude-only role: the session's own DM reasoning at higher
  effort for question/approach selection, experiment design, material interpretation or route
  correction. It returns a decision memo; the session accepts, reviews and publishes. It edits,
  launches, sends and spawns nothing. It is not the Scientific Reviewer: an Oracle plan still goes
  to `hmasd-research-critic` in a separate context under constitution section 5, and
  MATERIAL_DISSENT stays with that reviewer. No section-2 role or authority is added.
- `tools/publish_claude_control.py`: `DIRECT_AGENTS = {'hmasd-oracle'}` — `--check` neither
  regenerates nor reports a directly maintained Claude-only agent; every other `hmasd-*.md`
  stray is still reported. Test `test_direct_agent_is_not_reported_but_strays_still_are`.
- `CLAUDE.md`: one sentence naming the Oracle and the effort policy (separate commit).
- Other agents' `model`/`effort` unchanged (see 2026-09-26-subagent-effort-levels.md); AGENTS.md,
  the constitution, Codex role files and generated bodies untouched.

Effort is configured through the documented subagent frontmatter field; whether the runtime honours
it is not observable from inside a session (CLAUDE.md rule), so report it as configured, not verified.

Owner authority: 2026-09-15 lifting of the control-plane restriction (any file, traceable in Git,
documented here). No science, run, record type or message channel changed.

## Addendum 2026-09-28 (later): Oracle body names the owner-adopted comparison/decision-exposure method

Root published the owner-requested method revision at 2a9073410 (`hmasd-scientific-tools`
"Design the comparison and decision exposure"; loop-dispatch; DM/critic bodies; generated `.claude`
consumers, publisher drift 0) and sent `docs/Claude_docs/inbox/20260928_method_workflow_lessons_ROOT.md`
with the owner's authorisation for Claude to adjust its own workflow. Change (commit a4dd9c9a0):
`.claude/agents/hmasd-oracle.md` gains one sentence directing the Oracle to state whether a question
buys package reuse or component attribution, to pick the comparator for that decision, to trace only
consequential premises to the actual host and policy interface, to plan requested/executed readings
that separate nonactivation, sparse exposure and an active adverse intervention, and to say what each
outcome would change. Frontmatter (model fable, effort max, tools) unchanged. Directly maintained
Claude-only role; `tools/publish_claude_control.py --check` re-run from this checkout: `drift: 0`.
No science, run, record type, role or message channel changed; the running `b05_canonical_frame_a01`
operation is untouched.

## Addendum (2026-09-28, later): owner-approved attention refinement mirrored for the Claude DM

Owner question: the Codex-side workflow tuning reduces meaningless experiments; should Claude do the
same? Root's second refinement (858e8cff5) changed only `hmasd-loop-dispatch` and
`hmasd-portfolio-task` (Root/portfolio skills), so its two points — attention on consequential
questions rather than diagnosis/baseline attribution by default, and decision-based round reviews
(which belief/reference/investment changed, uninformative outcomes and their cost) — were not in
the bodies the Claude DM reads (`hmasd-research-hub`, `hmasd-scientific-tools`, the Oracle).
Change: one paragraph in `CLAUDE.md` (Claude runtime section) applying the refinement to the Claude
DM, and one sentence in `.claude/agents/hmasd-oracle.md` for question-selection decisions.
Frontmatter unchanged; `tools/publish_claude_control.py --check` still `drift: 0` (generated bodies
untouched). No new record type, score, form, role or channel; accepted operations untouched.

## Addendum (2026-09-28, later): reference-library pointers

Owner request: put the two independent local libraries (Inst-sci `papers/MyLib`, 190 PDFs/JSON with
`metadata/integrity.json` authoritative; My-lib corpus at `/mnt/c/Projects/My-lib`, 1,519 arXiv PDFs
under `.local-formal-capture/corpus/papers/`) into `AGENTS.md` so Claude, Root and the DM/Oracle roles
can find references, and build a simple LLM hint index over the My-lib corpus with `agy`/`omp` headless
Gemini 3.8 Flash (medium). Change: new `AGENTS.md` section "Reference libraries" (also lists
`docs/new-libs/`), one sentence in `.claude/agents/hmasd-oracle.md` pointing at it; builder and search
scripts under `tools/reference_libraries/` with tests (Implementer task from
`temp/directions/energy_relay_benchmark/L0_mylib_llm_index.md`); index outputs under the git-ignored
`/mnt/c/Projects/My-lib/.local-llm-index/`. Publisher drift unaffected (generated bodies untouched).
