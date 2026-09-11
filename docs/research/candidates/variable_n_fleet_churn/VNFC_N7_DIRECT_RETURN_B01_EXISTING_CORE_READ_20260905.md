# B01 existing core read and next-path comparison

DM authorized one short read-only lookup for formal01 PID1702677, its timestamp and WSL capture.
The targeted remote read began2026-09-06T00:04:41Z and completed by00:06:02Z. No model,
simulation, native build, replay, new timing run or source change occurred. The later arithmetic
below only applies stored check02 unit timings to proposed counts. No next invocation is selected.

## Existing capture recovered for inspection

The matching651,046,912-byte file exists at:

`/mnt/c/Users/wu/AppData/Local/Temp/wsl-crashes/wsl-crash-1788652306-1702677-_home_wu_.local_share_uv_python_cpython-3.10.21-linux-x86_64-gnu_bin_python3.10-11.dmp`

Its mtime is2026-09-06 07:51:54.117694200+0800. `file` identifies an ELF64 x86-64 core from
the selected formal runner; its process ID and timestamp match the kernel/supervisor record.
The original remains in place, not copied into Git or deleted. GDB inspected the core with
the recorded Python executable, from the actual execution cwd so its native library resolves.
Debuginfod downloads were disabled; no packages or debugger helpers were installed.

Raw backtrace: `evidence/b01_formal_20260905_01/existing_core_backtrace.txt`.
The faulting main-thread stack is:

```text
subtype_dealloc
builtin_sum
cfunction_vectorcall_FASTCALL_KEYWORDS
call_function / _PyEval_EvalFrameDefault / _PyFunction_Vectorcall
...
THPFunction_apply (libtorch_python.so)
```

The two other captured threads were waiting in PyTorch autograd ReadyQueue and CUDA-driver
polling. This stack does not show a native environment function actively executing at the fault;
it cannot exclude earlier memory corruption. GDB warned that the core may not match the supplied
executable and that libcuda build ID differed, despite using the recorded executable path/identity;
retain those limitations. The available GDB has no `py-bt` command and no matching Python GDB
helper was found under the inspected interpreter. Therefore no Python source line or object
identity has been recovered. The fault is not reproduced by this read.

The reused R09 `_ExactRosterMean.forward` invokes `exact_binary64_mean`, whose implementation
uses `sum(Fraction.from_float(...), Fraction())`. Its custom autograd/Python-sum structure is
consistent with the captured chain. That is a **candidate call path inference**, not a proved
faulting Python line or an identified defect. Neither replacing the mean nor changing HMAC,
Torch, Python, dtype or native semantics is justified by this evidence alone.

## Minimal alternatives, not added launch prerequisites

| Option | Concrete work and value | Limit |
| --- | --- | --- |
| Longer non-target diagnostic | Eleven rounds is the smallest integer beyond the ten completed formal rounds. Retain32 episodes/round,4 PPO epochs/minibatch24,64 evaluation episodes at0/5/11 and64 BCRH once. That is352 steps/arm,704 training+448 evaluation episodes,276,480 native ticks. Check02-unit planning estimate approximately91.91s. | Non-target seeds change the trajectory, so11 rounds may not reproduce the failure. Current CLI profiles are2 or64 rounds; this would need an explicitly frozen diagnostic configuration/entry, not a covert formal change. |
| Frozen formal with `-X faulthandler` | Same scientific source/configuration/seed and full comparison, while Python prints available thread stacks if the fault recurs. It retains the chance of producing the B result. Original conditional complete projection remains approximately282.61s, plus unmeasured failure-handler overhead. | Python3.10 faulthandler gives Python frames, not a complete native root-cause proof; corrupted state may limit its output. It does not fix the error or guarantee completion. |

For the purpose of obtaining a Python fault stack, the formal alternative provides the same
kind of observation as the non-target diagnostic and exposes the actual failed trajectory.
There is **no identified primary-integrity dependency requiring the non-target run first**.
The existing check already exercised reward, public information, actions, actual learning and
publication. The unresolved risk is execution survival to the final measurement, not a known
wrong primary metric or comparator. Unknown root cause is not an extra automatic prerequisite.

If DM selects formal with fault observation, changing the interpreter invocation to
`python -X faulthandler scripts/run_vnfc_n7_direct_b01.py ...` need not alter the frozen model,
RNG, optimizer or episode semantics. Preserve one scientific process and all existing settings;
no silent runtime/library substitution. It must account for87.86s already spent and at most
2612.14s remaining formal investment. No new2700s allowance, automatic retry or new seed follows.
The DM selects between these paths; CM has executed neither.
