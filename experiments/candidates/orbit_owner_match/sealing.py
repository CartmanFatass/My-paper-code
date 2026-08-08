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
import pathlib
import sys
import types

from fractions import Fraction

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


_PACKAGE = "experiments.candidates.orbit_owner_match."

# Every module of the executable contract (round-7 correction D05-C02).  D0.5
# owned six of these plus the inherited module and left out numerics, sealing,
# gates and precommit -- so the terminal path, the gate builders, the
# authenticity gates and the platform-admission machinery were all outside the
# fingerprinted graph while the freeze described that graph as the contract.
#
# Resolved by NAME through ``sys.modules`` rather than by object at import
# time: gates and precommit import this module, so referencing them here
# directly would be a cycle.  By the time any of these functions is CALLED,
# the package is fully imported.
#
# ``baseline`` is deliberately absent.  It holds the frozen expected digests
# that the seal gate compares against; if it were inside the sealed set, every
# literal it stores would change the digests it is storing.  It carries no
# functions, and it is authenticated the same way the reviewer authenticated
# the rest of the package this round -- by its git blob id, published in the
# freeze document and pinned in the precommit envelope.
OWNED_MODULE_NAMES = frozenset({
    _PACKAGE + "canon",
    _PACKAGE + "records",
    _PACKAGE + "trust",
    _PACKAGE + "block",
    _PACKAGE + "controls",
    _PACKAGE + "discriminator",
    _PACKAGE + "numerics",
    _PACKAGE + "sealing",
    _PACKAGE + "gates",
    _PACKAGE + "precommit",
    "experiments.candidates.orbit_shadow_read.eight_cell_audit",
})


# Modules that are authenticated from OUTSIDE the process, by git blob id,
# and therefore must not appear inside any digest they anchor.
UNSEALED_MODULE_NAMES = frozenset({_PACKAGE + "baseline"})

# Module attributes that are live interpreter state rather than contract
# content.  Pinned by name; see :func:`_module_binding_digest`.
LIVE_PROCESS_ATTRS = {
    "sys": frozenset({"modules", "path", "argv", "stdout", "stderr", "stdin",
                      "meta_path", "path_hooks", "path_importer_cache"}),
}

# Globals of our OWN that are observation state rather than contract content.
# They are pinned by type, not by value, because their value is supposed to
# change: the seal owes that the object is still the right kind of thing, and
# a separate gate owns what its contents must be.  Enumerated explicitly and
# exhaustively -- a general "skip mutable things" rule would be a hole.
PROCESS_STATE_GLOBALS = frozenset({
    # The clone observation log.  Grows by sixteen on every block build; its
    # CONTENT is what ``clone_independence_gate`` reads, per census, from the
    # witnesses rather than from this list.
    (_PACKAGE + "block", "_OBSERVED_CLONES"),
    # The execution ledger.  Rises whenever the discriminator runs; its
    # contents are the business of ``execution_ledger_gate``.
    (_PACKAGE + "discriminator", "EXECUTION_LEDGER"),
})


def _resolve_module(name: str):
    """Resolve an owned module, importing it if this is the first reach.

    Import happens at CALL time, never at module-import time: ``gates`` and
    ``precommit`` import this module, so binding them at the top would be a
    cycle.  Resolving here means the audited set is the whole package however
    the caller happened to enter it -- a reviewer who imports only ``sealing``
    still audits the terminal path.
    """
    module = sys.modules.get(name)
    if module is not None:
        return module
    import importlib
    try:
        return importlib.import_module(name)
    except Exception as failure:
        raise ContractError(
            "owned module %r could not be resolved: %s" % (name, failure), "T3")


def owned_modules() -> tuple:
    """The owned modules, resolved live and fail-closed on any absence."""
    return tuple(_resolve_module(name) for name in sorted(OWNED_MODULE_NAMES))



