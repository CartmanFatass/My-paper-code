"""Exact fixed-width r05 wire codecs used by preactivity conformance tests.

The codec is result-blind and authority-free.  It materializes only TEST wire
fixtures, applies the registered float32 rounding, and verifies the first-four-
SHA256-byte integrity rule.  It creates no scientific identity or coordinate.
"""

from __future__ import annotations

import hashlib
import math
import struct
from typing import Mapping, Sequence


class ProductionProtocolError(ValueError):
    pass


WIRE_SIZES = {
    "SOURCE": 40,
    "SERVICE_RELAY": 64,
    "STATE": 64,
    "SNAPSHOT": 96,
    "READINESS": 48,
    "COMMIT_INTENT": 32,
    "NOOP_INTENT": 32,
    "COMMIT_RESULT": 24,
}


def _u8(value: object) -> int:
    result = int(value)
    if not 0 <= result <= 0xFF:
        raise ProductionProtocolError("uint8 field is out of range")
    return result


def _u16(value: object) -> int:
    result = int(value)
    if not 0 <= result <= 0xFFFF:
        raise ProductionProtocolError("uint16 field is out of range")
    return result


def _u32(value: object) -> int:
    result = int(value)
    if not 0 <= result <= 0xFFFFFFFF:
        raise ProductionProtocolError("uint32 field is out of range")
    return result


def _floats(values: object, count: int) -> tuple[float, ...]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes, bytearray)):
        raise ProductionProtocolError("float-vector field is not a sequence")
    result = tuple(float(value) for value in values)
    if len(result) != count or not all(math.isfinite(value) for value in result):
        raise ProductionProtocolError("float-vector field differs")
    return result


def _finish(kind: str, body: bytes) -> bytes:
    size = WIRE_SIZES[kind]
    if len(body) + 4 > size:
        raise ProductionProtocolError(f"{kind} body exceeds its fixed wire size")
    encoded = body + hashlib.sha256(body).digest()[:4]
    return encoded + bytes(size - len(encoded))


def encode_wire(kind: str, fields: Mapping[str, object]) -> bytes:
    """Encode one exact fixed-width message with registered field order."""

    if kind not in WIRE_SIZES:
        raise ProductionProtocolError("wire message kind is not registered")
    try:
        if kind == "SOURCE":
            body = struct.pack(
                "<II4f", _u32(fields["source_sequence"]), _u32(fields["source_tick"]),
                *_floats(fields["z"], 4),
            )
        elif kind == "SERVICE_RELAY":
            source = bytes(fields["source_body"])
            if len(source) != WIRE_SIZES["SOURCE"] or not verify_wire("SOURCE", source):
                raise ProductionProtocolError("SERVICE_RELAY source body is not one valid opaque SOURCE")
            body = struct.pack(
                "<HII B", _u16(fields["service_epoch"]), _u32(fields["payload_sequence"]),
                _u32(fields["relay_tick"]), _u8(fields["sender_id"]),
            ) + source + struct.pack("<f", _floats((fields["source_first_hop_margin"],), 1)[0])
        elif kind == "STATE":
            body = struct.pack(
                "<I6f f B 2f B H H 3B",
                _u32(fields["sender_tick"]), *_floats(fields["motion"], 6),
                _floats((fields["battery"],), 1)[0], _u8(fields["camera_missing"]),
                *_floats(fields["margins"], 2), _u8(fields["owner_bit"]),
                _u16(fields["service_epoch"]), _u16(fields["k_epoch"]),
                _u8(fields["D"]), _u8(fields["G1"]), _u8(fields["G5"]),
            )
        elif kind == "SNAPSHOT":
            body = struct.pack(
                "<B H I I H I 4f 10f 2f 2f",
                _u8(fields["owner_id"]), _u16(fields["service_epoch"]),
                _u32(fields["post_reservation_next_payload_sequence"]),
                _u32(fields["common_source_sequence"]), _u16(fields["k_epoch"]),
                _u32(fields["snapshot_tick"]), *_floats(fields["prediction_mean"], 4),
                *_floats(fields["prediction_covariance_upper"], 10),
                *_floats(fields["margins"], 2), *_floats(fields["raw_boundary_mean"], 2),
            )
        elif kind == "READINESS":
            body = struct.pack(
                "<B B I I H I I H f f 2f f",
                _u8(fields["sender_id"]), _u8(fields["accepted_snapshot_owner"]),
                _u32(fields["readiness_tick"]), _u32(fields["accepted_snapshot_tick"]),
                _u16(fields["service_epoch"]),
                _u32(fields["post_reservation_next_payload_sequence"]),
                _u32(fields["common_source_sequence"]), _u16(fields["k_epoch"]),
                _floats((fields["Q95"],), 1)[0], _floats((fields["d_m_squared"],), 1)[0],
                *_floats(fields["candidate_raw_mean"], 2),
                _floats((fields["commit_probability"],), 1)[0],
            )
        elif kind in ("COMMIT_INTENT", "NOOP_INTENT"):
            request = _u8(fields["request_transfer"])
            if request != (1 if kind == "COMMIT_INTENT" else 0):
                raise ProductionProtocolError("intent kind and transfer bit disagree")
            body = struct.pack(
                "<I I B B H I I H B B",
                _u32(fields["origin_tick"]), _u32(fields["bound_readiness_tick"]),
                _u8(fields["old_owner"]), _u8(fields["new_owner"]),
                _u16(fields["service_epoch"]),
                _u32(fields["post_reservation_next_payload_sequence"]),
                _u32(fields["common_source_sequence"]), _u16(fields["k_epoch"]),
                _u8(fields["origin_certificate_pass"]), request,
            )
        else:
            body = struct.pack(
                "<I B B B H I H",
                _u32(fields["application_tick"]), _u8(fields["success"]),
                _u8(fields["reason_code"]), _u8(fields["owner_id"]),
                _u16(fields["service_epoch"]), _u32(fields["next_payload_sequence"]),
                _u16(fields["k_epoch"]),
            )
    except KeyError as error:
        raise ProductionProtocolError(f"{kind} field is absent: {error.args[0]}") from error
    return _finish(kind, body)


