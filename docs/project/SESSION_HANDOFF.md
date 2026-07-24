# HMASD Session Restart Handoff

Updated: 2026-07-23
Status: `RESTART_REQUIRED_BEFORE_BROWSER_PRO_SUBMISSION`

## Resume authority

- Active controller task restarts under `AGENTS.md` and reads
  `docs/project/CURRENT_WORK.md` first.
- Branch: `Claude`; push only `Claude`.
- The user-authorized chain remains active: ten conclusion-bearing CPU
  simple-scene iterations for an individual skill lifetime decoupled from the
  shared global cycle `k`, with no intermediate approval prompts inside the
  frozen grant.
- Each conclusion-bearing result returns to the same registered GPT-5.6 Pro
  conversation before the next scientific action is selected.
- Local implementation uses the native `.omp/agents/` profiles. The registered
  Experiment Monitor remains `ARCHIVED_REBUILD_REQUIRED` and must be rebuilt as
  `gpt-5.3-codex-spark` at `medium` before the first authorized run.

## Git and working-tree boundary

- Pushed review stage commit:
  `7ff4d216e2ce23415c2b3b9ca671c7a76dde7801`.
- Review evidence commit:
  `f073d8e77a006515c7800f04e616d5b62a5e4e26`.
- `origin/Claude` equalled the stage commit immediately before this handoff
  update; the containing handoff commit becomes the new branch tip.
- The working tree was clean before writing this handoff.
- `origin/aggressive` was observed at
  `b125efd205e302666aea78b286d6857f8ecf9286` immediately before this handoff.
  That external advance was not made by this Controller. Do not mutate or merge
  `aggressive`.

## Active Pro round

- Round: `20260723_decoupled_skill_lifetime_direction`.
- Round path:
  `docs/external-review/rounds/20260723_decoupled_skill_lifetime_direction/`.
- Canonical question:
  `docs/external-review/rounds/20260723_decoupled_skill_lifetime_direction/20_PRO_OPEN_QUESTION.md`.
- Question body SHA-256:
  `bb358220131cf87077be68aa29be8d7cbdfc1400b00fcf41c3cd113e13551d43`.
- Deterministic dispatch SHA-256:
  `b509ff783a76f381a4aeef4098a098e5e2253d2b29e0ce5fcee2fa67b84305cb`.
- Dispatch length: 311 UTF-16 code units, no CR/LF.
- Registered conversation:
  `https://chatgpt.com/c/6a61d27c-9278-83e8-ae96-c65c1b52d207`.
- Expected model UI: `Pro`.
- `19_BROWSER_PRO_SUBMISSION.json` is absent.
- `21_PRO_OPEN_RAW.md` is absent.
- No review message was submitted and no submission receipt was created.
  Therefore the durable round state is still `READY_TO_SUBMIT`.

Exact dispatch after deterministic re-rendering:

    HMASD_BP_D1 repo=CartmanFatass/My-paper-code b=Claude stage=7ff4d216e2ce23415c2b3b9ca671c7a76dde7801 q=bb358220131cf87077be68aa29be8d7cbdfc1400b00fcf41c3cd113e13551d43 round=20260723_decoupled_skill_lifetime_direction file=20_PRO_OPEN_QUESTION.md Read via GitHub connector; follow fully; no upload/code/compute.

## BrowserMCP failure facts

1. The first and only `browser_type` action on the original live connection
   timed out after the upstream 30-second WebSocket deadline. A later read-only
   snapshot showed that the exact dispatch had reached the old composer.
2. The Controller did not press Enter, click Send, clear the composer, publish
   a receipt or retry on that indeterminate connection.
3. The user disconnected, moved to a new tab, closed the old tab and fully
   restarted Chrome. The old unsent draft was never submitted.
4. Subsequent fresh-page snapshots showed the registered URL, authenticated Pro
   account, visible `Pro` model and empty composer. Interaction calls nevertheless
   failed before acting with `No tab with given id 507029451`; no new draft or
   user turn was created.
5. After the user requested a task/session restart, the Controller verified the
   stale BrowserMCP process tree as a direct child of the current `omp.exe` and
   terminated only that tree. `taskkill` reported all four stale descendants
   terminated successfully. OMP automatically spawned a replacement
   `@browsermcp/mcp@0.1.3` process, but the current pre-migration session is not a
   valid continuation surface.

Treat these as transport facts only. Do not create a failure disposition, alter
Pro science, paste the full question into ChatGPT, use another browser, or infer
that submission occurred.

## Exact restart procedure

1. Start one fresh long-lived OMP Controller session in this repository. The
   restart is required so native `.omp/skills/` discovery and the pinned MCP
   process both begin cleanly; this old session began before the `.omp`
   migration and retained stale Skill/MCP runtime state.
2. Read `AGENTS.md`, `docs/project/CURRENT_WORK.md`, this file,
   `.omp/skills/hmasd-review-round/SKILL.md`, and
   `.omp/skills/hmasd-browser-pro-exchange/SKILL.md`.
3. Before any browser action, run the canonical round validator. Branch only on
   its real state:
   - `ALREADY_ARCHIVED`: perform no browser or receipt work;
   - `RESUME_SUBMITTED`: verify the complete trusted identity tuple and observe
     without resubmitting;
   - `READY_TO_SUBMIT`: continue the steps below.
4. Verify the pushed boundary using stage
   `7ff4d216e2ce23415c2b3b9ca671c7a76dde7801`, evidence
   `f073d8e77a006515c7800f04e616d5b62a5e4e26`, repository
   `CartmanFatass/My-paper-code`, remote `origin`, branch `Claude`, and the
   canonical question path. The later handoff commit may be the remote tip; the
   stage need only remain reachable with byte-identical question and manifest.
5. Re-render the dispatch and require `DISPATCH_READY`, question hash and
   dispatch hash to match the values above.
6. Only after the fresh OMP MCP server is live, have the user connect exactly
   one fully loaded registered Pro tab. Require correct URL, authenticated
   account, visible model `Pro`, empty composer and no active generation.
7. Follow the Browser Pro Skill state machine exactly: one `browser_type`, save
   a temporary pre-submit snapshot, separate `browser_press_key Enter`, save a
   distinct post-submit snapshot, record the immutable v2 receipt, observe in
   20-second chunks, capture two stable snapshots at least ten seconds apart,
   and archive the natural marked response. Never blind retry an indeterminate
   action.
8. Perform direct factual reconciliation and CDC intake. Only then freeze the
   Controller-owned executable algorithm plan for iteration 1. No algorithm
   implementation or compute has yet been authorized by a Pro decision.

## Remaining chain

- Archive and reconcile the initial Pro scientific direction.
- Freeze the exact iteration-1 executable plan.
- Run the ten evidence-dependent conclusion-bearing iterations serially, using
  local OMP implementation/review/verification and the registered Monitor as
  required.
- Write one Chinese user report per conclusion-bearing iteration.
- Return each result to the same Pro conversation and schedule only one next
  action at a time.
- Close with one independent evidence review, update the control plane, and
  push only `Claude`.
