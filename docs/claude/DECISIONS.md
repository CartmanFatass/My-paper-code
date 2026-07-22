# Claude Decisions Log

Durable decisions and the reasoning behind them, for the Claude Code controller
on branch `Claude`. Append; do not rewrite history and do not restate Git.

Each entry: what was decided, why, and what would reverse it.

---

## D1 — The comparison measures outcomes, not process (2026-07-22)

Claude Code on `Claude` versus Codex Desktop on `aggressive`, same research
line. This branch is **not** kept mergeable into `aggressive`.

**Why:** a 1:1 mirror of the Codex role topology would mostly measure Claude's
ability to emulate Codex ceremony. The Codex contract is bound to Codex
primitives — persistent task UUIDs, a dispatch registry, `codex_app__send_message_to_thread`
delivery — none of which exist in Claude Code. Porting the mechanism would test
the wrong thing.

**Reverses if:** the user wants a controlled process comparison instead.

---

## D2 — Scientific authority sits with external GPT-5.6 Pro (2026-07-22)

Via the GitHub connector. The controller owns implementation, verification and
Git; the user owns resources and scope; Pro decides what evidence means and what
comes next.

**Why:** the person who wrote the code should not rule on what its results mean.
This session produced a live example within an hour: a measurement
(`dense_batch_invariance == 0.0`, D5) that was *convenient for the path the
controller had just recommended*. That is exactly the condition under which an
independent judgment is load-bearing.

---

## D3 — Two operating modes (2026-07-22)

With a standing authorization, proceed autonomously inside it without re-asking.
Without one, work to the boundary, then stop and put a decision to the user with
a recommendation.

Unconditional stops in both modes: protected semantics, compute launch, commit
or push, and anything that changes what a result is allowed to mean.

---

## D4 — Subagent roster reduced to three (2026-07-22)

Kept `hmasd-scout` and `hmasd-reviewer`; rewrote `hmasd-implementer`; deleted
`hmasd-monitor`.

**Why the monitor went:** it existed to watch long remote runs. Local work is a
background task plus a log tail; a dedicated agent adds context cost and no
signal.

**Why the implementer was rewritten — two silent defects in the inherited
definition, both found by checking rather than reading:**

1. It instructed the agent to read
   `.agents/skills/hmasd-implementer/references/engineering-principles.md`,
   which **does not exist**. The agent's stated engineering constraints were
   unreachable.
2. Its `PreToolUse` hook — the sole mechanism preventing a subagent from running
   `git commit` — piped stdin through **`jq`, which is not installed on this
   host**. With `jq` absent the extracted command was empty, the `grep` never
   matched, and `exit 2` never fired. **The guard failed open.** It has been
   reimplemented without `jq` and now fails closed.

**Standing lesson:** a safety mechanism that has never been observed to fire is
an assumption, not a guard.

---

## D5 — CPU is the registered formal backend on this branch (2026-07-22)

`FORMAL_EXECUTION_BACKEND` changed `"cuda"` → `"cpu"`. User instruction, and the
code already supports it: `REGISTERED_EXECUTION_BACKENDS = ("cuda", "cpu")` with
CPU admitted explicitly as "not a fallback", and `PINNED_COLLECTOR_DIGESTS`
already carrying a verified CPU entry.

**The standing objection, P1b, does not reproduce on this host.**
`PROBLEM_CACHE.md` records that the fork engine cannot run on CPU, citing a
measured batch-invariance error of `5.72e-06`. On this machine the same probe
measures exactly **`0.0`** — invariance holds. The recorded figure was a property
of the *previous* machine's CPU kernels, encoded in a test as a universal
property of "CPU".

**Not yet settled:** P1b itself warns the synthetic probe is necessary but not
sufficient — "only the real fork is decisive". The real-fork test on this host is
the open falsifier. Until it runs, D5 rests on a partial result.

**Independent of all this:** P1 blocks the `A_KEEP`/`A_RENEW` gates on *either*
backend, because the fork engine is deterministic-only while Replacement C is
defined on held-out stochastic. So the CPU move costs no evidence that CUDA
currently delivers.

**Reverses if:** the real fork proves non-exact here, and the fork evidence
becomes reachable some other way.

---

## D6 — Test repairs measure the host; they do not re-pin it (2026-07-22)

The three CPU failures encode the old machine's measurements as universal facts.
They are repaired by deriving from a measurement of the active host, keeping the
fail-closed property, and retaining the old machine's numbers as recorded
history rather than deleting them.

**Why not re-pin outright:** the old measurements are real evidence about real
hardware. A test that asserts "CPU behaves this way" was always the bug; the fix
is to stop asserting a universal, not to swap in a new one.

---

## D7 — Codex plugin: review by default, disclosed for implementation (2026-07-22)

The plugin is authorized for use in the workflow. Default use is independent
review and cross-validation. When it is used for *implementation*, that is
disclosed in the turn.

