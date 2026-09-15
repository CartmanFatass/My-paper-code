# RCLE administrative closeout escalation: investigation and repair

The owner asked why RCLE still requested Root/owner approval after full DM lifecycle delegation.
Root examined the actual B10 card, intake, task messages, main controls and all four registered
DM session/authoring checkout entrypoints. This investigates workflow, not RCLE scientific value.

## Observed causal sequence

- B10's card explicitly says locally selected OWNER_DELEGATED and "this card's local ceilings":
  native/support/complete 300/600/900 seconds. No owner direction-wide cumulative limit was
  identified in the escalation. The completed experiment and DM PARK are separate facts.
- The DM's actual send_message_to_thread call to Root requested owner selection of an additional
  60 seconds for the already accepted scientific review. Its next message told Clerk that this
  owner choice had been requested. The message tool delivered the DM-authored request; there is
  no evidence that the tool generated an approval requirement or automatically routed a receipt.
- The DM later confirmed the direct reasoning: it had read main `4dfdb5f8f` section 2 and knew
  the full-lifecycle delegation, but misclassified the card's local 300/600/900-second ceilings,
  the 46.7-second transport repair and 10-second observation as an owner/shared-resource
  exception. The “cannot reset the original cap, therefore ask for 60 seconds” step was the
  DM's own finite-grant habit, not a rule in the card or the repaired controls. The initial
  b984 session AGENTS text was stale background that increased propagation risk, but the DM
  confirms current owner messages and main controls superseded it; stale text is not the sole
  direct cause. Clerk did not instruct the DM to seek approval; the DM independently sent Root
  the request and copied Clerk.
- The intake records support approximately 595.669065 seconds plus UNKNOWN tails and now call
  the prior approval request an over-escalation of its own selected card ceiling. DM has selected
  finite administrative continuation under existing delegation; no experiment or Send is added.

## Control defects

Main 4dfdb5f8f introduced full lifecycle ownership, but AGENTS section 2 left "new resource
commitments" undefined. The DM role's authorization-continuity paragraph still sent exhausted
invocation budgets to the assigning parent for reconciliation. These statements allowed a local
support planning limit to be treated as an owner-only funding boundary. The actual request follows
that interpretation; the DM's precise self-report is a separate evidence source when returned.

All four registered session checkouts (4c59, d4a4, b984, 8f07) and their designated authoring
checkouts still contained AGENTS "Decision ladder" and "Portfolio Pro finality" at this audit.
RCLE session AGENTS last changed at 5460020a9; authoring at 574098921. Main alone held 4dfdb5f8f.
Thus Root's prior acceptance verified publication/messages, not effective instruction propagation.
Stale files are a demonstrated conflicting input; this alone does not prove which sentence the
DM used. An independent task also does not acquire new role instructions merely from a TOML edit.

## Repair and acceptance

L0: Root owns four shared control files, this record and explicit rollout to existing task owners.
No scientific card, frozen input, accepted provider request or resource admission rule is changed.
AGENTS section 2 now distinguishes owner/shared/physical resource boundaries from DM planning
allowances. DM can select bounded prospective support/closeout within existing direction resources,
disclosing cumulative costs, unknowns and original-plan deviations. No frozen-run extension,
disguised retry or original-cap compliance claim follows. Ordinary outcomes go to Clerk; an actual
owner exception identifies its source and affected action. No new approval checklist is introduced.

The DM role and ROOT_OPERATIONS apply that distinction; SIBLING_COMMUNICATION covers direct Root
exceptions and publication into session plus authoring entrypoints. Current explicit instructions
apply to ongoing turns without claiming that old injected text has disappeared. Each existing
editing owner synchronizes control paths at a clean boundary and reports actual sync or conflict
to Clerk; publication/delivery is not recorded as completed synchronization.

Independent engineering Reviewer found no substantive issue in the four-file diff. Root checked
diff whitespace and parsed the DM TOML successfully. This documentation/role change requires no
new experiment, Pro request or repeated scientific test suite. Research and current review continue.

For the rollout, use the current published revision's paths from the prior 4dfdb5f8f control change:
AGENTS.md, CLAUDE.md, .codex/config.toml, .codex/agents/hmasd-direction-manager.toml,
.codex/agents/hmasd-transport.toml, its changed .agents/skills paths, docs/project control paths,
docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md and portfolio/owner/README.md. Bring the three
associated tests/skills changes with the renderer/consumer source where needed. Do not overwrite
live .codex/hmasd-*.toml registries, current Portfolio snapshots, direction science or accepted
packet bytes; resolve operational routes from main. The new four-file repair is included in that
same current source revision. Clerk records actual propagation separately from Root publication.