ALLOWED_IMPORTED_MODULES = frozenset({"math", "hashlib", "hmac", "struct",
                                      "dis", "sys", "types", "json",
                                      "fractions", "dataclasses", "enum",
                                      "pathlib", "mpmath", "builtins",
                                      "importlib"})


# ---------------------------------------------------------------------------
# Code fingerprints
# ---------------------------------------------------------------------------


# Bytecode differs between interpreter versions, so every fingerprint-bearing
# digest is meaningful only relative to a declared interpreter.  Freezing that
# declaration turns "this reviewer got a different digest" into a clear
# mismatch error instead of an unattributable disagreement.
INTERPRETER_CONTRACT = ("cpython", 3, 11, 9)

# The high-precision reference is computed with mpmath, so its version is part
# of the numeric contract in exactly the way the interpreter is part of the
# bytecode contract.  D0.5 recorded the version in the envelope but had no
# gate, so running under a different mpmath changed a frozen input silently.
MPMATH_CONTRACT = "1.4.1"


def interpreter_gate() -> None:
    """The interpreter is the one the frozen digests were produced under.

    Pinned to the exact patch level (round-7 correction D05-C11).  D0.5
    checked only ``(cpython, 3, 11)``, so any 3.11.x admitted digests frozen
    under 3.11.9 -- and CPython does change bytecode within a minor series.
    """
    name = sys.implementation.name
    major, minor, micro = sys.version_info[:3]
    if (name, major, minor, micro) != INTERPRETER_CONTRACT:
        raise ContractError(
            "interpreter %s %d.%d.%d does not match the frozen contract %r"
            % (name, major, minor, micro, INTERPRETER_CONTRACT), "T3")


def dependency_gate() -> None:
    """mpmath is the version the curvature reference was frozen under."""
    import mpmath
    if mpmath.__version__ != MPMATH_CONTRACT:
        raise ContractError(
            "mpmath %s does not match the frozen contract %s"
            % (mpmath.__version__, MPMATH_CONTRACT), "T3")


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
    """Fingerprint a function's code AND its default arguments.

    D0.5 banned defaults outright.  That was a blunt stand-in for the real
    requirement -- defaults are behavior, and behavior must be pinned, not
    forbidden -- and it stopped being tenable once the call graph widened to
    the whole contract in round 7, where several audited functions legitimately
    carry one.  Folding them into the digest is strictly stronger than the ban:
    "there are none" becomes "they are exactly these".

    A closure is still refused.  A cell is mutable state reachable from
    outside the function, which is a channel rather than a value.
    """
    if fn.__closure__ is not None:
        raise ContractError("registered function must have no closure", "T3")
    parts = [_enc_str(fingerprint_code(fn.__code__))]
    defaults = fn.__defaults__ or ()
    parts.append(_enc_int(len(defaults)))
    for value in defaults:
        parts.append(encode_code_constant(value, fingerprint_code))
    kwdefaults = fn.__kwdefaults__ or {}
    parts.append(_enc_int(len(kwdefaults)))
    for name in sorted(kwdefaults):
        parts.append(_enc_str(name))
        parts.append(encode_code_constant(kwdefaults[name], fingerprint_code))
    return sha256_hex(b"".join(parts))


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


