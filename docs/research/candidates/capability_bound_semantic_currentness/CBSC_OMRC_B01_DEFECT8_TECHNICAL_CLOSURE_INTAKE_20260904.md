# CBSC-OMRC-B01 defect 8 technical closure intake — 2026-09-04

- Direction: `capability_bound_semantic_currentness`
- Scientific object preserved: `CBSC-OMRC-B01` (`B/EXPLORE`)
- Engineering disposition: **ACCEPTED_COMPLETE**
- Scientific-result status: **none**
- Implementation commit: `4f8fe0f6eaca799a79e05fe75ec408acb05f979f`
- Historical failure bytes: `81dfbd72ef038db67119e5ecb7a9b61b944bbb8f`
- Independent review: **PASS**
- Final committed-byte profile: **17 passed**

This intake closes only the publication-path engineering defect selected in
`CBSC_OMRC_B01_DEFECT8_DECISION_INTAKE_20260904.md`. It does not reinterpret attempts `r01` through
`r05`, produce a formal B artifact, consume a scientific object, or authorize `r06`.

## 1. What I checked

I checked the CM return against the selected option, the unchanged 512 MiB durable cap, the literal
binding and metrics-only contracts, evidence-spec section 11, the one carded engineering-scope item,
the direct failure reproduction, the final diff, the independent review, and the exact-SHA remote
profile receipts.

The CBSC source, runner, and affected test surface at entry was byte-identical to historical commit
`81dfbd72ef038db67119e5ecb7a9b61b944bbb8f`. The recorded unified profile was then run directly on
those bytes. It reached the publication consumer and failed after `3,360.13` seconds with one test
failure. The first observed exception was:

```text
MetricsArtifactError: derived field names/order differ
```

The test had expected the later consumer-reconstruction refusal. Direct source inspection showed
that canonical JSON serialization had sorted object keys while `_validate_null_packet` incorrectly
required insertion order. This is a reproduced post-learner validator/publication defect. It has no
mechanism polarity and does not consume the B object.

## 2. Accepted implementation

The repair makes `summary.json` the standalone interface for the quantities the frozen result rule
actually reads. Complete worker and replay canonical result payloads remain durable in deterministic
stdlib gzip containers (`compresslevel=9`, `mtime=0`, empty stored filename). Formal locators refer
only to `.json.gz`; readers decompress and recheck canonical JSON, the decoded-source SHA, pointer
identity, shape, dtype and nonzero facts. There is no raw-JSON fallback.

The formal validator independently reconstructs the summary from the 15 canonical tables and
reconstructs RAW competence from truth, terminal RAW policy and curves. A coordinated mutation of
the summary and nearby raw fields is still refused. The artifact continues to retain the 15 tables,
all checkpoints, B0 evidence, admission receipts and telemetry. Descriptor/audit SHAs bind the
decoded canonical bytes; the artifact inventory separately binds the stored gzip bytes.

The historical null-packet rule still requires the exact field set and literal-null values. Only
the erroneous dependence on object insertion order was removed. The descriptive reader accepts the
already canonical lower-case eight-hex FP32 representation while continuing to reject noncanonical
case, NaN and infinity.

The one carded section-4 item is a static incident-root path budget. Its projection includes the
staging root, incident root and worker/replay `.json.gz` paths. Windows enforces `MAX_PATH`; Linux
records the projection without imposing a Windows-only refusal.

Formal scientific semantics are unchanged: three seeds, 448 held-out tapes per seed, 48 updates,
eight episodes per update, four epochs, four minibatches, the original FP32 learner, PPO constants,
RNG addressing, host, comparator arms and checkpoint format. The fixed TEST_ONLY seam uses the same
real components with six held-out tapes and 48 one-episode updates; callers cannot select these
counts or enable that seam on the formal path.

## 3. Verification and receipts

Independent reviewer findings:

- no material finding after the final separator-neutral path assertion;
- source diff `+479/-109`, test diff `+279/-70`, runner diff `0`;
- conservative publication/path routing `106/479 = 22.1%`, below the 30% budget;
- no unrequested retry/lease/resume, registry, incident tree, compatibility fallback, provenance
  predicate, schema layer, telemetry layer, or repeated checkpoint guard.