def integrity_offset(kind: str) -> int:
    return {
        "SOURCE": 24, "SERVICE_RELAY": 55, "STATE": 49, "SNAPSHOT": 89,
        "READINESS": 42, "COMMIT_INTENT": 24, "NOOP_INTENT": 24,
        "COMMIT_RESULT": 15,
    }[kind]


def verify_wire(kind: str, encoded: bytes) -> bool:
    if kind not in WIRE_SIZES or len(encoded) != WIRE_SIZES[kind]:
        return False
    offset = integrity_offset(kind)
    return (
        encoded[offset:offset + 4] == hashlib.sha256(encoded[:offset]).digest()[:4]
        and not any(encoded[offset + 4:])
    )


def test_wire_fixture_inventory() -> dict[str, object]:
    """Encode, verify, and tamper-check all eight wire identities."""

    source = encode_wire("SOURCE", {"source_sequence": 7, "source_tick": 9, "z": (1, 2, 3, 4)})
    common = {
        "service_epoch": 2, "post_reservation_next_payload_sequence": 11,
        "common_source_sequence": 7, "k_epoch": 3,
    }
    rows = {
        "SOURCE": source,
        "SERVICE_RELAY": encode_wire("SERVICE_RELAY", {
            "service_epoch": 2, "payload_sequence": 10, "relay_tick": 9,
            "sender_id": 1, "source_body": source, "source_first_hop_margin": 8.25,
        }),
        "STATE": encode_wire("STATE", {
            "sender_tick": 9, "motion": (1, 2, 3, 4, 5, 6), "battery": 1234,
            "camera_missing": 0, "margins": (7.5, 8.5), "owner_bit": 1,
            "service_epoch": 2, "k_epoch": 3, "D": 1, "G1": 0, "G5": 1,
        }),
        "SNAPSHOT": encode_wire("SNAPSHOT", {
            "owner_id": 1, **common, "snapshot_tick": 9,
            "prediction_mean": (1, 2, 3, 4), "prediction_covariance_upper": tuple(range(10)),
            "margins": (7.5, 8.5), "raw_boundary_mean": (0.25, -0.5),
        }),
        "READINESS": encode_wire("READINESS", {
            "sender_id": 0, "accepted_snapshot_owner": 1, "readiness_tick": 10,
            "accepted_snapshot_tick": 9, **common, "Q95": 0.75, "d_m_squared": 1.5,
            "candidate_raw_mean": (0.25, -0.5), "commit_probability": 0.6,
        }),
        "COMMIT_INTENT": encode_wire("COMMIT_INTENT", {
            "origin_tick": 11, "bound_readiness_tick": 10, "old_owner": 1,
            "new_owner": 0, **common, "origin_certificate_pass": 1,
            "request_transfer": 1,
        }),
        "NOOP_INTENT": encode_wire("NOOP_INTENT", {
            "origin_tick": 11, "bound_readiness_tick": 10, "old_owner": 1,
            "new_owner": 0, **common, "origin_certificate_pass": 1,
            "request_transfer": 0,
        }),
        "COMMIT_RESULT": encode_wire("COMMIT_RESULT", {
            "application_tick": 12, "success": 1, "reason_code": 0, "owner_id": 0,
            "service_epoch": 3, "next_payload_sequence": 11, "k_epoch": 3,
        }),
    }
    for kind, encoded in rows.items():
        if not verify_wire(kind, encoded):
            raise ProductionProtocolError(f"{kind} fixture failed its integrity contract")
        tampered = bytearray(encoded); tampered[0] ^= 1
        if verify_wire(kind, bytes(tampered)):
            raise ProductionProtocolError(f"{kind} tamper was accepted")
    return {
        "schema": "DISH_RBHR_R05_WIRE_FIXTURE_INVENTORY_V1",
        "message_count": len(rows), "wire_sizes": dict(WIRE_SIZES),
        "all_integrity_verified": True, "all_tamper_rejected": True,
        "sha256": hashlib.sha256(b"".join(rows[kind] for kind in WIRE_SIZES)).hexdigest(),
        "test_only": True, "question_relevant_output": False,
    }


__all__ = [
    "ProductionProtocolError", "WIRE_SIZES", "encode_wire", "integrity_offset",
    "test_wire_fixture_inventory", "verify_wire",
]
