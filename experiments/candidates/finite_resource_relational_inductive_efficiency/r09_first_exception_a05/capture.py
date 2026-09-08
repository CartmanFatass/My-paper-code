"""One bounded A05 post-mortem read; loaded standalone by the fixed pdb input."""

import dataclasses
import inspect
import itertools
import json
import os
from pathlib import Path
import sys
import types


PREFIX = "experiments.candidates.finite_resource_relational_inductive_efficiency"
COORDINATES = (
    "seed_block", "purpose", "roster", "update", "episode", "basin",
    "event_ordinal", "slot", "public_role", "role_local_index", "sender",
    "receiver", "kind", "draw",
)
NULLABLE = frozenset(COORDINATES[5:12])
ARMS = ("PHY_TRUST", "EDGE_FLEX")
MISSING = object()
DICT_VALUES_ITERATOR = type(iter({}.values()))


def text(value):
    return {"value": value[:256], "truncated": len(value) > 256}


def identity(value):
    cls = type(value)
    return {
        "id": id(value), "type_id": id(cls),
        "type_name": text(type.__getattribute__(cls, "__name__")),
        "type_module": text(type.__getattribute__(cls, "__module__")),
    }


def primitive(value):
    """Render exact builtins only; never call an observed object's repr/str."""
    if value is MISSING:
        return {"status": "missing"}
    result = {"status": "observed", **identity(value)}
    if value is None or type(value) is bool:
        result["value"] = value
    elif type(value) is str:
        result.update(text(value))
    elif type(value) is int:
        if int.bit_length(value) <= 840:
            result["value"] = value
        else:
            result.update(status="integer_rendering_bounded", truncated=True)
    elif type(value) is float:
        # hex also preserves nonfinite values without nonstandard JSON numbers.
        result["hex"] = float.hex(value)
    else:
        result["status"] = "unexpected_type_not_rendered"
    return result


def reference(value):
    return {"status": "missing"} if value is MISSING else {"status": "observed", **identity(value)}


def field_record(value):
    result = identity(value)
    ordinary = type(value) is dataclasses.Field
    if ordinary:
        result["name"] = primitive(value.name)
        result["field_kind"] = identity(value._field_type)
        result["field_kind_is_FIELD"] = value._field_type is dataclasses._FIELD
    else:
        result["status"] = "unexpected_field_type_not_read"
    return result


def field_table(value):
    if value is MISSING:
        return {"status": "absent_attribute"}, False
    result = identity(value)
    if type(value) is not dict:
        result["status"] = "unexpected_container_not_iterated"
        return result, False
    result.update(status="observed_dict", length=len(value), truncated=len(value) > 14)
    entries = []
    names = set()
    ordinary = len(value) == 14
    for key, field in itertools.islice(dict.items(value), 14):
        entries.append({"key": primitive(key), "field": field_record(field)})
        expected = type(key) is str and key in COORDINATES
        if expected:
            names.add(key)
        ordinary &= (
            expected and type(field) is dataclasses.Field
            and type(field.name) is str and field.name == key
            and field._field_type is dataclasses._FIELD
        )
    result["entries"] = entries
    return result, ordinary and names == set(COORDINATES)


def frame_identity(frame, line):
    code = frame.f_code
    module = dict.get(frame.f_globals, "__name__", MISSING)
    return {
        "frame_id": id(frame), "code_id": id(code),
        "module": primitive(module), "filename": text(code.co_filename),
        "function": text(code.co_qualname), "line": line,
    }


def matches(frame, module, function, suffix):
    return (
        dict.get(frame.f_globals, "__name__") == module
        and frame.f_code.co_qualname == function
        and frame.f_code.co_filename.replace("\\", "/").endswith(suffix)
    )


def exception_record(error):
    result = identity(error)
    args = BaseException.args.__get__(error)
    result["args"] = [primitive(item) for item in args[:14]]
    result["args_truncated"] = len(args) > 14
    result["message"] = primitive(args[0]) if len(args) == 1 else {"status": "not_single_argument"}
    return result


