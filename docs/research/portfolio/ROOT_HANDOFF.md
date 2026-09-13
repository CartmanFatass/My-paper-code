# HMASD Root restart handoff — 2026-09-12

This is the sole current Root restart handoff. Replace this file at the next Root handoff; do not
append historical snapshots. Repository history preserves superseded states.

## Restart entry state

- Control checkout: `C:/Projects/HMASD`, Windows PowerShell.
- Current integrated main at handoff preparation: `34382425abd4bdda9bcb71847c0f016d9af9483a`.
- Root task: `01a095b7-850f-7401-ad4e-5e4320d285f1`.
- Transport: `01a095ca-7b4a-7940-8acf-fca1b52c784d`.
- Monitor: `01a095d0-21ee-7c02-9d97-3681b5678200`.
- Relay: `01a095ca-8676-74e1-b78c-ea459d41e905`.
- Transport registry is the effect authority. At this handoff all four recently queued responses
  listed below are `ARCHIVED`, have exactly one Send, and have an accepted Root receipt.
- Monitor has no active experiment handle. ACPS-B02 both arms completed and its goal closed.

Do not reset, stash, or include unrelated working-tree changes. Another control-plane batch was
still editing while this handoff was written. The final observed dirty set before restart was:
modified `.agents/skills/hmasd-chatgpt-pro-transport/SKILL.md`,
`.agents/skills/hmasd-loop-dispatch/SKILL.md`, `.codex/agents/hmasd-direction-manager.toml`,
`.codex/agents/hmasd-experiment-operator.toml`, `.codex/config.toml`, `AGENTS.md`,
`docs/project/EXPERIMENT_MONITOR.md`, `docs/project/ROOT_OPERATIONS.md`,
`docs/project/SIBLING_COMMUNICATION.md`, and `docs/research/portfolio/EXPERIMENT_TRACKING.md`;
deleted `.codex/hmasd-monitor.toml` and `.codex/hmasd-relay.toml`; and untracked
`.codex/agents/hmasd-experiment-monitor.toml`. Inspect and preserve that batch as one unit. It was
not included in the handoff commits. Because it changes Monitor/Relay configuration, re-read the
resulting committed control plane after restart before using the endpoint snapshot above.

## First restart pass — exact order

1. Run the `hmasd-loop-dispatch` stable next-action trigger and re-read current owner instructions.
2. Integrate each response commit below if it is not already an ancestor of `HEAD`, then immediately
   wake the named original DM with the immutable response for complete conformance/scientific intake.
   These responses already exist; do not Send or reconcile them again.
3. Integrate the three ready MGTAP Portfolio-investment author commits in order and dispatch their
   exact HANDOFF once through Transport. Check the current `portfolio:cross_direction` registry
   binding first because the preceding ACPS request is already archived.
4. Apply each DM intake as it returns. A finite allocation ending does not stop or release an ACTIVE
   direction. Only an explicit Portfolio/owner lifecycle decision may change ACTIVE/PARKED.
5. Refresh `PORTFOLIO.md` and `EXPERIMENT_TRACKING.md` from actual DM/provider/handle states. Do not
   count completed responses, cleanup, queued intentions, Transport, Monitor, or Root as directions.
   Restore five independent advancing direction chains by dispatching ready continuations and proper
   node questions; do not invent local science to fill a slot.

## Completed responses awaiting Root integration and DM intake

