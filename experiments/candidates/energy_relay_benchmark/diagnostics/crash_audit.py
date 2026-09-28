"""Opt-in in-process crash audit for energy-relay training runners (default off).

Motivation (crash-debug 2026-09-28): two CUDA fits died with ``SystemError:
Objects/listobject.c:2529`` raised by CPython's ``LIST_TO_TUPLE`` opcode at
``numpy/core/fromnumeric.py:56`` -- the interpreter's own freshly built list failed
``PyList_Check``, i.e. process memory was corrupted earlier by native code.  This module records
what a later occurrence would need: native/Python stacks on a fatal signal, periodic heap and
refcount samples, and the state at the uncaught exception.

Enabling (environment, read once by :func:`install_from_environment`):

``HMASD_CRASH_AUDIT=1``                  turn the audit on (anything else / unset: nothing happens)
``HMASD_CRASH_AUDIT_INTERVAL=<s>``       minimum seconds between periodic samples (default 300)
``HMASD_CRASH_AUDIT_WATCHDOG=<s>``       hang watchdog: dump every thread's stack if no sample was
                                        taken for this long (default 0 = off; see the cadence note)
``HMASD_CRASH_AUDIT_FORCE_GC=1``         also run a full ``gc.collect()`` at each sample (default
                                        off: a full collection empties CPython's list/dict/float
                                        freelists, the very allocation pattern under suspicion, so
                                        turning it on may suppress or move the fault)

Side logs go to ``<out>/logs/crash-audit/`` (``logs`` is excluded from the b05 manifest):
``faulthandler.log`` (fatal-signal and watchdog stacks, all threads) and ``audit.jsonl`` (one JSON
record per sample, plus an ``install`` and an ``uncaught_exception`` record).  At an uncaught
exception ``sys._debugmallocstats()`` is also called; CPython writes it to the C ``stderr``
(the launcher's ``stderr.log``), not to the side log.

Sampling cadence: samples are taken at the end of an automatic (or explicit) garbage
collection, at most once per interval.  In this training loop the collector is rare in steady
state: the CPU reproduction (crash-debug 2026-09-28) counted about two generation-0 collections
per 15,000 collector steps, i.e. one sample every 15-25 min of CPU wall, and no full collection
after start-up.  A watchdog shorter than the longest gap would dump stacks spuriously; if one is
wanted, use >= 3600 s.

What turning it on changes: wall-clock timing and heap layout only.  The sampler runs inside a
``gc.callbacks`` hook (no thread, no edit of the training loop), allocates a few small objects
per sample and reads ``/proc/self/statm``; the watchdog is ``faulthandler``'s C thread, which
touches no Python object until it fires.  No random number is drawn and no training value is
read or written; the b05 collector is bitwise identical with the audit on (pinned by test).
What leaving it off changes: nothing beyond one ``os.environ.get`` in the runner.
"""

from __future__ import annotations

import faulthandler
import gc
import json
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any

ENV_VAR = "HMASD_CRASH_AUDIT"
INTERVAL_VAR = "HMASD_CRASH_AUDIT_INTERVAL"
WATCHDOG_VAR = "HMASD_CRASH_AUDIT_WATCHDOG"
FORCE_GC_VAR = "HMASD_CRASH_AUDIT_FORCE_GC"
SIDE_DIR = Path("logs") / "crash-audit"

_STATE: dict[str, Any] = {}


def enabled(environ=None) -> bool:
    environ = os.environ if environ is None else environ
    return environ.get(ENV_VAR, "") == "1"


def _float_env(environ, name: str, default: float) -> float:
    raw = environ.get(name)
    if raw is None or raw == "":
        return float(default)
    value = float(raw)
    if value < 0:
        raise ValueError(f"{name} must be >= 0, got {raw!r}")
    return value


def _rss_kib() -> int | None:
    try:
        with open("/proc/self/statm", "rb") as handle:
            pages = int(handle.read().split()[1])
        return pages * os.sysconf("SC_PAGE_SIZE") // 1024
    except (OSError, ValueError, IndexError):
        return None


def path_objects() -> dict[str, Any]:
    """Long-lived objects on the failing path whose refcounts should stay flat.

    A monotone drift of one of these counts localises an over-decref (or leak) to code that
    touches that object.  Resolved lazily; missing modules are skipped.
    """
    objects: dict[str, Any] = {}
    fromnumeric = sys.modules.get("numpy.core.fromnumeric")
    if fromnumeric is not None:
        for name in ("_wrapit", "_wrapfunc", "clip"):
            objects[f"numpy.core.fromnumeric.{name}"] = getattr(fromnumeric, name, None)
    relay = sys.modules.get("envs.pettingzoo.relay.energy_aware")
    env_class = getattr(relay, "UAVEnergyAwareRelayEnv", None) if relay is not None else None
    function = getattr(env_class, "_spectral_efficiency", None)
    code = getattr(function, "__code__", None)
    if code is not None:
        for index, constant in enumerate(code.co_consts):
            if isinstance(constant, float):
                objects[f"_spectral_efficiency.co_consts[{index}]={constant!r}"] = constant
    return {name: value for name, value in objects.items() if value is not None}


