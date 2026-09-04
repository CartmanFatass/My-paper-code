# CBSC-LR01 execution incident — 2026-08-31

The first production invocation began only after the focused suite, direct preflight, resource
projection, and independent review had passed. The native child conversation then failed while
returning control because of external model-capacity transport.

Root initially inspected only the output-root inventory. The sole file was named `manifest.json`,
which Root incorrectly classified as the prospective invocation manifest. The production API in
fact treats the `--manifest` argument as its create-only terminal publication path. A later direct
schema validation established that this file was the complete result published by the first
invocation. The first invocation therefore completed successfully; only the child conversation's
final report failed.

Before discovering that naming mismatch, Root explicitly authorized one identical replacement
invocation after recording what appeared to be a no-output infrastructure interruption. The
replacement recomputed the same deterministic registered panel, then the create-only writer
correctly rejected publication because the first result already existed. It did not overwrite or
create a second artifact. No block, seed, codec, learner, endpoint, margin, or branch law changed.

The accepted scientific artifact is the first create-only `cbsc_lr01_complete_result_v1` object.
The duplicate invocation is an orchestration error with no independent scientific status. There
will be no further CBSC-LR01 execution.
