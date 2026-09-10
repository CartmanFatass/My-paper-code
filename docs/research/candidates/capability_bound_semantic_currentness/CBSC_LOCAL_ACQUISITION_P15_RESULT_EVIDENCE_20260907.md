# CBSC P15 — E0 local metadata evidence

**Local direct header access is observed; no complete acquisition command is
accepted.** Four HEAD requests returned HTTP 200 with no body read. No matching
complete Torch/Triton input was identified in the inspected local cache paths.
The exact bounded setup/import route remains incomplete under P15's scope.

## Assignment, source and reading rule

Class A/RECON; [P15 card](CBSC_LOCAL_ACQUISITION_P15_SCIENCE_CARD_20260907.md)
at `9339bb925`, **Question and prospective reading / Inputs, bounds and exposure**.
Authority: the CBSC section of the P15 handoff at main
`25b1a88b162ae137b5071ca2d9acb87007fb3ea9`. This authorizes bounded local metadata
inquiry after P11's yield, while preserving its exhausted acquisition allocation.

Card reading applied verbatim:

> A successful header response alone establishes access, not body delivery or a
> repair. Local-cache absence is limited to the inspected roots. If no supported
> change is found, yield without a new execution command/budget.

The card's MEI is a complete metadata-supported proposal with exact input,
whole-work command and budget. The narrower new access condition is supported;
the complete command is not supplied by the inspected facilities. Retain those
different ceilings. No wheel-body or candidate invocation was selected here.

The historical 23 pins, two exact cp312 bodies, 21 retained remote containers and
complete install/metadata semantics remain those of payload
`71131d728a0b5f04663301e3d838e699ce70af41`, separately from preflight
`ec8866b3968fcb1566976ce405d7c552d4d9a5de`. Nothing rewrites the failed full-body
attempt, old partial files, RAW-only B04 or missing STRUCT comparison.

## Actual request evidence

Client: local Windows PowerShell using existing `System.Net.Http.HttpClient`,
HEAD with ResponseHeadersRead, strict default TLS validation, no default
credentials/cookies, no automatic redirects/retries. Each client used a 30 s timeout
and a 64 KiB response-header limit, below the 2 MiB request allowance. No response
body was consumed. Requests 1–2 explicitly used the observed localhost:7890 HTTP
proxy; 3–4 used `UseProxy=false`. Global configuration was not changed.

All requests occurred on 2026-09-08 UTC, September 7 PDT. The times below are the
request's local receipt timestamps, not the older HTTP Date header.

| Request | Artifact / local condition | Start UTC | HTTP | Wall s | Serialized header bytes | Body bytes read |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 1 | Torch / explicit proxy | 00:33:53.2448412 | 200 | 1.0556872 | 647 | 0 |
| 2 | Triton / explicit proxy | 00:33:54.3109725 | 200 | 0.9318604 | 643 | 0 |
| 3 | Torch / direct | 00:34:35.0681078 | 200 | 1.1191192 | 647 | 0 |
| 4 | Triton / direct | 00:34:36.1959699 | 200 | 1.1469363 | 643 | 0 |

All responses were HTTP 1.1 with AmazonS3/CloudFront headers and these source facts:

| Artifact source | Declared length | Advertised SHA256 |
| --- | ---: | --- |
| [torch-2.7.0+cu118-cp312-cp312-manylinux_2_28_x86_64.whl](https://download.pytorch.org/whl/cu118/torch-2.7.0%2Bcu118-cp312-cp312-manylinux_2_28_x86_64.whl) | 955,455,844 | f536e66abf9a989e66a19ef460f54f6014db54cbdbb04c6daf7ddf0b8f3151c4 |
| [triton-3.3.0-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl](https://download.pytorch.org/whl/triton-3.3.0-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl) | 156,503,769 | 0f12a8611eff721d3fd837d0cc2a1f2f8a4d382ec3fc3a8d6a07a5b1e535c81c |

These are header advertisements, not digests calculated over acquired wheel
bytes. No throughput, complete delivery, physical proxy identity or causal
comparison is established. Direct access by this Windows client does not
establish remote Linux no-proxy access. Historical HEAD successes and failed
full transfers remain compatible with these observations.

Stdlib JSON/Decimal analysis: 4 requests, 4.2536031 s summed request wall, maximum
1.1469363 s per request, 2,580 serialized header bytes summed, maximum 647 per
response, 0 body bytes read. Each respected the 30 s / 2 MiB bounds. Two requests were
left unused because another header would not resolve the complete-command gap.
Complete preparation wall and CPU/RSS are unmeasured (`resources_unmeasured` for
those quantities); request time is not that whole-work quantity. No tests or
runtime resource claims are inferred from it.

## Local cache/artifact metadata and its limits

The local roots record identifies the existing uv/pip caches under
`C:/Users/fires/AppData/Local/`, `.conda/pkgs`, selected project temp roots and
Downloads. Alternative `.cache/uv`, `.cache/pip`, miniconda3/pkgs and
anaconda3/pkgs roots were absent. No credentials were recorded; proxy metadata
is reduced to scheme/host/port and whether credentials were present (false).

One uv archive/project-metadata pass inspected 103 archive entries and found no
Torch, Triton or NumPy dist-info/project entries. The conda inventory exposed
NumPy 2.4.6 py311 names, which do not match the pinned 1.26.3 input; no Torch/Triton
package name was found there. This is scoped cache metadata, not package execution.

For pip, the installed file-cache source's SHA224 URL mapping was read at
`pip/_vendor/cachecontrol/caches/file_cache.py` lines 55–63. Six exact URL forms
(canonical/R2 and encoded/literal plus where applicable) were checked in both
http-v2 and legacy http layouts: 12 keys, 0 metadata hits, 0 body hits, 0 body bytes read.
The readable pip wheel cache, scoped CBSC artifact roots and Downloads returned
no named wheel match. Three historical CBSC artifact subdirectories refused
access. A broader primary-temp filename scan also hit many permission-limited
historical directories; it supplies no complete artifact-absence conclusion.
No permissions were changed, inaccessible tree retried or unrelated content read.

No complete local Torch/Triton body can be credited from these observations.
This does not claim absence from the entire machine or from inaccessible roots.

## Exact evidence paths and downstream boundary

Compact receipts are under the shared authoring checkout:
`temp/directions/capability_bound_semantic_currentness/exp/local_acquisition_p15_20260907/`:
`local_roots.json`, `local_cache_inventory.json`, `pip_exact_url_cache.json`,
`requests_01_02_proxy.json`, `requests_03_04_direct.json`, `request_summary.json`.
The two request receipts contain the exact URLs, configured conditions, timestamps,
selected response fields and measured header/time counts. No cookies or credentials
are retained. The filename-scan permission limits above are reported as limits,
not converted into unobserved empty-cache facts.

The same CM's [route note](CBSC_LOCAL_ACQUISITION_P15_ROUTE_NOTE_20260907.md),
`a463df10accb1caf0571ebf25575f0f64ea183a2`, evaluates the existing facilities
without additional requests/probes. It identifies no existing enclosing deadline
and termination path for observed local .NET acquisition, transfer and detached
remote install/import under one complete bound. That is an engineering-expression
gap in the inspected route, not proof of impossibility or a scientific negative.

All wheel-body acquisition, source staging, candidate creation and installer/import
counts are 0. Scientific host/model/RNG, optimizer, learner and evaluation counts
are 0. No new runner, timer/transport implementation or section 4 machinery was
built; no section 5 budget breach was observed. P15 did not reopen P11's invocation.
