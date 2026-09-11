"""Candidate-only instructions and level-limited reference material."""
import json
from pathlib import Path
import re

FIVE_ITEMS = """1. Deliverable and goal.
2. Owned paths and code entry points.
3. Scientific and compatibility semantics to preserve, with precise task references.
4. Observable acceptance and relevant checks.
5. Budget, execution limits and stop condition.
"""
LEVELS = {
    "L0": "Use the current five-item handoff; leave ordinary implementation choices to the implementer.",
    "L1": "Use the five-item handoff plus task-specific interfaces, shapes, types, mutation/error behavior and existing code/test conventions.",
    "L2": "Use L1 engineering detail plus the actual data/state flow, operation order, important branches and concise pseudocode.",
    "L3": "Use L2 detail plus a small applicable code example or local function skeleton and input/output example. Do not implement the whole task for the child.",
}
COMMON = """Preserve the task's frozen scientific meaning and owned paths. Read the current
assignment and affected code first; expand only to resolve a concrete dependency or fact.
Complete authorized, reversible engineering and focused checks without another approval step.
Preserve other writers' changes. Stage and commit explicit paths; never use git add -A,
stash, reset, force-push, history rewrites or a production remote. Push commits to the supplied
local bare origin immediately. No research training, external services or dependency upgrades.
Use supplied task facts for reward, masks, time, state, RNG and numerical semantics; do not
guess them from an algorithm name. A test pass establishes the tested behavior, not science.
Ordinary repairs continue to acceptance or a concrete blocker. Report unresolved scope or
meaning conflicts and continue independent work. All scratch belongs in this workspace's
temp/<invocation>/ and its creator removes it after retaining necessary diagnostics.
Never read host files, task-bank code, reference fixes, hidden checks, other runs or production
HMASD files. Supplied benchmark.py commands are the sole exception for executing host code;
do not inspect that host implementation. All agents must obey this candidate boundary.
"""
CM = """You are the Code Manager for a bounded sequence of engineering tasks. Own coherence,
technical acceptance, review disposition and Git facts. Check actual artifacts and affected
behavior rather than accepting a child's completion assertion. Reuse an implementer for
same-module corrections; give concise, precise gaps. Do not duplicate a child's assigned work.
Use an independent cm_reviewer for each semantic change, with the task's facts, protected
invariants and fixed diff. Reviewers do not receive implementation discussion before their
first review. Disposition material findings; independent review is evidence, not an approval
gate. Do not simulate any child or reviewer. Continue in the SAME CM session until the
task sequence has ended, including status questions, late receipts and Git chores.
"""
IMPLEMENTER = """You are the implementation worker for the assigning CM's bounded handoff.
You are not alone in this workspace; preserve unrelated edits. Implement and check the owned
surface directly, without spawning more agents. Resolve ordinary in-scope choices yourself;
return concrete missing scientific facts to the CM. Report changes, checks, remaining issues
and actual artifacts. The CM retains acceptance and shared-index ownership unless delegated.
Do not operate benchmark checkpoints; those belong to the CM.
"""
REVIEWER = """You are the independent engineering reviewer. Read the task contract, fixed diff,
affected behavior and callers. Check material correctness and regressions yourself; use
focused existing checks when useful. Tie findings to a concrete fact, reachable failure and
impact, with a path/line or reproducer. Do not impose speculative style preferences or extra
scientific requirements. Remain read-only except invocation-owned test scratch. Return your
findings to the CM, who decides their disposition. Do not spawn children or operate checkpoints.
"""


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def toml_string(value):
    return json.dumps(str(value), ensure_ascii=False)


