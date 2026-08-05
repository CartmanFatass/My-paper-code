"""Code fingerprints, call-graph closure, and live-object sealing.

Round 6 rejected D0.4's closure story on four grounds, all answered here.

``the fingerprint erased signed zero``
    ``_encode_const`` routed finite floats through the DATA encoder, which
    canonicalizes ``-0.0`` to ``+0.0``.  A mutant differing only in the sign
    of a zero constant fingerprinted identically -- defeating exactly the
    distinction the positive-orientation argument depends on.
    :func:`fingerprint_code` now uses the raw-bit encoder and also covers
    ``co_stacksize`` and ``co_qualname``.
``trusted inherited callees were outside the freeze``
    Fingerprinting two entry points does not fingerprint what they call.
    :func:`call_graph` walks ``LOAD_GLOBAL`` transitively and returns every
    reachable function, including the inherited ones, and the audit machinery
    itself.
``the runtime trust surface was mutable``
    ``frozen=True`` freezes instance assignment, not class dictionaries,
    module globals, or descriptor installation.  :func:`live_object_gate`
    pins global bindings by digest, checks class behavior, and refuses to run
    under a tracing or profiling hook.
``T2 was a subset test on names``
    Delegated to :func:`trust.t2_surface_descriptor_gate`, which compares the
    complete descriptor including normalized types.

What this cannot prove is stated plainly rather than papered over: a
sufficiently privileged in-process actor can defeat any in-process audit.
The claim is closure against the ambient and object-behavior channels the
contract enumerates, checked before and after the audited phase, not
closure against an adversary who controls the interpreter.
"""

from __future__ import annotations

import builtins as _builtins
import dis
import sys
import types

from experiments.candidates.orbit_shadow_read import eight_cell_audit

from experiments.candidates.orbit_owner_match import block as block_module
from experiments.candidates.orbit_owner_match import canon as canon_module
from experiments.candidates.orbit_owner_match import controls as controls_module
from experiments.candidates.orbit_owner_match import (
    discriminator as discriminator_module,
)
from experiments.candidates.orbit_owner_match import records as records_module
from experiments.candidates.orbit_owner_match import trust as trust_module
from experiments.candidates.orbit_owner_match.canon import (
    ContractError,
    REGISTRY_VIEW,
    _PRIMITIVE_ENCODERS,
    _enc_bytes,
    _enc_int,
    _enc_str,
    _enc_typed,
    descriptor_of,
    encode_code_constant,
    encode_float_raw,
    sha256_hex,
)
from experiments.candidates.orbit_owner_match.records import (
    CodeFingerprintRecord,
    SCHEMA_ACTOR_INPUT_D2,
    _D1_ACTOR_FIELDS,
    _SCHEMA_TABLE,
    D2,
)
from experiments.candidates.orbit_owner_match.trust import (
    GUARDED_CONSTRUCTORS,
    t2_surface_descriptor_gate,
    actor_input_schema_binding_gate,
)


OWNED_MODULES = (
    canon_module,
    records_module,
    trust_module,
    block_module,
    controls_module,
    discriminator_module,
    eight_cell_audit,
)

OWNED_MODULE_NAMES = frozenset(module.__name__ for module in OWNED_MODULES)

ALLOWED_IMPORTED_MODULES = frozenset({"math", "hashlib", "hmac", "struct",
                                      "dis", "sys", "types", "json",
                                      "fractions", "dataclasses", "enum",
                                      "pathlib", "mpmath"})


# ---------------------------------------------------------------------------
# Code fingerprints
# ---------------------------------------------------------------------------


# Bytecode differs between interpreter versions, so every fingerprint-bearing
# digest is meaningful only relative to a declared interpreter.  Freezing that
# declaration turns "this reviewer got a different digest" into a clear
# mismatch error instead of an unattributable disagreement.
INTERPRETER_CONTRACT = ("cpython", 3, 11)


def interpreter_gate() -> None:
    """The interpreter is the one the frozen digests were produced under."""
    name = sys.implementation.name
    major, minor = sys.version_info[:2]
    if (name, major, minor) != INTERPRETER_CONTRACT:
        raise ContractError(
            "interpreter %s %d.%d does not match the frozen contract %r"
            % (name, major, minor, INTERPRETER_CONTRACT), "T3")


