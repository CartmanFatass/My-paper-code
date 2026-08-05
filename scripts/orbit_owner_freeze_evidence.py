"""Externally launched freeze evidence for the ORBIT owner-match contract.

Round 7 rejected D0.5's execution evidence.  The ledger was a module-level
dict, so ``EXECUTION_LEDGER["actor_calls"] = 0`` restored an all-zero reading
after a full run and the gate passed; the claim "the counters are monotone,
therefore this process never ran the discriminator" was false.

The counters are now increment-only, but no in-process counter can exclude an
in-process adversary, and the contract no longer pretends otherwise.  What
this script adds is the part that does not depend on trusting the process:

*   It is a SEPARATE interpreter.  Nothing has run in it before the import.
*   It imports the package and calls the audit.  It does not import the
    discriminator's evaluation path itself, and it never calls
    ``terminal_controller``.
*   It prints the evidence to stdout, so the caller reads a result from a
    process boundary rather than from a value handed back inside one.

Usage::

    python scripts/orbit_owner_freeze_evidence.py
    python scripts/orbit_owner_freeze_evidence.py --emit-baseline
    python scripts/orbit_owner_freeze_evidence.py --json

``--emit-baseline`` prints the frozen-digest table for
``experiments/candidates/orbit_owner_match/baseline.py``.  It is the only
supported way to regenerate those literals, and it deliberately writes
nothing: pasting the output into the module is a visible, reviewable diff.
"""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _emit_baseline() -> int:
    """Print the baseline table WITHOUT running the seal gate.

    The seal gate compares against the very literals being regenerated, so it
    cannot be a precondition of regenerating them.  Every other static gate
    still runs, so a baseline can only be emitted from a package that is
    otherwise internally consistent.
    """
    from experiments.candidates.orbit_owner_match import canon, gates, sealing
    from experiments.candidates.orbit_owner_match import precommit

    sealing.interpreter_gate()
    sealing.dependency_gate()
    digests = {
        "fingerprint_set": sealing.fingerprint_set_digest(),
        "global_binding": sealing.global_binding_digest(),
        "class_behavior": sealing.class_behavior_digest(),
        "schema_registry": canon.schema_registry_digest(),
        "gate_order": gates.gate_order_digest(),
        "package_source": precommit.package_source_digest(),
    }
    print("FROZEN_INTERPRETER = %r" % (sealing.INTERPRETER_CONTRACT,))
    print("FROZEN_MPMATH = %r" % (sealing.MPMATH_CONTRACT,))
    print("EXPECTED_DIGESTS = {")
    for name in sorted(digests):
        print('    "%s": "%s",' % (name, digests[name]))
    print("}")
    print("EXPECTED_BLOB_MANIFEST = (")
    for name, blob in precommit.package_blob_records():
        # baseline.py is omitted on purpose: pasting its own blob id into
        # itself would change the file and invalidate the entry.  Its blob is
        # published in the freeze document and read from the object store.
        if name in precommit.UNSEALED_MODULES:
            continue
        print('    ("%s", "%s"),' % (name, blob))
    print(")")
    return 0


def _evidence() -> dict:
    from experiments.candidates.orbit_owner_match import precommit
    return precommit.freeze_evidence()


def main(argv: list) -> int:
    if "--emit-baseline" in argv:
        return _emit_baseline()
    evidence = _evidence()
    ledger = evidence["execution_ledger"]
    if any(ledger[name] != 0 for name in ledger):
        print("FREEZE EVIDENCE INVALID: ledger nonzero %r" % (ledger,),
              file=sys.stderr)
        return 2
    if "--json" in argv:
        print(json.dumps(evidence, indent=2, sort_keys=True, default=repr))
        return 0
    for key in sorted(evidence):
        value = evidence[key]
        if isinstance(value, tuple):
            print("%s:" % key)
            for item in value:
                print("    %r" % (item,))
        else:
            print("%s: %r" % (key, value))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