The final profile ran on the configured remote node in a detached worktree at exact pushed commit
`4f8fe0f6eaca799a79e05fe75ec408acb05f979f`. Its direction-local basetemp was
`temp/directions/capability_bound_semantic_currentness/test/d8final4`. Task
`cbsc-d8-profile-4f8fe0f6e-04` completed `17 passed` with one pytest-configuration warning in
`23.67` seconds; the unified test took `18.77` seconds. The task ran no preflight, scientific
runner, `r06`, model training, or B invocation.

Remote GitHub HTTPS was unavailable during preparation. Because the commit was already pushed, the
same complete-history Git object was moved as a request-specific bundle rather than copying a
working tree. Local and remote bundle SHA-256 were both
`2555b847ec385667fbe091bf622f770a4eee1266feb7024bf5927b7b962a9647`; bundle verification passed,
and detached HEAD matched the pushed commit with a clean tracked tree. The fixed Pro archive link
was checked after sparse-checkout preparation: 12 files were present and the three response
digests matched their recorded values.

Preparation attempts are retained transparently:

- task 01: launcher quoting failure, exit 4, zero tests collected;
- task 02: missing sparse `docs` surface and missing basetemp parent, 6 passed, 1 failed and 10 setup
  errors before a complete profile;
- task 03: sparse-checkout refresh removed the ignored archive link, 10 passed and 7 failed; the
  unified path stopped at fixed evidence staging;
- task 04: complete preparation and the accepted green profile above.

These are reproduced remote-preparation failures, not source or scientific results. Each prior task
was terminal before the next exact retry and no duplicate process remained.

## 4. Durable-size evidence

Read-only projection over the historical r05 bytes gives:

| quantity | bytes |
| --- | ---: |
| complete raw worker/replay payloads | `238,753,173` |
| deterministic gzip projection | `18,628,924` |
| retained artifact before summary/manifest | `496,554,518` |
| headroom below 512 MiB | `40,316,394` |

The TEST_ONLY remote artifact's manifest total was `26,514,440` bytes, with `26,440,611` bytes in
its inventory and a `16,974`-byte summary. These observations support the storage representation and
the test path only. The r05 calculation is not a formal production artifact. The production code
still performs a prospective census and a final actual-file census and refuses publication above
`536,870,912` bytes.

Gzip stored bytes may differ across zlib builds; decoded canonical JSON and its SHA are the
cross-platform evidence invariant. This does not weaken the actual stored-byte inventory or cap
check for a particular artifact.

## 5. Bounded reading and remaining risk

Direct observation: defect 8 was reproduced on the recorded bytes, repaired without changing the
frozen scientific surface, independently reviewed, and covered by a green exact-commit Linux
publication profile.

Inference: the bounded publication/codec/path surface is prospectively usable on the configured
remote node. Test success cannot establish learner competence, a formal artifact, CBSC value,
structured-over-RAW advantage, any result branch, or permission to launch B.

The runner's non-Windows descendant-process kill behavior remains outside this bounded change. It
must be resolved separately before any future remote scientific invocation that relies on that
supervision behavior. No `r06` invocation is queued here; the current Root assignment moves next to
the read-only headroom evidence census.

## 6. Decisions this intake produces

### Decision 1 — exact committed-byte transport after remote GitHub failure (Object tier, technical)

Options:

- **(a)** transfer the already pushed exact commit as a verified Git bundle, build the detached
  remote worktree from that object, and continue the engineering profile;
- **(b)** stop at a remote-profile blocker because GitHub HTTPS is unavailable; or
- **(c)** copy a working-tree source snapshot or silently fall back to a local profile.

Recommendation: **(a)**. It preserves the pushed commit identity and remote-first route without
moving uncommitted source. Option (b) would leave a safely recoverable but unresolved profile;
option (c) would weaken provenance or routing discipline.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Provenance label:
`OWNER_DELEGATED`. The action was reversible and request-scoped.

### Decision 2 — accept or quarantine the bounded closure (Object tier, technical)

Options:

- **(d)** accept defect 8 as technically closed at the exact pushed commit and preserve the
  scientific object unlaunched;
- **(e)** quarantine the implementation despite the reproduced failure, independent PASS and green
  final profile; or
- **(f)** expand this closure to the unrelated Linux process-tree supervisor or launch `r06` now.

Recommendation: **(d)**. All requested engineering boundaries are directly covered. Option (e)
would discard conformant evidence; option (f) exceeds the card and current Root assignment.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (d).** Provenance label:
`OWNER_DELEGATED`. The scientific object remains unlaunched and unchanged.