def sample(reason: str, **extra: Any) -> dict[str, Any]:
    """One audit record (does not write it)."""
    record: dict[str, Any] = {
        "event": reason, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "monotonic": time.monotonic(), "rss_kib": _rss_kib(),
        "allocated_blocks": sys.getallocatedblocks(),
        "gc_count": list(gc.get_count()),
        "gc_collections": [row.get("collections") for row in gc.get_stats()],
        "gc_collected": [row.get("collected") for row in gc.get_stats()],
        "refcounts": {name: sys.getrefcount(value) for name, value in path_objects().items()},
    }
    record.update(extra)
    return record


def _write(record: dict[str, Any]) -> None:
    handle = _STATE.get("audit_handle")
    if handle is None:
        return
    handle.write(json.dumps(record, sort_keys=True, default=repr) + "\n")
    handle.flush()


def _rearm_watchdog() -> None:
    watchdog = _STATE.get("watchdog", 0.0)
    if watchdog > 0:
        faulthandler.dump_traceback_later(watchdog, repeat=False,
                                          file=_STATE["fault_handle"], exit=False)


def _gc_callback(phase: str, info: dict[str, Any]) -> None:
    if phase != "stop" or _STATE.get("busy"):
        return
    now = time.monotonic()
    if now - _STATE["last_sample"] < _STATE["interval"]:
        return
    _STATE["busy"] = True
    try:
        _STATE["last_sample"] = now
        _STATE["samples"] += 1
        forced = None
        if _STATE["force_gc"]:
            # Re-entrant collections do not re-run this callback (``busy``).
            forced = gc.collect()
        _write(sample("periodic", trigger_generation=info.get("generation"),
                      sample_index=_STATE["samples"], forced_gc_collected=forced))
        _rearm_watchdog()
    except Exception as exc:   # the audit must never raise into the collector
        _STATE["errors"] = _STATE.get("errors", 0) + 1
        try:
            _write({"event": "audit_error", "type": type(exc).__name__, "message": str(exc)})
        except Exception:
            pass
    finally:
        _STATE["busy"] = False


def _excepthook(exc_type, exc, tb) -> None:
    try:
        frames = traceback.extract_tb(tb)
        _write(sample("uncaught_exception", type=getattr(exc_type, "__name__", repr(exc_type)),
                      message=str(exc),
                      innermost=[f"{frame.filename}:{frame.lineno} {frame.name}"
                                 for frame in frames[-6:]],
                      samples=_STATE.get("samples"), audit_errors=_STATE.get("errors", 0)))
        faulthandler.dump_traceback(file=_STATE["fault_handle"], all_threads=True)
        _STATE["fault_handle"].flush()
        sys.stderr.flush()
        sys._debugmallocstats()   # C stderr: pymalloc arenas/pools at the moment of death
    except Exception:
        pass
    _STATE["previous_excepthook"](exc_type, exc, tb)


def install(out: Path, *, environ=None) -> dict[str, Any]:
    """Enable the audit writing under ``out/logs/crash-audit`` (idempotent per process)."""
    environ = os.environ if environ is None else environ
    if _STATE.get("installed"):
        return dict(_STATE["config"])
    side = Path(out) / SIDE_DIR
    side.mkdir(parents=True, exist_ok=True)
    interval = _float_env(environ, INTERVAL_VAR, 300.0)
    watchdog = _float_env(environ, WATCHDOG_VAR, 0.0)
    force_gc = environ.get(FORCE_GC_VAR, "") == "1"
    if 0 < watchdog <= interval:
        raise ValueError(f"{WATCHDOG_VAR} ({watchdog}) must exceed {INTERVAL_VAR} ({interval}) "
                         "or be 0: the watchdog is re-armed at each periodic sample")
    fault_handle = open(side / "faulthandler.log", "a", encoding="utf-8")
    audit_handle = open(side / "audit.jsonl", "a", encoding="utf-8")
    config = {"side_dir": str(side), "interval_s": interval, "watchdog_s": watchdog,
              "force_gc": force_gc, "pid": os.getpid(),
              "faulthandler_was_enabled": faulthandler.is_enabled(),
              "python": sys.version, "pythonmalloc": environ.get("PYTHONMALLOC"),
              "dev_mode": bool(sys.flags.dev_mode)}
    _STATE.update(installed=True, config=config, fault_handle=fault_handle,
                  audit_handle=audit_handle, interval=interval, watchdog=watchdog,
                  force_gc=force_gc, last_sample=time.monotonic(), samples=0, busy=False,
                  previous_excepthook=sys.excepthook,
                  previous_faulthandler=faulthandler.is_enabled())
    faulthandler.enable(file=fault_handle, all_threads=True)
    _rearm_watchdog()
    gc.callbacks.append(_gc_callback)
    sys.excepthook = _excepthook
    _write(sample("install", config=config))
    return dict(config)


def install_from_environment(out: Path, *, environ=None) -> dict[str, Any] | None:
    """The runner hook: ``install(out)`` if ``HMASD_CRASH_AUDIT=1``, otherwise nothing."""
    if not enabled(environ):
        return None
    return install(out, environ=environ)


def uninstall() -> None:
    """Undo :func:`install` (tests; a runner never needs it)."""
    if not _STATE.get("installed"):
        return
    try:
        gc.callbacks.remove(_gc_callback)
    except ValueError:
        pass
    faulthandler.cancel_dump_traceback_later()
    if sys.excepthook is _excepthook:
        sys.excepthook = _STATE["previous_excepthook"]
    faulthandler.disable()
    if _STATE["previous_faulthandler"]:
        faulthandler.enable(file=sys.__stderr__, all_threads=True)
    _STATE["fault_handle"].close()
    _STATE["audit_handle"].close()
    _STATE.clear()
