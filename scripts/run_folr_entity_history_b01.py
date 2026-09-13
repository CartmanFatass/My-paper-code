"""One complete allocated E arm; adjacent admission and timeout enclose this entry."""
import time
START = time.monotonic()
import argparse
import json
from pathlib import Path
import random
import signal
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def publish(out, summary):
    import resource
    summary['runner_wall_seconds'] = time.monotonic() - START
    summary['peak_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    encoded = json.dumps(summary, indent=2, allow_nan=False) + '\n'
    path = out / 'summary.json'
    path.write_text(encoded)
    if json.loads(path.read_text()) != summary:
        raise IOError('summary publication/readback mismatch')


def add_bank_comparison(summary, generic):
    from experiments.candidates.vap_folr_core.entity_history_b01.publication import pair_result
    if generic['status'] == 'incomplete':
        summary['pair_primary'] = None
        summary['pair_primary_unavailable'] = 'Collected Generic arm is incomplete; no BANK-minus-Generic estimate or MEI branch.'
    else:
        summary['pair_primary'] = pair_result(generic, summary)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--arm', choices=['GENERIC_RETAIN', 'BANK'], required=True)
    parser.add_argument('--seed', type=int, required=True)
    parser.add_argument('--evaluation-seed', type=int, required=True)
    parser.add_argument('--cap-seconds', type=int, required=True)
    parser.add_argument('--launch-sha', required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--generic-summary', type=Path)
    args = parser.parse_args()
    if args.cap_seconds != {'GENERIC_RETAIN': 1800, 'BANK': 3000}[args.arm]:
        parser.error('cap must match this arm of the E allocation')
    generic = None
    if args.arm == 'BANK':
        if args.generic_summary is None:
            parser.error('BANK requires the technically collected Generic summary')
        generic = json.loads(args.generic_summary.read_text())
        if generic['status'] not in ('complete', 'incomplete') or generic['arm'] != 'GENERIC_RETAIN':
            raise ValueError('BANK requires the technically collected selected Generic arm')
        if (generic['training_seed'], generic['evaluation_seed']) != (args.seed, args.evaluation_seed):
            raise ValueError('different selected seed binding')
    args.out.mkdir(parents=True, exist_ok=True)
    summary = dict(object='FOLR_ENTITY_HISTORY_B01_781201', arm=args.arm,
                   training_seed=args.seed, evaluation_seed=args.evaluation_seed,
                   launch_sha=args.launch_sha, cap_seconds=args.cap_seconds,
                   status='incomplete', training_episodes=0, training_ticks=0,
                   optimizer_steps=0, evaluation_episodes=0, evaluation_ticks=0,
                   training_returns=[], evaluation_returns=[])

    def timed_out(signum, frame):
        raise TimeoutError(f'{args.cap_seconds}-second complete arm cap')

    signal.signal(signal.SIGTERM, timed_out)
    try:
        import numpy as np
        import torch
        from experiments.candidates.vap_folr_core.entity_history_b01.environment import EntityHistoryEnv
        from experiments.candidates.vap_folr_core.entity_history_b01.learner import Learner
        from experiments.candidates.vap_folr_core.entity_history_b01.publication import arm_result
        from experiments.candidates.vap_folr_core.public_lifecycle_b01.collection import collect, sample, epsilon_at
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        random.seed(args.seed)
        np.random.seed(args.seed)
        torch.manual_seed(args.seed)
        learner = Learner(args.arm)
        initial = {name: p.detach().clone() for name, p in learner.actor.named_parameters()}
        env = EntityHistoryEnv(difficulty='easy', vision=1, seed=args.seed)
        replay = []
        for episode_num in range(1, 5001):
            episode, score, _ = collect(env, learner.actor, epsilon_at(summary['training_ticks']))
            replay.append(episode)
            summary['training_returns'].append(score)
            summary['training_episodes'] += 1
            summary['training_ticks'] += 20
            if len(replay) >= 32:
                learner.update(sample(replay), episode_num)
                summary['optimizer_steps'] += 1
            if episode_num % 200 == 0:
                print(json.dumps(dict(episode=episode_num, updates=summary['optimizer_steps'],
                                      wall_seconds=time.monotonic() - START)), flush=True)
        learner.save(args.out / 'final.pt')
        summary['actor_initial_l2'] = sum(v.double().square().sum().item() for v in initial.values()) ** 0.5
        summary['actor_change_l2'] = sum((p.detach().double() - initial[name].double()).square().sum().item()
                                       for name, p in learner.actor.named_parameters()) ** 0.5
        summary['actor_parameters'] = sum(p.numel() for p in learner.actor.parameters())
        learner.actor.eval()
        random.seed(args.evaluation_seed)
        np.random.seed(args.evaluation_seed)
        torch.manual_seed(args.evaluation_seed)
        env = EntityHistoryEnv(difficulty='easy', vision=1, seed=args.evaluation_seed)
        for _ in range(128):
            _, score, _ = collect(env, learner.actor, 0.0)
            summary['evaluation_returns'].append(score)
            summary['evaluation_episodes'] += 1
            summary['evaluation_ticks'] += 20
        summary['native_panel'] = arm_result(summary['evaluation_returns'])
        summary['status'] = 'complete'
        summary['exposure'] = '100000 native train ticks; 4969 RMSprop actor/mixer steps at lr=.0005; 128 final greedy episodes/2560 native ticks; no checkpoint selection'
        summary['rng'] = 'Fresh Python/global NumPy/Torch before construction; arm-specific constructors isolated; native environment and replay share NumPy; selector retains greedy/terminal Torch draws; fresh evaluation reset; no claimed episode coupling.'
        summary['torch_version'], summary['numpy_version'] = torch.__version__, np.__version__
        summary['torch_threads'] = [torch.get_num_threads(), torch.get_num_interop_threads()]
        if generic is not None:
            summary['generic_input'] = str(args.generic_summary)
            add_bank_comparison(summary, generic)
        publish(args.out, summary)
        if time.monotonic() - START >= args.cap_seconds:
            raise TimeoutError('runner publication exceeded the complete arm cap')
    except BaseException as exc:
        summary['status'] = 'incomplete'
        summary.pop('pair_primary', None)
        summary['failure_count_scope'] = 'Completed episodes/updates only; interrupted prefix unmeasured.'
        summary['error'] = type(exc).__name__ + ': ' + str(exc)
        publish(args.out, summary)
        raise
    print(json.dumps(dict(arm=args.arm, status=summary['status'], panel=summary['native_panel'])), flush=True)


if __name__ == '__main__':
    main()
