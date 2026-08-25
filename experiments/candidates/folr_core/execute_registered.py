"""FOLR: execute the eight registered branches under External Pro's approval.

Sequence 01.  This module is deliberately **not** one of the eleven files in
``registration.SCIENTIFIC_GRAPH_SOURCES``, and it must not become one before
this execution runs.  Pro's approval says so outright:

    Do not modify any of the eleven fingerprinted files before execution. Any
    modification requires a new fingerprint and invalidates this approval.

Adding this driver to the fingerprint list would require editing
``registration.py``, which is exactly the modification that is forbidden.  The
separation is safe because nothing here decides anything: every scientific
choice -- the cell, the payloads, the branches, the margin, the gates, the
precedence order and the terminals -- lives in the fingerprinted modules.  This
file constructs no state, compares no kernels and routes no outcome.  It calls
``branches.execute_all``, ``certificates.certify_all``, ``branches.contrasts``
and ``outcome.decide`` in that order and serializes what they return.

THE APPROVED DIGEST IS SUPPLIED FROM OUTSIDE
--------------------------------------------
    Pass the approved digest as the external precommitment literal [...] It must
    not be treated as authoritative merely because the running registration
    recomputes the same value internally.

So ``--approved-digest`` is required on the command line and is never defaulted
from ``registration_digest()``.  ``outcome.decide`` compares the two and fails
the ``registration_digest_equals_the_precommitment`` interface gate if they
differ; this module additionally refuses to run at all, so a mismatch cannot
produce a kernel observation in the first place.

WHAT IS PRESERVED
-----------------
    Preserve the raw eight branch results, direct kernels, immutable rows,
    certificates, contrasts, source identity, registration record, and complete
    outcome report for the alignment audit.

All of it, in one JSON artifact.  Float32 vectors are written both as decimal
values and as their exact little-endian bytes, so the record is bitwise
recoverable rather than merely legible.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
from dataclasses import fields, is_dataclass
from typing import Any, Mapping

import numpy as np
import torch

from experiments.candidates.folr_core import branches as br
from experiments.candidates.folr_core import certificates as ct
from experiments.candidates.folr_core import outcome as oc
from experiments.candidates.folr_core import registration as reg
from experiments.candidates.folr_core import s03_binding as sb

RAW_OUTPUT_BINDING = "folr_core.execute_registered.v1"


class ApprovalMismatch(RuntimeError):
    """The running registration is not the one External Pro approved."""


def _array_record(array: np.ndarray) -> dict[str, Any]:
    contiguous = np.ascontiguousarray(array)
    return {
        "dtype": str(contiguous.dtype),
        "shape": list(contiguous.shape),
        "values": contiguous.tolist(),
        "bytes": contiguous.tobytes().hex(),
        "digest": sb.vector_digest(contiguous),
    }


def _plain(value: Any) -> Any:
    """A JSON-shaped view that keeps float32 exact and drops live objects."""
    if isinstance(value, np.ndarray):
        return _array_record(value)
    if isinstance(value, torch.Tensor):
        return _array_record(value.detach().cpu().numpy())
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _plain(getattr(value, field.name)) for field in fields(value)
        }
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


def _kernel_record(kernel: sb.DirectKernel) -> dict[str, Any]:
    return {
        "owner_lifecycle_key": kernel.owner_lifecycle_key,
        "membership_epoch": kernel.membership_epoch,
        "token_position": kernel.token_position,
        "masked_logits": _array_record(kernel.masked_logits),
        "probabilities": _array_record(kernel.probabilities),
        "actor_preimage_digest": kernel.actor_preimage_digest,
        "model_state_digest": kernel.model_state_digest,
        "common_snapshot_digest": kernel.common_snapshot_digest,
        "intervention_manifest_digest": kernel.intervention_manifest_digest,
    }


def execute(*, approved_digest: str, approved_digest_source: str) -> dict[str, Any]:
    """Run the eight branches and route the result.  Observes nothing else."""
    registration = reg.registered_cell()
    if registration.development_only:
        raise ApprovalMismatch("the registered cell must not be DEVELOPMENT_ONLY")

    current = registration.registration_digest()
    if current != approved_digest:
        raise ApprovalMismatch(
            "the running registration digest does not equal the approved "
            f"precommitment: current {current}, approved {approved_digest}. "
            "No registered branch will be executed."
        )

    identity = reg.actor_path_source_identity()
    registered = registration.source_identity
    if (
        identity["scientific_graph_fingerprint"]
        != registered["scientific_graph_fingerprint"]
    ):
        raise ApprovalMismatch("the scientific graph is not the approved one")
    for library in ("torch_version", "numpy_version"):
        if identity[library] != registered[library]:
            raise ApprovalMismatch(f"{library} differs from the registration")

    # From here the registered kernels become observable.  Pro: "Do not select,
    # alter, replace, or retune the cell after observing the first registered
    # branch."  Nothing below constructs or modifies a registration.
    results = br.execute_all(registration)
    certificates = ct.certify_all(results, registration=registration)
    contrasts = br.contrasts(results)
    report = oc.decide(
        results=results,
        contrasts=contrasts,
        certificates=certificates,
        registration=registration,
        expected_registration_digest=approved_digest,
    )

    branches: dict[str, Any] = {}
    for name, result in results.items():
        evidence = {
            key: value for key, value in result.evidence.items() if key != "core"
        }
        branches[name] = {
            "spec": _plain(result.spec),
            "direct_kernel": _kernel_record(result.kernel),
            "immutable_row": _plain(result.row),
            "evidence": _plain(evidence),
        }

    return {
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "approved_registration_digest": approved_digest,
        "approved_digest_source": approved_digest_source,
        "executed_registration_digest": current,
        "execution_source_identity": _plain(identity),
        "registration_record": _plain(registration.frozen_record()),
        "branches": branches,
        "certificates": _plain(certificates),
        "contrasts": _plain(contrasts),
        "outcome_report": _plain(report),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--approved-digest",
        required=True,
        help="the registration digest External Pro approved, as an external "
        "literal; execution refuses if the running registration differs",
    )
    parser.add_argument(
        "--approved-digest-source",
        required=True,
        help="where the literal came from, recorded in the artifact",
    )
    parser.add_argument("--out", required=True, help="artifact path")
    arguments = parser.parse_args()

    artifact = execute(
        approved_digest=arguments.approved_digest,
        approved_digest_source=arguments.approved_digest_source,
    )
    path = pathlib.Path(arguments.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(artifact, indent=2, sort_keys=True).encode("utf-8")
    path.write_bytes(payload)
    print(f"terminal: {artifact['outcome_report']['terminal']}")
    print(f"reason:   {artifact['outcome_report']['reason']}")
    print(f"contrast: {artifact['outcome_report']['payload_contrast']}")
    print(f"artifact: {path} ({len(payload)} bytes)")
    print(f"sha256:   {hashlib.sha256(payload).hexdigest()}")


if __name__ == "__main__":  # pragma: no cover
    main()
