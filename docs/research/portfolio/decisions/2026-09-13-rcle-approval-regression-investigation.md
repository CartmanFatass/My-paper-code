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
