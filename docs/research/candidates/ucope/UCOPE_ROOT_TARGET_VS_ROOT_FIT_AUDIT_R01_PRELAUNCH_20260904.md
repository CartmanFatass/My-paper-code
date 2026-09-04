# UCOPE root target-versus-fit R01 — prelaunch admission record

- Object: `UCOPE-A-RECON-THREE-WITNESS-ROOT-TARGET-VS-ROOT-FIT-AUDIT-R01`
- Evidence class: `A/RECON`
- Status: `RESOURCE_ADMISSION_REFUSED / NOT_LAUNCHED / NO_RESULT`
- Implementation SHA: `997f49c3cbefffee88d83d7b7de750a078d1a1ca`
- Date: 2026-09-04 PDT

## Accepted engineering boundary

CM and an independent static reviewer accepted the bounded implementation at the SHA above. The
final CM suite passed `8/8`; the committed-byte prelaunch suite first reached five passing tests
and three setup errors because the ignored `--basetemp` parent directory did not exist, then passed
`8/8` in 5.64 seconds after that directory alone was created. The setup failure did not execute or
change scientific code. The committed-byte outcome-free cost command reported:

```text
replayed_environment_episodes=983040
replayed_environment_transitions=4915200
live_exact_root_solves=12
policy_pairs=6
projected_total_seconds=185.481
total_machine_time_cap_seconds=185.481
within_cap=true
```

The retained input was directly bound before admission at 1,273,684 bytes and SHA-256
`1c8b1d217fc924271da62061f7226642a3d040995aba069cabb5df9ff336b676`.

## Direct admission observation

The experiment operator took one fresh central memory receipt immediately before the proposed
invocation:

```text
runtime_receipt=temp/directions/ucope/exp/root_target_vs_root_fit_audit_r01_20260904_admission.json
preflight_exit=6
minimum_available_bytes=4294967296
available_physical_bytes=3893518336
effective_available_bytes=3893518336
physical_floor_pass=false
effective_floor_pass=false
passed=false
reason=available physical memory is below 4 GiB
```

The operator therefore did not invoke the runner. Directly observed invocation facts are:

```text
accepted_result_bearing_processes=0
pid=none
result_root_created=false
summary_created=false
stdout_created=false
stderr_created=false
```

This is a resource-admission refusal, not a scientific or engineering result. The object remains
unconsumed; there is no mechanism polarity and no result branch to intake.

## Decisions this admission produces

### Decision 1 — disposition after refused admission (object tier)

Options:

- **(a) Queue the unchanged committed invocation.** Wait until read-only availability indicates
  that a new fresh receipt can satisfy both 4 GiB floors; then use a new receipt path and start the
  still-unused single authorized runner invocation exactly once.
- **(b) Park the object indefinitely.** Preserve the implementation but do not seek another
  admission opportunity.
- **(c) Lower or bypass the 4 GiB floor.** This would violate the repository resource-admission
  contract and is not an admissible unattended action.

Recommendation: **(a)**. It preserves the frozen object and is fully reversible; the refused
preflight created no scientific state.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**

## Exact resume boundary

Before resuming, keep the implementation and science card unchanged, require the result root and
stdout/stderr paths to remain absent, and use a new receipt path such as
`temp/directions/ucope/exp/root_target_vs_root_fit_audit_r01_20260904_admission_02.json`. Take that
fresh receipt immediately before the runner and require both recorded availability values to be at
least 4 GiB. The result-bearing invocation allowance remains unused; no retry of a scientific
process has occurred.
