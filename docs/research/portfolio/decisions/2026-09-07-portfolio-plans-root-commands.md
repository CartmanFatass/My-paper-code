# Portfolio plans bounded commands; Root executes and reports

Provenance: **OWNER_DIRECT, 2026-09-07**. The owner requested:

> 请用边界清楚的命令 且将判断的职责进一步拿过来 尽量在portfolio做好规划 然后再命令的发送 root只需要知道何时上报即可

## Applied responsibility change

Portfolio determines queue readiness, concrete tasks, dependencies, replacements and the action
to take after a return. It sends Root exact targets/actions, current inputs, task bounds,
prewritten return routes and report conditions. Root executes all independent commands, follows
those routes and reports completion, missing inputs, failed actions, conflicts, uncertain external
acceptance or a required action outside the command. Productive native children remain awaited;
an empty observation queue does not end their work.

The current procedure lives in [ROOT_OPERATIONS.md](../../../project/ROOT_OPERATIONS.md).
AGENTS, Portfolio/Author/Transport skills, DM/CM role instructions and communication/observation
entry points are aligned with it. This record is evidence of the owner instruction, not another
workflow entry. No old operating procedure is inserted into the current command path.

DM retains delegated object-tier science and proper Pro escalation; CM retains technical judgment,
in-scope repairs and acceptance. A command can preauthorize collection, intake, integration or
transport without another owner/Portfolio vote. Preparation-only and read-only commands retain
their own scope. Scientific definitions, budgets, lifecycle, priority, roles' models/efforts and
permissions are unchanged. No new scheduler, registry, validator or standing agent is introduced.

## Application and validation

The existing `hmasd-experiment-monitor` prompt now directs command execution and exception reports
to Portfolio. Its id, thirty-minute schedule, Root target and failed-runs-only notification policy
were preserved; status at the update/readback was PAUSED. Future accepted work activates the same
observer under the existing adoption procedure.

Live application: Root returned factual dispatch receipts, the RCLE unmatched/unknown Send
observation and the DISH HTTPS staging failure. Portfolio, rather than Root, selected the bounded
committed-Git-object staging repair. No new invocation budget followed from that staging failure.
Current research commands and their actual state are recorded in Portfolio/tracking, not here.

Focused validation: changed skill metadata validates; changed role TOMLs parse with all fields
outside developer instructions unchanged; diff whitespace checks pass. Independent Astra/max
review exercised five static routing cases and found two wording gaps (residual admission/
sequencing judgment and ambiguous native waiting); both were corrected. The same reviewer rechecked the fixes plus Author/Transport operation
boundaries and returned no further concrete gap; no additional approval gate was found.
These checks do not establish that future execution can never deviate from the instructions.
