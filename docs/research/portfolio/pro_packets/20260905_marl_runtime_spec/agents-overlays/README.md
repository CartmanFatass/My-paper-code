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
| `<library>/AGENTS.md` | library root navigation overlay | assigned to library worker |
| `<library>/<module>/AGENTS.md` | relevant module navigation overlay | assigned to library worker after source inspection |