## Clerk propagation receipts

- FOLR returned a concrete successful rollout: its registered session and authoring checkout each
  synchronized the exact 25 control paths from the repaired main revision, with 25/25 blob matches
  before/after, three local suites reporting 160 passed in each checkout, parsed TOML and
  skill-frontmatter checks, and clean final trees. Live `hmasd-*.toml` registries, reports,
  direction science and accepted packets were outside the sync scope. Session sync was
  `27316d65315e7296a19368445b8e49b4384824f3`; authoring sync was
  `98875c4b6211b1f53ad54e29ce7479b26716a12`.
- ACVC later returned a concrete successful rollout as well: its registered session and authoring
  checkout matched all 25 named blobs from the repaired main revision, both trees were clean
  before/after, and each focused consumer suite passed 160 tests (3.46s and 3.66s). Its sync
  commits were session `d95fd8ec55159367197ab9d4acaabd54c1aef753` and authoring
  `ebf214476904dcf980ba09b2e62b91427c183d50`; live registries, snapshots, science and packets
  were unchanged. ACVC's separate scientific-review producer remains pending with an actual
  `TIMEOUT_WAITING_FOR_PROMPT` receipt (`sendAttempted=false`); the DM is repairing that same
  request without a new seed, consultation or approval request.
- MGTAP and RCLE still returned `no rollout found` for their registry thread IDs, while FOLR and
  ACVC later supplied concrete receipts above. RCLE subsequently returned a concrete rollout:
  its session commit `2e12ccc0d03918378f0efcebcb1216d22e847414` and authoring merge
  `34afdc8262b05b08f2ed8f8aa057f323be93d375` have all 25 scoped blobs equal to the repaired
  source, each checkout passed 160 focused tests and parsed the three scoped TOMLs, and no target
  overlap/conflict occurred. Its independently delivered scientific response was preserved in
  the authoring merge; main was not edited for that response. Until a concrete receipt exists,
  message delivery is not counted as synchronization.

The current owner-console interface has one separate traceability gap: `portfolio/owner/README.md`
recommends `--authority 'OWNER_DELEGATED / DM_DECISION'`, while the current `item.py trace --help`
accepts only `OWNER_DIRECT` or `PRO_FINAL / OWNER_DELEGATED`. No synthetic Pro/owner decision was
created to bypass this mismatch; existing owner items and direction intake/audit records remain the
source of truth pending a control-owner repair.
- MGTAP subsequently returned the same concrete 25-path rollout: authoring commit
  `fea6df33ced6a6cfb2028cb9a9171b70024a0559` (pushed on `codex/mgtap`) and detached session
  commit `f00416a0cb23efc00cc394f703b80f49c514352d` both match the repaired source; both checkouts
  are clean, six skill quick-validations and three TOML parses pass, and live registries,
  portfolio/report state, direction science and fixed packets were excluded. Its B8241 result
  and full scientific-review intake are separate accepted research evidence, not a control-sync
  approval or a new Portfolio request.
- Clerk's own session checkout synchronized the same 25 control paths from `origin/main` and
  committed detached `7bb9240682f7f81ead8a9892a802b92c896bf964`; live registries, snapshots,
  science and accepted packets were excluded. The session tree is clean at that receipt.
- RCLE later completed a second, five-path synchronization for published `d2227e4bd` (AGENTS,
  the DM role TOML, and three project control files): session commit
  `64cd253a7632bdae9d40f1ef341a1a6723175706` and authoring commit
  `9b46cc3d7bdd75c4b4fa420ca37922c16ed2160e` are byte/Git-blob equal and clean, with TOML parse
  and whitespace checks passing. The other 20 paths and focused suites were not redundantly rerun;
  live registries, science, source and accepted requests were excluded.
- ACVC also completed that five-path synchronization: authoring `88840bbc30f1c28429bc12ebfa3ef459d6a31f1f`
  and detached session `ade16c8a2c1d114c3a1af71728c55aa8075dde10` are clean and blob-equal to
  `d2227e4bd`, with whitespace and DM-TOML checks passing. Its scoped exact-PID Agentify restart
  command was refused before execution by policy; ACVC did not retry, terminate anything, or route
  around the refusal. Read-only checks found PID/Chrome, operation-store hash and the original
  `sendAttempted=false` operation unchanged; no provider generation is active, and the DM retains
  same-request repair responsibility.
