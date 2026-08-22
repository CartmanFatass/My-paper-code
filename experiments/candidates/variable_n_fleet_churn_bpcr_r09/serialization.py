"""Frozen compact, canonical, independently decodable construction schemas."""

from __future__ import annotations

import hashlib
import struct
from typing import Mapping, Sequence
import zlib


BCRH_RECORD_SCHEMA="VNFC-BPCR-R09-BCRH-CANDIDATE-COMPARISON-LE-v1"
BCRH_RECORD=struct.Struct("<4i3i4Q3i4Qi")
if BCRH_RECORD.size!=108:raise AssertionError("BCRH packed record width differs")


def encode_bcrh_records(records:Sequence[Mapping[str,object]])->dict[str,object]:
    raw=bytearray()
    for record in records:
        command=tuple(255 if x is None else int(x) for x in record["command"])
        floor=tuple(int(x) for x in record["floor"]);objective=tuple(int(x) for x in record["objective_limbs"])
        checker_floor=tuple(int(x) for x in record["checker_floor"]);checker_objective=tuple(int(x) for x in record["checker_objective_limbs"])
        if len(command)!=4 or len(objective)!=4 or len(checker_objective)!=4:raise ValueError("BCRH record shape differs")
        raw.extend(BCRH_RECORD.pack(*command,*floor,int(record["releases"]),*objective,*checker_floor,int(record["checker_releases"]),*checker_objective,int(bool(record["exact_match"]))))
    payload=bytes(raw);compressed=zlib.compress(payload,level=9)
    return {"schema":BCRH_RECORD_SCHEMA,"record_count":len(records),"record_bytes":BCRH_RECORD.size,"uncompressed_bytes":len(payload),"uncompressed_sha256":hashlib.sha256(payload).hexdigest(),"codec":"zlib-level9-wbits15-no-dictionary","payload":compressed}


def decode_bcrh_records(packet:Mapping[str,object])->tuple[dict[str,object],...]:
    if packet.get("schema")!=BCRH_RECORD_SCHEMA or packet.get("record_bytes")!=108:raise ValueError("BCRH packet schema differs")
    raw=zlib.decompress(bytes(packet["payload"]));count=int(packet["record_count"])
    if len(raw)!=count*108 or hashlib.sha256(raw).hexdigest()!=packet.get("uncompressed_sha256"):raise ValueError("BCRH packet size/hash differs")
    rows=[]
    for offset in range(0,len(raw),108):
        x=BCRH_RECORD.unpack_from(raw,offset)
        rows.append({"command":tuple(None if v==255 else v for v in x[0:4]),"floor":x[4:6],"releases":x[6],"objective_limbs":x[7:11],"checker_floor":x[11:13],"checker_releases":x[13],"checker_objective_limbs":x[14:18],"exact_match":bool(x[18])})
    return tuple(rows)


def storage_contract()->dict[str,object]:
    return {"schema":"VNFC-BPCR-R09-COMPRESSED-STORAGE-CONTRACT-v1","byte_order":"little","bcrh_candidate_record_bytes":108,"bcrh_native_abi_record_bytes":120,"codec":"zlib level=9 wbits=15 no dictionary","hash_scope":"uncompressed canonical bytes","maximum_candidate_rows":12_050_000,"maximum_candidate_record_bytes":12_050_000*108}
