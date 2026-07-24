# HMASD External Review Workflow

External GPT-5.6 Pro owns scientific CDC direction. The unified Controller owns
round sequencing, direct BrowserMCP exchange, factual reconciliation, evidence
intake, durable record application, executable realization, local OMP agent
coordination, resource authorization and every Git-visible boundary. The pinned
BrowserMCP server transports one review through the user-connected ChatGPT Pro
tab; there is no persistent review relay.

## Scientific sequence

1. GPT-5.6 Pro performs CDC scientific review of the Git-visible evidence under
   `OPEN_REVIEW_PRINCIPLES.md`, preserving plural conjectures while selecting
   one scheduled research action.
2. The Controller writes factual reconciliation without changing the science,
   applies the exact durable CDC record deltas and shows the Pro user brief.
3. The Controller writes `50_DISPOSITION.md` and updates project control once.
4. If implementation is selected and separately authorized, the Controller
   freezes the executable plan from the Pro scientific direction, estimand,
   evidence and resource boundary, then directly manages its project-local OMP
   agent task tree.

Review and direct evidence intake do not authorize code or training. Pro owns
science; the Controller owns authorized executable realization, workflow and
the resource gate. The target remains a stronger MARL algorithm, while
hierarchy, skills, variable lifetime, ordinary-MARL controls and causal
diagnostics are mechanisms or evidence, not universal prerequisites.

`docs/project/ALGORITHM_PRINCIPLES.md` is the common scientific contract and
`OPEN_REVIEW_PRINCIPLES.md` specializes the external Pro role. Direct intake
guidance lives in the Controller `hmasd-review-round` Skill.

## Direct BrowserMCP interface

The Controller first pushes the result, evidence and reference-code boundary as
one 40-character evidence commit. It then writes and pushes the question and
shared manifest as a stage commit; both review artifacts name the GitHub
repository, current pushed branch, evidence commit, exact evidence files,
reference-code paths and relevant symbols. The stage commit cannot name its own
hash. After canonical-path and remote-boundary validation agree, the Controller
operates the registered ChatGPT Pro conversation directly through
`browsermcp-pro`; Pro reads the named evidence commit through its GitHub
connector:

```text
BROWSER_PRO_REVIEW
reviewer_role=OPEN_DIVERGENT
round=<round-id>
stage_commit=<40-character pushed SHA>
evidence_commit=<40-character pushed evidence SHA>
repository=<GitHub owner/repository>
review_branch=<pushed branch>
round_path=docs/external-review/rounds/<round-id>
source_manifest=01_SHARED_SOURCE_MANIFEST.md
question=20_PRO_OPEN_QUESTION.md
raw=21_PRO_OPEN_RAW.md
conversation=<registered ChatGPT conversation URL>
expected_model_ui=Pro
evidence_transport=github_connector
completion_policy=ARCHIVE_NATURAL_RESPONSE_EXACTLY
```

The long-lived OMP Controller starts the pinned MCP server first. Only then does
the user connect BrowserMCP to the exact authenticated ChatGPT tab, after which
the Controller verifies the registered conversation, visible `Pro` model,
repository and current branch. An ephemeral OMP process cannot carry the
connection because exit destroys its server. A disconnected extension, wrong
page/model/account/repository/branch, login page, CAPTCHA or ambiguous state is
`BROWSERMCP_PRO_BLOCKED`. There is no headless, CDP or Codex-Exchange fallback.

BrowserMCP transports the question and captures the response. It does not upload
source files. Pro reads only pushed evidence through the GitHub connector and
cites the commit and paths used. Connector failure is
`GITHUB_CONNECTOR_EVIDENCE_BLOCKED`; repair the pushed boundary or manifest
instead of pasting uncommitted local code into chat.

The Controller submits the exact question, waits for natural completion, and
requires two stable snapshots before archiving the complete visible response.
Whitespace-only capture is rejected. Archival writes, flushes and exactly
rereads a same-directory temporary file, then atomically moves it without
replacement to the absent final raw path. An existing raw blocks submission;
every naturally completed response remains immutable even when its content has
gaps. The Controller records quality
separately and decides whether the scientific contract needs a focused
follow-up. An externally accepted stage is never resubmitted.

BrowserMCP is local but highly privileged. Its package is pinned, it may operate
only the dedicated connected ChatGPT tab, and the extension is disconnected
after archival. The workflow has no persistent review task, callback, relay or
heartbeat.

## Round files

New review work lives under one round directory:

```text
rounds/YYYYMMDD_topic/
  00_REVIEW_BRIEF.md
  01_SHARED_SOURCE_MANIFEST.md
  20_PRO_OPEN_QUESTION.md
  21_PRO_OPEN_RAW.md
  30_EVIDENCE_RECONCILIATION.md
  50_DISPOSITION.md
```

Raw responses are preserved before downstream use. Controller round behavior
lives in `.omp/skills/hmasd-review-round/SKILL.md`; BrowserMCP transport
behavior lives in
`.omp/skills/hmasd-browser-pro-exchange/SKILL.md`. Direct scientific
evidence intake lives in the Controller round Skill. Algorithm realization and
implementation behavior live in the unified Controller's project-local OMP
task tree. Persistent task IDs in the dispatcher's `session-roles.json` are
limited to the Controller and Experiment Monitor; the external reviewer
conversation URL lives only in `REVIEWER_CONVERSATIONS.json`.