**Why the disclosure:** "Claude delegates the coding to Codex" would hollow out
an outcome comparison against Codex Desktop. The user's grant is broader than
this; the narrowing is self-imposed to keep the result interpretable, and can be
lifted.

---

## D8 — Compute efficiency is out of scope unless asked (2026-07-22)

GPU/CPU availability, throughput and optimization are not part of the research
line and are not tracked or reported unprompted.

**Why it is written down:** the surrounding documents are dense with throughput
measurements, and the pull toward optimizing them is strong precisely because
they are easy to measure. They are not the mission.

---

## D9 — Falsifiable next action before any long investigation (2026-07-22)

State what is being checked and what result would prove the direction wrong,
before starting.

**Why:** `AGENT_CONTEXT.md` records that an agent on this project once produced
zero file writes in an hour of reasoning and had to be killed. A stated falsifier
lets an unproductive direction be stopped by the user instead of run to
exhaustion.

---

## D10 — Subagents run the same models Codex uses (2026-07-22)

User directive, for comparison validity: the worker layer is held constant
across both sides so the comparison isolates the **controller** rather than
confounding controller and workers.

Codex's registered assignments, read from `.codex/agents/*.toml`:

| Role | Model | Effort | Sandbox |
|---|---|---|---|
| code-scout | `gpt-5.6-luna` | medium | read-only |
| implementer | `gpt-5.6-sol` | high | workspace-write |
| reviewer | `gpt-5.6-sol` | **xhigh** | read-only |
| verifier | `gpt-5.6-luna` | high | workspace-write |

**Verified reachable, not assumed.** `.codex/config.toml` warns that Luna "is
account-visible but currently omitted from the Sol/v2 child-agent surface", so
availability was probed directly through the plugin runtime:

```
--model gpt-5.6-luna --effort medium  -> PARITY_PROBE_OK
--model gpt-5.6-sol  --effort xhigh   -> PARITY_PROBE_SOL
```

Prerequisites established this session: `npm install -g @openai/codex`
(codex-cli 0.145.0); ChatGPT auth was already active. The plugin requires a
globally installed binary — it does not fall back to `npx`.

**Consequence that changes the architecture:** these workers are **Codex CLI
tasks, not Claude Task subagents**. The `.claude/agents/*.md` definitions and
their `PreToolUse` hooks — including the Git guard repaired in D4 — **do not
apply** to them. Boundaries must instead be enforced the way Codex enforces
them: read-only roles get no `--write`; only the implementer is write-capable.

**Cost accepted:** Claude Code's native subagent layer is no longer exercised
for these roles. That is the price of holding workers constant, and it is the
intended trade.

**Reverses if:** the comparison shifts to whole-system rather than controller.

---

## D11 — Three Codex-backed roles; verification stays in the controller (2026-07-22)

**All** delegated work runs on Codex models. Nothing delegated runs on a Claude
model, so the worker layer is exactly Codex's. The `.claude/agents/*.md`
definitions were deleted rather than kept as a fallback: two parallel worker
layers would make the comparison unreadable later, and retaining hook-bearing
definitions that do not govern the actual workers would read as protection that
is not there.

Their content was migrated to `docs/claude/roles/`, not discarded — it carries
hard-won specifics worth keeping, notably the `requires_grad is False` inside
`torch.no_grad()` example of a vacuously passing test, and the observation that
silent divergence between a copy and its source has been this codebase's most
dangerous pattern.

**No verifier**, deliberately, against Codex's four-profile roster. Codex
delegates verification to `hmasd-verifier`; this controller keeps it in its own
loop. Controller design is precisely what the comparison measures, so it is
allowed — and expected — to differ here. The rule that a worker's claim of
passing tests is not evidence (D-contract, `CLAUDE.md`) only means something if
the controller re-runs the suite itself.

**Enforcement note.** Codex enforces read-only through `sandbox_mode`; here the
boundary is *omitting `--write`*, with nothing behind it. Same for commits: the
assignment says do not commit, and the controller checks `git status` after.
This is weaker than the hook-based guard it replaces, and is recorded as a known
gap rather than an assumed protection.

---

## D12 — Two negative results about the Codex CLI child-agent surface (2026-07-22)

Both were tested, not assumed. Recorded because rediscovering them costs real
Codex spend.

**The named-profile registry is Codex Desktop only.** An isolated `CODEX_HOME`
(`C:\Users\fires\.codex-claude`) was built registering all three
`.codex/agents/*.toml` profiles with `multi_agent_v2 = true`. `codex doctor`
confirms it is live: `config.toml parse ok`, `overrides: multi_agent_v2`.
`collaboration.spawn_agent` still exposes **no `agent_type` parameter**. Its
schema is `task_name`, `message`, `model?`, `reasoning_effort?`, `fork_turns?`
— nothing more. So `developer_instructions`, `sandbox_mode` and
`approval_policy` from those profiles are unreachable from the CLI path, and
role identity can only travel in `message` text.

**The model-catalog workaround does not expand the child surface.** With
`model_catalog_json` pointed at the workaround catalog, spawning Luna fails:

```
Unknown model `gpt-5.6-luna` for spawn_agent.
Available models: gpt-5.6-sol, gpt-5.6-terra
```

The catalog *was* loaded — proven by pointing the key at a nonexistent path,
which makes config load fail outright (`✗ config could not be loaded`). So the
key is honored and the real catalog parsed. The allowlist is therefore enforced
server-side. This is consistent with the catalog's own provenance note: Luna is
"omitted from the Sol/v2 child-agent surface" and the workaround "changes only
the routing-version field" — enough for Desktop, not for the CLI spawn tool.

**Consequence for the roster:** implementer and reviewer are both `gpt-5.6-sol`
in Codex's registry, so PM-spawning them costs no model fidelity. Scout is
`gpt-5.6-luna`, which works as a top-level task but cannot be a child — so scout
stays controller-dispatched. That is a structural deviation from Codex, forced
by the platform rather than chosen.

**Isolated runtime retained** for controller separation: session state, memories
and history stay out of Codex Desktop's `~/.codex`. It requires `CODEX_HOME` to
be set on *every* plugin invocation — omitting it silently falls back to the
other controller's home, which is an operational footgun worth guarding.

---

## D13 — A Project Manager owns the code side; the controller keeps the reviewer (2026-07-22)

User directive: add a PM matching Codex's `project_manager`, at `gpt-5.6-sol`
xhigh, able to spawn workers. Verified buildable — a plugin-launched Sol task
spawned a child, waited for it, and returned its output (`CHILD_SAID: NESTED_OK`).

Final roster:

| Role | Model | Effort | Dispatched by | Write |
|---|---|---|---|---|
| Project Manager | `gpt-5.6-sol` | xhigh | controller | yes |
| Implementer | `gpt-5.6-sol` | high | PM | inherits PM |
| Reviewer | `gpt-5.6-sol` | xhigh | controller | no |
| Scout | `gpt-5.6-luna` | medium | controller | no |

Implementer and reviewer are both `sol` in Codex's own registry, so routing the
implementer under the PM costs no model fidelity.

**The reviewer stays with the controller**, against Codex's org chart. Two
reasons, both about the audit being worth something. A PM-spawned reviewer would
inherit the PM's write capability, so its read-only status would be prompt-text
with nothing behind it. And it would be auditing its own parent, seeing only
what the parent chose to pass down — with `fork_turns: all` it would inherit the
parent's rationalisations wholesale. The reviewer is the main thing standing
between a wrong change and a commit; independence is worth one deviation from
the org chart.

**Scout stays with the controller** because the platform forces it (D12), not by
choice.

**Accepted weakness:** the PM's own no-commit rule is text, not enforcement.
The controller checks `git status` after every write-capable run.

---

## D14 — Threads are reused; the reviewer is the deliberate exception (2026-07-22)

User directive: keep context, do not open a new session per dispatch. Verified —
a token stored in one turn was recalled after `--resume-last`
(`Resuming thread 019f8a8a-…` → `ZEBRA-7741`).

| Role | Policy |
|---|---|
| Project Manager | One persistent thread per work package; id recorded in `SESSION_STATE.md` |
| Implementer | Inside the PM's thread tree |
| **Reviewer** | **Always fresh — never resumed** |
| Scout | Fresh |

**The reviewer exception is not an oversight.** Its value comes entirely from
uncontaminated context; a resumed reviewer accumulates exactly the reasoning it
exists to audit, and would drift toward agreeing with what it already saw. The
same logic that kept the reviewer out of the PM's hands (D13) keeps it out of a
persistent thread.

**Known hazard.** `--resume-last` resolves the most recent thread *in this
repository*, not per role — there is no resume-by-id flag on the plugin's `task`
command. Any fresh dispatch becomes "latest", so a scout run after the PM
silently hijacks the next resume. Mitigation: every task prints
`Resuming thread <id>`; verify against the recorded PM id and stop on mismatch.
`codex exec resume <id>` targets a thread explicitly but bypasses the plugin's
subagent-drain handling, so it is a fallback for child-free turns only.

---

## C1 — Correction to D11 and D13: read-only *is* enforced (2026-07-22)

D11 and D13 recorded that omitting `--write` was a prompt-level boundary with
"nothing behind it", and the claim was repeated to the user three times. **It was
wrong.** The plugin passes

```js
sandbox: request.write ? "workspace-write" : "read-only"
```

to the app-server turn, so a reviewer or scout dispatched without `--write` runs
in a real sandbox. The claim was made from the absence of an `agent_type`
parameter without reading the dispatch path that was already in hand.

What survives the correction: the PM runs `workspace-write`; its spawned children
inherit that with no per-child restriction; and no sandbox prevents a commit. The
`git status` check after every write-capable run remains load-bearing.

**Standing lesson, the inverse of D4's.** D4 warned that an unobserved guard is
an assumption. This is the mirror: an *assumed absence* of a guard is equally
unverified. Both directions need evidence before they go into a contract.