def _referenced_functions(fn) -> list:
    """Every owned function this one can reach by name from its own code.

    Two spellings are resolved (round-7 correction D05-C02):

    ``LOAD_GLOBAL f``
        a bare global naming a function.
    ``LOAD_GLOBAL m; LOAD_ATTR f`` / ``LOAD_METHOD f``
        a module-qualified call.  D0.5 followed only the first form, so every
        ``discriminator_module.calibrate``-style call -- which is how the
        terminal path and the gate builders call almost everything -- was
        invisible to the closure, and the graph stopped at the module object.
    """
    found = []
    globals_map = fn.__globals__
    stack = [fn.__code__]
    while stack:
        current = stack.pop()
        instructions = list(dis.get_instructions(current))
        for index, instruction in enumerate(instructions):
            if instruction.opname not in ("LOAD_GLOBAL", "LOAD_NAME"):
                continue
            target = globals_map.get(instruction.argval)
            if type(target) is types.FunctionType:
                found.append(target)
                continue
            if type(target) is not types.ModuleType:
                continue
            if target.__name__ not in OWNED_MODULE_NAMES:
                continue
            following = instructions[index + 1] if index + 1 < len(
                instructions) else None
            if following is None or following.opname not in (
                    "LOAD_ATTR", "LOAD_METHOD"):
                continue
            attribute = getattr(target, following.argval, None)
            if type(attribute) is types.FunctionType:
                found.append(attribute)
        for const in current.co_consts:
            if hasattr(const, "co_code"):
                stack.append(const)
    return found


def call_graph(roots: tuple) -> dict:
    """Transitive closure of ``roots`` over bare and module-qualified calls.

    Only functions defined in :data:`OWNED_MODULE_NAMES` are followed;
    anything else (builtins, allowed stdlib) is a leaf, recorded by the
    binding audit rather than fingerprinted.
    """
    reached = {}
    pending = list(roots)
    while pending:
        fn = pending.pop()
        qualname = fn.__module__ + "." + fn.__qualname__
        if qualname in reached:
            continue
        reached[qualname] = fn
        for target in _referenced_functions(fn):
            if target.__module__ not in OWNED_MODULE_NAMES:
                continue
            pending.append(target)
    return reached


# (module suffix, attribute) pairs, resolved live.  Named rather than bound at
# import time so that the terminal path and the gate builders -- which live in
# modules that import this one -- can be roots without a cycle.
ACCEPTED_ROOT_NAMES = (
    ("block", "build_target_cell"),
    ("block", "build_block"),
    ("block", "block_cells"),
    ("block", "block_image"),
    ("block", "observe_clone"),
    ("block", "census_key_authenticity_gate"),
    ("block", "exact_key_domain_gate"),
    ("block", "cross_m_closure_gate"),
    ("block", "cross_q_closure_gate"),
    ("block", "clone_independence_gate"),
    ("block", "public_write_invariance_gate"),
    ("block", "lineage_rebuild_gate"),
    ("trust", "verify_write_d2"),
    ("trust", "declassify"),
    ("trust", "extend_d1_actor_input"),
    ("trust", "build_write_d2_with_b"),
    ("trust", "project_write_D1"),
    ("trust", "strip_predicate"),
    ("trust", "compute_transcript"),
    ("trust", "binding_for_source"),
    ("discriminator", "owner_predicate_actor"),
    ("discriminator", "evaluate_block"),
    ("discriminator", "estimands"),
    ("discriminator", "calibrate"),
    ("discriminator", "four_replica_diameter"),
    ("discriminator", "float_accumulate"),
    ("discriminator", "calibration_authenticity_gate"),
    ("discriminator", "estimand_authenticity_gate"),
    ("discriminator", "calibration_disjointness_gate"),
    ("discriminator", "execution_ledger_gate"),
    ("controls", "exact_accumulate"),
    ("controls", "oriented_pair_first_m_blind"),
    ("controls", "oriented_pair_first_b_blind"),
    ("controls", "check_value_domain"),
    ("controls", "coefficient_map"),
    # The terminal path itself.  D0.5 left every one of these outside the
    # graph, which is what made the "rebind a module attribute and steer the
    # terminal without running the experiment" attack work: the audit
    # fingerprinted the function objects it held, not the live attributes the
    # controller resolves at call time.
    ("gates", "terminal_controller"),
    ("gates", "run_gate_sequence"),
    ("gates", "run_static_gates"),
    ("gates", "gate_order_gate"),
    ("gates", "classify_science"),
    ("gates", "runtime_seal_gate"),
    ("numerics", "binary64_recovery"),
    ("numerics", "recovery_gate"),
    ("numerics", "curvature_gate"),
    ("numerics", "curvature_mutant_response_gate"),
    ("numerics", "curvature_accumulate"),
    ("sealing", "fingerprint_set"),
    ("sealing", "fingerprint_set_digest"),
    ("sealing", "global_binding_digest"),
    ("sealing", "call_graph"),
    ("sealing", "live_object_gate"),
    ("precommit", "build_precommit_envelope"),
    ("precommit", "precommit_digest"),
    ("precommit", "package_source_digest"),
)