| Direction | Request | Immutable response commit | Response SHA-256 | Restart action |
| --- | --- | --- | --- | --- |
| ACPS | `2026-09-12-acps-post-b02-investment-01` | `f63980ab1acdcf9fad0ec8b1ac9770c864a6b988` | `0e654363ff33c2dc8316f7cf4682bf5b30ee98662216ce63fb6e4c2d576443da` | Integrate; wake `/root/dm_a_mx_portfolio_resume` for Portfolio intake and execution mapping. |
| ACVC | `2026-09-12-acvc-post-cluster-use-convergence-01` | `d9a1426af03c42bdcbb8e4f84413f94493a58ebf` | `4deb7f4c27dafdcd6634b898722aa3e2e667e4334335fad72bfa368095f78816` | Integrate; wake `/root/dm_a_mx_acvc_resume` for direction intake and conforming continuation. |
| RCLE | `2026-09-12-rcle-joint-quota-phase-family-01` | `8aa3f7bd764ecf9bb7704ccab98c1bd990afd6c0` | `de03b11d82bfbd7e1bed120ae1f1d079130d69c86797f53b2dde858e731119d3` | Integrate; wake `/root/dm_a_mx_rcle_intake`; activate conditional B only if the exact offered family was selected. |
| FOLR | `folr-entity-history-post-b01-discriminator-20260912` | `d6a29b287612f21fd5ddbb0cc19fbae4e8c1fb12` | `3d2f63f5beb9221e2206b24c491bb01130437185d6b6d499b27455513125fb74` | Integrate; wake `/root/dm_folr_post_b03` for direction intake; no Generic retry without an explicit decision. |

MGTAP's earlier use response `71baa4a814fb8cb5d0cd2944deb0548b8fc644b2` and its DM intake
`e4aa3566ff1f5b3163a168225dc0d6172e2a093e` are already integrated. It selected one fresh
mean-COND512/intact-DENSE768 scientific comparison but granted no experiment. MGTAP remains
ACTIVE/MEDIUM and DENSE remains default.

## Ready MGTAP Portfolio investment handoff

Integrate these commits in order, excluding any sync-only commits named by the DM:

1. `e0196a1e1c9aa53c2dc3e978ab199c4adfe84eac`
2. `a52d4dcb43625dc5ef1f009c9f578a20089c5d14`
3. `ada5eade08d7c849f6111d6ea6eca72ad03734bb`

Then execute exactly once:

`C:\Projects\HMASD-worktrees\codex-portfolio\docs\research\portfolio\pro_packets\20260912_mgtap_unequal_exposure_investment\delivery\HANDOFF.json`

Request `2026-09-12-mgtap-unequal-exposure-investment-01` asks Portfolio to buy exactly one complete
fresh mean-COND512/intact-DENSE768 pair or buy nothing. The proposed workload is 344,064 team ticks
and 2,560 Adam updates plus all required support. New costs and caps are UNKNOWN/UNASSIGNED; no
historical cap or balance may be reused, and there is no current implementation or experiment grant.

## Current scientific control facts

- ACPS: ACTIVE/HIGH. B01 was ADVERSE `-0.0368081418 J`; B02 was negative INSIDE_MEI
  `-0.0051864274 J`, conditional SE `0.00545885`, 12 positive/20 adverse. B02 intake and four-target
  cleanup are complete. SHARED remains the measured-use default. Its completed Portfolio response
  above must be intaken before any next action.
- CADC: explicit Portfolio reversible PARKED/HIGH, recasts0. This is the only recent lifecycle stop.
- FSD: ACTIVE/HIGH, limited optional I1280 with authentic D0 default; no LONG or repeat U funded.
- MGTAP: ACTIVE/MEDIUM. Original node selected the unequal-exposure pair; separate Portfolio funding
  remains pending through the ready handoff above.
- RCLE: ACTIVE/MEDIUM. The family response is complete but not yet intaken; before conforming intake,
  its conditional 900-native + 900-support = 1800-complete B remains inactive.
- ACVC: ACTIVE/MEDIUM and second-recast lowest-contestion ordering. K completed with both cluster
  contrasts UP. Its new direction response is complete but not yet intaken.
- FOLR: ACTIVE/MEDIUM. BANK completed, Generic had no final, so no paired primary or polarity exists.
  Its new direction response is complete but not yet intaken.

The last published current tables may lag these newly discovered archived responses. Treat this file,
the Transport registry, immutable response commits, and subsequent DM intakes as restart inputs; then
replace the table rows with the resulting current facts rather than retaining stale prose.