def fingerprint_code(code) -> str:
    """Recursive, fail-closed fingerprint of a code object.

    ``co_filename`` and ``co_firstlineno`` are deliberately excluded: they
    encode where the file happens to live and how it happens to be laid out,
    which would make every fingerprint checkout-dependent and therefore
    useless as a frozen literal an external reviewer can reproduce.

    ``co_qualname`` and ``co_exceptiontable`` are required rather than
    defaulted.  Reading them through ``getattr`` with a fallback meant that
    on an interpreter lacking them the fingerprint silently covered less
    while still claiming to cover them.
    """
    if not hasattr(code, "co_qualname") or not hasattr(code,
                                                       "co_exceptiontable"):
        raise ContractError(
            "interpreter lacks co_qualname/co_exceptiontable; fingerprints "
            "would silently cover less than the contract claims", "T3")
    parts = [
        _enc_str(code.co_name),
        _enc_str(code.co_qualname),
        _enc_int(code.co_argcount),
        _enc_int(code.co_posonlyargcount),
        _enc_int(code.co_kwonlyargcount),
        _enc_int(code.co_nlocals),
        _enc_int(code.co_stacksize),
        _enc_int(code.co_flags),
        _enc_bytes(code.co_code),
        _enc_typed(code.co_names, "tuple[str;%d]" % len(code.co_names)),
        _enc_typed(code.co_varnames, "tuple[str;%d]" % len(code.co_varnames)),
        _enc_typed(code.co_freevars, "tuple[str;%d]" % len(code.co_freevars)),
        _enc_typed(code.co_cellvars, "tuple[str;%d]" % len(code.co_cellvars)),
        _enc_bytes(code.co_exceptiontable),
        b"".join(encode_code_constant(const, fingerprint_code)
                 for const in code.co_consts),
    ]
    return sha256_hex(b"".join(parts))


def fingerprint_function(fn) -> str:
    if fn.__defaults__ is not None or fn.__kwdefaults__ is not None:
        raise ContractError("registered function must have no defaults", "T3")
    if fn.__closure__ is not None:
        raise ContractError("registered function must have no closure", "T3")
    return fingerprint_code(fn.__code__)


# ---------------------------------------------------------------------------
# Call-graph closure
# ---------------------------------------------------------------------------


def _global_names(code) -> set:
    names = set()
    stack = [code]
    while stack:
        current = stack.pop()
        for instruction in dis.get_instructions(current):
            if instruction.opname in ("LOAD_GLOBAL", "LOAD_NAME"):
                names.add(instruction.argval)
        for const in current.co_consts:
            if hasattr(const, "co_code"):
                stack.append(const)
    return names


def call_graph(roots: tuple) -> dict:
    """Transitive closure of ``roots`` over ``LOAD_GLOBAL`` references.

    Only functions defined in :data:`OWNED_MODULES` are followed; anything
    else (builtins, allowed stdlib) is a leaf, recorded by the binding audit
    rather than fingerprinted.
    """
    reached = {}
    pending = list(roots)
    while pending:
        fn = pending.pop()
        qualname = fn.__module__ + "." + fn.__qualname__
        if qualname in reached:
            continue
        reached[qualname] = fn
        for name in _global_names(fn.__code__):
            target = fn.__globals__.get(name)
            if type(target) is not types.FunctionType:
                continue
            if target.__module__ not in OWNED_MODULE_NAMES:
                continue
            pending.append(target)
    return reached


ACCEPTED_ROOTS = (
    block_module.build_target_cell,
    block_module.build_block,
    block_module.cross_m_closure_gate,
    block_module.cross_q_closure_gate,
    block_module.clone_independence_gate,
    block_module.public_write_invariance_gate,
    block_module.lineage_rebuild_gate,
    trust_module.verify_write_d2,
    trust_module.declassify,
    trust_module.extend_d1_actor_input,
    trust_module.build_write_d2_with_b,
    trust_module.project_write_D1,
    trust_module.strip_predicate,
    discriminator_module.owner_predicate_actor,
    discriminator_module.evaluate_block,
    discriminator_module.estimands,
    discriminator_module.calibrate,
    controls_module.exact_accumulate,
    controls_module.oriented_pair_first_m_blind,
    controls_module.oriented_pair_first_b_blind,
    eight_cell_audit.actor,
    eight_cell_audit._softmax,
    eight_cell_audit.q_adapter,
    eight_cell_audit.write_sibling,
    eight_cell_audit.verify_sibling,
    eight_cell_audit.restore_clone,
    eight_cell_audit.serialize_snapshot,
)


