# VSP03 B04 / P67 source acceptance and exact launch

Candidate source: **828da00343e5036a4de93ccf1ec636e3b8c777b7**, pushed on the existing
shared direction branch. [P67 card](VSP03_B04_P67_SCIENCE_CARD_20260908.md) sections2,
4–5 allocate one new submission. Old P64/P65's code2, zero scientific exposure,
spent allowance and raw evidence remain unchanged.

## Complete source and narrow correction

The synchronized direction source already contains the canonical admission helper
and its sole repository dependency: scripts/hmasd_resource_preflight.py blob
4127cd22d2e0c4cc1ad6df85aafeb7131c3d07b2 and scripts/hmasd_platform.py blob
eb54e7c31170ad14c903ba87e55b1a479416b51b. Both match canonical888bd9f50 exactly.
No helper reimplementation or shared-core change was needed. The platform module
otherwise imports only standard library modules; its POSIX fcntl is standard library.
The admission script supports the direct-script fallback import of hmasd_platform.
Its admit-memory body writes the receipt and returns0 only when both physical and
effective available memory meet the fixed4GiB floor; that exit controls the && runner.

The sole new code is the eight-line committed launch_p67.sh, which calls the accepted
P65 launch adapter with new P67 handle/output names. It retains the literal
"$VSP03_B04_STARTED" inside the bash command and its adjacent admission&&runner order.
B04 runner, B01/B02/B03 scientific modules and P65 launch/control/deadline bytes are
unchanged against b5d605bf4. Output object remains VSP03_B04, seed6/Torch40006/G1.

[Source checks](VSP03_B04_P67_SOURCE_CHECK_20260908.json) enumerate the11 declared
source/import files with Git blobs, SHA256 and sizes. All committed bytes are LF;
Python AST parsing and bash -n passed. Canonical admission admit-memory --help exited0,
checking its imports/parser without capturing resources, admitting a run or executing
science. No scratch or scientific check invocation was needed. Reuse prior seed/object,
five lifecycle checks and B03's complete output/readback evidence. The independent
[focused review](VSP03_B04_P67_SOURCE_REVIEW_20260908.md) covers the new binding only.
There is no changed scientific or deadline semantic boundary.

## Frozen invocation

Node: wsl_4070 via hmasd-wsl-node. Python: /home/wu/.venvs/hmasd/bin/python;
CPU float32, one compute thread; inherited float64 worlds. No local fallback.
Exact new detached cwd:
`/home/wu/hmasd-worktrees/vsp03-b04-p67-828da00343e5036a4de93ccf1ec636e3b8c777b7`.
Launch the committed LF bytes, without reconstructing the nested command:

```bash
bash /home/wu/hmasd-worktrees/vsp03-b04-p67-828da00343e5036a4de93ccf1ec636e3b8c777b7/experiments/candidates/vsp_03/vsp03_b04/launch_p67.sh /home/wu/hmasd-worktrees/vsp03-b04-p67-828da00343e5036a4de93ccf1ec636e3b8c777b7
```

Unit and supervisor handle: vsp03-b04-p67-20260908. Scientific output root:
`/home/wu/projects/HMASD/temp/directions/vsp_03/exp/b04_seed6_p67_20260908`.
Adjacent admission is that root plus _admission.json; whole-task receipt is
_terminal.json; payload receipt is _terminal.payload.json. Original supervisor
files remain /home/wu/.agent-tasks/vsp03-b04-p67-20260908/. Private-server status:

```bash
env -u TMUX TMUX_TMPDIR=/home/wu/projects/HMASD/temp/directions/vsp_03/exp/b04_seed6_p67_20260908_terminal.tmux /usr/local/bin/agent-task status vsp03-b04-p67-20260908
journalctl --user -u vsp03-b04-p67-20260908.service --no-pager
systemctl --user show vsp03-b04-p67-20260908.service
```

## Execution, budget and observation

After DM source acceptance, the same CM fetches the committed revision through the
configured zsh-lic network environment and creates the named detached exact-SHA cwd.
Verify its11 declared source files against the committed digests, LF shell bytes,
actual cwd and shell syntax before submission. Confirm the new handle/output are
unused. This is source/input verification, not a scientific payload run. Do not
repair or populate an old evidence root. Any mismatch is corrected before submission.

Use the existing configured agent-task through the accepted transient unit: the
manager's single pre-start monotonic origin reaches admission and runner; work stops
by110s, cleanup by118s, and hard cgroup kill is armed for119s inside the complete120s
cap. Required outputs/readback/exit and descendant termination remain inside that
boundary. Actual manager, supervisor and task receipts are distinct; systemd-run's
client1 is not the actual task exit code. Missing evidence remains missing.

Per-arm projection reuses the card's unchanged one-G law and prior B03 outer3.50s
planning observation. Complete120s remains the bound; new learner wall/CPU are unknown.
Post-learner coverage reuses the accepted scientific readback and lifecycle evidence;
no timing, scientific smoke, extra evaluation or independent-run comparison is added.
This8-line command adds no scope-spec section4 machinery; it reuses only the existing
cardsection5 task-local adapter. No standing observer, recovery or retry is added.

CM is the sole executor/observer through terminal collection. Report the actual
accepted handle/source/cwd/paths/observer to Root /root and DM immediately; no Root
parallel polling or per-shell relay. Stop on any accepted exit, timeout, admission
refusal or failure and collect all outcomes, with no resubmission. Uncertain acceptance
is reconciled on that same handle. DM owns scientific intake. Old cleanup is not retried.

## Parent-requested final argv quoting check

Parent inspection raised a possible literal-backslash/quote defect in line8 and the
old saved payload. [Exact argv evidence](VSP03_B04_P67_ARGV_CHECK_20260908.json)
closes that question without a source change. The committed P67 bash-c argument
contains zero literal backslash bytes; decoded P64 payload JSON likewise contains
zero. JSON's escaped representation of double quotes is distinct from the command's
actual bytes. Control.py shlex.join followed by shell token recovery preserves the
original bash-c argument. A harmless capture substitutes only the two absolute Python
executable tokens with /usr/bin/printf, so neither admission nor runner can execute.
The resulting --started-monotonic argument is exactly375534.924519, without quote
characters, and float parsing succeeds for both supplied commands.

The initial fixture incorrectly expected the historical payload's parse to fail;
its assertion failed after both captures. That harness expectation was corrected
and retained in the record. No production source repair was needed or made, and
this observation does not change the old missing-file failure or spent allowance.
No scientific validation, submission, scratch or lifecycle fixture was added.
Source binding remains828da00343e5036a4de93ccf1ec636e3b8c777b7 and the exact cwd/argv
above. The same reviewer independently dispositions the requested quoting boundary.
