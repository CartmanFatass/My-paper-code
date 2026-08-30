---
name: hmasd-experimental-design-tools
description: Build or validate a frozen, deterministic experimental randomization or bounded full-factorial schedule on demand. This tool does not launch experiments, collect observations, analyze outcomes, or make scientific decisions.
---

# HMASD experimental-design tools

Use this optional tool only when EM has frozen an exact experimental protocol and CM needs a reproducible schedule artifact or needs to validate that artifact. It is not autoloaded by Root, EM, or CM. It creates no external effects beyond explicitly requested local JSON/CSV files; it never launches an experiment or interprets its results.

## Authority and protected semantics

EM freezes the protocol ID/version, randomized unit and randomization level, units, blocking and stratification, arms or factor levels, sample structure, balance tolerance, outcome branches, and seed. CM may construct or validate only that frozen artifact. A changed seed, schedule hash, randomization level, arms, factors, levels, blocking, stratification, or unit list is a new scientific protocol version and must return to EM.

A successful schedule is only a reproducible allocation/design artifact. It does **not** establish balance beyond the emitted count/deviation checks, prevent pseudoreplication outside the frozen independent unit, validate a statistical model, launch a run, or imply an outcome or scientific disposition.

## Supported bounded constructions

- `blocked_arms`: permuted-arm allocation within the declared block/stratum groups. It requires explicit `arms`, positive integer `ratio`, and `balance_checks.maximum_absolute_deviation`.
- `full_factorial`: every declared combination of explicit factor levels, replicated exactly as declared and assigned one unique independent unit per run. Blocking and stratification must be explicitly `null` for this minimal construction.

The tool uses a private seeded `random.Random` instance. It never uses or mutates global RNG state. It rejects missing/invalid seeds, mismatched randomization and independent-unit levels, duplicate units or levels, malformed grouping, factor/run mismatches, and resource-unsafe requests. Hard limits are 10,000 units, 16 arms, 12 factors, 32 levels per factor, and 4,096 full-factorial runs.

## Frozen input schema

Provide a JSON object with all of these fields:

```json
{
  "protocol_id": "enzyme-screen-v1",
  "protocol_version": "v1",
  "seed": 2401,
  "randomization_level": "sample",
  "unit": {
    "randomization_level": "sample",
    "units": [
      {"id": "sample-01", "batch": "A"},
      {"id": "sample-02", "batch": "A"},
      {"id": "sample-03", "batch": "B"},
      {"id": "sample-04", "batch": "B"}
    ]
  },
  "blocking": {"field": "batch"},
  "stratification": null,
  "sample_structure": {"independent_unit": "sample", "unit_count": 4},
  "factor_design": {
    "kind": "blocked_arms",
    "arms": ["control", "treatment"],
    "ratio": [1, 1]
  },
  "balance_checks": {"maximum_absolute_deviation": 1},
  "outcome_branches": ["positive", "negative", "null", "ambiguous"]
}
```

For `full_factorial`, set `blocking` and `stratification` to `null`, use:

```json
"factor_design": {
  "kind": "full_factorial",
  "factors": {"temperature_C": [20, 40], "catalyst": ["A", "B"]},
  "replicates": 1
}
```

The product of levels times replicates must equal `sample_structure.unit_count`; this prevents a schedule from claiming more independent runs than frozen units.

## Commands and artifacts

```bash
python -m tools.research.experimental_design generate \
  --input frozen-protocol.json \
  --json-output schedule.json \
  --csv-output schedule.csv

python -m tools.research.experimental_design validate --input schedule.json
```

`generate` emits machine-readable JSON. Without output paths it emits the complete artifact to stdout; with paths it writes the requested JSON/CSV and emits its artifact type, input hash, schedule hash, and row count. `validate` checks the SHA-256 `schedule_hash` and one-unique-unit-per-run invariant. Invalid input exits with code 2 and a machine-readable error object.

Archive the resulting schedule JSON and its `input_hash`/`schedule_hash` with the frozen protocol. CSV is a convenience execution view, not the authoritative frozen artifact.

## Source attribution and MIT notice

This local, deliberately reduced implementation is adapted from the experimental-design principles and interfaces in:

- K-Dense-AI/scientific-agent-skills, commit `f6fcafeb1cc8c82eca0160a18bc41c38427b8e0f`
- `skills/experimental-design/SKILL.md`
- `skills/experimental-design/scripts/randomization.py`
- `skills/experimental-design/scripts/doe_designs.py`

The upstream source is MIT licensed. Copyright (c) 2025 K-Dense Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