def observe(error):
    result = {
        "observation": "no_active_exception_at_entry_prompt" if error is None else "post_mortem",
        "original_exception": None if error is None else exception_record(error),
        "frames": [], "frames_truncated": False, "missing_components": [],
        "capture_errors": [], "structure_checks": {}, "components": {},
        "capture_complete": False,
    }
    if error is None:
        return result
    frames = []
    tb = BaseException.__traceback__.__get__(error)
    while tb is not None and len(frames) < 32:
        frames.append(tb.tb_frame)
        result["frames"].append(frame_identity(tb.tb_frame, tb.tb_lineno))
        tb = tb.tb_next
    result["frames_truncated"] = tb is not None
    if tb is not None:
        result["missing_components"].append("traceback_beyond_32_frames")

    selectors = {
        "address": (PREFIX + ".rng", "SemanticRNGAddress.canonical_bytes", "/finite_resource_relational_inductive_efficiency/rng.py"),
        "fields": ("dataclasses", "fields", "/dataclasses.py"),
        "generator": ("dataclasses", "fields.<locals>.<genexpr>", "/dataclasses.py"),
        "execute": (PREFIX + ".b01_contact_r02.experiment", "execute", "/b01_contact_r02/experiment.py"),
    }
    selected = {}
    for name, selector in selectors.items():
        candidates = [frame for frame in frames if matches(frame, *selector)]
        if len(candidates) == 1:
            selected[name] = candidates[0]
        else:
            result["missing_components"].append(name + "_frame")
            result["components"][name] = {"status": "missing_or_ambiguous_frame", "matches": len(candidates)}

    def read(name, action):
        try:
            action()
        except Exception as failure:
            result["capture_errors"].append({"component": name, "error": exception_record(failure)})

    checks = result["structure_checks"]
    components = result["components"]
    address = MISSING
    instance_table = MISSING

    def address_state():
        nonlocal address, instance_table
        frame = selected["address"]
        address = dict.get(frame.f_locals, "self", MISSING)
        cls = dict.get(frame.f_globals, "SemanticRNGAddress", MISSING)
        if address is MISSING or cls is MISSING:
            result["missing_components"].append("address_self_or_declared_class")
            return
        state = {"object": identity(address), "declared_class": identity(cls), "coordinates": {}}
        components["address"] = state
        checks["address_has_declared_type"] = type(address) is cls
        for name in COORDINATES:
            value = inspect.getattr_static(address, name, MISSING)
            if type(value) is types.MemberDescriptorType:
                value = value.__get__(address, type(address))
            state["coordinates"][name] = primitive(value)
            checks["coordinate_" + name + "_type"] = (
                type(value) is str if name in ("seed_block", "purpose", "kind")
                else type(value) is int or (name in NULLABLE and value is None)
            )
        instance_table = inspect.getattr_static(address, "__dataclass_fields__", MISSING)
        class_table = inspect.getattr_static(cls, "__dataclass_fields__", MISSING)
        state["instance_table"], checks["instance_table_shape"] = field_table(instance_table)
        state["class_table"], checks["class_table_shape"] = field_table(class_table)
        checks["instance_class_tables_identical"] = instance_table is class_table and instance_table is not MISSING

    if "address" in selected:
        read("address", address_state)

    def fields_state():
        locals_ = selected["fields"].f_locals
        value = dict.get(locals_, "fields", MISSING)
        obj = dict.get(locals_, "class_or_instance", MISSING)
        components["fields"] = {"fields": reference(value), "class_or_instance": reference(obj)}
        if value is MISSING or obj is MISSING:
            result["missing_components"].append("fields_locals")
        else:
            checks["fields_local_is_instance_table"] = value is instance_table
            checks["fields_argument_is_address"] = obj is address

    if "fields" in selected:
        read("fields", fields_state)

    def generator_state():
        locals_ = selected["generator"].f_locals
        iterator = dict.get(locals_, ".0", MISSING)
        field = dict.get(locals_, "f", MISSING)
        components["generator"] = {
            "iterator": reference(iterator),
            "f": {"status": "absent_local"} if field is MISSING else field_record(field),
        }
        if iterator is MISSING:
            result["missing_components"].append("generator_iterator")
        else:
            checks["generator_has_dict_values_iterator"] = type(iterator) is DICT_VALUES_ITERATOR
        if field is not MISSING:
            checks["generator_f_is_Field"] = type(field) is dataclasses.Field

    if "generator" in selected:
        read("generator", generator_state)

    def counters_state():
        locals_ = selected["execute"].f_locals
        state = {}
        components["execute"] = state
        for name in ("number", "update", "paired_updates", "adam", "backward", "training_slots"):
            value = dict.get(locals_, name, MISSING)
            if value is MISSING:
                state[name] = primitive(value)
                result["missing_components"].append("execute_" + name)
            elif name in ("number", "update", "paired_updates"):
                state[name] = primitive(value)
                checks[name + "_nonnegative_integer"] = type(value) is int and value >= 0
            elif type(value) is not dict:
                state[name] = primitive(value)
                checks[name + "_arm_counters"] = False
            else:
                state[name] = {"object": identity(value), "entries": [], "truncated": len(value) > 2}
                ordinary = len(value) == 2
                arms = set()
                for arm, count in itertools.islice(dict.items(value), 2):
                    state[name]["entries"].append({"arm": primitive(arm), "count": primitive(count)})
                    expected = type(arm) is str and arm in ARMS
                    if expected:
                        arms.add(arm)
                    ordinary &= expected and type(count) is int and count >= 0
                checks[name + "_arm_counters"] = ordinary and arms == set(ARMS)

    if "execute" in selected:
        read("execute", counters_state)
    result["capture_complete"] = not result["missing_components"] and not result["capture_errors"]
    return result


def publish(error, output):
    try:
        result = observe(error)
    except Exception as failure:
        result = {
            "observation": "capture_failed", "capture_complete": False,
            "original_exception": None if error is None else exception_record(error),
            "capture_errors": [{"component": "capture", "error": exception_record(failure)}],
        }
    path = Path(output) / "summary.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print("A05_SUMMARY_WRITTEN")


if __name__ == "__a05_post_mortem__":
    publish(sys.exception(), os.environ["FRRIE_A05_OUTPUT"])
