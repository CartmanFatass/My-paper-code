# VSP03 B02 P10 — LF delivery ready for Root

The specifically selected shell-delivery repair is complete. The committed UTF-8 LF
file was copied with configured SCP, inspected on `wsl_4070`, and passed remote
`bash -n` without execution. Root alone may dispatch the one repaired attempt below.
Preparation consumed zero admission checks, models, episodes, optimizer steps or
evaluations. No scientific source, old receipt, prediction or card was changed.

## Artifact and direct byte evidence

Selection: [P10 LF repair](VSP03_B02_P10_LF_REPAIR_SELECTION_20260907.md), implementing
`P10-VSP03-LF-REPAIR-01`. Existing authoring checkout is
`C:/Projects/HMASD-worktrees/dm-vsp03-p07-prep-20260907`, branch
`codex/pro-vsp03-shared-service-convergence-20260906`; it was clean when CM took the index.

- Command artifact: [b02_p10_lf_20260907/run.sh](b02_p10_lf_20260907/run.sh).
- Only file attribute: [b02_p10_lf_20260907/.gitattributes](b02_p10_lf_20260907/.gitattributes),
  `run.sh text eol=lf`.
- Full artifact commit: `4e02c34bc4548f016d1d61ad16fc92430a25117c`, pushed to the configured
  upstream before SCP; push advanced `014b59cdb..4e02c34bc`.
- Committed blob and local `git hash-object` both:
  `441ce73fb10816ba126c01a5b9e72f40d2132ee7`.
- Local and remote SHA-256 both:
  `b3f41a72d91ce296274d609249e4c6de4d4819bd183368be6b1831cc4fbea6b5`.
- Local and remote length847 bytes; CR count0; LF count6; no UTF-8 BOM.
- Remote file: `/home/wu/hmasd-inputs/vsp03-b02-p10-lf-20260907.sh`.

The artifact is the accepted payload with only the selected new output/admission paths
and a Bash shebang. The scientific source/cwd, seed4, node argument, thread limits,
timestamp/admission adjacency, runner,120s timeout and wall/RSS wrapper are preserved.
The actual remote node line ends `--node wsl_4070'` followed by LF; the quote closes
the shell command string and does not enter the argument. There is no CR byte.

## Operations actually performed

Local file writing used .NET UTF8Encoding without BOM and explicit LF bytes; file
contents were never piped through PowerShell stdin. After the explicit-path artifact
commit and successful immediate push, this SCP completed exit0, wall0.7857364s:

```powershell
scp -o BatchMode=yes -o ConnectTimeout=10 docs/research/candidates/vsp_03/b02_p10_lf_20260907/run.sh hmasd-wsl-node:/home/wu/hmasd-inputs/vsp03-b02-p10-lf-20260907.sh
```

One configured SSH read-only Python command read that file's bytes. It printed length,
SHA-256, CR/LF counts, BOM status and the full decoded node line. Its direct output was:

```json
{
  "bytes": 847,
  "sha256": "b3f41a72d91ce296274d609249e4c6de4d4819bd183368be6b1831cc4fbea6b5",
  "cr_count": 0,
  "lf_count": 6,
  "utf8_bom": false,
  "node_line": "/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/projects/HMASD/temp/directions/vsp_03/exp/b02_seed4_p10_lf_20260907_admission.json && exec /home/wu/.venvs/hmasd/bin/python scripts/run_vsp03_b02.py --seed 4 --out /home/wu/projects/HMASD/temp/directions/vsp_03/exp/b02_seed4_p10_lf_20260907 --started-monotonic \"$VSP03_B02_STARTED\" --node wsl_4070'"
}
```

The final syntax-only operation completed exit0, wall0.4851824s, empty stdout/stderr:

```powershell
ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node '/bin/bash -n /home/wu/hmasd-inputs/vsp03-b02-p10-lf-20260907.sh'
```

These observations establish the selected delivery repair, not runtime or scientific
acceptance. The P09 static source review and local-Conda helper tests were not repeated.
No general validator, runtime byte guard or new supervisor was added (`scope: none`).

## Exact one-attempt dispatch for Root

Root runs the following command on the configured node through its ordinary SSH command
argument route. Pass the command-file path; never send the file contents via stdin:

```bash
/usr/local/bin/agent-task run vsp03-b02-p10-lf-20260907 '/bin/bash /home/wu/hmasd-inputs/vsp03-b02-p10-lf-20260907.sh'
```

The P10 handle has not been requested or accepted by this CM. Root resolves any newly
uncertain acceptance against that same handle and never blindly dispatches again.
The file itself changes cwd to the existing detached scientific checkout:
`/home/wu/hmasd-worktrees/vsp03-b02-p09-00ebefa5823dbb41e64aed11b90ba26a8ff97020`.
Scientific source SHA is still `00ebefa5823dbb41e64aed11b90ba26a8ff97020`, distinct from
the delivery artifact commit. No new source checkout or scientific input is needed.

New output is `/home/wu/projects/HMASD/temp/directions/vsp_03/exp/b02_seed4_p10_lf_20260907`;
the adjacent fresh admission is its sibling `b02_seed4_p10_lf_20260907_admission.json`.
The unchanged outer timeout encloses timestamp, admission, imports, the sole8-episode
check, both learners, all six final sets including R/R0, publication/readback and exit.
The existing `/usr/bin/time` observes that whole timeout command. P10 grants one
complete120-second repaired attempt and no retry, fallback, extra seed or cap expansion.

## Collection and technical acceptance

Root launches and observes the accepted handle, then returns authoritative terminal
status/exit and supervisor evidence locations to the same CM
`/root/dm_amx_vsp03_next/cm_vsp03_b02`. After terminal status, CM physically copies the
output directory to `C:/Projects/HMASD/temp/directions/vsp_03/exp/b02_seed4_p10_lf_20260907`,
with the admission receipt and supervisor evidence beside it, including complete
stdout/stderr and outer wall/RSS. CM performs technical acceptance and writes a new
`VSP03_B02_P10_RESULT_EVIDENCE_20260907.md`; the earlier PATH_UNAVAILABLE record
`VSP03_B02_RESULT_EVIDENCE_20260907.md` remains unchanged. DM then performs the
all-outcome scientific intake and Chinese brief.

Full conditions remain [Root handoff, Acceptance and collection](VSP03_B02_ROOT_HANDOFF_20260907.md#acceptance-and-collection-for-return):
fresh physical/effective memory at least4GiB, terminal exit0 and complete wall within120s,
38920 joint episodes/1556800 team ticks/3113600 target transitions, two model constructions,
256 steps,128 curve rows and2048 evaluation episodes per learner, the8-episode zero-step
check, six1024-world endpoints plus paired differences, all declared primary/secondary
comparisons, exposure, final weights and in-run readback. Required files are `summary.json`,
`focused_check.json`, `T_curve.jsonl`, `G_curve.jsonl`, `T_final.pt`, `G_final.pt`,
`T_greedy.json`, `T_stochastic.json`, `G_greedy.json`, `G_stochastic.json`, `R.json`,
`R0.json` and `paired_differences.json`. Another failure returns every available narrower
fact promptly, without retry or scientific polarity. A complete output retains every sign.

Preserve accepted P09 handle `vsp03-b02-p09-20260907`, exit2, its1.59s wall and old
receipt/output paths separately, along with the earlier pre-connection PATH_UNAVAILABLE
record. P09's receipt does not admit P10. Neither prior failure is overwritten or
reported as a result of the corrected file.
