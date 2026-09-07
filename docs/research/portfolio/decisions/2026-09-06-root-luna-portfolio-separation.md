# Root integration and independent Portfolio — OWNER_DIRECT

The owner approved the following design, then instructed implementation and migration
preparation on 2026-09-06:

> 我们使用luna xhigh作为root模型 然后将monitor和transport的职责并入

> 同意 我们开始做相应改动 准备迁移

The subsequent clarification requires Portfolio directly on main and permits Astra/max:

> 使用Astra max也行 就这样吧 但是应该在main上

## Applied design

- Existing Root task `01a07249-b095-7821-8ce2-e9c32ba85267` becomes Luna/xhigh,
  retaining its native DM children and absorbing experiment observation and exact Pro transport.
- Independent Portfolio task `01a07a3e-29bf-7f52-bc1e-cfa214b8d94a` uses Astra/max
  and the primary `C:/Projects/HMASD` checkout on main. Its scientific file ownership and
  direct-main exception are explicit; other CM/implementer isolation rules remain.
- DM/CM settings, object/direction/Portfolio authority and current scientific cards remain.
  Portfolio recommends candidate order and drives Portfolio Pro intake. Root executes ordinary
  scheduling and engineering integration. No new per-object approval or Pro launch condition.
- The existing thirty-minute `hmasd-experiment-monitor` automation is reused for Root's union
  of pending experiments and Pro requests; no new per-request scheduler is introduced.

The detailed operating procedure is `docs/project/ROOT_OPERATIONS.md`. This owner-directed
workflow edit needs no new Portfolio Pro approval. It changes no direction lifecycle,
scientific comparator, budget, evidence polarity or provider conversation binding.

## Handover facts and outstanding work

Monitor task `01a0791b-0d2d-7b43-85b6-cd5632e0b007` reported no live/unknown handles,
all DISH B05/CBSC B04/RCLE A02 notifications collected, no pending assignments, and its
existing heartbeat PAUSED. Root can adopt future handles without migrating a live experiment.

Transport task `01a06f0e-5eab-7431-8491-e7c2c62705b6` explicitly relinquished all provider
actions, observations and archive mutations after Root acknowledged handover. It reported no
active request heartbeat; all existing saved automations were PAUSED. Archives, registry and
tabs are preserved. It must not receive new dispatches after the endpoint cutover.

Two current handoffs require Root's acceptance reconciliation before any first Send:

| Request | Exact fixed TASK | Existing conversation | Next action |
| --- | --- | --- | --- |
| `2026-09-06-vsp03-shared-service-convergence-01` | `e7a83daab6c25444641865d3d8307a15b2beb78b` | `6a9cbb9d-374c-83e8-b600-23d3a8033a69` | Check original continuation's actual provider state; preserve prior correction |
| `2026-09-06-rcle-post-a02-innovator-01` | `c5c96eecb27f60609d195320467b6dbc29af013d` | `6a9d9a3a-fd40-83e8-9e80-ad720582aaee` | Reconcile exact post-A02 user message; old post-B02 response is historical |

Original HANDOFF/DISPATCH and current VSP03 correction are in each direction's
`pro_packets/20260906_*` directory. Root does not treat a missing registry row as proof of
an unsent request. Transport's final inventory repeated the superseded VSP03 mismatch and
mistyped its own RCLE executor UUID; these assertions are not adoption evidence. The actual
VSP03 raw-action/DOM correction at `VSP03_B02_TRANSPORT_BLOCKER_INTAKE_20260906.md` and the
RCLE committed HANDOFF retain the concrete facts. No migration Send was performed.

The VSPC1 reactive-queue Pro response is already delivered at `67f4d3837`; DM owns
intake/card `503043dda`, CM implementation stops before launch pending acceptance/integration.
DISH intake `f44e08ae9` and CBSC terminal intake `d4dfdb8ac` are pending integration at
this initial handover boundary. These are existing authorized research, not migration tests.

## Verification and actual cutover

Baseline independent review found standalone routing, self-dispatch/receipt and conflicting
per-request heartbeat rules. Targeted tests reproduced self-dispatch and self-receipt failures.
The implementation reuses local execution and local receipt records instead of sending to
Root itself. Scientific checks are not repeated for this workflow migration.

Runtime retargeting, Portfolio checkout handoff, final review/test results and Root model
activation will be recorded below when actually completed; configuration alone is not proof
of those external task settings.

scope: none

### Preparation verification

- Independent reviewer closed all three material findings: unattempted adopted receipts
  convert locally; shared-wake references agree; adopted old handoffs are reconciled under
  their original validation evidence rather than forced through a new-endpoint validator.
- Focused Author/Transport/binding suites: 115 passed in 1.73 s. Three old Author string
  assertions failed identically on unchanged main; they were replaced with the relevant
  actual handoff behavior. No research invocation or provider Send was used as a test.
- Five edited/new TOML files parsed and `git diff --check` passed. The pytest invocation
  emits its existing cache_dir warning when the cache plugin is disabled.
- Portfolio handoff succeeded into the primary checkout. The app returned destination task
  `01a07a3e-29bf-7f52-bc1e-cfa214b8d94a`, superseding initial worktree task
  `01a07a37-7aca-7022-8c13-4324dddd5f9d`; Root restored the clean checkout to main and
  Portfolio confirmed cwd/main/Astra-max. Its handover618bdd0fb is integrated as7b06e26d9.
- Shared automation readback confirms the Root target and 30-minute interval, initially
  PAUSED until source integration. The owner explicitly replaced the short cadence after
  considering the integrated workload. No goal was created and no extra automation added.
- Pending science intakes now integrated/pushed: CBSC7dbc08c0d, DISHc0edc3aae,
  VSPC1 7b4948f8b; concurrent audit rows preserved. VSPC1 implementation delivery
  0652103f6/103d96790/64895a181 and DISH post-B05 preparation199bc19c1 remain for
  normal Root acceptance after the migration. No launch was added by this record.

### Runtime cutover completed

Migration source27f637b10 was integrated and pushed on main as2a5cadd41.
The existing automation `hmasd-experiment-monitor` was updated to `HMASD Root pending work`,
target Root01a07249, ACTIVE with a30-minute interval; saved configuration readback confirmed
all three fields and preserved the full combined long-term prompt. The two current Pro
reconciliation rows keep it active despite no live experiments.

The old Monitor01a0791b and Transport01a06f0e were archived only after explicit clean
handover/relinquishment. Portfolio received the routing-ready release at its actual destination
01a07a3e on main/Astra-max. DISH and VSPC1 native DMs received the new direct routing and
kept their existing scientific/launch bounds. Other pending DMs remain reachable in the same
Root native tree; their exact request routes are in the current tracking table.

Root's task model setting was explicitly submitted through the app as
`model=gpt-5.6-luna`, `thinking=xhigh` for subsequent work; the app accepted the update on
the existing Root task. This one administrative model-setting message is not a Transport
receipt and is not to be repeated. No global default or DM/CM model was changed.
No experiment or provider Send occurred as a migration test. Actual provider acceptance
reconciliation and new research are follow-on operational work, not claimed completed here.