def fingerprint_set() -> tuple:
    graph = call_graph(ACCEPTED_ROOTS)
    records = []
    for qualname in sorted(graph):
        records.append(CodeFingerprintRecord(
            qualname, fingerprint_function(graph[qualname])))
    return tuple(records)


def fingerprint_set_digest() -> str:
    from experiments.candidates.orbit_owner_match.canon import serialize_struct
    return sha256_hex(b"".join(
        serialize_struct("CodeFingerprintRecord" + D2, record)
        for record in fingerprint_set()))


# ---------------------------------------------------------------------------
# Bytecode audit
# ---------------------------------------------------------------------------

_FORBIDDEN_OPS = frozenset({"STORE_GLOBAL", "DELETE_GLOBAL", "IMPORT_NAME",
                            "IMPORT_FROM", "IMPORT_STAR", "LOAD_BUILD_CLASS",
                            "STORE_ATTR", "DELETE_ATTR"})

_D1_FIELD_NAMES = frozenset(name for name, _ in _D1_ACTOR_FIELDS)

AUDIT_ALLOWLISTS = {
    "owner_predicate_actor": (
        frozenset({"type", "int", "ActorInput_D2", "ContractError",
                   "EXECUTION_LEDGER"}),
        frozenset({"actor_tensor", "verified_owner_match"})),
    "actor": (frozenset({"int"}), frozenset({"actor_tensor"})),
    "_softmax": (frozenset({"max", "tuple", "sum", "math"}),
                 frozenset({"exp"})),
    "declassify": (frozenset({"type", "bool", "VerificationResult",
                              "VerifiedOwnerPredicate", "ContractError"}),
                   frozenset({"auth_ok", "owner_match"})),
    "extend_d1_actor_input": (
        frozenset({"type", "bool", "ActorInput", "ActorInput_D2",
                   "VerifiedOwnerPredicate", "ContractError"}),
        _D1_FIELD_NAMES | frozenset({"value"})),
    "project_write_D1": (frozenset({"type", "SiblingWrite_D2", "SiblingWrite",
                                    "ContractError"}),
                         frozenset({"public"})),
    "strip_predicate": (frozenset({"type", "ActorInput", "ActorInput_D2",
                                   "ContractError"}), _D1_FIELD_NAMES),
}


def audit_callable(fn, allowed_globals: frozenset,
                   allowed_attrs: frozenset) -> None:
    if fn.__defaults__ is not None or fn.__kwdefaults__ is not None:
        raise ContractError("defaults forbidden", "T3")
    if fn.__closure__ is not None:
        raise ContractError("closure forbidden", "T3")
    stack = [fn.__code__]
    while stack:
        code = stack.pop()
        for instruction in dis.get_instructions(code):
            if instruction.opname in _FORBIDDEN_OPS:
                raise ContractError("forbidden opcode %s in %s"
                                    % (instruction.opname, fn.__qualname__),
                                    "T3")
            if instruction.opname in ("LOAD_GLOBAL", "LOAD_NAME"):
                if instruction.argval not in allowed_globals:
                    raise ContractError(
                        "global %r outside allowlist in %s"
                        % (instruction.argval, fn.__qualname__), "T3")
            if instruction.opname in ("LOAD_ATTR", "LOAD_METHOD"):
                if instruction.argval not in allowed_attrs:
                    raise ContractError(
                        "attribute %r outside allowlist in %s"
                        % (instruction.argval, fn.__qualname__), "T3")
        for const in code.co_consts:
            if hasattr(const, "co_code"):
                stack.append(const)


def actor_path_audit_gate() -> None:
    """The narrow actor path satisfies its per-function allowlists."""
    targets = {
        "owner_predicate_actor": discriminator_module.owner_predicate_actor,
        "actor": eight_cell_audit.actor,
        "_softmax": eight_cell_audit._softmax,
        "declassify": trust_module.declassify,
        "extend_d1_actor_input": trust_module.extend_d1_actor_input,
        "project_write_D1": trust_module.project_write_D1,
        "strip_predicate": trust_module.strip_predicate,
    }
    if frozenset(targets) != frozenset(AUDIT_ALLOWLISTS):
        raise ContractError("allowlist and audited-function sets differ", "T3")
    for name, fn in sorted(targets.items()):
        allowed_globals, allowed_attrs = AUDIT_ALLOWLISTS[name]
        audit_callable(fn, allowed_globals, allowed_attrs)


