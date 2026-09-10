# FSD B03 P47 exact Root launch binding

**Ready for P47's one G→D0→H panel.** [The P47 FSD command](../../portfolio/handoffs/2026-09-08-p47-research-resume-and-recovery.md#fsd-b03-implementation-through-the-already-selected-comparison)
already allocates this implementation and execution under [B03 card §§2–7](FSD_NATIVE_RENEWAL_LEARNING_B03_SCIENCE_CARD_20260908.md).
[DM readiness intake](FSD_NATIVE_RENEWAL_LEARNING_B03_P47_READINESS_INTAKE_20260908.md)
accepts the committed implementation and independent review. Root integrates the
named accepted commits, then launches and observes these commands. No additional
planning or permission round is needed.

Scientific intake: `/root/dm_fsd_p47_resume`.
Technical collection: `/root/dm_fsd_p47_resume/cm_am_fsd_b03_p47`.
These fresh recipients replace the historical stopped DM/CM identities. Reuse
them for the supplied return route and in-scope corrections. Binding performed
zero admissions, learner/host/model construction, experiment launches or reruns.

## Exact source, staged bytes and setup facts

Accepted source is **f09aa00ba0e6f7c709af188b61be6ff8e7e6bc96**, pushed on
`codex/fsd`, and integrated by Root on main as
`c8f4449b1885663b79bb1bd8c73eee0b0bf4c0c3`. Committed source/test/technical-record
paths are identical between those two revisions. The shared authoring checkout remains
`C:/Projects/HMASD-worktrees/codex-fsd`. The source was fetched through the
configured network shell into a new detached execution cwd:

`/home/wu/hmasd-worktrees/fsd-native-renewal-b03-p47-f09aa00ba`.

Observed remote HEAD equals the full source above and `git status --porcelain=v1
--untracked-files=all` is empty. Node `wsl_4070`, SSH `hmasd-wsl-node`, configured
host `LAPTOP-U9TDKC8A`, Python `/home/wu/.venvs/hmasd/bin/python`. CPU4, FP32 learner
and FP64 host/reward remain the card's scientific boundary; physical host identity
is not the estimand. Existing prospective portability/admission rules apply.

Scripts were committed at **c0e85ea16095c8b93fc9228d3a4f47a4879e9094**:
[G.sh](native_renewal_learning_b03_p47_20260908/G.sh),
[D0.sh](native_renewal_learning_b03_p47_20260908/D0.sh),
[H.sh](native_renewal_learning_b03_p47_20260908/H.sh).
Python extracted each committed Git blob with `subprocess.check_output` and
`Path.write_bytes` into the authoring checkout's
`temp/directions/flexible_skill_duration/exp/p47-command-bytes/`; SCP staged those
bytes at `/home/wu/hmasd-inputs/fsd-native-renewal-b03-p47-20260908/`.
There was no command-body PowerShell text round-trip.

| Script | Bytes | Committed/staged SHA256 |
| --- | ---: | --- |
| G.sh | 543 | `b378875c324689e9eaf02a5bdbe0e48c42db53b5a90827d6f3288add5ab81729` |
| D0.sh | 546 | `b12b798118fc4b4a4ec4dc0c0c8e8d1e1875e2db1454d92d57b231991333351c` |
| H.sh | 757 | `f465570eeb83f1f3c9689061b36d80e72b300caddbea8ad329c1f44bdd0268d2` |

All committed scripts have zero CR bytes. Remote `sha256sum` matches; `bash -n`
parsed all three without executing them. The configured Python, supervisor,
`/usr/bin/time` and `/usr/bin/timeout` are executable. At final binding check,
the scientific parent and all three proposed supervisor task directories were
absent. These are command/setup facts, not new scientific evidence or readiness
machinery in the runner. No production smoke, cost probe or focused-suite repeat
was performed.

## Literal Root commands and complete caps

Run each line separately **once**, G then D0 then H, after each predecessor's
terminal fact. An unfavorable or failed companion does not suppress independently
authorized arm facts. The names below are **proposed**, not accepted handles;
Root records actual supervisor acceptance and reconciles any uncertain response
before another send of the same invocation.

