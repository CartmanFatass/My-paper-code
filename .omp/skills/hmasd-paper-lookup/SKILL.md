---
name: hmasd-paper-lookup
description: Normalize bounded scholarly-paper retrieval fixtures and make explicitly authorized named-endpoint requests.
---

# HMASD Paper Lookup

## Purpose and authority boundary

This is an **on-demand** retrieval aid for an EM or Research Scout resolving one
frozen evidence gap. It is not loaded by Root, EM, CM, or Portfolio by default;
it does not start research, widen a query, or select a direction. It retrieves
or normalizes source records only. It does not synthesize evidence, decide
novelty, establish scientific truth, assert evidence of absence, change a
claim, or grant an acceptance/lifecycle decision.

The requester owns the bounded question and must separately verify every
source, locator, excerpt, version, and applicability before relying on it.
Discovery is not verification: a normalized title, abstract, DOI, or result
count is untrusted third-party metadata, not a human-verified source claim.

## Frozen input contract

Before using the tool, the accountable EM or Research Scout supplies:

- the assignment/gap ID, bounded query or exact identifier, and date boundary;
- an approved named endpoint (`arxiv` or `openalex`), page/record/call bounds,
  external-data classification, and stop condition;
- the required identifiers, source version policy, and requested fields;
- the required packet fields: source ID, DOI/version where present, endpoint
  parameters, access date, locator/excerpt, count reconciliation,
  support/challenge/limits, and observed errors; and
- the reentry condition and explicit non-goals.

An incomplete, unbounded, credential-bearing, or synthesis-seeking request is
refused. An empty result says only that no record was returned within the
frozen endpoint/query/date/page boundary. It never becomes "no prior work
exists."

## Local, deterministic normalizers

`tools/research/paper_lookup/cli.py` accepts a local fixture path or `-` for
stdin and emits sorted JSON with local `schema_version: 1`,
`scientific_effect: "none"`, and `network_used: false`:

```bash
python3 tools/research/paper_lookup/cli.py arxiv recorded-feed.xml
python3 tools/research/paper_lookup/cli.py openalex recorded-work.json
python3 tools/research/paper_lookup/cli.py jats recorded-article.xml
python3 tools/research/paper_lookup/cli.py paginate recorded-pages.json
```

The normalizers are dependency-free and do not perform network I/O:

- arXiv Atom records preserve versioned and bare IDs, normalize wrapped text,
  choose links by `rel`/MIME type, and reject an HTTP-200 `Error` feed or
  throttle body;
- OpenAlex inverted abstracts retain every token at a colliding position and
  report invalid/gapped positions rather than silently overwriting words;
- JATS records distinguish a readable `<body>` from metadata-only XML and never
  label metadata as full text; and
- pagination uses the recorded pages in order, validates each reported count,
  exposes endpoint-reported total versus retrieved total, and marks shortfalls
  or HTTP-200 error objects visibly.

Malformed inputs are rejected as deterministic JSON errors. The normalizers do
not invent missing DOI, author, locator, abstract, endpoint parameter, or
count metadata.

## Explicit network boundary

Network access is disabled unless the requester invokes the named fetch command
with all of `--allow-network`, `--endpoint`, `--params-json`, bounded
`--timeout-seconds` (1–30), and UTC `--access-date`:

```bash
python3 tools/research/paper_lookup/cli.py fetch \
  --allow-network --endpoint arxiv --timeout-seconds 10 \
  --access-date 2026-08-30 --params-json '{"id_list":"1706.03762"}'
```

The boundary accepts only named public endpoints, URL-encodes sorted string
parameters, never accepts arbitrary URLs, credentials, personal contact
values, or environment-derived authentication, and returns the observed body
and HTTP status for subsequent local inspection. An HTTP 200 is not a success
claim: pass returned arXiv/OpenAlex data through the corresponding normalizer
and preserve any reported error. Default tests use fixtures only and must never
send a live request.

## Required return packet

The manager incorporates the local tool output into the common analytical
product, retaining assignment/gap ID, task family, claim, exact source URLs and
locators, assumptions, falsifier/counterexample, uncertainty/limitations,
consequence/decision relevance, and recommendation. The retrieval portion must
also retain endpoint name/parameters, access date, source IDs, DOI/version when
present, excerpt/locator, pagination/count reconciliation, and observed
transport or payload errors. Keep source facts separate from inference and
from unverified discovery. `NO_MATERIAL_INSIGHT` remains a successful bounded
return only when the documented search boundary produced no answer-changing
material; it is not an absence claim or technical failure.

## Provenance and license

This compact local adaptation derives its parser and pagination safeguards from
K-Dense Inc., `scientific-agent-skills`, commit
`f6fcafeb1cc8c82eca0160a18bc41c38427b8e0f`, paths:

- `skills/paper-lookup/SKILL.md`
- `skills/paper-lookup/scripts/_common.py`
- `skills/paper-lookup/scripts/arxiv_atom.py`
- `skills/paper-lookup/scripts/openalex_abstract.py`
- `skills/paper-lookup/scripts/jats_to_text.py`
- `skills/paper-lookup/scripts/paginate.py`

Copyright (c) 2025 K-Dense Inc. MIT License: permission is granted to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell copies,
provided this copyright and permission notice is retained; the software is
provided "AS IS", without warranty.