# ---------------------------------------------------------------------------
# Construction-site closure (the static half of predicate provenance)
# ---------------------------------------------------------------------------


_TYPE_TEST_OPS = frozenset({"IS_OP", "COMPARE_OP"})


def _references_for_construction(code, guarded: str) -> bool:
    """Does this code object load ``guarded`` for anything but a type test?

    ``type(x) is not Cls`` compiles to a load of ``Cls`` immediately followed
    by ``IS_OP``, while construction compiles to that load followed by
    argument pushes and a ``CALL``.  Anything that is not immediately
    consumed by a type test is therefore treated as a potential construction.
    The rule is deliberately conservative: it can only over-report, so a
    novel spelling of construction fails the gate rather than slipping past
    it.

    ``LOAD_ATTR``/``LOAD_METHOD`` are scanned alongside the global loads
    because module-qualified construction -- ``records.VerifiedOwnerPredicate
    (True)`` -- never emits ``LOAD_GLOBAL`` for the class name at all, so a
    scan restricted to global loads would miss it entirely.
    """
    interesting = ("LOAD_GLOBAL", "LOAD_NAME", "LOAD_ATTR", "LOAD_METHOD")
    stack = [code]
    while stack:
        current = stack.pop()
        instructions = list(dis.get_instructions(current))
        for index, instruction in enumerate(instructions):
            if instruction.opname not in interesting:
                continue
            if instruction.argval != guarded:
                continue
            following = (instructions[index + 1]
                         if index + 1 < len(instructions) else None)
            if following is not None and following.opname in _TYPE_TEST_OPS:
                continue
            return True
        for const in current.co_consts:
            if hasattr(const, "co_code"):
                stack.append(const)
    return False


# Names that would give the accepted graph a handle to a guarded class
# without ever mentioning its name, defeating a name-based construction scan.
# ``registered_class`` and ``SCHEMA_OF_CLASS`` are in-package, first-class
# lookups from schema id to class; the reflection builtins are the generic
# escape hatches.
FORBIDDEN_HANDLE_NAMES = frozenset({
    "getattr", "setattr", "delattr", "globals", "vars", "eval", "exec",
    "compile", "__import__", "__class__", "registered_class",
    "SCHEMA_OF_CLASS", "REGISTRY_VIEW",
})


def _type_result_is_called(code) -> bool:
    """Does this code call the result of ``type(...)``?

    ``type(x)(y)`` is a name-free construction of ``x``'s class.  A legitimate
    type TEST consumes the ``type(...)`` result with a comparison; a
    construction consumes it with another ``CALL``.
    """
    stack = [code]
    while stack:
        current = stack.pop()
        instructions = list(dis.get_instructions(current))
        for index, instruction in enumerate(instructions):
            if instruction.opname not in ("LOAD_GLOBAL", "LOAD_NAME"):
                continue
            if instruction.argval != "type":
                continue
            calls = 0
            for follower in instructions[index + 1:]:
                if follower.opname in ("IS_OP", "COMPARE_OP"):
                    break
                if follower.opname == "CALL":
                    calls += 1
                    if calls >= 2:
                        return True
        for const in current.co_consts:
            if hasattr(const, "co_code"):
                stack.append(const)
    return False


def forbidden_handle_gate() -> None:
    """The accepted graph holds no name-free handle to a guarded class.

    A construction scan that matches class NAMES is only as strong as the
    absence of ways to reach a class without naming it.  This removes those
    ways rather than leaving the name scan to carry a claim it cannot bear.
    """
    graph = call_graph(ACCEPTED_ROOTS)
    for qualname in sorted(graph):
        fn = graph[qualname]
        # Attribute names as well as global names: ``canon.registered_class``
        # emits LOAD_GLOBAL 'canon' + LOAD_ATTR 'registered_class', so a scan
        # of global names alone would never see the handle it is looking for.
        used = _global_names(fn.__code__) | _attr_names(fn.__code__)
        offending = sorted(used & FORBIDDEN_HANDLE_NAMES)
        if offending:
            raise ContractError(
                "reflection handle %r reachable in %s" % (offending, qualname),
                "T3")
        if _type_result_is_called(fn.__code__):
            raise ContractError(
                "type(...) result is called in %s (name-free construction)"
                % (qualname,), "T3")


