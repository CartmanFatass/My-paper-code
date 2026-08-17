# Native Semantic Activation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable the semantic MCP and ACTIVE hooks through the Codex configuration surface that the CLI actually loads, and prove it with local and native-child smoke tests.

**Architecture:** `.codex/config.toml` is the sole live Codex configuration source.  The activation scripts install/remove one delimited TOML hook block and toggle the existing semantic MCP block atomically; legacy JSON templates may remain as inactive artifacts but never determine live hook delivery.  Tests validate both activation transforms and a real `codex exec` audit event before the live workspace is activated.

**Tech Stack:** PowerShell activation operators, Codex CLI 0.147.0, Python 3.11 SB3 environment, MCP 2.0, pytest.

## Global Constraints

- Invoke every project Python command with `C:\\Users\\wu\\.conda\\envs\\SB3\\python.exe`.
- Runtime/state paths must remain repository-relative (`runtime/codex-semantic-mvp`).
- Use the current native child mechanism with `model=gpt-5.6-luna`, `reasoning_effort=high`, and `fork_turns=1` for smoke testing.
- No refresh-model-catalog script or `model_catalog_json` workaround is permitted.
- ACTIVE is accepted only when an actual native CLI hook writes a new audit record; stdout alone is insufficient.

---

### Task 1: Make TOML hooks the live activation surface

**Files:**
- Modify: `.codex/config.toml`
- Modify: `scripts/codex-semantic-mvp-enable.ps1`
- Modify: `scripts/codex-semantic-mvp-disable.ps1`
- Modify: `tests/codex_semantic_mvp/test_activation_assets.py`

**Interfaces:**
- Consumes: the delimited `# BEGIN/END HMASD CODEX SEMANTIC MVP` MCP block.
- Produces: one delimited semantic hook TOML block containing handlers for `SessionStart`, `SubagentStart`, `SubagentStop`, `Stop`, and `PreToolUse`; ACTIVE enables the MCP and installs that block, disable removes it and restores MCP `enabled = false`.

- [ ] **Step 1: Write failing tests** asserting that ACTIVE activation produces all five inline TOML handlers, preserves the SB3 command and relative state directory, enables exactly one semantic MCP setting, and disable removes the semantic hook block.
- [ ] **Step 2: Run the focused test** with `C:\\Users\\wu\\.conda\\envs\\SB3\\python.exe -m pytest tests\\codex_semantic_mvp\\test_activation_assets.py -q` and confirm it fails because the scripts only replace JSON templates.
- [ ] **Step 3: Implement minimal activation mutation** with one validated hook marker pair, preserving atomic compensation and rejecting duplicate/malformed hook blocks.
- [ ] **Step 4: Run the focused and full MVP suites** and confirm they pass.
- [ ] **Step 5: Commit** with a focused activation-source message.

### Task 2: Verify actual delivery and activate the live workspace

**Files:**
- Modify: `scripts/codex-semantic-mvp-test.ps1`
- Modify: `tests/codex_semantic_mvp/test_activation_assets.py`
- Modify: `docs/research/workflow-runs/2026-08-15_codex-semantic-mvp/ACCEPTANCE_REPORT.md`

**Interfaces:**
- Consumes: Task 1's inline TOML hook block and `runtime/codex-semantic-mvp/audit.jsonl`.
- Produces: a smoke command that asserts new audit event records from native `codex exec`, then an enabled current-workspace configuration and a native Luna-high child smoke result.

- [ ] **Step 1: Write a failing smoke-test contract** that requires a new audit record from a bounded CLI execution; do not accept CLI stdout as proof.
- [ ] **Step 2: Implement the smallest safe smoke command** using the actual live configuration and audit cursor/count, with a bounded timeout and actionable failure output.
- [ ] **Step 3: Run the smoke command in the feature worktree**, confirm an audit event, then run a same-configuration native Luna-high child and verify its `SubagentStart`/`SubagentStop` records.
- [ ] **Step 4: Restore the user-authorized current workspace configuration from the verified feature branch, run activation with a reviewed baseline hash, and repeat the native smoke test.**
- [ ] **Step 5: Update the acceptance report, run the full MVP suite, review the diff, and commit.**