_INHERITED_ROOT_NAMES = (
    "actor", "_softmax", "q_adapter", "write_sibling", "verify_sibling",
    "restore_clone", "serialize_snapshot",
)


def accepted_roots() -> tuple:
    roots = []
    for suffix, attribute in ACCEPTED_ROOT_NAMES:
        module = _resolve_module(_PACKAGE + suffix)
        target = getattr(module, attribute, None)
        if type(target) is not types.FunctionType:
            raise ContractError(
                "accepted root %s.%s is not a function" % (suffix, attribute),
                "T3")
        roots.append(target)
    for attribute in _INHERITED_ROOT_NAMES:
        target = getattr(eight_cell_audit, attribute, None)
        if type(target) is not types.FunctionType:
            raise ContractError(
                "inherited root %r is not a function" % (attribute,), "T3")
        roots.append(target)
    return tuple(roots)


def fingerprint_set() -> tuple:
    graph = call_graph(accepted_roots())
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
        # ``increment`` is the ledger method, not a field read; the exact
        # FIELD read set is checked separately by ``actor_read_set_gate``.
        frozenset({"actor_tensor", "verified_owner_match", "increment"})),
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


# The read set the design registers for the target actor.  This is the claim
# the whole treatment rests on: the actor sees the sanctioned predicate and
# the last two tensor slots, and nothing else.
REGISTERED_ACTOR_READ_SET = frozenset({"verified_owner_match", "actor_tensor"})


def actor_read_set_gate() -> None:
    """The actor's read set is DERIVED and equals the registered set exactly.

    Round 7 found :func:`actor_path_audit_gate` insufficient for this: it
    compares against a hardcoded allowlist and only rejects reads OUTSIDE it,
    so removing a sanctioned read still passed.  That direction matters --
    round 4 rejected D0.2 precisely because the actor did NOT read
    ``verified_owner_match``, which made the target M-blind and unable to
    realize the estimand at all.  A subset test cannot catch a recurrence.

    The set is read off the actor's own bytecode and compared for EQUALITY.
    Scope: attribute names are filtered to the fields of ``ActorInput_D2``, so
    ``EXECUTION_LEDGER.increment`` and similar non-field attribute access do
    not enter the comparison.  A field whose name collided with a method used
    on some other object in the same function would evade that filter; no
    such collision exists in the frozen field set, and the registration gates
    fix that set.
    """
    derived = actor_field_reads()
    if derived != REGISTERED_ACTOR_READ_SET:
        raise ContractError(
            "actor read set is %r; the registered set is %r"
            % (sorted(derived), sorted(REGISTERED_ACTOR_READ_SET)), "T1")


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


# The subgraph that can construct or carry a guarded value: authentication,
# declassification, cell construction, and the actor itself.  The reflection
# ban is scoped HERE rather than to the whole package.
#
# D0.5 applied it to every audited function, which was tenable only because
# the audited set was small.  Round 7 required the graph to cover the whole
# executable contract (D05-C02), and the audit machinery legitimately uses
# ``getattr`` -- ``_module_binding_digest`` cannot pin a module's attributes
# without reading them.  Banning reflection there would mean either a false
# gate or an unfingerprinted auditor.  The claim the ban actually supports is
# about the construction path, so that is where it is enforced, and the
# narrower scope is stated rather than left implicit.
PROVENANCE_ROOT_NAMES = (
    ("trust", "verify_write_d2"),
    ("trust", "declassify"),
    ("trust", "extend_d1_actor_input"),
    ("trust", "build_write_d2_with_b"),
    ("trust", "project_write_D1"),
    ("trust", "strip_predicate"),
    ("trust", "compute_transcript"),
    ("block", "build_target_cell"),
    ("block", "build_block"),
    ("block", "lineage_rebuild_gate"),
    ("discriminator", "owner_predicate_actor"),
)


