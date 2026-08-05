"""canon-v1 serialization for the ORBIT owner-match D2 contract.

This module owns two encoders that must never be shared, because they answer
two different questions:

*   The DATA encoder (``serialize_struct`` and the ``_enc_*`` primitives)
    answers "what are these values".  It rejects nonfinite floats and
    canonicalizes ``-0.0`` to ``+0.0`` so that two structurally equal records
    always serialize to the same bytes.
*   The CODE-CONSTANT encoder (``encode_code_constant``) answers "what is
    this code object exactly".  It preserves the raw binary64 bit pattern of
    every float constant, including the sign of zero and nonfinite payloads.

Round-6 external validation found that D0.4 routed code constants through the
data encoder, so a mutant whose only difference was ``(-0.0, -0.0)`` in place
of ``(0.0, 0.0)`` produced an identical fingerprint.  That defeated the exact
freeze the positive-zero orientation argument depends on.  The two encoders
are kept in one module precisely so the separation is visible and testable in
one place.

Serialized form (canon-v1)::

    struct  := S(schema_id) T(n) field_0 .. field_{n-1}
    bool    := "B" 0x00|0x01
    int     := "I" u32(len) decimal-ascii        (bool is not an int here)
    float   := "F" big-endian-binary64           (finite only, -0.0 -> +0.0)
    bytes   := "Y" u32(len) raw
    str     := "S" u32(len) utf-8
    tuple   := "T" u32(count) item_0 .. item_{count-1}
    nested  := "Y" u32(len) struct               (length-framed)

Every field type is declared in the schema descriptor, so the reader never
infers a type from the value.  ``object.__getattribute__`` is used for field
access so an overridden ``__getattribute__`` on an instance cannot redirect a
read; note that this does NOT defeat a data descriptor installed on the exact
registered class, which is why :mod:`sealing` audits class dictionaries
separately.
"""

from __future__ import annotations

import hashlib
import struct as _structmod
from dataclasses import fields as _dc_fields
from types import MappingProxyType


SERIALIZER_VERSION = "orbit-owner-canon-v1"

_U32_MAX = 2**32 - 1


class ContractError(Exception):
    """A validity failure.

    ``terminal_class`` routes the outer controller.  It is constrained at
    construction time so that no ContractError can carry a class the terminal
    map does not know how to route -- round 6 found that an unrecognized
    class produced a bare KeyError inside the router itself.
    """

    VALID_CLASSES = frozenset({"T1", "T2", "T3", "T4"})

    def __init__(self, message: str, terminal_class: str = "T4") -> None:
        super().__init__(message)
        if type(terminal_class) is not str:
            raise TypeError("terminal_class must be str")
        if terminal_class not in ContractError.VALID_CLASSES:
            raise ValueError("unknown terminal_class %r" % (terminal_class,))
        self.terminal_class = terminal_class


def sha256_hex(data: bytes) -> str:
    if type(data) is not bytes:
        raise ContractError("exact bytes required for digest")
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# Primitive DATA encoders
# ---------------------------------------------------------------------------


def _u32(n: int) -> bytes:
    if type(n) is not int or n < 0 or n > _U32_MAX:
        raise ContractError("length outside u32 framing")
    return _structmod.pack(">I", n)


def _enc_bool(v: object) -> bytes:
    if type(v) is not bool:
        raise ContractError("exact bool required")
    return b"B" + (b"\x01" if v else b"\x00")


def _enc_int(v: object) -> bytes:
    # ``type(v) is not int`` rejects bool, which is a subclass of int.  Round 6
    # found bool silently admitted as an analysis label; this is the choke
    # point that makes that impossible at the serialization boundary.
    if type(v) is not int:
        raise ContractError("exact int required")
    text = str(v).encode("ascii")
    return b"I" + _u32(len(text)) + text


def _enc_float(v: object) -> bytes:
    if type(v) is not float:
        raise ContractError("exact float required")
    if v != v or v in (float("inf"), float("-inf")):
        raise ContractError("nonfinite float rejected")
    if v == 0.0:
        v = 0.0  # canonicalize -0.0 to +0.0 for DATA only
    return b"F" + _structmod.pack(">d", v)