```powershell
ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node "/usr/local/bin/agent-task run fsd_native_b03_p47_G_f09aa00ba '/usr/bin/time -f elapsed_seconds=%e,peak_rss_kib=%M,exit_status=%x -o /home/wu/hmasd-inputs/fsd-native-renewal-b03-p47-20260908/G_process_time.txt /usr/bin/timeout --signal=KILL 60s /bin/bash /home/wu/hmasd-inputs/fsd-native-renewal-b03-p47-20260908/G.sh'"
ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node "/usr/local/bin/agent-task run fsd_native_b03_p47_D0_f09aa00ba '/usr/bin/time -f elapsed_seconds=%e,peak_rss_kib=%M,exit_status=%x -o /home/wu/hmasd-inputs/fsd-native-renewal-b03-p47-20260908/D0_process_time.txt /usr/bin/timeout --signal=KILL 1200s /bin/bash /home/wu/hmasd-inputs/fsd-native-renewal-b03-p47-20260908/D0.sh'"
ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node "/usr/local/bin/agent-task run fsd_native_b03_p47_H_f09aa00ba '/usr/bin/time -f elapsed_seconds=%e,peak_rss_kib=%M,exit_status=%x -o /home/wu/hmasd-inputs/fsd-native-renewal-b03-p47-20260908/H_process_time.txt /usr/bin/timeout --signal=KILL 900s /bin/bash /home/wu/hmasd-inputs/fsd-native-renewal-b03-p47-20260908/H.sh'"
```

Each script changes to the exact detached cwd, then takes fresh on-node physical
and effective memory admission ≥4GiB, joined immediately by `&&` to the runner.
The outer timeout surrounds the entire script: admission, startup/import, all
configuration/model/optimizer creation, five real learning rollouts, final own
evaluator construction/sync, endpoint, pair/reference arithmetic and closed-file
publication. G60/D01200/H900 seconds sum2160. KILL adds no grace or retry; the
cooperative runner timer is supplementary. `time` measures the complete bounded
command and writes outside the scientific root, so it requires no pre-admission
result directory. No cap transfer or post-cap scientific completion is allowed.

Fixed training770403/evaluation770404, two learners×five16×400 and three final32×400
endpoints mean 64,000 training transitions and 96 final episodes. There are no
intermediate endpoints, extra seeds, tuning or automatic successor. The card's
existing historical cost/exposure anchors are reused; actual D0/H optimizer work,
parameter movement and complete wall are unknown until this run.

## Paths, observation and all-outcome return

Relative scientific parent:
`temp/directions/flexible_skill_duration/exp/native_renewal_learning_b03_770403`.
Each G/D0/H child contains `admission.json`, `summary.json` and any arm-local logs.
H consumes only this parent's D0/G summaries. Source, object, card, seed/master
and actual companion identity must remain those of this panel.

For each `fsd_native_b03_p47_<arm>_f09aa00ba`, supervisor evidence lives under
`/home/wu/.agent-tasks/<handle>/`: `task.log`, `status`, `exit_code`, `pid`,
`start_time`, `runner.sh`; tmux session `agent_<handle>`. Complete time/RSS files
are `/home/wu/hmasd-inputs/fsd-native-renewal-b03-p47-20260908/<arm>_process_time.txt`.
Root owns routine observation from its own accepted launch, records exact handle
facts in existing tracking, and uses [EXPERIMENT_MONITOR](../../../project/EXPERIMENT_MONITOR.md).
The expected bound/reminder is the current arm's complete cap above; timeout/exit
is a process fact and does not establish scientific validity.

Return each terminal handle and those exact roots to the fresh CM, with DM copied
or resumed for the complete intake. The CM collects raw summaries, admissions,
complete timing/RSS, full logs and supervisor witnesses, checks the actual counts,
config/infinity/mask-exposure/identity and published primary/reference readback,
then commits/pushes technical evidence. Collection does not rerun the panel or
fill a missing comparison after H's cap. DM applies the original card §5 branches
to all outcomes, scores the recorded prediction and writes the scientific intake
and valid-result Chinese brief when applicable.

Missing/damaged D0 prevents complete H−D0 polarity but preserves H's own credible
endpoint. Missing/damaged G makes the three-policy card incomplete while leaving
independently trustworthy H/D0 facts reportable; weak valid D0 remains in the
comparison. Stop affected execution at completion, cap, nonfinite or a concrete
integrity failure. No retry, replacement pair, extra evaluation, cap increase,
retrospective old-D0 substitution or automatic scientific successor follows.
Engineering conformance and every empirical result remain separate; the claim
ceiling is this single-pair B/EXPLORE comparison, with no stable superiority,
learned-renewal or UAV-transfer conclusion.