def construction_site_gate() -> None:
    """Each guarded class NAME is loaded only by its permitted constructor.

    Stated precisely, because the scan is a bytecode name scan: it proves
    that within the accepted call graph the name of each guarded record is
    loaded only where construction is permitted.  On its own that is a claim
    about names, not about origins -- ``registered_class(schema_id)(...)`` or
    ``type(existing)(...)`` would construct without naming anything.
    :func:`forbidden_handle_gate` removes those spellings from the graph, and
    :func:`block.lineage_rebuild_gate` checks the resulting objects
    extensionally.  The three together are what close provenance; none of
    them does it alone.

    Type tests against a guarded class stay legal everywhere; they are reads,
    not origins.
    """
    graph = call_graph(ACCEPTED_ROOTS)
    for guarded, permitted in sorted(GUARDED_CONSTRUCTORS.items()):
        sites = set()
        for fn in graph.values():
            if _references_for_construction(fn.__code__, guarded):
                sites.add(fn.__qualname__)
        unexpected = sorted(sites - {permitted})
        if unexpected:
            raise ContractError(
                "guarded record %s constructed outside %s: %r"
                % (guarded, permitted, unexpected), "T2")
        if permitted not in sites:
            raise ContractError(
                "permitted constructor %s never constructs %s"
                % (permitted, guarded), "T2")


# ---------------------------------------------------------------------------
# Live-object sealing
# ---------------------------------------------------------------------------


def _raw_typed_bytes(value, normalized_type: str) -> bytes:
    """Like the canonical typed encoder, but floats keep their exact bits."""
    if normalized_type == "float":
        return encode_float_raw(value)
    if normalized_type in _PRIMITIVE_ENCODERS:
        return _PRIMITIVE_ENCODERS[normalized_type](value)
    if normalized_type.startswith("tuple["):
        inner, _ = normalized_type[6:-1].rsplit(";", 1)
        return b"T" + b"".join(_raw_typed_bytes(item, inner) for item in value)
    if normalized_type.startswith("struct:"):
        return b"Y" + _record_raw_bytes(normalized_type[7:], value)
    raise ContractError("unknown normalized type in raw encoder", "T3")


def _record_raw_bytes(schema_id: str, value) -> bytes:
    parts = [_enc_str(schema_id)]
    for field_name, normalized_type in descriptor_of(schema_id):
        field_value = object.__getattribute__(value, field_name)
        parts.append(_raw_typed_bytes(field_value, normalized_type))
    return b"".join(parts)


def _value_digest(value, depth: int = 0) -> bytes:
    """Recursive content digest for a live global binding.

    Runtime globals are richer than code constants -- tuples of frozen
    records, mappings, module objects -- so they cannot go through the
    code-constant encoder.  Registered records are digested by their
    canonical serialization, containers recurse, and anything outside the
    covered set collapses to its type identity and is reported as ``opaque``
    so a reviewer can see exactly which bindings are only weakly pinned
    rather than being told everything is sealed.
    """
    if depth > 8:
        raise ContractError("global binding nested too deeply", "T3")
    from experiments.candidates.orbit_owner_match.canon import serialize_struct
    from experiments.candidates.orbit_owner_match.records import SCHEMA_OF_CLASS

    if type(value) is types.FunctionType:
        # NOT ``fingerprint_function``: that one enforces the contract's
        # no-defaults/no-closure rule, which is right for our own audited
        # functions and wrong for arbitrary bound values -- ``json.dumps``
        # has keyword defaults and is a perfectly legitimate binding.  Here
        # the job is to digest content, so defaults are folded in instead of
        # rejected.
        parts = [b"fn", _enc_str(fingerprint_code(value.__code__))]
        for extra in (value.__defaults__, value.__kwdefaults__):
            if extra is None:
                parts.append(b"-")
            elif type(extra) is dict:
                for key in sorted(extra):
                    parts.append(_enc_str(str(key)))
                    parts.append(_value_digest(extra[key], depth + 1))
            else:
                for item in extra:
                    parts.append(_value_digest(item, depth + 1))
        return b"".join(parts)
    if type(value) is types.ModuleType:
        return b"mod" + _enc_str(value.__name__)
    if type(value) in (types.BuiltinFunctionType, types.BuiltinMethodType):
        return b"bi" + _enc_str(value.__name__)
    if isinstance(value, type):
        # ``isinstance`` rather than ``type(value) is type``: classes with a
        # metaclass (``Fraction`` uses ABCMeta) would otherwise fall through
        # to the opaque branch and be reported as unpinned.
        fields = getattr(value, "__dataclass_fields__", None)
        shape = tuple(sorted(fields)) if fields else ()
        return (b"cls" + _enc_str(value.__module__ + "." + value.__qualname__)
                + _enc_typed(shape, "tuple[str;%d]" % len(shape)))
    if type(value) in SCHEMA_OF_CLASS:
        # NOT ``serialize_struct``: the canonical DATA encoder folds -0.0 into
        # +0.0, so digesting a record through it would re-open the round-6
        # signed-zero collision one layer down, the moment any record with
        # float fields becomes a module global.
        return b"rec" + _record_raw_bytes(SCHEMA_OF_CLASS[type(value)], value)
    if type(value) in (tuple, list):
        return (b"seq" + _enc_str(type(value).__name__)
                + b"".join(_value_digest(item, depth + 1) for item in value))
    if type(value) in (set, frozenset):
        parts = sorted(_value_digest(item, depth + 1) for item in value)
        return b"set" + b"".join(parts)
    if type(value) is dict:
        parts = []
        for key in sorted(value, key=repr):
            parts.append(_value_digest(key, depth + 1))
            parts.append(_value_digest(value[key], depth + 1))
        return b"map" + b"".join(parts)
    if type(value) in (str, int, float, bool, bytes, complex) or value is None:
        return b"const" + encode_code_constant(value, fingerprint_code)
    return b"opaque" + _enc_str(type(value).__qualname__)


