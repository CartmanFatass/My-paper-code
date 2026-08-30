---
name: hmasd-symbolic-counterexample-tools
description: Run one bounded on-demand SymPy algebra check or Z3 counterexample search for an exact HMASD research gap.
---

# HMASD Symbolic Counterexample Tools

Use this Skill only when the accountable manager has declared an exact algebra
check or encoded counterexample gap. It is an on-demand observation tool, not a
Root, EM, or CM autoload. It does not allocate work, change scientific status,
select a favored conclusion, or execute a result command on its own.

## Authority and interpretation

The wrapper returns replayable tool facts under schema version 1. A SymPy zero
residual is a derivation aid, not a proof. A Z3 `SAT` result is a concrete model
for the frozen encoding. `UNSAT` is only relative to the recorded encoding,
logic, domain bounds, assumptions, and options. `UNKNOWN`, including timeout or
resource exhaustion, is inconclusive and must never be translated into proof,
`UNSAT`, or scientific failure. EM retains scientific interpretation and
claim-ceiling authority.

Every successful product retains the common analytical fields: assignment ID,
gap ID, task family, claim, exact evidence references and locators, assumptions,
falsifier/counterexample, uncertainty/limitations, consequence/decision
relevance, and recommendation. `scientific_disposition` is always
`NOT_PERFORMED`; a technically completed `UNKNOWN` remains distinct from a
technical wrapper failure.

## Entry contract

Invoke only with a UTF-8 JSON file no larger than 65,536 bytes:

```bash
python tools/research/symbolic/symbolic_tools.py --input request.json
```

The process writes exactly one canonical, key-sorted JSON object to stdout and
no artifact or state file. Exit code `0` means the wrapper completed; exit code
`2` means fail-closed request/dependency rejection. Print the authoritative,
closed JSON schemas or dependency record without importing the optional tools:

```bash
python tools/research/symbolic/symbolic_tools.py --schema sympy_identity
python tools/research/symbolic/symbolic_tools.py --schema z3_check
python tools/research/symbolic/symbolic_tools.py --metadata
```

Both schemas set `additionalProperties: false`. Their shared required fields
are:

- `schema_version` (integer `1`), `operation`, `assignment_id`, `gap_id`,
  `task_family`, and the exact `claim`;
- `evidence_references`, each with non-empty `reference` and exact `locator`;
- declared `assumptions`; and
- `consequence_decision_relevance`.

The output records a SHA-256 of the complete canonical input, the complete
request, runtime and distribution versions, active limits, exact encoded
expressions, observation, common analytical product, and interpretation
boundary. Inputs contain no provider calls, network endpoints, secrets, RNG, or
checkpoint effects.

## SymPy identity operation

Use `operation: "sympy_identity"`. The remaining required fields are:

- `variables`: at most 12 unique symbols. Each declares `name`, one domain from
  `integer`, `rational`, `real`, or `complex`, and a unique assumptions array.
  Permitted extra assumptions are `positive`, `nonnegative`, `negative`,
  `nonpositive`, `nonzero`, `even`, `odd`, and `finite`.
- `lhs` and `rhs`: exact expression strings, each at most 2,048 characters and
  256 syntax nodes.
- `simplification_operations`: an ordered unique subset of `expand`, `cancel`,
  `together`, `factor`, and `trigsimp`, with at most five operations.
- `expected_residual`: `zero`, `nonzero`, or `unspecified`.
- `precision`: 15 through 100 decimal digits, used only to report a numerical
  rendering alongside the exact residual.
- `cross_check_points`: one through 32 complete exact substitutions. Every
  declared symbol must occur in every point. Values use the same safe constant
  expression grammar.

The expression grammar permits numeric literals; declared symbol names; unary
`+`/`-`; `+`, `-`, `*`, `/`; integer powers of magnitude at most 16; and the
one-argument functions `Abs`, `sin`, `cos`, `exp`, `log`, and `sqrt`. Attribute
access, imports, comprehensions, lambdas, subscripts, strings, keyword calls,
and every undeclared function or symbol are rejected before SymPy construction.
The wrapper never uses Python `eval` or a SymPy parser that evaluates Python.

`CAS_ZERO_WITH_EXACT_CROSS_CHECKS` means only that the selected CAS operations
produced exact zero and the recorded substitutions also produced exact zero.
`COUNTEREXAMPLE_FOUND` includes the first deterministic exact nonzero residual
and substitution witness. `NOT_ESTABLISHED` preserves the inconclusive branch.

## Z3 counterexample operation

Use `operation: "z3_check"`. The remaining required fields are:

- `logic`: one of `QF_LIA`, `QF_LRA`, `QF_NIA`, `QF_NRA`, or `QF_UF`;
- `variables`: at most 12 unique `Bool`, `Int`, or `Real` symbols. Every numeric
  symbol requires integer `lower` and `upper` bounds in
  $[-1{,}000{,}000{,}000, 1{,}000{,}000{,}000]$; Boolean symbols take no bounds;
- `assertions`: one through 48 Boolean formulas, at most 2,048 characters each,
  8,192 characters total, and 256 syntax nodes per formula;
- `timeout_ms`: 1 through 5,000;
- `rlimit`: 1 through 1,000,000 deterministic Z3 resource units; and
- `random_seed`: 0 through 2,147,483,647.

The safe JSON expression grammar permits declared names; Boolean and bounded
integer literals; unary `not`, `+`, and `-`; Boolean `and`/`or`; arithmetic
`+`, `-`, `*`, `/`, `%`; nonnegative integer powers through 16; single
comparisons; and only `And`, `Or`, `Not`, `Implies`, `If`, and `Distinct` calls.
It cannot submit arbitrary Python, SMT-LIB commands, files, native libraries, or
shell operations. The wrapper generates and records the exact solver s-expression,
encoding hash, logic, domain constraints, assertions, timeout, resource limit,
seed, solver result, and model or `reason_unknown`.

Stop after one result. Do not silently increase a bound, timeout, resource
limit, seed, expression, logic, assumption, or simplification sequence; any
change is a new frozen request and input hash.

## Dependency source and license metadata

This wrapper is original HMASD code and copies no dependency code.

- **SymPy 1.13.3** (`sympy`): BSD-3-Clause, repository
  <https://github.com/sympy/sympy>, release `sympy-1.13.3`, annotated tag object
  `e7c0f3d9002e88ae2518961a22b9aff019615146`, peeled source commit
  `b4ce69ad5d40e4e545614b6c76ca9b0be0b98f0b`. Runtime reporting uses
  `sympy.__version__` and `importlib.metadata.version("sympy")`.
- **z3-solver 4.13.4.0 / Z3 runtime 4.13.4**: MIT, repository
  <https://github.com/Z3Prover/z3>, release `z3-4.13.4`, source commit
  `6f24123f0c9d1d8bd84dec275c5c7aea939a19fe`. Runtime reporting uses
  `z3.get_version_string()` and `importlib.metadata.version("z3-solver")`.

The reviewed versions are enforced exactly. Missing or different dependency
versions fail closed. `--metadata` reports the exact public APIs used. The
wrapper uses SymPy construction, simplification, substitution, `srepr`,
`count_ops`, and numerical-rendering APIs; and Z3 sort constructors, safe
formula combinators, `SolverFor`, solver option/add/check/model/unknown/sexpr
APIs, and model evaluation. No code from either dependency is copied or
substantially adapted.
