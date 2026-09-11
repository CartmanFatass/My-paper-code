# Recoverable local navigation overlays

This directory mirrors the local `AGENTS.md` navigation overlays written under
`C:/Projects/ref-lib`. It is a recoverable copy for the Pro evidence packet; the reference clones
remain outside HMASD and their upstream source bytes are never copied here.

Each child path is relative to `C:/Projects/ref-lib`. Library workers add their own overlays and
record every added path in `SOURCE_MANIFEST.json`. The copy must preserve the same file text as the
external overlay at the capture commit. Upstream `AGENTS.md` files, if discovered, are listed
separately and are never replaced by these local files.

Current coverage:

| Relative path | Kind | Status |
| --- | --- | --- |
| `ref-lib/AGENTS.md` | collection root navigation overlay | captured |
| `epymarl/**/AGENTS.md` | EPyMARL root and source module overlays | captured; paths listed in manifest |
| `BenchMARL/**/AGENTS.md` | BenchMARL root and source module overlays | captured; paths listed in manifest |
| `on-policy/**/AGENTS.md` | MAPPO on-policy root and source module overlays | captured; paths listed in manifest |
| `JaxMARL/**/AGENTS.md` | JaxMARL root and source module overlays | captured; paths listed in manifest |
| `MARLlib/**/AGENTS.md` | MARLlib root and source module overlays | captured; paths listed in manifest |
| `Mava/**/AGENTS.md` | Mava root and source module overlays | captured; paths listed in manifest |

The full worker reports are archived under `../worker-reports/<library>/`; a library row may show
its overlays captured while its core evidence report is still pending.