def install(workspace, state, source):
    """All files here are public to this run; never copy whole host/shared trees."""
    mode, level, delivery = state["mode"], state["level"], state["delivery"]
    policy = "CM implements directly; do not create an implementer. Independent review remains required."
    if mode == "delegation":
        policy = ("CM delegates the complete owned coding task to cm_implementer. Write the exact "
                  "handoff to work/handoffs/<task-id>.md before spawning. " + LEVELS[level])
        policy += (" Use only the supplied versioned reference library, select applicable parts and "
                   "write this task's delta. Library assumptions never override the task facts."
                   if delivery == "reuse" else
                   " Write the handoff fresh from the task and code; no reusable pattern library is supplied.")
        policy += " Record any CM coding takeover, its reason and changed paths in work/takeovers.md."
    task_access = ("All six task contracts and source packages are available immediately; read TASKS.md. "
                   "You may inspect all listed tasks now; complete their checkpoints in the listed order."
                   if state.get("all_tasks_upfront") else
                   "The two tasks are frozen before execution. Task identities arrive sequentially.")
    protocol = f"""# CM benchmark run {state['id']}

{COMMON}
{CM}
{policy}

The currently opened top-level session IS the CM. Never create another CM agent or launch
another CM CLI from this session. Only the implementer (delegation mode) and reviewer are
candidate child agents. The host starts a separate post-run evaluator after you finish.

This is an isolated adaptation of the current HMASD workflow, not production research.
{task_access} Essential facts,
source, public acceptance and final checks are identical across treatment groups.
Five-item handoff structure:
{FIVE_ITEMS}
Use real independent reviewer and (delegation only) implementer agents. The supplied
cm_reviewer/cm_implementer roles are convenient defaults; user-selected model/effort combinations
and equivalent child names are allowed. Record actual child IDs and assigned roles in the
handoff/review records. Spawn with
no inherited conversation (`fork_turns="none"`, or the runtime's fresh-context equivalent).
If the runtime cannot provide real independent agents, record the deviation and stop the
dependent task honestly; never replace the agent with a written imitation. Use the owner's
chosen models/efforts, or the supplied defaults when none were specified. Child tools follow the same scope.

Run `python -B benchmark.py next` now. For EACH task, visit these boundaries in order:

1. `located`: after inspecting the assignment and locating the affected code, before editing.
2. `checked`: after the first implementation and public check attempt, BEFORE independent review.
3. `reviewed`: after the actual reviewer returns; retain its verbatim report plus CM disposition.
4. `accepted`: after necessary fixes, checks, explicit commits and local push, or a recorded failure.

At each boundary, write/update a concise work/<task-id>.md and invoke
`python -B benchmark.py checkpoint --boundary <name> --note work/<task-id>.md`.
The checkpoint saves the actual work and AUTOMATICALLY delivers the next fixed event; process
it and continue. `next` reprints the current event without advancing. Failed checks do not skip
boundaries: record failed/blocked work honestly. Never claim acceptance just to advance.
Copy real review reports to work/reviews/<task-id>.md; record actual native child IDs there.
Keep optional notes yourself. No host-generated memory summary or fresh CM between tasks.

Background receipt files are historical synthetic fixtures, never evidence for this candidate
patch. Maintain work/background.json keyed by run_id, each with status complete/incomplete/failed
and missing (list of filenames). A complete successful background run needs a matching terminal
receipt and BOTH metrics.json and returns.json; trust actual delivered files, not a completion
claim alone. Preserve earlier evidence. A status question requests an answer in work/status.md
and continuation. Preserve notes/neighbor.md as an unrelated, uncommitted change.
Before the last accepted checkpoint write work/final.md with delivered work, checks, unresolved
issues and background collection state. Do not grade yourself or read hidden materials.
If this run was started with start.py/begin in an existing CM session, the last checkpoint
starts automatic post-run collection. End the CM turn after your delivery; do not wait for
your own turn-completion event or call the grader/cost tool while still executing the task.

Task checks use this interpreter: {state['python']}
Per-task engineering time reference: {state['task_minutes']} minutes, including children/review.
This is a soft recorded budget; on exhaustion record remaining work and visit remaining
boundaries without pretending success. No extra task, training run or matrix is authorized.
"""
    write(workspace / "AGENTS.md", protocol)
    write(workspace / "materials/POLICY.md", policy + "\n\n" + FIVE_ITEMS)
    if mode == "delegation" and delivery == "reuse":
        write(workspace / "materials/patterns/HANDOFF.md", FIVE_ITEMS)
        if level != "L0":
            ceiling = int(level[1])
            for path in sorted((source / "patterns").glob("[0-9]*.md")):
                body = path.read_text(encoding="utf-8")
                match = re.search(rf"(?m)^## L{ceiling + 1} 增量", body)
                if match:
                    body = body[:match.start()]
                write(workspace / "materials/patterns" / path.name, body)
            if level == "L3":
                for path in (source / "patterns/examples").glob("*.py"):
                    write(workspace / "materials/patterns/examples" / path.name,
                          path.read_text(encoding="utf-8"))
    roles = {"cm_reviewer": (state["reviewer"], REVIEWER)}
    if mode == "delegation":
        roles["cm_implementer"] = (state["implementer"], IMPLEMENTER)
    for name, (config, instructions) in roles.items():
        text = (f'name = "{name}"\ndescription = "CM benchmark {name}"\n'
                f'model = {toml_string(config[0])}\nmodel_reasoning_effort = {toml_string(config[1])}\n'
                f'developer_instructions = {toml_string(COMMON + instructions)}\n')
        write(workspace / f".codex/agents/{name}.toml", text)
    config = (f'model = {toml_string(state["cm"][0])}\n'
              f'model_reasoning_effort = {toml_string(state["cm"][1])}\n'
              'approval_policy = "never"\nsandbox_mode = "workspace-write"\n'
              '[agents]\nenabled = true\nmax_concurrent_threads_per_session = 3\n')
    write(workspace / ".codex/config.toml", config)
