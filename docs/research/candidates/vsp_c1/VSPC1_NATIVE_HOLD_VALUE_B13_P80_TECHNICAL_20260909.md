# B13 P80 technical source acceptance and execution

The selected intact 136→128→133→1 ordinary body is constructed before the
128×5 zero gate in GATED-V. Actual critic counts are 35467/34827, actor 32264.
Private extra rows/biases and zero extra output weights agree between independent
arm copies. Older default bindings are preserved. Final-only evaluation now
uses four independent train/evaluation environments without a 512 panel.
Checkpoint metadata records the actual architecture and 768 training episodes.

Designated checkout: C:/Projects/HMASD-worktrees/dm-vspc1-next-20260906,
codex/direction-vsp_c1, initially clean at 0886e5ea4b18816d9f7750f81134aa3d8307fd12.
Owned source: native_hold_value_b01/{critic,study}.py and the new B13 runner;
new B13 tests and this evidence. UCOPE, native environment, WideCritic and
normalization dependencies have no diff from the bound starting source.
Engineering scope §4: none per card §5; 62 added production lines, 35 runner lines.

## Focused acceptance

[Exact check receipt](VSPC1_NATIVE_HOLD_VALUE_B13_SOURCE_CHECKS_20260909.json):
34 passed, exit 0; pytest 3.56s, whole 4.2679593s within the 300s total budget.
New B13 binding, actual FP32 critic construction/counts/private RNG/zero-gate
numerical agreement and nonzero gate gradient checks; stubbed full 768 schedule,
four constructors, two final checkpoints, frozen moments, complete and partial
primary/H publication. Existing B05 critic, B08 schedule and B10 endpoint/deadline
checks establish relevant legacy defaults and continuous cap behavior. The actual
critic test constructs models but no native environment or fit; schedule tests
use fakes. No scientific native step, fit or evaluation occurred in these checks.
The existing disabled-cacheprovider cache_dir warning is retained.

Independent reviewer review_b10_boundary inspected the changed factory, private
initialization, parameter independence, final-panel isolation, moments, metadata,
primary/H dependencies and caps: no material finding and no required repair.
Reviewer ran no tests or native code; runtime/publication conformance still needs
terminal artifacts. The complete diff was inspected after review; no source change
followed review. New test scratch was resolved and removed by its creator; absent
at completion. Historical P76 scratch remains creator-owned after its recorded
policy rejection; no repeated rejected cleanup or bypass.

## Cost and publication coverage

Card §5 projects each arm from 196608 training steps, 1536 Adam, 384 moment
merges, 8192 learned evaluation steps and one endpoint publication; GATED pays
startup and MLP also pays 8192 H steps and pair readback/exit. Prior complete
pair walls 475.85/507.29/504.91s inform planning beneath 1800s per complete arm
and 3600s whole. New-width component costs and aggregate CPU remain unknown;
no new cost probe. Stubbed final-only publication and readback exercise the
affected post-learner path, including missing H versus damaged learned primary.
Existing actual final checkpoint collection supplies credible unchanged-path
coverage. Engineering checks establish conformance, not performance.

CM continues the one allocated accepted remote submission through exact committed
source and literal-wrapper binding, fresh joined actual-node admission, sole
observation and all-outcome collection. CPU FP32, one process/numerical thread;
no retry, resume, extra evaluation or successor. DM owns scientific intake and
Root owns completed remote-worktree reclamation.
