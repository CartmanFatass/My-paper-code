# UCOPE B05 transport quoting correction — technical record

Replacement CM: `/root/cm_ucope_p11_b05_collect`, assigned by Root under P11 terminal-failure disposition. This continues the already-started B05 execution task; no model-comparison enrollment or source implementation is involved.

## Preserved failed attempt

Accepted handle `ucope-shared-return-b05-seed6701-20260907` on `wsl_4070` ended with exit code **2**, at `2026-09-08T05:07:12+08:00` (2026-09-07 21:07:12 UTC), with supervisor duration **0 s**. The [verbatim log](b05_transport_correction_20260907/task.log) records `unexpected EOF while looking for matching` a single quote at `runner.sh: eval: line 8`. The [saved runner](b05_transport_correction_20260907/runner.sh) retains the exact malformed command, alongside copied `exit_code`, `status` and `start_time` files. Original evidence remains under `/home/wu/.agent-tasks/ucope-shared-return-b05-seed6701-20260907/`.

Inspection of the saved eval argument shows its inner `bash -c` string lacks the closing quote. Shell parsing failed before admission or runner execution. Read-only SSH collection also confirmed both B05 seed output roots absent and the source checkout HEAD still `71433bfabb70481def4329e622a838fa0cd9eeec`. There is no admission receipt, learner output or primary for this failed command; it is a transport failure with zero scientific exposure, not a scientific result. Seed 6702 remains blocked until the corrected seed-6701 continuation is reconciled.

## Smallest correction

The [seed6701 command artifact](b05_transport_correction_20260907/seed6701-command.sh) contains exactly the command argument decoded from the frozen [B05 handoff §2, seed 6701](UCOPE_SHARED_DATA_RETURN_MODEL_B05_EXECUTION_HANDOFF_20260907.md#seed-6701), with one terminal LF. Staging this file and passing its path to Bash removes the nested command transport quoting that was damaged. No runner, source, supervisor or scientific argument is changed.

- Encoding: UTF-8 without BOM, LF only, **687 bytes**.
- SHA-256: `24ab424d7868d229b0a9c3375b9feb1560140387dbdb1f0e46817eb23de1f78e`.
- Suggested remote artifact path: `/home/wu/hmasd-inputs/ucope-b05-seed6701-command-20260907.sh`.
- Payload for Root's separately selected distinct supervisor handle: `/bin/bash /home/wu/hmasd-inputs/ucope-b05-seed6701-command-20260907.sh`.

Root owns any staging and continuation authorization/handle selection. The original failed handle must not be overwritten or reused. This correction has not staged or executed the payload and authorizes no additional seed or invocation.

## Acceptance and unchanged boundaries

Local `C:/Program Files/Git/bin/bash.exe -n <artifact>` returned 0. A second syntax-only Bash check of the decoded inner `-c` string returned 0. Python standard-library `shlex.split` verified that the artifact is byte-for-byte the frozen handoff's decoded supervisor command plus terminal LF and that its outer argv retains time, the 600-second KILL timeout and Bash flags. Byte inspection verified UTF-8/no BOM/LF and the digest above. These checks never executed the payload, imported experiment code, or called the environment/learner. They establish command syntax and frozen argument identity; runtime admission and successful continuation remain unobserved.

Preserved: exact source SHA above; order 6701 then 6702; existing `run(out, seed, object_id, batches)` API with B05 identity and 512 batches; binary64 scalar order/RNG/information/metrics; full three-policy evaluation; all outcomes; remote cwd `/home/wu/hmasd-worktrees/ucope-shared-return-b04-20260907`; each fresh destination admission immediately adjacent to its runner by `&&`; outer 600 s per complete dataset and 1200 s pair cap. The existing cost projection and prior publication-path coverage in card §5 remain unchanged. No new timing or research check was run. Whole runtime and resource conformance for the pair remain pending.

ENGINEERING_SCOPE_SPEC §4 additions: **none**. This is a fixed command artifact and evidence record, with no new runtime implementation or machinery. Read-only SSH/SCP evidence collection and the required Git push were expressly clarified by Root as allowed; no network experiment or endpoint probe occurred. Scientific intake remains with `/root/dm_ucope_p10_pair_prep`; Root receives these corrected bytes for the specified continuation route.
