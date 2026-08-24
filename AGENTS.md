# HMASD native Codex workflow

This repository uses Codex native agents for context separation and parallel
work. Roles are capabilities, not permission gates. The active user-facing
Root has authority to complete every reversible action inside the user's
request and may do CM, EM, Portfolio, implementation, review, transport, or
recovery work directly.

## Roles

- **Root / Portfolio**: user-facing integration, priorities, research choices,
  Git, and final delivery.
- **EM** (`hmasd-independent-research-explorer`): bounded scientific research
  and synthesis.
- **CM** (`hmasd-code-project-manager`): bounded engineering coordination and
  technical judgment.
- **Implementer**: source changes for an assigned scope.
- **Reviewer / Verifier / Scout**: optional independent checks when they add
  useful information.
- **Experiment Operator**: owns one actual train/evaluate/analyze command from
  launch through terminal return.
- **Transport**: performs one explicitly requested external send and archives
  its response.
- **WRM**: repairs one repeated workflow failure with the smallest causal fix.

Delegation is optional. Do not create a manager, reviewer, verifier, receipt,
handoff document, lease, or test merely to satisfy a workflow shape. No role
may bounce an authorized task to another role solely for permission.

## The only hard boundaries

1. Resolve destructive targets exactly and stay inside the user's scope.
2. Never expose secrets. Ask only when credentials or an irreversible external
   action genuinely require the user.
3. External provider sends are at-most-once per operation. If commitment is
   unknown, do not resend without an explicit recovery decision.
4. Dispatch at most one Experiment Operator for one actual result-bearing
   command. The Operator owns that foreground process until terminal.

A resource lease is scheduling metadata for a real long experiment, not a
general authorization token. PRESTART files, timestamps, dashboards, reports,
review results, tests, hashes, role names, and historical session documents do
not grant or deny ordinary work. A missing lease cannot block code, research,
diagnostics, local tests, or other non-effectful work.

## Working style

- Prefer direct progress and the smallest useful decomposition.
- Preserve user changes and avoid unrelated edits.
- Tests and reviews are proportional evidence. Run the smallest check that can
  catch a material defect; report nonessential failures without manufacturing
  another approval layer.
- Scientific claims remain separate from engineering facts, but either may be
  communicated directly in ordinary prose with file pointers.
- Children do not commit or push unless their exact assignment says so. Root
  performs normal Git integration.
- For project Python commands, prefer
  `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`.

Historical CM/EM/lease terminology in research artifacts is provenance only.
It is never executable control state.
