# ESCALATION: the cross-machine replay gate needs one workflow job

Status: **blocked on the user.** Workflow-file pushes are user-side gated on this
line. Everything else this job needs is committed and verified.

Ordered by the Pro ruling of 2026-07-30,
`docs/external-review/rounds/20260730_d7_s_manifest_replay_gate_result/`, §8
item 8, and §3:

> then run the same committed development manifest on two independent cloud jobs.

> The next gate should use the same committed development manifest bytes on two
> independently provisioned cloud jobs. [...] Only a corrected cross-machine
> `MANIFEST_REPLAY_PASS` may select A1 and release the deterministic
> fresh-population rule for application.

## Why this is an escalation and not a workaround

The previous round rode an existing job: `d7_s_clone_conformance_check.py` already
tees its stdout into the `conformance.txt` that the `benchmark` job uploads, so the
R4 world-digest block reached the cloud **without any workflow change**. I looked
for the same ride here and it does not work, for a reason worth recording rather
than engineering around:

```text
benchmark   timeout-minutes: 30, and its existing step already spends
            --search-budget-seconds 900 on the clone conformance search
probe cost  the full registered horizon, H_STABLE=139 and H_FLEX=550 on both
            limbs, measured at roughly 15 minutes per run locally
```

Riding `benchmark` means either exceeding the 30-minute timeout, or silently
changing what that job measures so the probe fits. The second is worse than the
first: a job whose name says `benchmark` and which quietly stopped running the
conformance search is exactly the kind of drift that is invisible until someone
cites it.

`workers` has the time (340 minutes) but its invocation is fixed to the audit
script, so using it needs a workflow edit anyway — the same gate, for a worse fit.

**So the honest answer is one small new job, not a contortion.**

## What is already done, and verifiable without approving anything

```text
manifests/d7s_dev/                       COMMITTED, 3 files, ~10 KB
  inventory.json                         set_hash 0212ef4613fb5974c9...
  D7_S_MANIFEST_REPLAY_DEVELOPMENT/20260725/audit/0/{world.npz,identity.json}
scripts/d7_s_manifest_replay_probe.py    the producer, refuses any R4 topology
scripts/d7_s_manifest_replay_gate.py     the comparator, three outcomes, no escape
```

The committed set verifies in place: `verify_manifest_inventory` returns the same
`set_hash` from the repository copy as from the machine that generated it, so the
bytes two runners would load are provably the bytes that were frozen.

## The exact job to add

Append to `.github/workflows/d7s-audit.yml` under `jobs:`. Nothing else in the file
changes.

```yaml
  replay:
    if: inputs.mode == 'replay' || startsWith(github.ref, 'refs/tags/d7s-replay')
    runs-on: ubuntu-latest
    timeout-minutes: 60
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.10"
          cache: pip
          cache-dependency-path: requirements_d7s_audit.txt
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements_d7s_audit.txt
      - name: Manifest replay probe over the full registered horizon
        env:
          OMP_NUM_THREADS: "1"
          MKL_NUM_THREADS: "1"
        run: |
          python scripts/d7_s_manifest_replay_probe.py \
            --mode replay \
            --manifest-root manifests/d7s_dev \
            --episodes 1 \
            --out replay_probe.json
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: d7s-replay-${{ github.run_id }}
          path: replay_probe.json
          retention-days: 90
```

`mode: replay` also needs adding to the `workflow_dispatch` input's option list, if
that input enumerates choices.

## How it is used, and what it costs

Tag twice: `d7s-replay-1`, `d7s-replay-2`. Two tags on a public repo, roughly 20
minutes of runner time each, free. Two independently provisioned jobs is exactly
the independence this gate requires — the ruling is explicit that **differing CPU
models are NOT needed** for byte replay, only independent executions, and the probe
records `github_run_id`, `github_job` and `runner_name` for that reason.

Then download both artifacts and run:

```bash
python scripts/d7_s_manifest_replay_gate.py --samples a.json b.json --out gate.json
```

## What this job cannot do, stated so it is not assumed

- It cannot touch a confirmatory topology. The probe **refuses** any seed in the
  frozen R4 population, and the committed manifest set is `TOPOLOGY_SEED_DEV`
  only.
- It authorizes no formal compute and produces no conclusion-bearing artifact.
  Its output is apparatus evidence: whether replay reproduces an episode across two
  machines.
- A `MANIFEST_REPLAY_PASS` from it does not by itself wire the manifest into the
  audit path. It is the precondition the ruling names for **selecting A1**, and the
  wiring is a separate decision.

## The alternative, if the gate stays shut

The local cross-process result stands and is honestly labelled as cross-process:
the gate reports independence from `pid` and says so. Under the ruling that is
sufficient to continue development work and **not** sufficient to freeze A1, wire
the manifest in, bind the fresh inventory, or authorize a formal source result.

So the cost of not approving this job is that A1-versus-A2 stays `UNTESTED` and the
successor population stays uninstantiated. Nothing is lost or invalidated; the line
simply does not advance past the gate.
