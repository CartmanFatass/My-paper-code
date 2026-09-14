# Capacity and transport update — 2026-09-14

This updates execution/coordination facts only. The DM CONTINUE decision,
selected MGTAP-LR-SELECTION-B01 science,13 successful protocol tests and zero new
native exposure at that boundary remain unchanged.

## Capacity snapshot is not an instruction to restore other directions

Commit304450d6f9f776c2e72fe6d3517a6909e9ee83ae used the then-observed RCLE/FOLR
occupancy2 and MGTAP reservation1. Applying MGTAP alone would have yielded3/0
if no other direction changed. FOLR subsequently chose PARK; that newer decision
must not be overwritten to force the old total.

A fresh read of C:/Projects/HMASD/.codex/hmasd-dm-sessions.toml now shows:

- MGTAP: implementation_in_progress, occupies_slot=true, event
  MGTAP_REENTRY_LR_SELECTION_CONTINUE_20260914.
- RCLE: occupies_slot=true.
- FOLR (vap_folr_core): scientific_park_archived, occupies_slot=false.
- reserved_slots=0; two actual occupied directions, not three.

This is a read of the live control file, not a claim that all Clerk Git integration
or unrelated registry fields have finished. EVENT.json therefore expresses the
MGTAP change as +1 occupied/-1 same-request reservation; original totals are a
labelled planning snapshot. The remaining FOLR vacancy is Clerk/owner coordination,
not permission for this DM to create another direction or reopen FOLR.

## New Transport route, no pending request to migrate

Root delivered OWNER_DIRECT replacing Agentify MCP/native Transport assignments.
DM fully read the updated live skill and C:/Projects/HMASD/.codex/hmasd-transport.toml.
The next ACTUAL request uses REUSE_SINGLETON and the independent Luna/high iab
Transport task01a09ea0-4a86-75b0-826d-6f864efa7480, with this DM App task as parent.
The live config remains the routing source while its main publication is pending.

There is no pending MGTAP Pro request or old executor to transfer. Completed reviews,
provider identities and full archives remain untouched. No test scientific request,
readiness Send or replacement review was created. No Root ACK/report is needed for
routine work. The separate owner-requested permission audit is a one-time exception.

## No continuation approval wait

The native runner still needs implementation and focused acceptance; that is DM
work, not a Clerk receipt, main integration, file-path rule or approval blocker.
Authoring remains on codex/mgtap in its existing writable checkout. Shared main
and other directions are not edited by this DM. No actual file/tool denial is
currently preventing the next implementation action. Policy-rejected historical
duplicate deletions remain untouched and do not block research.
