# SCDMP D6 duration-action relevance A01 — attempt-01 intake (2026-09-04)

- Object: `SCDMP-D6-DURATION-ACTION-RELEVANCE-A01`
- Evidence class and claim ceiling: A/RECON; finite native duration-action relevance on the exact
  frozen six-state/action/tape panel only
- Attempt launch SHA: `3b462583837c4f7bff440afce6349b91d2044c6d`
- Attempt disposition: **technical quarantine; no scientific observation and no polarity**
- Repair commit: `8abe26362816f0bb25e84496361a1a447cc4e72e`

## What this intake checked

1. The detached invocation used seed `9029`, the exact frozen runner command and a previously
   absent root. Its fresh admission receipt passed with physical and effective available memory
   both `4,887,252,992` bytes, above the `4 GiB` floor.
2. The only file under the result root is `summary.json`, SHA-256
   `c25bd195f9fa65eadc71fd812b048895dbdafbc4f067552bbb3c8b259787a5a2`. The admission receipt
   SHA-256 is `54017ece1d2c41f5a24f888e67c61b1d243217f2ba55f86bf4a5b84ec0612368`.
   Stdout contains only the admission JSON and stderr is empty.
3. The summary reports `admission_passed=true`, `integrity_valid=false`,
   `branch=A_INVALID_EVIDENCE`, wall `8.84559470001841 s`, missing peak RSS with
   `resources_unmeasured=true`, and the recorded `WinError 267` native-DLL path. It contains no
   source-trajectory, renewal, state, candidate-mission, evaluator-call, transition, terminal,
   `S/V/B7/B13/D/R7/R13/W_j/W`, or endpoint-family fact.
4. CM reproduced the failing step over the recorded launch bytes without preflight, source census
   or any scientific coordinate. Native compilation and `ctypes` loading completed and the probe
   printed `loaded`; leaving `TemporaryDirectory` then raised `WinError 5` while deleting the
   still-loaded DLL and ended with the same `WinError 267` path. This direct reproduction classifies
   the attempt as a Windows DLL lifecycle/temporary-directory cleanup failure, not a native
   equation, source-population or endpoint result.
5. The repair changes only `Host.__exit__`: restore the prior ABI provider, transfer and zero the
   loaded handle, then call Windows `FreeLibrary` before temporary-directory exit. The generated
   native source, equations, precision, RNG addresses, state/action/tape order, endpoint arithmetic,
   counts, result rule and publication schema are unchanged. Independent high-risk review found no
   commit blocker; research code is `724/2,000`, runner `172/600`, and conservative orchestration is
   `217/724 = 29.9724%`. `scope: none`.
6. The single post-repair pytest invocation returned `8 passed, 1 failed`. The seven rule cases and
   technical runner smoke passed. The new directory-deletion regression failed before native
   compilation because pytest's nested temporary path was 261 characters and `write_text` raised
   `FileNotFoundError`; the fixture was then statically narrowed to the short system temporary
   directory and was not rerun. This fixture failure neither verifies nor contradicts final
   directory deletion. The passing technical runner smoke did execute the repaired
   `Host.__exit__/FreeLibrary` path and observed two missions, 687 transitions, no scientific branch,
   `t_native_mission=0.003209300004527904 s`, and
   `P=67.4070644104504 s < 1,800 s`.
7. No attempt-01 state, DLL, count, endpoint or partial output will be resumed, salvaged, copied or
   interpreted. A fresh run at the repair SHA is a new evidence attempt of the unchanged A object.

## Rule applied verbatim

The first matching frozen branch is:

> **`A_INVALID_EVIDENCE`** — outside the intended source-population failure below, native execution
> or endpoint arithmetic is incomplete/nonfinite; a required cell is missing or duplicated; a
> state/tape is outcome-replaced; the declared source/tape law is not executed; the hard cap is
> crossed before completion; transition/evaluator counts are zero or incompatible; or publication
> is incomplete. No scientific observation; repair only.

The attempt stopped before scientific counts existed, so this rule produces no duration-action
reading. A/RECON has no consumption state; the object remains unanswered.

## Observation, bounds and flags for the owner

Direct observation is limited to successful resource admission, the invalid summary and CM's exact
failure reproduction. The strongest support for a fresh attempt is the reproduced lifecycle cause,
the narrow reviewed repair and the passing toy path through `Host.__exit__/FreeLibrary`. The
strongest contradiction is that the newly shortened exact directory-deletion regression has not
been executed. That residual is an engineering risk for the next invocation, not evidence against
the A question and not a new launch condition. If it recurs, the fresh attempt is quarantined with
no polarity under the same rule.

No resource-budget breach occurred. Peak RSS is unmeasured, which is permitted because the claim is
not a resource claim. No §5 engineering budget was breached and no unrequested machinery was added.

## Decisions this intake produces

Options:

1. **(a), recommended:** quarantine attempt-01 permanently, accept the narrow reviewed repair and
   appended current projection, and launch one fresh attempt-02 at commit
   `8abe26362816f0bb25e84496361a1a447cc4e72e` under a new root and fresh 4 GiB admission.
2. **(b):** park the unchanged A object solely for an additional technical pass, despite the
   executed repaired `Host.__exit__` smoke and without a section 4 integrity fact that requires a
   new launch gate.
3. **(c):** change the frozen host, coordinates or result rule in response to an operator-lifecycle
   defect, creating a different scientific object.

Recommendation: (a). It preserves every scientific byte, treats attempt-01 as nonpolar and uses a
fresh SHA/root. Options (b) and (c) either add an unrequested repeat gate or alter the question.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Provenance label:
`OWNER_DELEGATED`. This reversible decision authorizes exactly one detached invocation:

```text
python scripts/run_scdmp_d6_duration_action_relevance_a01.py --seed 9029 run
  --output-root temp/directions/semigroup_consistent_duration_model_policy/exp/d6_duration_action_relevance_a01/A01_ATTEMPT_02_20260904
  --receipt temp/directions/semigroup_consistent_duration_model_policy/exp/d6_duration_action_relevance_a01/A01_ATTEMPT_02_20260904_admission.json
  --projected-seconds 67.4070644104504
```

All attempt-02 target paths must be absent before launch. The runner must take the fresh admission
before native state creation. No retry, resume, reused attempt-01 path, changed coordinate or
result-aware extension is authorized.
