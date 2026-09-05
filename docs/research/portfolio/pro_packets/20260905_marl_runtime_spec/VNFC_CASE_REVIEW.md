# VNFC case and proposed object appendix

Status: DRAFT_NOT_OPERATIVE. This is an engineering investment proposal for Portfolio Pro,
not permission to run. The accepted direction decision and exact response are in
`docs/research/candidates/variable_n_fleet_churn/VNFC_R03_COST_CONVERGENCE_INTAKE_20260905.md`
and its linked four-artifact archive. The source-library study is being completed alongside it.

## Facts and competing interpretations

One accepted synthetic calibration took 4.096142977999989 seconds. The full original R03
planning estimate was 347623.18427552027 seconds, over 128 times the original 2700-second
wall cap. About 97.3 percent is complete BCRH calls; the remaining generic solver alone was
projected at 9152.017350242992 seconds. Source already uses C++20/-O2 and a coarse ctypes
call. It retains serial loops under the original one-process/one-thread requirement.
No full census implementation, target-world endpoint, learned model or new RNG draw was
produced by the calibration. This is a specific implementation's cost evidence, not an
optimized lower bound or a no-headroom result. No library has measured this VNFC workload.

Pro selected one changed, outcome-blind execution feasibility assessment. The constructive
possibility is exact per-class selection using public failed-zone separation, cross-call
immutable public-input weight reuse, and one fixed native batch team. The strongest contrary
fact is the enormous existing gap: removing only one cost term would still exceed the cap.
The feasibility of the full unchanged computation remains unknown.

## Prospective resource proposal to decide

Read-only observation of the configured `wsl_4070` node on 2026-09-05 found 20 online logical
CPUs and allowed list 0–19. The user slice and user-1000 slice each reported `cpu.max` as
`max 100000`; the root cgroup had no cpu.max file. This observes those limits only, not a
reserved exclusive CPU allocation or every possible descendant restriction. `free -b`
reported total memory 16,568,725,504 bytes and available 15,341,309,952 bytes at the first
probe. It is a planning snapshot, not the fresh actual-invocation memory admission.

The concrete proposal is a single process with four total native compute participants and
one fixed batch width of eight independent full calls, deterministic tail handling, no
extra concurrent compute pool, and no changes to the frozen scientific inputs or device.
The coordinator must not become an extra fifth compute participant. Existing BLAS/Torch
background parallelism and any compiler invocation must be accounted for; no hidden worker
pool follows from choosing four. Inspect actual native scratch/output ownership before
implementing and report its memory bound. If this fixed configuration does not fit, return
the gap rather than search widths, threads or nodes.

Proposed one-time engineering evaluation allowance: at most 60 seconds elapsed wall and
300 aggregate CPU seconds for the complete invocation, including required import/build,
comparison, batching, checks and publication; peak RSS reported, with the existing fresh
4 GiB physical/effective admission. These are explicit proposed ceilings, not measurements
or inherited leftover calibration time. Pro must accept or replace the exact numbers and
the minimal CPU-accounting scope under Engineering Scope §4. No new general telemetry or
scheduler is proposed. An incomplete CPU account cannot establish compliance with that
resource allowance. The original full census wall cap remains 2700 seconds.

Before any measured output, the CM must freeze one deterministic non-target fixture
covering all six epochs, equal/different public-weight tuples, varying physical states,
complete candidate records, ties and the full publication path. The exact fixture and
one invocation are part of the implementation assignment, not optimized after timings.
Use the original exact arithmetic, all independent checkers/enumerators, canonical tie
rules, all four selected maps and the same one-global-epoch policy class. The already
completed six-call calibration is not repeated as a new timing object.

## Acceptance and stop boundary

The implementation must justify and verify each reuse/decomposition on this exact object.
Preserve all 94,128 continuations, 376,688 complete calls, 738,685,168 candidate rows and
9,418,560 ticks in its full-work accounting; exact choice simplification does not skip
native consequences. Checker independence cannot be traded for speed. Retain deterministic
logical merge/error order and no administrative-world label in the causal decision key.

Use new complete-batch measurements, not old serial timing divided by four. Include all
setup, history, exact selection, ties, map construction, recording, publication and uncovered
work; preserve the original factor two and 60-second full-run fixed allowance. Only complete
equivalence/coverage, compliant resource use and a full projection strictly below 2700 seconds
support entering original R03 full implementation and technical acceptance. It is not a
headroom result or an automatic full launch. Otherwise stop this one investment and return
the exact gap to the existing Convergence node; no automatic extra optimization or timings.

Original source budgets are cumulative: 483 non-test source lines and 58 runner lines already
exist. The 2000/600 limits and existing orchestration/test requirements remain unless this
proper-node decision specifies an exact object exception. No silent budget reset or inheritance
from CBSC/N3. No new scientific RECAST, lifecycle/priority change or general MARL theorem.

## Questions the Portfolio decision must settle

Decide whether this exact E01 is worth the additional engineering investment under the new
source-backed runtime spec. If yes, give the final object-limited change to the single-thread
restriction, exact fixed team/batch and CPU/wall ceilings, allowed minimal machinery/accounting,
and implementation/verification/stop boundary. If not, give the specific unresolved evidence
or investment reason without turning runtime into a scientific negative. The owner has
already delegated execution of a complete final plan and its stated spec/AGENTS updates;
no repeated per-item approval is requested.
