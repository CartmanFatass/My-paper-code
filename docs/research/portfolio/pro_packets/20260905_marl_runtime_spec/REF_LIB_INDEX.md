# MARL reference collection index (draft)

Status: **reference collection in progress; not an operative engineering policy**.

The source clones are external to HMASD at `C:/Projects/ref-lib`. Their exact immutable-at-capture
identity is in [`SOURCE_MANIFEST.json`](SOURCE_MANIFEST.json). The collection was cloned shallowly
on 2026-09-05 from the public GitHub remotes below. No third-party dependency was installed or
executed.

| Name | Clone directory | Fixed commit | License | Worker overlay status |
| --- | --- | --- | --- | --- |
| EPyMARL | `C:/Projects/ref-lib/epymarl` | `cbc38c09588064eab978501d0f12c2cf58fa7fc2` | Apache-2.0 | overlay captured; evidence pending |
| MAPPO on-policy | `C:/Projects/ref-lib/on-policy` | `de66d7a4b23fac2513f56f96f73b3f5cb96695ac` | MIT | report and overlay archived |
| BenchMARL | `C:/Projects/ref-lib/BenchMARL` | `65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1` | MIT | report and overlay archived |
| MARLlib | `C:/Projects/ref-lib/MARLlib` | `80e9973a430271a93c781d7422133acb1198f84b` | MIT | overlay archived; evidence pending |
| Mava | `C:/Projects/ref-lib/Mava` | `83f7f0d19d6fdbe07264bb226a64baf8a0b17514` | Apache-2.0 | core/root report and overlay archived; AGENTS_INDEX pending |
| JaxMARL | `C:/Projects/ref-lib/JaxMARL` | `b0c4d77b2cc06711031aec846a55ed0c8cf0f6e9` | Apache-2.0 | report and overlay archived |

The collection root navigation overlay is mirrored at
[`agents-overlays/ref-lib/AGENTS.md`](agents-overlays/ref-lib/AGENTS.md). Each library worker owns
the overlays below its own clone and must add an identical recoverable copy under
`agents-overlays/<library>/...`, then update `SOURCE_MANIFEST.json` with actual paths. No blanket
overlay generation is permitted: module overlays must correspond to directories that the worker
actually used as evidence.

The pinned sources are used to compare environment sampling, learner batching, model inference,
independent-arm scheduling, native/JAX/PyTorch hotpaths, and host/device transfer. A source pattern
is a candidate engineering idea only; it is not a speedup promise and cannot change a scientific
card's comparator, precision, RNG, complete-checker obligations, or result claim.
