"""Fixed-workload benchmark for the scenario1-3 step path-loss cache."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path
from statistics import median
import sys
from time import perf_counter

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np

from envs.pettingzoo.scenario1 import UAVBaseStationEnv
from envs.pettingzoo.scenario2 import UAVCooperativeNetworkEnv
from envs.pettingzoo.scenario3 import UAVMultiHopEnv


CASES = (
    ("scenario1", UAVBaseStationEnv, {"n_uavs": 8, "n_users": 80}),
    (
        "scenario2",
        UAVCooperativeNetworkEnv,
        {"n_uavs": 8, "n_users": 80, "n_ground_bs": 4},
    ),
    (
        "scenario3",
        UAVMultiHopEnv,
        {"n_uavs": 12, "n_users": 100, "n_ground_bs": 4, "n_clusters": 5},
    ),
)
SOURCE_FILES = (
    "envs/pettingzoo/uav_env.py",
    "envs/pettingzoo/scenario1.py",
    "envs/pettingzoo/scenario2.py",
    "envs/pettingzoo/scenario3.py",
    "tools/benchmarks/benchmark_uav_path_loss_cache.py",
)
BENCHMARK_SEED = 20260815
ORACLE_RESET_SEED = 20260816
WARMUP_STEPS = 3


def _assert_equal(reference, optimized, path="output") -> None:
    if isinstance(reference, dict):
        if reference.keys() != optimized.keys():
            raise RuntimeError(f"{path}: mapping keys differ")
        for key in reference:
            _assert_equal(reference[key], optimized[key], f"{path}.{key}")
    elif isinstance(reference, np.ndarray):
        if not np.array_equal(reference, optimized):
            raise RuntimeError(f"{path}: arrays differ")
    elif isinstance(reference, (tuple, list)):
        if len(reference) != len(optimized):
            raise RuntimeError(f"{path}: sequence lengths differ")
        for index, (first, second) in enumerate(zip(reference, optimized)):
            _assert_equal(first, second, f"{path}[{index}]")
    elif reference != optimized:
        raise RuntimeError(f"{path}: values differ")


def _rng_state_equal(first, second) -> bool:
    return (
        first[0] == second[0]
        and np.array_equal(first[1], second[1])
        and first[2:] == second[2:]
    )


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _rng_fingerprint(state) -> str:
    generator, keys, position, has_gauss, cached_gaussian = state
    payload = bytearray(generator.encode("ascii"))
    payload.extend(np.asarray(keys, dtype="<u4").tobytes())
    payload.extend(
        json.dumps(
            [int(position), int(has_gauss), float(cached_gaussian)],
            separators=(",", ":"),
        ).encode("ascii")
    )
    return _sha256_bytes(bytes(payload))


def _source_fingerprint() -> dict[str, object]:
    file_digests = {}
    aggregate = hashlib.sha256()
    for relative_path in SOURCE_FILES:
        contents = (PROJECT_ROOT / relative_path).read_bytes()
        digest = _sha256_bytes(contents)
        file_digests[relative_path] = digest
        aggregate.update(relative_path.encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(contents)
        aggregate.update(b"\0")
    return {
        "algorithm": "sha256",
        "digest": aggregate.hexdigest(),
        "files": file_digests,
    }


def _git_directory() -> Path:
    dot_git = PROJECT_ROOT / ".git"
    if dot_git.is_dir():
        return dot_git
    if dot_git.is_file():
        declaration = dot_git.read_text(encoding="utf-8").strip()
        prefix = "gitdir:"
        if not declaration.lower().startswith(prefix):
            raise RuntimeError("unrecognized .git indirection file")
        candidate = Path(declaration[len(prefix):].strip())
        return candidate if candidate.is_absolute() else (PROJECT_ROOT / candidate).resolve()
    raise RuntimeError("benchmark requires a Git checkout for commit fingerprinting")


def _commit_fingerprint() -> str:
    git_directory = _git_directory()
    head = (git_directory / "HEAD").read_text(encoding="ascii").strip()
    if head.startswith("ref: "):
        reference = head[5:]
        loose_reference = git_directory / reference
        if loose_reference.is_file():
            commit = loose_reference.read_text(encoding="ascii").strip()
        else:
            commit = ""
            packed_refs = git_directory / "packed-refs"
            if packed_refs.is_file():
                for line in packed_refs.read_text(encoding="ascii").splitlines():
                    if line.startswith(("#", "^")):
                        continue
                    fields = line.split(" ", 1)
                    if len(fields) == 2 and fields[1] == reference:
                        commit = fields[0]
                        break
            if not commit:
                raise RuntimeError(f"cannot resolve Git reference {reference!r}")
    else:
        commit = head
    if len(commit) not in (40, 64) or any(
        character not in "0123456789abcdefABCDEF" for character in commit
    ):
        raise RuntimeError("resolved Git commit fingerprint is invalid")
    return commit.lower()


def _configuration_fingerprint(repeats: int) -> dict[str, object]:
    payload = {
        "cases": [
            {
                "name": name,
                "environment": f"{environment_type.__module__}.{environment_type.__qualname__}",
                "kwargs": kwargs,
            }
            for name, environment_type, kwargs in CASES
        ],
        "benchmark_seed": BENCHMARK_SEED,
        "oracle_reset_seed": ORACLE_RESET_SEED,
        "warmup_steps": WARMUP_STEPS,
        "repeats": repeats,
        "actions": {"kind": "all_zero", "dtype": "float64", "shape": ["n_uavs", 3]},
        "modes": {"reference": False, "optimized": True},
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"algorithm": "sha256", "digest": _sha256_bytes(encoded), "payload": payload}


def _make_env(environment_type, kwargs, *, cache):
    return environment_type(
        seed=BENCHMARK_SEED,
        max_steps=10000,
        step_path_loss_cache=cache,
        **kwargs,
    )


def _zero_actions(env):
    return {agent: np.zeros(3, dtype=float) for agent in env.agents}


def _oracle(environment_type, kwargs) -> dict[str, str]:
    reference = _make_env(environment_type, kwargs, cache=False)
    optimized = _make_env(environment_type, kwargs, cache=True)
    _assert_equal(
        reference.reset(seed=ORACLE_RESET_SEED),
        optimized.reset(seed=ORACLE_RESET_SEED),
    )
    reference_reset_state = reference.np_random.get_state()
    optimized_reset_state = optimized.np_random.get_state()
    if not _rng_state_equal(reference_reset_state, optimized_reset_state):
        raise RuntimeError("reference and optimized reset RNG states differ")
    actions = _zero_actions(reference)
    _assert_equal(reference.step(actions), optimized.step(actions))
    reference_step_state = reference.np_random.get_state()
    optimized_step_state = optimized.np_random.get_state()
    if not _rng_state_equal(reference_step_state, optimized_step_state):
        raise RuntimeError("reference and optimized RNG states differ")
    return {
        "after_reset": _rng_fingerprint(reference_reset_state),
        "after_oracle_step": _rng_fingerprint(reference_step_state),
    }


def _measure(environment_type, kwargs, repeats):
    reference = _make_env(environment_type, kwargs, cache=False)
    optimized = _make_env(environment_type, kwargs, cache=True)
    actions = _zero_actions(reference)
    for _ in range(WARMUP_STEPS):
        reference.step(actions)
        optimized.step(actions)

    reference_seconds = []
    optimized_seconds = []
    for repeat in range(repeats):
        # Alternate order so one mode does not systematically receive the first slot.
        ordered = (
            ((reference, reference_seconds), (optimized, optimized_seconds))
            if repeat % 2 == 0
            else ((optimized, optimized_seconds), (reference, reference_seconds))
        )
        for env, samples in ordered:
            started = perf_counter()
            env.step(actions)
            samples.append(perf_counter() - started)
    return reference_seconds, optimized_seconds


def run_benchmark(*, repeats: int = 31) -> dict[str, object]:
    if repeats < 31 or repeats % 2 == 0:
        raise ValueError("repeats must be an odd integer greater than or equal to 31")
    results = {}
    for name, environment_type, kwargs in CASES:
        rng_fingerprints = _oracle(environment_type, kwargs)
        reference_seconds, optimized_seconds = _measure(
            environment_type, kwargs, repeats
        )
        reference_median = median(reference_seconds)
        optimized_median = median(optimized_seconds)
        results[name] = {
            "workload": kwargs,
            "reference_seconds": reference_seconds,
            "optimized_seconds": optimized_seconds,
            "reference_median_seconds": reference_median,
            "optimized_median_seconds": optimized_median,
            "speedup": reference_median / optimized_median,
            "positive_median": optimized_median < reference_median,
            "rng_fingerprints": rng_fingerprints,
        }
    return {
        "schema": "uav_path_loss_cache_benchmark_v2",
        "cpu_only": True,
        "bitwise_output_and_rng_oracle": True,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "numpy": np.__version__,
        "source_fingerprint": _source_fingerprint(),
        "commit_fingerprint": _commit_fingerprint(),
        "configuration_fingerprint": _configuration_fingerprint(repeats),
        "seed": BENCHMARK_SEED,
        "warmup_steps": WARMUP_STEPS,
        "repeats": repeats,
        "cases": results,
        "optimized_default_eligible": all(
            result["positive_median"] for result in results.values()
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=31)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_benchmark(repeats=args.repeats)
    encoded = json.dumps(result, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    if not result["optimized_default_eligible"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
