---
name: hmasd-grok-cm
description: How the Claude Code research hub routes one direction's CM implementation to Grok Build headless (grok-4.6, effort high) to save Claude quota, with the task-file shape, tool and path fences, detached launch, wait, review and pathspec commit. Load when dispatching or taking in a Grok-implemented objective.
---

# Grok Build as CM implementer (Claude Code hub)

Owner decisions 2026-09-05 (22:40 and 22:57 PDT): with two directions advancing in a Claude
session, one direction's code tasks go to Grok Build to save Claude quota, model `grok-4.6` at
effort `high`, and this route is part of the stable workflow. Grok is a third agent runtime under
`AGENTS.md` (Appendix C); it receives a working method, never an authority. The hub still writes
the objective, reviews the diff, runs the focused tests itself, and commits by pathspec.

## What goes to Grok and what does not

- Goes: one meaning-complete `hmasd-cm` objective whose owned paths are direction-local
  (attempt module, runner, tests, CM record), read-only code maps, a second independent review.
- Stays on Opus `hmasd-cm`: changes inside shared core or a shared direction library, anything
  that touches probability, gradients, replay, recurrence, RNG streams of an existing object,
  checkpoint format, bit identity or the native ABI. The other advancing direction keeps Opus.
- Never: `hmasd-experiment-operator` launches, Pro transport, any scientific judgment.
- **Clerk tasks also go to Grok** (owner 2026-09-06 06:48 PDT: "尽量卸载给grok"; model
  `grok-4.5`, owner 06:49 PDT): every mechanical control-plane task whose content the hub has
  already fixed, i.e. what `hmasd-clerk` used to do. Examples: appending ledger rows the hub
  dictates verbatim, `tools/owner_console/item.py add` calls with hub-supplied arguments and
  packet JSON, copying evidence from a remote output root into the direction's evidence folder
  (exact `scp`/`ssh cat` commands supplied), writing `EXPOSURE_AND_COST.json` and
  `ISSUE_SNAPSHOT.json` from hub-supplied numbers and `gh api` readbacks, splicing hub-written
  addenda into `DIRECTION.md` / `PORTFOLIO.md` rows / `EXPERIMENT_TRACKING.md` at a named anchor,
  rendering and binding a Pro packet from a finished `REQUEST.json`, running a named test command.
  The hub writes the scientific words; Grok executes, verifies (re-reads the file, runs the
  check) and reports paths and sha256. Sonnet `hmasd-clerk` remains the fallback when Grok is
  unavailable.

## Clerk mode invocation

Same fences as CM mode but with `-m grok-4.5`, `--effort medium`, `--max-turns 80`, a TASK.md
that lists the exact operations in order with the exact content (prefer "write this file with
these bytes" and "run this command" over descriptions), and the same deny rules on governance
paths. For clerk tasks Grok MAY edit `docs/research/portfolio/audit/*.md`,
`docs/research/portfolio/owner/inbox/**` (only through `item.py`), `PORTFOLIO.md`,
`EXPERIMENT_TRACKING.md`, `DIRECTION.md` and packet folders **when the task names the file and
supplies the text**; it never composes a row, an option or a sentence of science itself. The hub
diffs the result and commits by pathspec with `Implemented-By: grok-build (grok-4.5, clerk)`.

## Procedure

1. **Objective first.** Write the CM objective and card exactly as for Opus (class, protected
   semantics, owned paths, bound, stop rule, deliverables) and commit them to `main`.
2. **Worktree.** `git worktree add -b grok/<direction>-<object>-<date> .claude/worktrees/grok-<slug> <main sha>`.
3. **Task file** at `temp/directions/<direction>/exp/grok/<task-id>/TASK.md`: the body of
   `.claude/agents/hmasd-cm.md` (frontmatter stripped) verbatim; then the objective and card
   paths to read first; the frozen-input local paths and digests; then the Grok-specific rules:
   interpreter `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`, scratch under
   `temp/directions/<direction>/{exp,test}/`, the explicit list of paths it may create or edit,
   **no git commands at all**, no formal launch, one local check-profile run allowed when the
   assignment says so, no web, no subagents, and the numbered final-report structure. Do not pass
   `--agent` with a Claude agent file (its `model:` pin is not a Grok model).
4. **Launch detached** from PowerShell (quote every argument that contains spaces; the CLI
   splits unquoted ones):

   ```
   $env:GROK_MEMORY="0"; $env:PYTHONUTF8="1"
   Start-Process C:\Users\fires\.grok\bin\grok.exe -ArgumentList @('--cwd','"<worktree>"','--prompt-file','"<TASK.md>"','-m','grok-4.6','--effort','high','--output-format','json','--always-approve','--tools','read_file,grep,list_dir,search_replace,run_terminal_cmd,todo_write','--disallowed-tools','Agent','--disable-web-search','--max-turns','250','--deny','"Bash(git *)"','--deny','"Bash(git:*)"','--deny','"Bash(pip *)"','--deny','"Edit(<protected>/**)"','--deny','"Write(<protected>/**)"', ...) -WorkingDirectory <worktree> -RedirectStandardOutput <task dir>\response.json -RedirectStandardError <task dir>\stderr.log -WindowStyle Hidden -PassThru
   ```

   Deny at least: `.claude/**`, `.codex/**`, `.agents/**`, `AGENTS.md`, `CLAUDE.md`,
   `scripts/hmasd_*.py`, every shared library the objective marks read-only. Record the PID and
   argv in `launch.txt`.
5. **Wait** with one background `until` loop on the Windows PID (`ps -W`, fourth column), not by
   polling in the hub. The JSON receipt carries `stopReason`, `num_turns`, `usage.total_tokens`,
   `total_cost_usd` and the final report text; keep it beside the task file.
6. **Review and take in** (hub, never skipped): `git status` in the worktree must show only the
   owned paths; read the diff; run the focused tests yourself; check the CM record's frozen
   commands and projection; then `git add -- <paths>` and commit by pathspec on the worktree
   branch with the runtime trailers, `Implemented-By: grok-build <version> (grok-4.6-build)` and
   `scope:`; push; cherry-pick into `main`. Dispatch `hmasd-reviewer` (Opus) only when the diff
   touches a protected surface or the hub's own review finds a semantic doubt.
7. **Record** the run in the ledger as a `technical` row (`OWNER_DIRECT` routing) and, in the
   CM record or intake, the Grok session id, turn count and token usage.

## Observed on the first run (DISH-RENEWAL-BOUNDARY-A01, 2026-09-05)

23 turns, about 2.4 M tokens by the receipt, 12 minutes, four files in the owned paths, no
tracked file touched, focused tests written and passed, local check profile run in 5.2 s.
Token usage is high because the whole instruction stack (about 9.5 k tokens) plus every read
file re-enters each turn; keep objectives tight and the read list explicit.
