"""Constants shared by the repository-local Codex semantic MVP.

SQLite is a control-plane delivery and obligation ledger. It is not scientific
truth, canonical project memory, or a substitute for AGENTS.md reanchor.
"""

OFF_MODE = "off"
SHADOW_MODE = "shadow"
ACTIVE_MODE = "active"

STATE_DIR_ENV = "HMASD_CODEX_MVP_STATE_DIR"
KILL_SWITCH_ENV = "HMASD_CODEX_MVP_DISABLE"

RETURN_START = "<HMASD_SUBAGENT_RETURN_V1>"
RETURN_END = "</HMASD_SUBAGENT_RETURN_V1>"

MAX_RAW_MESSAGE_BYTES = 1_000_000
MAX_TYPED_JSON_BYTES = 32_768
MAX_WAIT_SECONDS = 1500
WAIT_POLL_SECONDS = 0.5

ALWAYS_ON_SCOPE = "session"
ALWAYS_ON_OBJECTIVE = "always-on managed semantic session"

# Project-convention default only. Activation may override it; doctor checks
# that MCP and hooks share one existing executable rather than this literal.
DEFAULT_PYTHON_EXECUTABLE = r"C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe"

CORE_HOOK_EVENTS = ("SessionStart", "SubagentStart", "SubagentStop", "Stop")
DIAGNOSTIC_HOOK_EVENTS = ("PreToolUse",)
ACTIVE_HOOK_EVENTS = CORE_HOOK_EVENTS
SHADOW_HOOK_EVENTS = CORE_HOOK_EVENTS + DIAGNOSTIC_HOOK_EVENTS
HOOK_ENTRY_MODULE = "tools.codex_semantic_mvp.hook_entry"

