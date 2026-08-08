"""Frozen expected digests for the runtime seal (round-7 correction D05-C01).

Round 7 rejected D0.5's sealing story in one sentence: the package computed
current binding digests but never compared them with a frozen expectation, so
it inventoried its runtime trust surface rather than sealing it.  Rebinding an
audited global from one supported object to another changed the freshly
computed digest and failed no gate, because no gate had anything to fail
against.

This module is that expectation.  :func:`gates.runtime_seal_gate` compares
every live digest against the literals below and refuses to continue on any
mismatch, before the audited phase and again after it.

WHY THIS FILE IS OUTSIDE THE SEALED SET
---------------------------------------
A digest cannot cover the literal that records it: writing the value in would
change the value.  So ``sealing.OWNED_MODULE_NAMES`` deliberately excludes
this module, ``EXPECTED_DIGESTS["package_source"]`` is taken over the other
ten modules, and ``EXPECTED_BLOB_MANIFEST`` carries no entry for
``baseline.py``.

That is not a hole, because this file is authenticated the way the reviewer
authenticated the rest of the package in round 7: by its git blob id, from the
commit, through the connector.  The blob id is published in the freeze
document.  A file with no functions and nothing but literals is exactly the
kind of artifact that anchoring works for -- there is no behavior in it to
subvert, only values, and every value here is checkable against the object
store without trusting this machine.

The one thing it must not become is a place where a digest is compared with a
literal stored inside the digested set.  That is self-consistency, which is
the defect round 7 named, not the repair.

The exclusion set above was independently traced in both directions before the
freeze and is correct: no path leads from any sealed digest back into this
file.  But the property is currently produced by ``runtime_seal_gate``
importing this module as a FUNCTION LOCAL, so it never enters the module-level
graph -- not by ``sealing.UNSEALED_MODULE_NAMES``, which is never reached.  The
outcome is right; the mechanism the comments credit is not the operative one.
Do not cite ``UNSEALED_MODULE_NAMES`` as an active control.

WHAT THIS SEAL DOES NOT DO
--------------------------
It detects drift and DIRECT rebinding of an audited global.  It does not
survive an adversary inside this process.  Two defeats are known, demonstrated
and deliberately unrepaired -- module substitution through ``sys.modules``, and
same-typed substitution of a ``PROCESS_STATE_GLOBALS`` slot.  See section 8 of
the D0.6 freeze document.  Treat an externally launched clean process, not this
seal, as the load-bearing evidence.

REGENERATION
------------
``python scripts/orbit_owner_freeze_evidence.py --emit-baseline`` prints this
table from a clean interpreter.  Regenerating it is a deliberate act that
shows up as a diff on this file; it is not something the audit does for you.
"""

from __future__ import annotations

# Interpreter and dependency the literals below were produced under.  These
# are duplicated from ``sealing`` on purpose: if the contract there is edited,
# the mismatch surfaces here rather than silently revaluing every digest.
FROZEN_INTERPRETER = ("cpython", 3, 11, 9)
FROZEN_MPMATH = "1.4.1"

# name -> frozen digest.  Regenerated only by the emit-baseline path above.
EXPECTED_DIGESTS = {
    "class_behavior": "a868553657d5cd37ddd86f681f5d1f40ce489b0d615433020e303ada1f8cbb09",
    "fingerprint_set": "47ef8c294d99e484fdd41f0f724924d63cd001b5f988e7f89e61296291a1ca58",
    "gate_order": "eac706beb1abaef02b1b38f33b49dcf083d6a2340d21cd1f6fda3566809795fc",
    "global_binding": "c94eb1e469d4da57e0970780ba4c7f740c5cf3ed47c03cf395aba3d4199bb7aa",
    "package_source": "d8846a2f2c5e36f5f5c68da97d067bcad4b28951219391f57fdfc96191217acc",
    "schema_registry": "b790aac1fbaad24f627a5ae9bd991fdbfb93035222546b68c5506170f5ed37a9",
}

# Git blob ids of every package module except this one, so an external
# reviewer can go from "the freeze says X" to "the object store says X"
# without running anything.  This file's own blob id is published in the
# freeze document instead: writing it in here would change the file and
# falsify the entry in the same edit.
#
# NOTE: this table is REFERENCE DATA, not an enforced control.  No gate reads
# it.  ``precommit.blob_manifest_digest()`` recomputes the manifest from the
# working tree and never compares it with these literals, so an edited module
# changes the computed manifest and mismatches nothing here.  The check it
# supports is a human or connector-driven one against the object store.
#
# The precommit envelope digest is likewise NOT stored here.  The envelope
# binds the blob manifest, which covers this file, so pinning the envelope
# digest inside this file would be circular.  It is published in the freeze
# document, computed after the commit, and reproducible by anyone who has the
# commit.
EXPECTED_BLOB_MANIFEST = (
    ("canon.py", "e61bd81dbdf1f9a7aba182aa78955af570acbf65"),
    ("records.py", "0027b9718973fa15f06d5b6e0aff8211941f9a6f"),
    ("trust.py", "71ac1a1a9463df12576fe083cd468141b2ee32d7"),
    ("block.py", "0447f0700ff614d20a896db3ca776f3c63f86fbb"),
    ("controls.py", "0c46aa6d63d10d64f2b7fc4b7c9e1e691728d997"),
    ("discriminator.py", "e4abf302a26da2b4fa6b3c67160ff07af757c716"),
    ("numerics.py", "fd41cb86417694ce2af93020c0f49a8e8e9af512"),
    ("sealing.py", "6df645022d65c4027637e4bf606c98ac2ef8b8ab"),
    ("gates.py", "acdbcb3e341fa94445f1a353359779f6b5822188"),
    ("precommit.py", "c244eaf32e7f554e1dc0d6a1be8765fa84fb516b"),
)
