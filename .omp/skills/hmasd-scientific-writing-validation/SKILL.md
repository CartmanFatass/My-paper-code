---
name: hmasd-scientific-writing-validation
description: Run explicit, offline, metadata-only scientific-writing record validation on demand.
---

# HMASD Scientific Writing Validation

## Purpose and activation

Use this skill only when an EM, CM, or operator explicitly requests one of these
local checks for named JSON artifacts:

1. validate a source manifest;
2. audit claim-to-evidence mappings against that manifest; or
3. check repeated numeric facts and method-result mappings for internal
   consistency.

This is an on-demand professional research tool, not standing manager context.
It does not draft or revise prose, create references, search for papers, resolve
identifiers, contact providers, generate figures, or submit anything.

## Verification and confidentiality boundary

The validator is offline and dependency-free on Python 3.11+. Give it only local
JSON metadata. Claim and reference text are represented by SHA-256 digests; the
claim audit does not read a manuscript. Never put unpublished prose, quotations,
source text, credentials, personal data, peer-review material, or other sensitive
content into these records merely to run a check.

Diagnostics contain only deterministic issue codes, JSON structural locators,
and syntactic record IDs. They never echo field values, source text, claim text,
paths, or exception messages. A successful check means only that declared local
records satisfy the documented schema and are internally consistent. It does
not establish that a source exists, that a human opened it, that a locator
supports a claim, that a claim is true, that authorship or reporting is complete,
or that a manuscript is confidential, compliant, publishable, approved, or
ready for submission. A `verified` source record is an unconfirmed declaration
supplied by the caller; this tool never claims or performs human verification.

Do not use a pass or failure to change scientific status, technical execution
status, direction or Portfolio authority, an EM disposition, or submission
state. Resolve every reported mismatch against the underlying authorized record.

## Commands

Run from the repository root:

```bash
python3 tools/research/scientific_writing/validate.py source-manifest SOURCE_MANIFEST.json
python3 tools/research/scientific_writing/validate.py claims CLAIMS.json SOURCE_MANIFEST.json
python3 tools/research/scientific_writing/validate.py consistency CONSISTENCY.json
```

There are no network flags or external-provider modes. A validation pass exits
0. Schema, support, verification, or consistency issues exit 1. Unsafe,
unreadable, malformed, duplicate-key, non-finite, oversized, or symlink inputs
fail closed as `INVALID_INPUT` and exit 1.

Every command emits one compact JSON object:

```json
{
  "schema_version": 1,
  "tool": "scientific_writing.source_manifest",
  "ok": false,
  "issues": [
    {"code": "SOURCE_UNVERIFIED", "locator": "$.sources[0].verification.status", "record_id": "E001"}
  ],
  "summary": {"issue_count": 1, "source_count": 1}
}
```

Issues are sorted by code, locator, and record ID. Counts and keys are
deterministic for identical input bytes and interpreter behavior.

## Source manifest v1

The root object has exactly `schema_version`, `artifact_sha256`,
`declarations`, and `sources`. `schema_version` is integer `1`;
`artifact_sha256` is the lowercase SHA-256 of the associated local source-set
or bibliography artifact chosen by the caller.

`declarations` contains exactly `authorship` and `reporting`. Each contains a
`status` and `artifact_sha256`. A `recorded` declaration requires a lowercase
artifact SHA-256; `not_applicable` requires a null hash; `unverified` fails
closed. These records declare local accounting only and do not establish
authorship, guideline compliance, human review, or completeness.

Each source has exactly:

- `evidence_id`: `E` plus 3-8 digits;
- `source_type`: one of the accepted bibliographic/source categories;
- `reference_sha256`: lowercase SHA-256 of the caller's canonical reference
  record, so the validator need not ingest or disclose its text;
- `locator`: a non-empty exact evidence locator declaration; and
- `verification`: exactly `status`, `source_opened`, `verified_by`, and
  `verified_on`.

Validation always requires `status: "verified"`, `source_opened: true`, a
non-empty verifier declaration, and a syntactic `YYYY-MM-DD` declaration.
`unverified`, `rejected`, missing, and internally incomplete sources fail closed.
The tool does not corroborate any declaration or date.

## Claim-to-evidence registry v1

The root object has exactly `schema_version` and `claims`. Each claim has exactly
`claim_id`, `claim_sha256`, and `evidence`. `claim_id` is `C` plus 3-8 digits;
`claim_sha256` is the lowercase digest of the caller's canonical claim text.
Each evidence mapping contains exactly an `evidence_id` and a non-empty
claim-specific `locator`.

A claim with no mapping is `UNSUPPORTED_CLAIM`. Unknown sources,
unverified sources, duplicate mappings, and missing locators fail. The audit
also validates the entire supplied source manifest, so a source cannot become
usable merely because a claim references its ID.

## Consistency registry v1

The root object has exactly `schema_version`, `numeric_facts`, `methods`, and
`results`.

A numeric fact declares `fact_id`, opaque `concept_id`, `analysis_set`,
`reported_section`, finite numeric `value`, `unit`, nullable positive
`sample_size`, paired nullable `numerator`/`denominator`, and non-empty
`evidence_ids`. For the same `(concept_id, analysis_set)`, value, unit, sample
size, numerator, and denominator must match exactly. The validator applies no
tolerance, conversion, rounding, or preferred value; a difference is
`CONFLICTING_NUMERIC_FACT`. Duplicate fact IDs fail.

A method declares `method_id`, `analysis_intent`, `protocol_status`, and one or
more `outcome_ids`. A result declares `result_id`, `method_id`, `outcome_id`,
the same `analysis_intent`, a positive `sample_size`, non-empty `evidence_ids`,
and one or more `reported_sections`. Missing, duplicate, or undeclared mappings,
intent mismatches, and declared outcomes without results fail. These are record
consistency checks, not statistical or methodological validation.

## Upstream provenance and license

This bounded validator set is adapted from the following directly inspected
files in `K-Dense-AI/scientific-agent-skills` at immutable commit
`f6fcafeb1cc8c82eca0160a18bc41c38427b8e0f`:

- `skills/scientific-writing/SKILL.md`;
- `skills/scientific-writing/scripts/_common.py`;
- `skills/scientific-writing/scripts/validate_manifest.py`;
- `skills/scientific-writing/scripts/audit_claims.py`; and
- `skills/scientific-writing/scripts/check_consistency.py`.

The adapted upstream material is provided under the MIT License:

> Copyright (c) 2025 K-Dense Inc.
>
> Permission is hereby granted, free of charge, to any person obtaining a copy
> of this software and associated documentation files (the "Software"), to deal
> in the Software without restriction, including without limitation the rights
> to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
> copies of the Software, and to permit persons to whom the Software is
> furnished to do so, subject to the following conditions:
>
> The above copyright notice and this permission notice shall be included in all
> copies or substantial portions of the Software.
>
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
> IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
> FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
> AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
> LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
> OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
> SOFTWARE.