def _binding_digest(value) -> tuple:
    from experiments.candidates.orbit_owner_match.records import SCHEMA_OF_CLASS

    if type(value) is types.FunctionType:
        kind = "function"
    elif type(value) is types.ModuleType:
        kind = "module"
    elif type(value) in (types.BuiltinFunctionType, types.BuiltinMethodType):
        kind = "builtin"
    elif isinstance(value, type):
        kind = "class"
    elif type(value) in SCHEMA_OF_CLASS:
        kind = "record"
    elif type(value) in (tuple, list, set, frozenset, dict):
        kind = "container"
    elif type(value) in (str, int, float, bool, bytes, complex) or value is None:
        kind = "constant"
    else:
        kind = "opaque"
    return (kind, sha256_hex(_value_digest(value)))


def opaque_binding_gate() -> None:
    """No audited global is pinned only by its type name.

    An ``opaque`` binding is one the digest cannot see inside, so a mutation
    of its contents would not change the sealed digest.  Reporting them is
    not enough -- the gate refuses them, which forces any new global to be a
    registered record, a container of them, or a primitive.
    """
    opaque = sorted(
        (record.function_qualname, record.global_name)
        for record in global_binding_records()
        if record.binding_kind == "opaque")
    if opaque:
        raise ContractError("opaque global bindings: %r" % (opaque[:8],), "T3")


def _attr_names(code) -> set:
    names = set()
    stack = [code]
    while stack:
        current = stack.pop()
        for instruction in dis.get_instructions(current):
            if instruction.opname in ("LOAD_ATTR", "LOAD_METHOD"):
                names.add(instruction.argval)
        for const in current.co_consts:
            if hasattr(const, "co_code"):
                stack.append(const)
    return names


def _module_binding_digest(module, used_attrs: frozenset) -> str:
    """Pin a module binding by the CONTENTS of the attributes actually used.

    Digesting a module by its name alone gives it exactly the property the
    opaque gate exists to forbid: rebinding ``math.exp`` or
    ``hmac.compare_digest`` leaves the digest unchanged.  Folding in the
    used attributes makes the seal cover the behavior the audited function
    can actually reach.
    """
    parts = [_enc_str(module.__name__)]
    for attr in sorted(used_attrs):
        if not hasattr(module, attr):
            continue
        parts.append(_enc_str(attr))
        parts.append(_value_digest(getattr(module, attr)))
    return sha256_hex(b"".join(parts))


