"""Fixed lossless B01 table and strict upstream token-sequence validation.

Importing this module performs no tokenization, model initialization or RNG draw.
The admitted caller verifies the artifact manifest before invoking the tokenizer.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
import json
from pathlib import Path
from typing import Any

from .contract import KINDS, digest, validate_features

MAX_LEN = 4096
HEAD_MAX_LEN = 192
QUESTION = ("Choose the complete UAV target plan with greatest mean backhauled-user "
            "fraction over 500 steps, including travel.")
HEADER = ("UAV plans; coordinates in metres. Six UAVs, fifty users, one base station. "
          "Speed 30 m/s; free-space, no shadowing; FDMA; ten connections/UAV; three hops. "
          "U=initial UAV XYZ; G=user XY; B=base XYZ; M=legal slots; D=display slots. "
          "P=slot,kind,k then six assigned XYZ triples in UAV identity order. "
          "Kinds: 0=kmeans_plain,1=subset_relay,2=subset_flat.")


def _numbers(value) -> str:
    return " ".join(format(float(x), ".17g") for x in value)


def render_state(features: dict[str, Any], *, reverse: bool = False) -> str:
    validate_features(features)
    if "display_order" not in features:
        raise ValueError("missing predeclared display order")
    order = list(features["display_order"])
    if reverse:
        order.reverse()
    lines = [HEADER, "U " + _numbers(x for row in features["initial_uav_xyz"] for x in row),
             "G " + _numbers(x for row in features["user_xy"] for x in row),
             "B " + _numbers(features["bs_xyz"]),
             "M " + " ".join(str(int(x)) for x in features["legal_mask"]),
             "D " + " ".join(str(x) for x in order)]
    for plan in sorted(features["plans"], key=lambda p: p["construction_slot"]):
        lines.append("P " + " ".join(map(str, [plan["construction_slot"],
                     KINDS.index(plan["kind"]), plan["k"]])) + " " +
                     _numbers(x for row in plan["assigned_targets_xyz"] for x in row))
    return "\n".join(lines)


def parse_state(text: str) -> dict[str, Any]:
    """Exact inverse, rejecting unexpected fields, rows and noncanonical numbers."""
    lines = text.splitlines()
    if not lines or lines[0] != HEADER or not 7 <= len(lines) <= 14:
        raise ValueError("invalid state header or row count")
    def values(index, prefix, count):
        parts = lines[index].split(" ")
        if parts[0] != prefix or len(parts) != count + 1:
            raise ValueError(f"invalid {prefix} row")
        result = list(map(float, parts[1:]))
        if _numbers(result) != " ".join(parts[1:]):
            raise ValueError("noncanonical coordinate spelling")
        return result
    def rows(flat, width):
        return [flat[i:i + width] for i in range(0, len(flat), width)]
    initial, users, bs = values(1, "U", 18), values(2, "G", 100), values(3, "B", 3)
    masks, order = lines[4].split(" "), lines[5].split(" ")
    if masks[0] != "M" or len(masks) != 9 or any(v not in ("0", "1") for v in masks[1:]):
        raise ValueError("invalid mask row")
    if order[0] != "D" or any(v not in tuple(map(str, range(8))) for v in order[1:]):
        raise ValueError("invalid order row")
    plans = []
    for line in lines[6:]:
        parts = line.split(" ")
        if parts[0] != "P" or len(parts) != 22:
            raise ValueError("invalid plan row")
        slot, kind, k = map(int, parts[1:4])
        if not 0 <= kind < len(KINDS):
            raise ValueError("invalid kind")
        xyz = list(map(float, parts[4:]))
        if _numbers(xyz) != " ".join(parts[4:]):
            raise ValueError("noncanonical target spelling")
        plans.append({"construction_slot": slot, "kind": KINDS[kind], "k": k,
                      "assigned_targets_xyz": rows(xyz, 3)})
    result = {"initial_uav_xyz": rows(initial, 3), "user_xy": rows(users, 2), "bs_xyz": bs,
              "legal_mask": [v == "1" for v in masks[1:]],
              "display_order": list(map(int, order[1:])), "plans": plans}
    validate_features(result)
    if render_state(result) != text:
        raise ValueError("state did not round trip canonically")
    return result


@lru_cache(maxsize=1)
def _tokenizer(model_root: str):
    from transformers import PreTrainedTokenizerFast
    root = Path(model_root) / "tokenizer"
    config = json.loads((root / "tokenizer_config.json").read_text())
    # Equivalent to upstream's compatibility rewrite, in memory only: preserve all
    # token identities and the downloaded bytes, without fetching another tokenizer.
    for key in ("tokenizer_class", "backend", "is_local", "tokenizer_file"):
        config.pop(key, None)
    return PreTrainedTokenizerFast(tokenizer_file=str(root / "tokenizer.json"), **config)


def encode_features(features: dict[str, Any], model_root: str | Path,
                    *, reverse: bool = False) -> dict[str, Any]:
    """Use the pinned upstream builder; fail closed on any lost token or field."""
    from .vendor import laya_common as upstream
    state = render_state(features, reverse=reverse)
    parsed = parse_state(state)
    expected = dict(features)
    expected["display_order"] = list(reversed(features["display_order"])) if reverse else features["display_order"]
    if parsed != expected:
        raise ValueError("typed/numeric record inequality")
    order = parsed["display_order"]
    tok = _tokenizer(str(Path(model_root).resolve()))
    refs = [f"P{slot}" for slot in order]
    q = {"t": "choice", "ins": QUESTION, "crit": {ref: "" for ref in refs}}
    state_ids = tok(state, add_special_tokens=False)["input_ids"]
    head_ids = tok("choice question: " + QUESTION, add_special_tokens=False)["input_ids"]
    option_ids = [tok(" " + ref, add_special_tokens=False)["input_ids"] for ref in refs]
    if any(len(ids) > 48 for ids in option_ids):
        raise ValueError("option would hit upstream 48-token cap")
    ids, markers, option_stats, truncation = upstream.build_sequence(
        tok, state, q, max_len=MAX_LEN, head_max_len=HEAD_MAX_LEN,
        state_ids=state_ids, return_stats=True, return_truncation_stats=True)
    # Reconstruct the expected untruncated sequence independently of upstream's
    # slice/statistics implementation, including instruction and option spans.
    expected_ids = [tok.cls_token_id] + head_ids + [tok.sep_token_id]
    expected_markers = []
    for option in option_ids:
        expected_markers.append(len(expected_ids))
        expected_ids.extend([tok.mask_token_id] + option)
    expected_ids += [tok.sep_token_id] + state_ids + [tok.sep_token_id]
    if (len(expected_ids) > MAX_LEN or ids != expected_ids or markers != expected_markers
            or truncation["truncated"] or truncation["state_tokens_dropped"] != 0
            or option_stats["options_distinct"] != len(refs)
            or len(set(tuple(x) for x in option_ids)) != len(refs)):
        raise ValueError(json.dumps({"reason": "non-lossless Laya input", "full_tokens": len(expected_ids),
                                     "returned_tokens": len(ids), "options": option_stats,
                                     "truncation": truncation, "feature_sha256": digest(features)}))
    return {"input_ids": ids, "marker_pos": markers, "construction_slots": order,
            "state": state, "question": q, "state_sha256": hashlib.sha256(state.encode()).hexdigest(),
            "feature_sha256": digest(features), "full_tokens": len(ids),
            "state_tokens": len(state_ids), "option_tokens": list(map(len, option_ids)),
            "reverse": reverse}


def validate_native_features(features: dict[str, Any], model_root: str | Path) -> dict[str, Any]:
    encoded = encode_features(features, model_root)
    # Reversal changes no token count or option tokens. The later paid reversed
    # encoder pass uses encode_features again and checks its actual sequence too.
    return {key: encoded[key] for key in ("state_sha256", "feature_sha256", "full_tokens",
                                        "state_tokens", "option_tokens", "construction_slots")}
