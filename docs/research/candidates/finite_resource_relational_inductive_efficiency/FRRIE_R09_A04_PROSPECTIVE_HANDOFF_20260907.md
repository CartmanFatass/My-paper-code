# FRRIE A04 prospective handoff — preparation only

**P11 allocates no execution.** This complete candidate uses existing code. No CM engineering
assignment, source implementation or model-comparison enrollment is needed by this preparation.
Any later changed-code request must receive its own complete common spec before CM starts.

## 1. Five-item execution/collection handoff

1. **Deliverable.** After a later explicit allocation, create the one dedicated system312/NumPy
   environment and attempt the single T0 workload, then return actual setup/probe receipts,
   counts, exception/digest table and technical acceptance. Question and result rules are in
   [card §§1–3](FRRIE_R09_A04_ALTERNATIVE_STACK_SCIENCE_CARD_20260907.md).
2. **Owned surfaces and checkout.** Reuse authoring checkout
   `C:/Projects/HMASD-worktrees/dm-frrie-a01-resume-20260905`, branch `codex/frrie`.
   Source is fixed at `d6844bb25f6f1030aa7123467935861dcc719450`. Entry points are the existing
   `scripts/run_frrie_r09_tape_isolation_a03.py` and candidate `tape_isolation_a03.py`.
   Their `rng.py`, `tapes.py`, `contracts/core.py` and package initializers remain unchanged.
   Remote execution uses a detached checkout at that SHA and the one proposed venv/output root
   below. CM owns collection/technical acceptance; this DM retains scientific intake.
3. **Preserved semantics.** Card §2 supplies root/label, exact T0 work, host, interpreter,
   FP32/int64, one thread and absence of torch/tracer/native/learner. Raw summary keeps its A03
   implementation object string; A04 card/handle/root provide the new attempt identity. Never
   relabel old files, substitute the shared project or CBSC venv, add an uv arm, retune NumPy,
   change tapes, or turn completion into R09 authorization.
4. **Acceptance.** Use card §3's first matching branch and evidence-spec §§4, 5.1, 11.8.5–7.
   Check actual committed source and declared invocation, installation/version log, same-node
   admission, supervisor exit and wall, and summary where present. Full completion means exactly
   3 repetitions × 2 phases × 64 tapes with no torch/tracer, recorded digest comparison and no
   original exception. Failure to install/import gives a setup fact; a fatal signal may leave
   no summary, in which case bounded direct log/exit/count facts survive. Do not run a separate
   workload smoke, regenerate A03 tapes, repeat the focused suite or require complete root-cause
   attribution. Missing RSS alone is `resources_unmeasured`.
5. **Budget and stop.** Exactly one proposed complete chain, 300 s TERM plus 5 s KILL grace,
   covering environment creation/install, admission, imports, T0 and publication. Stop on the
   first command failure, original workload failure, third repetition or cap. P11 allocation is
   zero; no retry, environment mutation or invocation may occur from this document alone.
   Return a missing dependency rather than install another version or use another host.

You are not alone in this checkout. Serialize overlapping edits and explicit-path Git operations;
preserve concurrent work. The candidate venv and detached worktree paths were absent in the
preparation's read-only node check. A later allocation must name the collector and reconcile its
own handle acceptance; never overwrite an existing run or relaunch an accepted handle.

## 2. Exact candidate command for a later allocation

Control-plane source staging is a detached worktree at the fixed SHA, at
`/home/wu/hmasd-worktrees/frrie-a04-d6844bb25f6f`. The source is already committed/pushed on main.
No staging or command below was executed during P11. It is to be delivered as UTF-8 LF text via
the existing Root file-delivery route, preserving quoting. Do not paste it through an additional
shell interpolation layer. Run it only after Portfolio supplies the named execution allocation.

```bash
/usr/local/bin/agent-task run frrie-a04-system312-p11-d6844bb25f6f 'cd /home/wu/hmasd-worktrees/frrie-a04-d6844bb25f6f && timeout --signal=TERM --kill-after=5s 300s bash -c "export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1; /home/wu/.local/bin/uv venv --no-config --no-python-downloads --python /usr/bin/python3.12 /home/wu/.venvs/hmasd-frrie-system312-a04-20260907 && /home/wu/.local/bin/uv pip install --no-config --python /home/wu/.venvs/hmasd-frrie-system312-a04-20260907/bin/python --default-index https://pypi.org/simple --only-binary :all: --no-deps numpy==1.26.3 && /usr/bin/python3.12 scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/frrie-a04-d6844bb25f6f/temp/directions/finite_resource_relational_inductive_efficiency/technical/a04_system312_admission.json && /home/wu/.venvs/hmasd-frrie-system312-a04-20260907/bin/python -X faulthandler -m scripts.run_frrie_r09_tape_isolation_a03 --arm T0 --repeat 3 --updates 2 --eval-episodes 256 --out /home/wu/hmasd-worktrees/frrie-a04-d6844bb25f6f/temp/directions/finite_resource_relational_inductive_efficiency/exp/a04_system312 --launch-sha d6844bb25f6f1030aa7123467935861dcc719450 --admission-receipt /home/wu/hmasd-worktrees/frrie-a04-d6844bb25f6f/temp/directions/finite_resource_relational_inductive_efficiency/technical/a04_system312_admission.json"'
```

This creates only the dedicated venv; it requests no seed packages, torch, source distribution
build, interpreter download or change to the live research interpreter. NumPy1.26.3 cp312 wheel
availability/download/import are **unverified**, and must be reported as part of this complete
chain if it is later allocated. The fixed path selects system CPython; uv is the environment
manager. The resource preflight uses system Python and is immediately joined by `&&` to the
actual T0 interpreter within the same supervisor command. It admits only this node/invocation.

Read original phase digests from:
`docs/research/candidates/finite_resource_relational_inductive_efficiency/a03_tape_isolation_20260906/t0/summary.json`.
Do not regenerate them or run historical A03 tests to obtain them.

## 3. Preparation checks and missing input

The full FRRIE candidate tree and A03 runner have an empty diff from accepted A03 source
`50283c9cfffeaba913572fe43f5a8dbf311abe7e` to the bound source. Source changes required: **none**.
Only text/static checks apply to this handoff; they do not establish NumPy availability,
importability, tape completion or resource admission. Existing `_process_facts` uses
`sys.flags.__match_args__`; system312 exposes that attribute in a stdlib-only version query.
The 1379-byte UTF-8 LF candidate and its extracted inner shell both passed `bash -n` (exit 0)
without execution. This is syntax evidence only; it does not represent accepted setup or a run.

Root returns this prepared route to Portfolio. The exact remaining input is a later allocation
of one complete setup/T0 invocation and a named CM collector. The unresolved old owner item is
not treated as a reply or a blanket installation-permission rule. No repeated T0, full R09,
Pro request, independent seed or host-repair task follows automatically.

After a later accepted handle, use EXPERIMENT_MONITOR.md and ROOT_OPERATIONS.md for Root's
observation adoption; transfer observation without relaunch. CM collects and technically accepts
every terminal outcome; this DM then applies card §3 and writes result intake. No branch grants
full R09 execution.

scope: none