def global_binding_records() -> tuple:
    """Every global every audited function can reach, pinned by digest."""
    from experiments.candidates.orbit_owner_match.records import (
        GlobalBindingRecord,
    )
    graph = call_graph(ACCEPTED_ROOTS)
    records = []
    for qualname in sorted(graph):
        fn = graph[qualname]
        used_attrs = frozenset(_attr_names(fn.__code__))
        for name in sorted(_global_names(fn.__code__)):
            if name in fn.__globals__:
                value = fn.__globals__[name]
            elif hasattr(_builtins, name):
                value = getattr(_builtins, name)
            else:
                raise ContractError(
                    "unresolved global %r in %s" % (name, qualname), "T3")
            if type(value) is types.ModuleType:
                kind = "module"
                digest = _module_binding_digest(value, used_attrs)
            else:
                kind, digest = _binding_digest(value)
            records.append(GlobalBindingRecord(qualname, name, kind, digest))
    return tuple(records)


def global_binding_digest() -> str:
    from experiments.candidates.orbit_owner_match.canon import serialize_struct
    return sha256_hex(b"".join(
        serialize_struct("GlobalBindingRecord" + D2, record)
        for record in global_binding_records()))


def imported_module_gate() -> None:
    """No audited module reaches an imported module outside the allowed set."""
    graph = call_graph(ACCEPTED_ROOTS)
    for qualname in sorted(graph):
        fn = graph[qualname]
        for name in _global_names(fn.__code__):
            value = fn.__globals__.get(name)
            if type(value) is types.ModuleType:
                base = value.__name__.split(".")[0]
                if (base not in ALLOWED_IMPORTED_MODULES
                        and value.__name__ not in OWNED_MODULE_NAMES):
                    raise ContractError(
                        "module %r reachable from %s is not allowed"
                        % (value.__name__, qualname), "T3")


def class_behavior_gate() -> None:
    """Registered record classes expose no behavior channel on field reads.

    ``object.__getattribute__`` in the serializer bypasses an instance-level
    override but still runs descriptor protocol, so a data descriptor
    installed on the exact registered class could still alter what a field
    read returns while ``type(value) is cls`` stays true.  This closes that.
    """
    for schema_id, cls, descriptor in _SCHEMA_TABLE:
        if cls.__getattribute__ is not object.__getattribute__:
            raise ContractError(
                "%s overrides __getattribute__" % (cls.__qualname__,), "T3")
        if getattr(cls, "__getattr__", None) is not None:
            raise ContractError(
                "%s defines __getattr__" % (cls.__qualname__,), "T3")
        params = getattr(cls, "__dataclass_params__", None)
        if params is None or not params.frozen:
            raise ContractError(
                "%s is not a frozen dataclass" % (cls.__qualname__,), "T3")
        for field_name, _ in descriptor:
            # Walk the MRO, not just ``cls.__dict__``: a data descriptor
            # installed on a base class intercepts the field read just as
            # effectively, and every registered record derives from object
            # today only by convention.
            for base in cls.__mro__:
                if base is object:
                    continue
                attribute = base.__dict__.get(field_name)
                if attribute is None:
                    continue
                if (hasattr(attribute, "__get__")
                        or hasattr(attribute, "__set__")):
                    raise ContractError(
                        "%s installs a descriptor on field %s (via %s)"
                        % (cls.__qualname__, field_name, base.__qualname__),
                        "T3")


def ambient_hook_gate() -> None:
    """No tracing or profiling hook is installed.

    A trace function observes and can alter local state at every line, which
    would make every other closure claim in this module vacuous.
    """
    if sys.gettrace() is not None:
        raise ContractError("a trace hook is installed", "T3")
    if sys.getprofile() is not None:
        raise ContractError("a profile hook is installed", "T3")


def t2_gate() -> None:
    """Exact actor-surface equality (round-6 correction D04-C10)."""
    actor_attrs = AUDIT_ALLOWLISTS["owner_predicate_actor"][1]
    t2_surface_descriptor_gate(
        _D1_ACTOR_FIELDS, actor_attrs, REGISTRY_VIEW[SCHEMA_ACTOR_INPUT_D2][1])
    actor_input_schema_binding_gate(REGISTRY_VIEW)


def live_object_gate() -> None:
    """Composite of the live-object checks, in the order the suite runs them.

    Kept as a single callable for external reproduction; the frozen suite in
    :mod:`gates` invokes the same sub-gates individually so that a failure
    names which one failed.
    """
    interpreter_gate()
    ambient_hook_gate()
    class_behavior_gate()
    imported_module_gate()
    opaque_binding_gate()
    forbidden_handle_gate()
