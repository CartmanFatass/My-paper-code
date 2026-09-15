# MGTAP reentry audit — 2026-09-14

| Event | Actual disposition | First action | Evidence |
| --- | --- | --- | --- |
| MGTAP_REENTRY_LR_SELECTION_CONTINUE_20260914 | DM CONTINUE; consume the existing LCAC vacancy reservation, not a fourth direction | Implement and test separate selection/holdout protocol and computed workload; no native launch yet | [DM intake](DM_REENTRY_INTAKE.md), [card](../MGTAP_LR_SELECTION_B01_SCIENCE_CARD_20260914.md), [engineering](ENGINEERING.md), [event](EVENT.json) |

The old PARK decision and all old results remain historical evidence.
Main registry application is the live Clerk's integration action, not a DM main write.

Owner-console items created by item.py, not hand-written: lifecycle decision
[20260913-mgtap-007](../../../portfolio/owner/inbox/2026-09-13/20260913-mgtap-007.json)
and prospective card
[20260913-mgtap-008](../../../portfolio/owner/inbox/2026-09-13/20260913-mgtap-008.json).
The console uses the local date; this audit uses the UTC event date. Both items
record the actual applied choice and are asynchronous, not approval waits.