def _enc_bytes(v: object) -> bytes:
    if type(v) is not bytes:
        raise ContractError("exact bytes required")
    return b"Y" + _u32(len(v)) + v


def _enc_str(v: object) -> bytes:
    if type(v) is not str:
        raise ContractError("exact str required")
    encoded = v.encode("utf-8", errors="strict")
    return b"S" + _u32(len(encoded)) + encoded


_PRIMITIVE_ENCODERS = {
    "bool": _enc_bool,
    "int": _enc_int,
    "float": _enc_float,
    "bytes": _enc_bytes,
    "str": _enc_str,
}

PRIMITIVE_TYPES = frozenset(_PRIMITIVE_ENCODERS)


# ---------------------------------------------------------------------------
# Schema registry
# ---------------------------------------------------------------------------

# schema_id -> (registered class, tuple of (field_name, normalized_type))
_REGISTRY: dict = {}
_SEALED: list = []

REGISTRY_VIEW = MappingProxyType(_REGISTRY)


def _validate_normalized_type(normalized_type: str) -> None:
    if type(normalized_type) is not str:
        raise ContractError("normalized type must be str")
    if normalized_type in PRIMITIVE_TYPES:
        return
    if normalized_type.startswith("tuple[") and normalized_type.endswith("]"):
        inner, count_text = normalized_type[6:-1].rsplit(";", 1)
        if not count_text.isdigit():
            raise ContractError("tuple cardinality must be a literal count")
        _validate_normalized_type(inner)
        return
    if normalized_type.startswith("struct:"):
        return
    raise ContractError("unknown normalized type %r" % (normalized_type,))


def register_schema(schema_id: str, cls: type,
                    descriptor: tuple) -> None:
    if _SEALED:
        raise ContractError("registry is sealed; late registration rejected")
    if type(schema_id) is not str or not schema_id:
        raise ContractError("schema id must be a non-empty str")
    if schema_id in _REGISTRY:
        raise ContractError("duplicate schema registration")
    if type(descriptor) is not tuple:
        raise ContractError("descriptor must be a tuple")
    declared = tuple(f.name for f in _dc_fields(cls))
    if declared != tuple(name for name, _ in descriptor):
        raise ContractError("descriptor does not match dataclass fields")
    for _, normalized_type in descriptor:
        _validate_normalized_type(normalized_type)
    _REGISTRY[schema_id] = (cls, descriptor)


def registered_class(schema_id: str) -> type:
    if schema_id not in _REGISTRY:
        raise ContractError("unknown schema id %r" % (schema_id,))
    return _REGISTRY[schema_id][0]


def descriptor_of(schema_id: str) -> tuple:
    if schema_id not in _REGISTRY:
        raise ContractError("unknown schema id %r" % (schema_id,))
    return _REGISTRY[schema_id][1]


def schema_ids() -> tuple:
    return tuple(sorted(_REGISTRY))


# ---------------------------------------------------------------------------
# Structured DATA serialization
# ---------------------------------------------------------------------------


def _enc_typed(value: object, normalized_type: str) -> bytes:
    if normalized_type in _PRIMITIVE_ENCODERS:
        return _PRIMITIVE_ENCODERS[normalized_type](value)
    if normalized_type.startswith("tuple["):
        inner, count_text = normalized_type[6:-1].rsplit(";", 1)
        count = int(count_text)
        if type(value) is not tuple:
            raise ContractError("exact tuple required")
        if len(value) != count:
            raise ContractError("tuple cardinality mismatch")
        body = b"".join(_enc_typed(item, inner) for item in value)
        return b"T" + _u32(count) + body
    if normalized_type.startswith("struct:"):
        nested_bytes = serialize_struct(normalized_type[7:], value)
        return b"Y" + _u32(len(nested_bytes)) + nested_bytes
    raise ContractError("unknown normalized type")


def serialize_struct(schema_id: str, value: object) -> bytes:
    if schema_id not in _REGISTRY:
        raise ContractError("unknown schema id %r" % (schema_id,))
    cls, descriptor = _REGISTRY[schema_id]
    if type(value) is not cls:
        raise ContractError("exact registered class required for %r"
                            % (schema_id,))
    body = []
    for field_name, normalized_type in descriptor:
        field_value = object.__getattribute__(value, field_name)
        body.append(_enc_typed(field_value, normalized_type))
    return (_enc_str(schema_id) + b"T" + _u32(len(descriptor))
            + b"".join(body))