def provenance_roots() -> tuple:
    roots = []
    for suffix, attribute in PROVENANCE_ROOT_NAMES:
        module = _resolve_module(_PACKAGE + suffix)
        target = getattr(module, attribute, None)
        if type(target) is not types.FunctionType:
            raise ContractError(
                "provenance root %s.%s is not a function" % (suffix, attribute),
                "T3")
        roots.append(target)
    return tuple(roots)


def forbidden_handle_gate() -> None:
    """The construction path holds no name-free handle to a guarded class.

    A construction scan that matches class NAMES is only as strong as the
    absence of ways to reach a class without naming it.  This removes those
    ways rather than leaving the name scan to carry a claim it cannot bear.
    """
    graph = call_graph(provenance_roots())
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
    graph = call_graph(accepted_roots())
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
    # Singletons and the value-like types the widened graph reaches
    # (round-7 correction D05-C01).  Each is digested by CONTENT, so it is
    # genuinely pinned; leaving them in the opaque branch would have meant
    # reporting "0 opaque" was only achievable by not looking at them.
    if value is Ellipsis or value is NotImplemented:
        return b"singleton" + _enc_str(repr(value))
    if type(value) is types.MappingProxyType:
        return b"proxy" + _value_digest(dict(value), depth + 1)
    if type(value) is Fraction:
        return (b"frac" + _enc_str(str(value.numerator))
                + _enc_str(str(value.denominator)))
    if isinstance(value, pathlib.PurePath):
        # Digested by the file NAME only.  An absolute path is a property of
        # this checkout, not of the contract, and folding it in would make
        # every frozen digest machine-dependent -- the CRLF defect in another
        # guise.
        return b"path" + _enc_str(value.name)
    if type(value).__qualname__ == "ExecutionLedger":
        # Pinned by TYPE, not by the counts.  The counts are process state by
        # design -- they rise whenever the discriminator runs -- so folding
        # them in would make the seal break the moment the experiment is
        # executed, including at the post-audit re-seal inside
        # ``terminal_controller``.  What the seal owes here is that the object
        # is still the contract's ledger class; what the COUNTS must be is the
        # separate business of ``execution_ledger_gate``, which is the gate
        # that actually makes the not-executed claim.
        return (b"ledger" + _enc_str(type(value).__module__)
                + _enc_str(type(value).__qualname__))
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
    elif value is Ellipsis or value is NotImplemented:
        kind = "singleton"
    elif type(value) is types.MappingProxyType:
        kind = "proxy"
    elif type(value) is Fraction:
        kind = "rational"
    elif isinstance(value, pathlib.PurePath):
        kind = "path"
    elif type(value).__qualname__ == "ExecutionLedger":
        kind = "ledger"
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
    # Live process state is digested by NAME, not content.  ``sys.modules`` is
    # the whole interpreter's import table: folding it in would make the seal
    # depend on what else happens to be loaded, so it would differ between two
    # runs of the same audit and could never equal a frozen expectation.
    # Owned-module identity is checked separately by :func:`owned_modules` and
    # :func:`imported_module_gate`; arbitrary rebinding inside ``sys.modules``
    # is process state this contract does not claim to seal, and says so.
    live = LIVE_PROCESS_ATTRS.get(module.__name__, frozenset())
    used_attrs = frozenset(used_attrs) - live
    if module.__name__ in UNSEALED_MODULE_NAMES:
        # The baseline module is the EXTERNAL anchor: it stores the expected
        # digests this audit compares against.  Folding its contents in would
        # make ``global_binding`` depend on the literal recording
        # ``global_binding``, so writing the value in would change the value
        # and no fixpoint would exist.  It is pinned by name here and by git
        # blob id outside the process -- which is the only place a frozen
        # expectation can honestly be pinned from.
        return sha256_hex(b"anchor" + _enc_str(module.__name__))
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
    graph = call_graph(accepted_roots())
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
            owning_module = fn.__module__
            if (owning_module, name) in PROCESS_STATE_GLOBALS:
                kind = "process-state"
                digest = sha256_hex(b"state" + _enc_str(name)
                                    + _enc_str(type(value).__module__)
                                    + _enc_str(type(value).__qualname__))
            elif type(value) is types.ModuleType:
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
    graph = call_graph(accepted_roots())
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


