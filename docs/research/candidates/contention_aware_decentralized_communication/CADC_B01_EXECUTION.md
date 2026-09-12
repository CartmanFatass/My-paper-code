# CADC-B01 exact execution inputs

Current state: both preselected arms completed once, exit0/COMPLETE, and original DM technically/scientifically accepted the full pair after Root routed terminal facts. Native wall195.00s/180.34s; [result](CADC_B01_RESULT.md), [intake](CADC_B01_INTAKE.md), [terminal collection](evidence/cadc_b01_9302/TERMINAL_COLLECTION.json). Prior [launch](execution/LAUNCH_RECEIPT.json) and actual [adoption](execution/MONITOR_ADOPTION.json) remain factual evidence. The [scoped cleanup inventory](CADC_B01_CLEANUP.md) awaits Root integration/retention, with no duplicate ADD, polling, retry or successor.

Source SHA: `22e009c9387f2507aab6ebab4555d92e27f5070e`, independent review and focused tests accepted in [TECHNICAL](CADC_B01_TECHNICAL.md). Source is published on `codex/cadc`; Root integrated unchanged code at main `1d68daff9`. Fixed card/master9302 and LEARNED/RR companion remain unchanged. Shared source and authoring paths are not execution outputs.

Host: configured `hmasd-wsl-node`, interpreter `/home/wu/.venvs/hmasd/bin/python`, CPU FP32/one thread. Detached runtime checkout `/home/wu/hmasd-worktrees/cadc-b01-9302-20260912` at the exact source SHA. Frozen command input directory `/home/wu/hmasd-inputs/cadc-b01-9302-20260912`. [LEARNED.sh](execution/LEARNED.sh) and [RR.sh](execution/RR.sh) are separately staged Git-blob LF bytes and syntax-checked without executing scientific payloads.

Handles, preselected once: `cadc-b01-9302-learned-20260912` and `cadc-b01-9302-rr-20260912`. Supervisor invocation, once per actual ready arm:

```text
ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node /usr/local/bin/agent-task run cadc-b01-9302-learned-20260912 bash /home/wu/hmasd-inputs/cadc-b01-9302-20260912/LEARNED.sh
ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node /usr/local/bin/agent-task run cadc-b01-9302-rr-20260912 bash /home/wu/hmasd-inputs/cadc-b01-9302-20260912/RR.sh
```

Each payload sets its chain clock before fresh destination `admit-memory && runner`, before scientific roots/RNG/model construction; memory receipts are sidecars in the frozen input directory. The actual runner outputs under its separate `temp/directions/contention_aware_decentralized_communication/exp/cadc_b01_9302/<arm>` directory. GNU time encloses timeout, adjacent admission, runner imports/model/train/final/checkpoint/publication and child exit, recording only wall, peak RSS and exit status. Internal elapsed cannot certify final tails. Timeout595s plus at most1s kill grace reserves four seconds inside the hard600s whole-arm limit for the outer wrapper; final whole-chain/support tails remain explicitly observed or unknown at collection. This is a technical reservation inside the existing cap, not extra time or altered learner work.

Root clarified that T→ACPS→CADC applies to actual contended admission; independent preparation and available capacity do not wait for a sibling result. Both arms remain preselected whatever the first outcome. A concrete integrity/resource/cap limitation limits the dependent step, not the direction's lifecycle or scientific polarity. No retry follows an uncertain handle: reconcile the same supervisor identity.

Actual accepted handles go directly to the live main Monitor endpoint. Payload must require get_goal, continue the matching unfinished goal or create_goal without a token budget, retain each handle through accepted terminal notice, report actual unfinished goal in MONITOR_ADOPTED, and send MONITOR_GOAL_COMPLETE to Root before completing an empty goal. Cross-task delivery alone is not adoption. Original DM owns collection, complete counts/primary/cost intake, archive and cleanup; Root integrates/retains before removal. Native send or short supervisor status is not a scientific result.

Cleanup inventory to prepare at collection: this exact remote runtime worktree (including output), exact frozen input directory, and these two terminal supervisor directories only. Preserve unique source/checkpoints/rows/wall/admission/log evidence first, leave shared repo/authoring and other handles untouched. The separately documented policy-rejected local synthetic scratch remains this creator's pending cleanup responsibility.

Owner-delegated decision (unattended, 2026-09-03 instruction): select the minimal 595s outer execution window/+1s kill grace within600s to reserve final exit cost; the alternative of spending the complete600s inside Python could omit outer tails. No extra arm, timing run or scope machinery is added.
