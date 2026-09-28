#!/usr/bin/env python3
"""Admission-guarded runner of ``b05_canonical_frame_a01`` (energy_relay_benchmark).

``train``: B = the frozen B02 SET recipe (``production_spec``: seed 925031, 2 lanes x 3000,
200 rollouts, 1.2 M transitions, checkpoints c00..c06) under the SW canonical frame; optional
``--resume-from checkpoints/cNN`` of the same B05 fit into a fresh ``--out``.
``panel``: one arm on one checkpoint under the SW wrapper -- ``B`` (a B05 checkpoint), ``C_SW``
(the frozen B02 c06), ``C_SW_FULL`` (c06, development worlds, deterministic, horizontal
proposals rescaled to unit norm before the shield); the hold-out 957001-957032 needs ``--final``.
``read``: the b05 readers over finished panels (zero episodes; no admission).
Seeds: the training seed (``--seed``), the worlds (``--worlds``) and B01's stochastic
``sample_seed(policy_seed, world, 0)``; nothing else is drawn.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TRAINING_SEEDS = (925031,)   # b02/configuration.py TRAINING_SEEDS (checked after admission)
MODES = ("deterministic", "stochastic")
ARMS = ("B", "C_SW", "C_SW_FULL")


def _modes(value: str) -> tuple[str, ...]:
    names = tuple(item.strip() for item in value.split(",") if item.strip())
    if not names or len(set(names)) != len(names) or any(name not in MODES for name in names):
        raise argparse.ArgumentTypeError(f"modes must be a comma list from {MODES}")
    return names


def _labelled(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("expected LABEL=VALUE")
    label, rest = value.split("=", 1)
    if not label or not rest:
        raise argparse.ArgumentTypeError("expected LABEL=VALUE")
    return label, rest


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    train = commands.add_parser("train")
    train.add_argument("--seed", type=int, choices=TRAINING_SEEDS, required=True)
    train.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    train.add_argument("--threads", type=int, default=4)
    train.add_argument("--launch-sha", required=True)
    train.add_argument("--out", type=Path, required=True)
    train.add_argument("--resume-from", type=Path, default=None,
                       help="checkpoints/c{ii} directory (agent.pt + record.json) of this B05 fit")
    train.add_argument("--resume-source-sha", default=None,
                       help="launch SHA the resumed checkpoint's record.json must carry")
    panel = commands.add_parser("panel")
    panel.add_argument("--arm", choices=ARMS, required=True)
    panel.add_argument("--checkpoint", type=Path, required=True,
                       help="checkpoints/c{ii} directory holding agent.pt and record.json")
    panel.add_argument("--out", type=Path, required=True)
    panel.add_argument("--worlds", default="955001-955032")
    panel.add_argument("--modes", type=_modes, default=MODES)
    panel.add_argument("--final", action="store_true",
                       help="read the hold-out 957001-957032 (declared once per arm endpoint)")
    panel.add_argument("--launch-sha", required=True)
    panel.add_argument("--workers", type=int, default=max(1, min(8, (os.cpu_count() or 1) // 2)))
    panel.add_argument("--threads", type=int, default=2)
    panel.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    read = commands.add_parser("read")
    read.add_argument("--out", type=Path, required=True)
    read.add_argument("--panel", type=_labelled, action="append", required=True,
                      metavar="LABEL=PANEL_JSON", help="traced B05 panel (traces/ beside panels/)")
    read.add_argument("--reference", type=_labelled, action="append", default=[],
                      metavar="LABEL=JSON", help="panel JSON or b04 block2/paired_rotation.json")
    read.add_argument("--pair", type=_labelled, action="append", default=[],
                      metavar="NAME=A:B", help="per-world A - B by spawn corner")
    read.add_argument("--access", default=None,
                      help="b04 block1/conditions.json (users_in_access_range_t0 by seed)")
    read.add_argument("--data-root", type=Path, default=ROOT,
                      help="checkout holding runs/; relative panel/reference paths resolve here")
    args = parser.parse_args(argv)
    if args.command == "train" and args.resume_source_sha is not None and args.resume_from is None:
        parser.error("--resume-source-sha requires --resume-from")
    if args.command == "read":
        for name, spec in args.pair:
            if spec.count(":") != 1 or not all(spec.split(":")):
                parser.error(f"--pair {name}: expected NAME=A:B")
    return args


def _resolve(root: Path, value: str) -> str:
    path = Path(value)
    return str(path if path.is_absolute() else root / path)


def main(argv=None):
    args = parse_args(argv)
    argv_record = sys.argv if argv is None else argv
    if args.command == "read":
        from experiments.candidates.energy_relay_benchmark.b04.run_geometry_probe import (
            canonical_data_root,
        )
        from experiments.candidates.energy_relay_benchmark.b05.readers import read

        root = canonical_data_root(args.data_root.resolve())
        read(args.out, panels={label: _resolve(root, path) for label, path in args.panel},
             references={label: _resolve(root, path) for label, path in args.reference},
             pairs={name: tuple(spec.split(":")) for name, spec in args.pair},
             access_path=_resolve(root, args.access) if args.access else None, argv=argv_record)
        print(f"read: wrote {args.out}")
        return 0
    # Admission precedes candidate imports, output creation, and torch effects.
    from scripts.hmasd_admission import require_admission

    admission = require_admission(__file__, direction="energy_relay_benchmark")
    if args.launch_sha != admission["sha"]:
        raise RuntimeError("launch SHA does not match admission")
    if args.command == "train":
        if os.environ.get("HMASD_CRASH_AUDIT") == "1":
            # Opt-in crash diagnostics (default off: this branch is the only effect).
            from experiments.candidates.energy_relay_benchmark.diagnostics.crash_audit import (
                install_from_environment,
            )

            install_from_environment(args.out)
        from experiments.candidates.energy_relay_benchmark.b05.training import (
            production_spec, run_training,
        )

        return run_training(out=args.out, launch_sha=args.launch_sha,
                            spec=production_spec(args.seed), device_name=args.device,
                            threads=args.threads, argv=argv_record, resume_from=args.resume_from,
                            resume_source_sha=args.resume_source_sha)
    from experiments.candidates.energy_relay_benchmark.b02.checkpoint_eval import parse_worlds
    from experiments.candidates.energy_relay_benchmark.b05.evaluation import run_panel

    return run_panel(arm=args.arm, checkpoint_dir=args.checkpoint, out=args.out,
                     worlds=parse_worlds(args.worlds), modes=args.modes, final=args.final,
                     launch_sha=args.launch_sha, workers=args.workers, threads=args.threads,
                     device_name=args.device, argv=argv_record)


if __name__ == "__main__":
    main()
