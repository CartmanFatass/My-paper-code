# HMASD Agent Context

Standing constraints for every subagent working in this repository. Read this
before doing anything else. Your assignment brief carries what is true for this
task; this file carries what is true every time.

## Execution environment

- Run Python with `C:/Users/wu/.conda/envs/SB3/python.exe` directly
  (`torch 2.7.0+cu118`, RTX 4070). The default `python` on PATH is a CPU-only
  build and will fail.
- Never use `conda run -n SB3`. It raises `UnicodeDecodeError` from a non-UTF-8
  `.pth` during `site.py`.
- For scripts outside the repository root, set `PYTHONPATH=C:/project/HMASD`.
- The focused suite requires CUDA and **fails closed** by design. Never add a
  CPU fallback, and never weaken a test so it passes without a GPU.
- Collections run at 16 parallel environments (`FORMAL_NUM_ENVS`). Never write a
  test at width 1 or 2; behavior at those widths is not representative and
  reconstruction drift is width-sensitive.

## Git

You do not commit. Leave your work in the working tree.

No `git add`, `commit`, `push`, `stash`, `reset`, `checkout` of tracked files, or
branch manipulation. The orchestrator verifies your work independently and owns
every commit. Read-only git (`status`, `diff`, `log`, `show`) is fine and
encouraged.

If a markdown file will not stage, that is the repository's bare `*.md` ignore
rule. The remedy is a per-directory negation in `.gitignore`, never `git add -f`.
Report it rather than working around it.

## Active-line development

This is an active research line, not a maintained product. Do not add backward
compatibility adapters, deprecated aliases, legacy branches, or inactive
fallbacks. When a path is superseded, delete it in the same change. Git history
is the archive.

## Working discipline

This is a requirement, not advice. A previous agent produced zero file writes in
an hour of reasoning and had to be killed.

- Make your first code edit within your first few tool calls, even if
  incomplete, then iterate against the tests.
- On a design question your brief does not answer, take the smallest reasonable
  choice, record it, and keep moving. Report the ambiguity at the end.
- A working implementation with a noted simplification beats an unwritten
  perfect one.
- If you conclude the task cannot be done as specified, say so early and
  plainly rather than continuing to search.

## Honest reporting

- Paste real command output. Never state that tests pass without the actual
  output line.
- Report what you could not do, plainly, rather than working around it silently.
- Disclose every simplification, assumption and known limitation. A disclosed
  gap is useful; an undisclosed one corrupts evidence.
- Do not describe a guard as proving something it does not prove. A test that
  passes trivially is worse than no test, because it reads as covered.

## Protected semantics

These carry experiment validity and are reviewed before any commit:
probability factorization, gradients and detach boundaries, RNG stream
ownership and consumption, replay, lifecycle clocks, credit assignment, masks,
and checkpoint meaning.

If your task appears to touch any of them and your brief did not say so, stop
and flag it rather than proceeding.

## Pointers

- `docs/project/IMPLEMENTATION_PLAN.md` — the frozen executable contract.
- `docs/project/CURRENT_WORK.md` — live project state and binding engineering
  constraints.
- `.agents/skills/hmasd-implementer/references/engineering-principles.md` —
  implementation engineering constraints.
- `.agents/skills/hmasd-reviewer/references/review-principles.md` — review
  constraints.
