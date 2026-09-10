"""One FOLR-PUBLIC-LIFECYCLE-TIMING-B02 arm; external timeout covers startup too."""
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
    import resource  # Declared Linux execution route.
    summary['wall_seconds'] = time.monotonic() - START
    summary['peak_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    (out / 'summary.json').write_text(json.dumps(summary, indent=2, allow_nan=False) + '\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--arm', required=True, choices=['RETAIN', 'EVENT', 'RANDOM'])
    parser.add_argument('--seed', type=int, default=7805)
    parser.add_argument('--evaluation-seed', type=int, default=107805)
    parser.add_argument('--launch-sha', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    summary = dict(arm=args.arm, training_seed=args.seed, evaluation_seed=args.evaluation_seed,
                   launch_sha=args.launch_sha, status='incomplete', training_episodes=0,
                   training_ticks=0, optimizer_steps=0, evaluation_episodes=0,
                   evaluation_ticks=0, evaluation_returns=[], training_return_sum=0.0,
                   training_events=dict(births=0, departures=0, survivor_opportunities=0, eligible_survivor_opportunities=0, survivor_resets=0),
                   evaluation_events=dict(births=0, departures=0, survivor_opportunities=0, eligible_survivor_opportunities=0, survivor_resets=0))

    def timed_out(signum, frame):
        raise TimeoutError('1800-second complete logical arm cap')

    signal.signal(signal.SIGTERM, timed_out)
    try:
        import numpy as np
        import torch
        from experiments.candidates.vap_folr_core.public_lifecycle_b01.environment import LifecycleEnv
        from experiments.candidates.vap_folr_core.public_lifecycle_b01.collection import collect, sample, epsilon_at
        from experiments.candidates.vap_folr_core.public_lifecycle_b01.learner import Learner
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        random.seed(args.seed)
        np.random.seed(args.seed)
        torch.manual_seed(args.seed)
        learner = Learner(args.arm)
        env = LifecycleEnv(difficulty='easy', vision=1, seed=args.seed)
        mask_rng = np.random.Generator(np.random.PCG64(207805)) if args.arm == 'RANDOM' else None
        replay = []
        for episode_num in range(1, 5001):
            episode, score, counts = collect(env, learner.actor, epsilon_at(summary['training_ticks']), mask_rng)
            replay.append(episode)  # Exactly 5000 episodes: capacity never exceeded.
            summary['training_episodes'] += 1
            summary['training_ticks'] += 20
            summary['training_return_sum'] += score
            for k, v in counts.items():
                summary['training_events'][k] += v
            if len(replay) >= 32:
                learner.update(sample(replay), episode_num)
                summary['optimizer_steps'] += 1
            if episode_num % 200 == 0:
                print(json.dumps(dict(episode=episode_num, updates=summary['optimizer_steps'],
                                      wall_seconds=time.monotonic() - START)), flush=True)
        learner.save(args.out / 'final.pt')
        learner.actor.eval()
        random.seed(args.evaluation_seed)
        np.random.seed(args.evaluation_seed)
        torch.manual_seed(args.evaluation_seed)
        env = LifecycleEnv(difficulty='easy', vision=1, seed=args.evaluation_seed)
        mask_rng = np.random.Generator(np.random.PCG64(307805)) if args.arm == 'RANDOM' else None
        for _ in range(128):
            _, score, counts = collect(env, learner.actor, 0.0, mask_rng)
            summary['evaluation_returns'].append(score)
            summary['evaluation_episodes'] += 1
            summary['evaluation_ticks'] += 20
            for k, v in counts.items():
                summary['evaluation_events'][k] += v
        summary['mean_native_return'] = float(np.mean(summary['evaluation_returns']))
        summary['status'] = 'complete'
        summary['exposure'] = '100000 real native training ticks; 4969 actor/mixer RMSprop steps at lr=0.0005; 128 final greedy evaluation episodes'
        if args.arm == 'RANDOM':
            summary['mask_rng'] = dict(bit_generator='PCG64', training_seed=207805,
                                       evaluation_seed=307805, probability=0.1,
                                       draws_per_episode=105, frequency_matched=False)
        summary['rng'] = f'Python/global NumPy/Torch seeded before model construction; native traffic and replay share global NumPy; source epsilon selector uses Torch including greedy and terminal draws; all three reset to{args.evaluation_seed} for final evaluation'
        summary['torch_version'] = torch.__version__
        summary['numpy_version'] = np.__version__
        summary['torch_threads'] = [torch.get_num_threads(), torch.get_num_interop_threads()]
        publish(args.out, summary)
        if time.monotonic() - START >= 1800:
            raise TimeoutError('publication exceeded complete logical arm cap')
    except BaseException as exc:
        summary['status'] = 'incomplete'
        summary['failure_count_scope'] = 'completed episodes and completed updates only; any interrupted episode/update prefix is unmeasured'
        summary['error'] = type(exc).__name__ + ': ' + str(exc)
        publish(args.out, summary)
        raise
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
