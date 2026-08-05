"""Canonical serialization and registry tests.

Each test names the wrong implementation it rejects.  A test that cannot fail
a plausible wrong implementation is decoration, not evidence.
"""

import struct

import pytest

from experiments.candidates.orbit_owner_match import canon
from experiments.candidates.orbit_owner_match import records


def test_code_encoder_separates_signed_zero():
    """Rejects: reusing the DATA encoder for code constants.

    This is the round-6 regression.  The data encoder folds -0.0 into +0.0 so
    that equal values serialize equally; if code fingerprints share it, a
    mutant differing only in the sign of a zero constant fingerprints
    identically and the positive-orientation freeze is defeated.
    """
    assert canon.encode_float_raw(0.0) != canon.encode_float_raw(-0.0)
    assert canon.encode_float_raw(-0.0) == b"f" + struct.pack(">d", -0.0)
    # ... while the data encoder deliberately does merge them.
    assert canon._enc_float(0.0) == canon._enc_float(-0.0)


def test_code_encoder_preserves_nan_payload_shape():
    """Rejects: encoding nonfinite constants through repr()."""
    nan = float("nan")
    encoded = canon.encode_code_constant(nan, lambda code: "00")
    assert encoded == b"P" + b"f" + struct.pack(">d", nan)


def test_data_encoder_rejects_nonfinite():
    with pytest.raises(canon.ContractError):
        canon._enc_float(float("inf"))
    with pytest.raises(canon.ContractError):
        canon._enc_float(float("nan"))


def test_int_encoder_rejects_bool():
    """Rejects: treating bool as int because it subclasses int."""
    with pytest.raises(canon.ContractError):
        canon._enc_int(True)
    assert canon._enc_bool(True) != canon._enc_int(1)


def test_serialize_requires_the_exact_registered_class():
    """Rejects: duck-typed serialization of a look-alike record."""

    class LookAlike:
        numerator = 1
        denominator = 2

    with pytest.raises(canon.ContractError):
        canon.serialize_struct("RationalValue" + records.D2, LookAlike())


def test_serialize_rejects_unknown_schema():
    with pytest.raises(canon.ContractError):
        canon.serialize_struct("no-such-schema", records.DecimalLiteral("x"))


def test_tuple_cardinality_is_exact():
    """Rejects: accepting a short or long tuple for a fixed-width field."""
    with pytest.raises(canon.ContractError):
        canon._enc_typed((1.0,), "tuple[float;2]")
    with pytest.raises(canon.ContractError):
        canon._enc_typed((1.0, 2.0, 3.0), "tuple[float;2]")


def test_schema_id_is_part_of_the_serialization():
    """Rejects: a serializer that lets two schemas collide on field values.

    Two records with identical field values under different schema ids must
    serialize differently, and the id must actually appear in the bytes.
    Comparing two encoded id strings would prove nothing about the
    serializer.
    """
    left = records.DecimalLiteral("same")
    right = records.CodeFingerprintRecord("same", "same")
    left_bytes = canon.serialize_struct("DecimalLiteral" + records.D2, left)
    right_bytes = canon.serialize_struct(
        "CodeFingerprintRecord" + records.D2, right)
    assert left_bytes != right_bytes
    assert canon._enc_str("DecimalLiteral" + records.D2) in left_bytes
    assert canon._enc_str(
        "CodeFingerprintRecord" + records.D2) in right_bytes


def test_registry_is_sealed_against_late_registration():
    """Rejects: a registry that can grow after the digest is frozen."""
    with pytest.raises(canon.ContractError):
        canon.register_schema("late" + records.D2, records.DecimalLiteral,
                              (("text", "str"),))


def test_registry_seal_gate_detects_descriptor_mutation():
    """Rejects: sealing that records a digest but never re-checks it."""
    canon.registry_seal_gate()
    victim = "DecimalLiteral" + records.D2
    saved = canon._REGISTRY[victim]
    canon._REGISTRY[victim] = (saved[0], (("text", "bytes"),))
    try:
        with pytest.raises(canon.ContractError):
            canon.registry_seal_gate()
    finally:
        canon._REGISTRY[victim] = saved
    canon.registry_seal_gate()


def test_registry_seal_gate_detects_a_repointed_class():
    """Rejects: a registry digest over ids and descriptors but not classes.

    With the class outside the digest, a schema id can be repointed to an
    impostor of the same field shape: the seal gate keeps passing while
    ``serialize_struct`` starts accepting the impostor and REJECTING the
    genuine record.  Mutating only the descriptor cannot detect this.
    """
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class Impostor:
        text: str

    canon.registry_seal_gate()
    victim = "DecimalLiteral" + records.D2
    saved = canon._REGISTRY[victim]
    canon._REGISTRY[victim] = (Impostor, saved[1])
    try:
        with pytest.raises(canon.ContractError):
            canon.registry_seal_gate()
    finally:
        canon._REGISTRY[victim] = saved
    canon.registry_seal_gate()


def test_every_record_class_is_registered():
    """Rejects: the round-6 defect of a lineage record left unregistered."""
    records.registration_completeness_gate()
    declared = {cls for _, cls, _ in records._SCHEMA_TABLE}
    assert records.TargetCell in declared


def test_completeness_gate_is_not_evaded_by_a_metaclass():
    """Rejects: ``type(value) is type``, which skips metaclassed dataclasses.

    One keyword -- ``metaclass=`` -- would otherwise put a record outside the
    digest-bearing contract while the gate reported completeness. That is the
    same defect class the gate was written to close.
    """
    import abc
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class Sneaky(metaclass=abc.ABCMeta):
        value: int

    Sneaky.__module__ = records.__name__
    setattr(records, "Sneaky", Sneaky)
    try:
        with pytest.raises(canon.ContractError):
            records.registration_completeness_gate()
    finally:
        delattr(records, "Sneaky")
    records.registration_completeness_gate()


def test_completeness_gate_sees_a_nested_record_class():
    """Rejects: scanning only ``dir(module)``, which misses nested classes."""
    from dataclasses import dataclass

    class Holder:
        pass

    @dataclass(frozen=True)
    class Inner:
        value: int

    Inner.__module__ = records.__name__
    Holder.__module__ = records.__name__
    Holder.Inner = Inner
    setattr(records, "Holder", Holder)
    try:
        with pytest.raises(canon.ContractError):
            records.registration_completeness_gate()
    finally:
        delattr(records, "Holder")
    records.registration_completeness_gate()


def test_analysis_key_rejects_bool_labels():
    """Rejects: membership tests that admit True as the integer 1."""
    with pytest.raises(canon.ContractError):
        records.AnalysisKey(True, 1, 1, 0)
    with pytest.raises(canon.ContractError):
        records.AnalysisKey(1, 1, 1, True)
    assert records.AnalysisKey(1, -1, 1, 0).as_tuple() == (0, 1, -1, 1)


def test_rational_requires_lowest_terms():
    """Rejects: two encodings of the same rational."""
    with pytest.raises(canon.ContractError):
        records.RationalValue(2, 4)
    assert records.RationalValue(1, 2).as_fraction() * 2 == 1