def class_behavior_digest() -> str:
    """Fingerprint every METHOD of every registered record class.

    :func:`class_behavior_gate` proves no descriptor intercepts a field read,
    and the binding audit pins each class by module, qualname and field-name
    shape.  Neither covers what the class's own methods DO, so
    ``AnalysisKey.as_tuple`` could have been rewritten to permute the census
    key, or ``RationalValue.as_fraction`` to return a different rational,
    without moving any frozen digest (round-7 correction D05-C01).

    Scope, stated exactly: this pins each method's CODE, its defaults, and the
    NUMBER of closure cells.  It does not pin cell CONTENTS.  Several of these
    methods are generated by :mod:`dataclasses` and legitimately close over
    field metadata, and following those cells would walk back into the class
    being digested.  Rewriting a method body -- the channel this exists to
    close -- changes the code and is caught; swapping what a dataclass-
    generated method closes over is not, and is left to
    :func:`class_behavior_gate` and the registration gates.
    """
    parts = []
    for schema_id, cls, _descriptor in _SCHEMA_TABLE:
        parts.append(_enc_str(schema_id))
        parts.append(_enc_str(cls.__module__ + "." + cls.__qualname__))
        seen = set()
        for base in cls.__mro__:
            if base is object:
                continue
            for name in sorted(base.__dict__):
                if name in seen:
                    continue
                value = base.__dict__[name]
                if type(value) is not types.FunctionType:
                    continue
                seen.add(name)
                parts.append(_enc_str(name))
                parts.append(_enc_str(fingerprint_code(value.__code__)))
                defaults = value.__defaults__ or ()
                parts.append(_enc_int(len(defaults)))
                for default in defaults:
                    parts.append(encode_code_constant(default,
                                                      fingerprint_code))
                parts.append(_enc_int(len(value.__closure__ or ())))
    return sha256_hex(b"".join(parts))


def ambient_hook_gate() -> None:
    """No tracing or profiling hook is installed.

    A trace function observes and can alter local state at every line, which
    would make every other closure claim in this module vacuous.
    """
    if sys.gettrace() is not None:
        raise ContractError("a trace hook is installed", "T3")
    if sys.getprofile() is not None:
        raise ContractError("a profile hook is installed", "T3")


def actor_field_reads() -> frozenset:
    """Attribute names the actor reads that are FIELDS of its input record.

    Method calls on other objects -- ``EXECUTION_LEDGER.increment`` -- are not
    reads of the actor surface and must not enter the surface comparison.
    """
    fields = frozenset(name for name, _type
                       in descriptor_of(SCHEMA_ACTOR_INPUT_D2))
    observed = frozenset(
        _attr_names(discriminator_module.owner_predicate_actor.__code__))
    return observed & fields


def t2_gate() -> None:
    """Exact actor-surface equality (round-6 correction D04-C10)."""
    actor_attrs = AUDIT_ALLOWLISTS["owner_predicate_actor"][1] & frozenset(
        name for name, _type in descriptor_of(SCHEMA_ACTOR_INPUT_D2))
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
