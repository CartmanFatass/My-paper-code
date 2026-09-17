# Transport receipt model override

Owner requested investigation of a cross-session model switch on 2026-09-05.
This is a local invocation defect; no provider-model change is inferred.

## Observed evidence

Read-only inspection of the two session rollouts and state_5.sqlite found:

| UTC timestamp | Event |
| --- | --- |
| 21:00:21.785 | Root turn context: gpt-6-astra / medium. |
| 21:09:25.012 | Root dispatches the exploration-calibration handoff to Transport with gpt-5.6-luna / xhigh, as intended for that destination. |
| 21:28:47.538 | Transport sends the archived receipt to Root, incorrectly including model=gpt-5.6-luna and thinking=xhigh. |
| 21:28:47.795 | Root's receiving turn context becomes gpt-5.6-luna / xhigh. |
| 21:36:15.985 | Root continuation still records gpt-5.6-luna / xhigh. |
| 21:49:59.592 | Current Root turn records gpt-6-astra / medium again. The cause of restoration was not established. |

Root: `01a07249-b095-7821-8ce2-e9c32ba85267`.
Transport: `01a06f0e-5eab-7431-8491-e7c2c62705b6`.
Local rollouts are under `C:/Users/fires/.codex/sessions/2026/09/05/`
and `2026/09/04/`, respectively, with those thread IDs in their filenames.
The offending receipt belongs to `2026-09-05-exploration-rigor-spec-portfolio-01`.

The message tool explicitly supports destination model/effort overrides and says
to omit them to retain destination settings. The explicit receipt arguments and
the receiving turn context establish this occurrence without reproducing another
unwanted model switch. Time proximity to request dispatch alone was insufficient;
the switch occurred on the return receipt, about nineteen minutes later.

## Repair

Correct the Transport skill's parent-receipt instructions and the Prompt Author
dispatch explanation: keep explicit Luna/xhigh on dispatch into Transport, omit
both override fields on all parent receipts. No script emits the offending tool
arguments; stage_receipt stages evidence, and the operator makes the tool call.
No model database, user preference, archived response, or research rule is edited.
This implementation correction follows the owner's current troubleshooting request.

Validation: inspected actual call arguments and turn contexts; reviewed the two
instruction edits and ran git diff --check. Future live receipt behavior remains
to be observed; do not resend the completed receipt merely to test the fix.