def schema_registry_digest() -> str:
    """Digest over the whole registry: schema ids, classes and descriptors.

    Sorted by schema id so the digest does not depend on registration order.

    The registered CLASS is part of the digest.  Digesting only ids and
    descriptors left a schema id repointable to an impostor class with the
    same field shape: the seal gate still passed, while ``serialize_struct``
    began accepting the impostor and rejecting the genuine record.  The
    binding from id to class is exactly what a schema registry is for, so it
    belongs in the digest.
    """
    entries = []
    for schema_id in sorted(_REGISTRY):
        cls, descriptor = _REGISTRY[schema_id]
        entries.append(_enc_str(schema_id))
        entries.append(_enc_str(cls.__module__ + "." + cls.__qualname__))
        entries.append(_enc_typed(
            tuple(name + "|" + typ for name, typ in descriptor),
            "tuple[str;%d]" % len(descriptor)))
    return sha256_hex(b"".join(entries))


def seal_registry() -> str:
    """Freeze the registry contents and remember their digest.

    After sealing, ``register_schema`` refuses to add anything and
    ``registry_seal_gate`` can detect post-seal mutation of the mapping.
    """
    if _SEALED:
        raise ContractError("registry already sealed")
    digest = schema_registry_digest()
    _SEALED.append(digest)
    return digest


def sealed_digest() -> str:
    if not _SEALED:
        raise ContractError("registry not sealed")
    return _SEALED[0]


def registry_seal_gate() -> None:
    """Validity gate: the live registry still matches its sealed digest."""
    if not _SEALED:
        raise ContractError("registry not sealed", "T3")
    if schema_registry_digest() != _SEALED[0]:
        raise ContractError("registry mutated after sealing", "T3")


# ---------------------------------------------------------------------------
# CODE-CONSTANT encoder (raw bits; never shared with the DATA encoder)
# ---------------------------------------------------------------------------


def encode_float_raw(v: float) -> bytes:
    """Encode a float by its exact binary64 bits.

    No canonicalization: ``-0.0`` and ``+0.0`` produce different bytes, and a
    NaN keeps its payload.  This is the encoder code fingerprinting must use.
    """
    if type(v) is not float:
        raise ContractError("exact float required")
    return b"f" + _structmod.pack(">d", v)


def encode_code_constant(value: object, fingerprint_code) -> bytes:
    """Encode one entry of ``co_consts``.

    ``fingerprint_code`` is injected rather than imported so this module has
    no dependency on :mod:`sealing`; the recursion for nested code objects
    still covers comprehensions and lambdas.  Any constant type outside the
    closed set fails closed rather than degrading to ``repr``.
    """
    if value is None:
        return b"N"
    if value is Ellipsis:
        return b"E"
    if type(value) is bool:
        return b"Pb" + (b"\x01" if value else b"\x00")
    if type(value) is int:
        text = str(value).encode("ascii")
        return b"Pi" + _u32(len(text)) + text
    if type(value) is float:
        return b"P" + encode_float_raw(value)
    if type(value) is complex:
        return (b"Pc" + encode_float_raw(value.real)
                + encode_float_raw(value.imag))
    if type(value) is str:
        encoded = value.encode("utf-8", errors="surrogatepass")
        return b"Ps" + _u32(len(encoded)) + encoded
    if type(value) is bytes:
        return b"Py" + _u32(len(value)) + value
    if type(value) is tuple:
        return (b"T" + _u32(len(value))
                + b"".join(encode_code_constant(item, fingerprint_code)
                           for item in value))
    if type(value) is frozenset:
        # Order-independent: fold the element encodings through XOR of their
        # digests so an equal frozenset always yields equal bytes.
        acc = bytearray(32)
        for item in value:
            item_digest = hashlib.sha256(
                encode_code_constant(item, fingerprint_code)).digest()
            for index in range(32):
                acc[index] ^= item_digest[index]
        return b"Pz" + _u32(len(value)) + bytes(acc)
    if hasattr(value, "co_code"):
        return b"C" + bytes.fromhex(fingerprint_code(value))
    raise ContractError("unsupported code constant type (fail closed)", "T3")
