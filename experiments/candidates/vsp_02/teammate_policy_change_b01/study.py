"""One prefix, two Adam descendants, and native-return publication."""
import csv
import json
import platform
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import torch
from torch.distributions import Categorical

from .host import HandoffEnv
from .learner import (Agent, RecurrentPolicy, adam_summary, fork_agents, generator,
                      make_optimizer, parameters, training_streams, update)


@dataclass(frozen=True)
class StudyConfig:
    seed: int = 1103
    engineering_fixture: bool = False

    @property
    def prefix_episodes(self):
        return 16 if self.engineering_fixture else 4096

    @property
    def adaptation_episodes(self):
        return 16 if self.engineering_fixture else 1024

    @property
    def evaluation_episodes(self):
        return 4 if self.engineering_fixture else 64

    @property
    def checkpoints(self):
        return (16,) if self.engineering_fixture else (16, 32, 64, 128, 256, 512, 768, 1024)

    @property
    def wall_seconds(self):
        return 60 if self.engineering_fixture else 1800

    def record(self):
        return dict(asdict(self), prefix_episodes=self.prefix_episodes,
                    adaptation_episodes=self.adaptation_episodes,
                    evaluation_episodes=self.evaluation_episodes,
                    checkpoints=self.checkpoints, wall_seconds=self.wall_seconds,
                    horizon=48, rollout_episodes=16, epochs=4, minibatch_episodes=4,
                    gamma=1, gae_lambda=0.95, ppo_clip=0.2, value_coefficient=0.5,
                    entropy_coefficient=0.01, gradient_clip=0.5, learning_rate=0.0003,
                    adam_betas=[0.9, 0.999], adam_epsilon=1e-8)


@torch.no_grad()
def collect(model, streams, batch_size, changed, check_deadline, record):
    """Only observations enter the network; report any executed partial batch."""
    check_deadline()
    lights = torch.randint(0, 2, (batch_size, 16), generator=streams['light']) * 2 - 1
    env = HandoffEnv(batch_size)
    obs = env.reset(lights, changed)
    hidden = None
    returns = torch.zeros(batch_size)
    steps = 0
    data = {key: [] for key in ('obs', 'actions', 'log_probs', 'values', 'rewards')}
    try:
        for _ in range(48):
            check_deadline()
            logits, values, hidden = model(obs[:, None, :], hidden)
            logits = logits[:, 0]
            actions = torch.multinomial(logits.softmax(-1), 1,
                                        generator=streams['action']).squeeze(-1)
            next_obs, reward, done = env.step(actions)
            # Count immediately after the actual joint transition, before publication.
            returns += reward
            steps += 1
            data['obs'].append(obs)
            data['actions'].append(actions)
            data['log_probs'].append(Categorical(logits=logits).log_prob(actions))
            data['values'].append(values[:, 0])
            data['rewards'].append(reward)
            obs = next_obs
        return {key: torch.stack(value, dim=1) for key, value in data.items()}
    finally:
        record([dict(episode=i + 1, **{'return': float(returns[i])},
                     joint_steps=steps, complete_episode=(steps == 48))
                for i in range(batch_size)])


def primary_readings(rows, q):
    partial = {}
    for arm in ('CARRY', 'RESET'):
        actual = [r for r in rows if r['phase'] == 'adaptation' and r['arm'] == arm]
        complete = [r['return'] for r in actual if r['complete_episode']]
        partial[arm] = dict(episodes=len(complete), episodes_started=len(actual),
                            joint_steps=sum(r['joint_steps'] for r in actual),
                            observed_mean=sum(complete) / len(complete) if complete else None)
    full = all(partial[arm]['episodes'] == q for arm in partial)
    primary = None
    if full:
        primary = dict(carry_mean=partial['CARRY']['observed_mean'],
                       reset_mean=partial['RESET']['observed_mean'],
                       delta_reset_minus_carry=(partial['RESET']['observed_mean']
                                               - partial['CARRY']['observed_mean']))
    return full, primary, partial


def exposure(training, evaluation, updates):
    keys = ('training_episodes', 'training_episodes_started', 'training_joint_steps',
            'optimizer_steps', 'evaluation_episodes', 'evaluation_episodes_started',
            'evaluation_joint_steps')
    detail = {}
    for rows, kind in ((training, 'training'), (evaluation, 'evaluation')):
        for row in rows:
            name = row['phase'] + '/' + row['arm']
            counts = detail.setdefault(name, dict.fromkeys(keys, 0))
            counts[kind + '_episodes'] += int(row['complete_episode'])
            counts[kind + '_episodes_started'] += 1
            counts[kind + '_joint_steps'] += row['joint_steps']
    for row in updates:
        name = row['phase'] + '/' + row['arm']
        counts = detail.setdefault(name, dict.fromkeys(keys, 0))
        counts['optimizer_steps'] += row['optimizer_steps']
    return dict(by_phase_arm=detail,
                total={key: sum(c[key] for c in detail.values()) for key in keys})


def training_bins(rows):
    bins = []
    for phase, arm in (('prefix', 'PREFIX'), ('adaptation', 'CARRY'), ('adaptation', 'RESET')):
        actual = [r for r in rows if r['phase'] == phase and r['arm'] == arm
                  and r['complete_episode']]
        for start in range(0, len(actual), 16):
            group = actual[start:start + 16]
            bins.append(dict(phase=phase, arm=arm, through_episode=group[-1]['episode'],
                             episodes_in_bin=len(group),
                             mean_return=sum(r['return'] for r in group) / len(group)))
    return bins


def evaluation_readings(rows):
    groups = {}
    for row in rows:
        key = (row['phase'], row['arm'], row['checkpoint'])
        groups.setdefault(key, []).append(row)
    return [dict(phase=phase, arm=arm, checkpoint=q,
                 complete_episodes=sum(r['complete_episode'] for r in group),
                 episodes_started=len(group),
                 mean_return=(sum(r['return'] for r in group if r['complete_episode'])
                              / sum(r['complete_episode'] for r in group)
                              if any(r['complete_episode'] for r in group) else None))
            for (phase, arm, q), group in groups.items()]


def write_figure(path, bins, evaluations):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    for arm in ('PREFIX', 'CARRY', 'RESET'):
        points = [r for r in bins if r['arm'] == arm]
        ax = axes[0 if arm == 'PREFIX' else 1]
        ax.plot([r['through_episode'] for r in points],
                [r['mean_return'] for r in points], marker='.', label=arm)
    old = [r for r in evaluations if r['arm'] == 'PREFIX' and r['mean_return'] is not None]
    if old:
        axes[0].scatter([old[0]['checkpoint']], [old[0]['mean_return']],
                        marker='x', label='sampled old endpoint')
    for arm in ('CARRY', 'RESET'):
        points = [r for r in evaluations if r['arm'] in ('SHARED', arm)
                  and r['mean_return'] is not None]
        axes[2].plot([r['checkpoint'] for r in points], [r['mean_return'] for r in points],
                     marker='.', label=arm)
    for ax, title in zip(axes, ('Prefix training', 'Adaptation training', 'Sampled new evaluation')):
        ax.set(title=title, xlabel='Phase episode', ylabel='Deliveries per episode')
        ax.legend()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def source_revision():
    """Read the local checkout record without spawning Git or imposing a guard."""
    root = Path(__file__).resolve().parents[4]
    try:
        git_dir = root / '.git'
        if git_dir.is_file():
            git_dir = (root / git_dir.read_text().strip().split(': ', 1)[1]).resolve()
        head = (git_dir / 'HEAD').read_text().strip()
        if not head.startswith('ref: '):
            return head
        ref = head[5:]
        common = git_dir
        if (git_dir / 'commondir').exists():
            common = (git_dir / (git_dir / 'commondir').read_text().strip()).resolve()
        if (common / ref).exists():
            return (common / ref).read_text().strip()
        for line in (common / 'packed-refs').read_text().splitlines():
            if line.endswith(' ' + ref):
                return line.split()[0]
    except OSError:
        pass
    return None


def run_study(config, out_dir, clock=time.monotonic, started_at=None):
    start = clock() if started_at is None else started_at
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rows = {'training': [], 'evaluation': [], 'updates': []}
    columns = {
        'training': ('phase', 'arm', 'episode', 'return', 'joint_steps', 'complete_episode',
                     'global_steps_before_collection'),
        'evaluation': ('phase', 'arm', 'checkpoint', 'episode', 'return', 'joint_steps',
                       'complete_episode'),
        'updates': ('phase', 'arm', 'rollout_index', 'optimizer_steps', 'total_global_steps',
                    'complete_update', 'mean_policy_loss', 'mean_value_loss', 'mean_entropy',
                    'max_pre_clip_gradient_norm')}
    filenames = dict(training='training_returns.csv', evaluation='evaluation_returns.csv',
                     updates='updates.csv')
    files, writers = {}, {}
    movement, fork = {}, {}
    prefix, arms, initial, fork_parameters = None, {}, None, None
    status, reason = 'COMPLETE', None

    def check_deadline():
        if clock() - start >= config.wall_seconds:
            raise TimeoutError('Complete invocation wall deadline reached')

    def append(kind, records):
        for row in records:
            rows[kind].append(row)
            writers[kind].writerow(row)
        files[kind].flush()

    def train_batch(agent, phase, arm, batch_index, changed):
        progress = agent.global_steps
        def record_batch(batch):
            for row in batch:
                row.update(phase=phase, arm=arm, episode=(batch_index - 1) * 16 + row['episode'],
                           global_steps_before_collection=progress)
            append('training', batch)
        rollout = collect(agent.model, agent.streams, 16, changed, check_deadline, record_batch)
        def record_update(row):
            row.update(phase=phase, arm=arm, rollout_index=batch_index)
            append('updates', [row])
        update(agent, rollout, check_deadline, record_update)

    def evaluate(model, phase, arm, q, offset, changed):
        check_deadline()
        streams = dict(light=generator(config.seed + offset),
                       action=generator(config.seed + offset + 1))
        for first in range(0, config.evaluation_episodes, 16):
            size = min(16, config.evaluation_episodes - first)
            def record_batch(batch):
                for row in batch:
                    row.update(phase=phase, arm=arm, checkpoint=q, episode=first + row['episode'])
                append('evaluation', batch)
            collect(model, streams, size, changed, check_deadline, record_batch)

    try:
        for kind, filename in filenames.items():
            files[kind] = (out / filename).open('w', newline='', encoding='utf-8')
            writers[kind] = csv.DictWriter(files[kind], fieldnames=columns[kind])
            writers[kind].writeheader()
            files[kind].flush()
        check_deadline()
        torch.set_num_threads(1)
        torch.manual_seed(config.seed)
        model = RecurrentPolicy()
        prefix = Agent(model, make_optimizer(model), training_streams(config.seed))
        initial = parameters(model)
        movement['initial_parameter_rms'] = initial.square().mean().sqrt().item()
        for batch_index in range(1, config.prefix_episodes // 16 + 1):
            train_batch(prefix, 'prefix', 'PREFIX', batch_index, False)
            if batch_index == 1:
                movement['first_prefix_rollout'] = dict(
                    displacement_rms=(parameters(model) - initial).square().mean().sqrt().item(),
                    global_steps=prefix.global_steps)
        movement['prefix_end'] = dict(
            displacement_rms=(parameters(model) - initial).square().mean().sqrt().item(),
            global_steps=prefix.global_steps)
        evaluate(model, 'prefix', 'PREFIX', config.prefix_episodes, 101, False)
        arms = fork_agents(prefix, config.seed)
        fork_parameters = parameters(model)
        fork = {name: dict(adam_summary(agent), model_max_absolute_difference=
                          (parameters(agent.model) - fork_parameters).abs().max().item(),
                          episode_hidden_state='zero at next episode')
                for name, agent in arms.items()}
        fork['PREFIX'] = adam_summary(prefix)
        evaluate(model, 'post', 'SHARED', 0, 201, True)
        for batch_index in range(1, config.adaptation_episodes // 16 + 1):
            for name, agent in arms.items():
                train_batch(agent, 'adaptation', name, batch_index, True)
            q = batch_index * 16
            if q in config.checkpoints:
                i = config.checkpoints.index(q) + 1
                for name, agent in arms.items():
                    evaluate(agent.model, 'post', name, q, 1000 + 10 * i, True)
        check_deadline()
    except TimeoutError as exc:
        status, reason = 'TIME_LIMIT', str(exc)
    except Exception as exc:
        status, reason = 'ERROR', f'{type(exc).__name__}: {exc}'
    finally:
        for file in files.values():
            file.close()

    if prefix is not None and initial is not None:
        movement['prefix_final_observed'] = dict(
            displacement_rms=(parameters(prefix.model) - initial).square().mean().sqrt().item(),
            global_steps=prefix.global_steps)
    for name, agent in arms.items():
        movement[name] = dict(displacement_rms=(parameters(agent.model) - fork_parameters)
                             .square().mean().sqrt().item(), global_steps=agent.global_steps,
                             steps_since_fork=agent.global_steps - prefix.global_steps,
                             adam=adam_summary(agent))
    full, primary, partial = primary_readings(rows['training'], config.adaptation_episodes)
    counts = exposure(rows['training'], rows['evaluation'], rows['updates'])
    for name in partial:
        partial[name]['optimizer_steps'] = sum(r['optimizer_steps'] for r in rows['updates']
                                               if r['arm'] == name)
    bins = training_bins(rows['training'])
    evaluations = evaluation_readings(rows['evaluation'])
    missing = []
    try:
        check_deadline()
        with (out / 'training_curve.csv').open('w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=('phase', 'arm', 'through_episode',
                                                     'episodes_in_bin', 'mean_return'))
            writer.writeheader()
            writer.writerows(bins)
        check_deadline()
        write_figure(out / 'curves.png', bins, evaluations)
        check_deadline()
    except TimeoutError as exc:
        status, reason = 'TIME_LIMIT', str(exc)
    except Exception as exc:
        missing.append(f'Publication: {type(exc).__name__}: {exc}')
    for filename in ('training_curve.csv', 'curves.png'):
        if not (out / filename).exists():
            missing.append(filename)
    peak_rss = None
    try:
        import resource
        peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if sys.platform != 'darwin':
            peak_rss *= 1024
    except ImportError:
        pass
    total = counts['total']
    expected_training = config.prefix_episodes + 2 * config.adaptation_episodes
    expected_evaluation = (2 + 2 * len(config.checkpoints)) * config.evaluation_episodes
    chain_complete = (total['training_episodes'] == expected_training
                      and total['training_joint_steps'] == expected_training * 48
                      and total['optimizer_steps'] == expected_training
                      and total['evaluation_episodes'] == expected_evaluation
                      and total['evaluation_joint_steps'] == expected_evaluation * 48
                      and all(r['complete_update'] for r in rows['updates']))
    elapsed = clock() - start
    if elapsed >= config.wall_seconds:
        status, reason = 'TIME_LIMIT', 'Complete invocation wall deadline reached'
    summary = dict(object_id='VSP02-TEAMMATE-POLICY-CHANGE-B01',
                   run_kind='ENGINEERING_FIXTURE' if config.engineering_fixture else 'B_EXPLORE',
                   config=config.record(), source_git_revision=source_revision(),
                   runtime=dict(python=sys.version, torch=torch.__version__, platform=platform.platform(),
                                device='cpu', dtype='float32', compute_threads=torch.get_num_threads(),
                                interop_threads=torch.get_num_interop_threads()),
                   status=status, stopping_reason=reason, error=reason if status == 'ERROR' else None,
                   counts=counts, model_selection_trials=0, independent_prefixes=1,
                   primary_window_complete=full, primary=primary, partial_observations=partial,
                   scientific_comparison_complete=(not config.engineering_fixture and chain_complete
                                                   and status == 'COMPLETE'),
                   claim_ceiling=('Engineering-only fixture; no B01 performance claim.'
                                  if config.engineering_fixture else
                                  'One prefix and one pair; initial local signal only.'),
                   limitation=reason, evaluations=evaluations,
                   terminal_means={name: next((r['mean_return'] for r in evaluations
                                               if r['arm'] == name and r['checkpoint'] == endpoint
                                               and r['complete_episodes'] == config.evaluation_episodes), None)
                                   for name, endpoint in (('PREFIX', config.prefix_episodes),
                                                          ('SHARED', 0),
                                                          ('CARRY', config.adaptation_episodes),
                                                          ('RESET', config.adaptation_episodes))},
                   movement=movement, fork=fork, wall_seconds=elapsed,
                   peak_rss_bytes=peak_rss, resources_unmeasured=(peak_rss is None),
                   missing_outputs=missing,
                   output_paths={name: str(out / name) for name in
                                 (*filenames.values(), 'training_curve.csv', 'curves.png', 'summary.json')})
    summary_path = out / 'summary.json'
    summary_path.write_text(json.dumps(summary, indent=2, allow_nan=False), encoding='utf-8')
    # Publication itself belongs to the cap; retain an overrun as TIME_LIMIT.
    summary['wall_seconds'] = clock() - start
    if summary['wall_seconds'] >= config.wall_seconds:
        summary.update(status='TIME_LIMIT', stopping_reason='Deadline crossed during publication',
                       scientific_comparison_complete=False, limitation='Publication exceeded deadline')
    summary_path.write_text(json.dumps(summary, indent=2, allow_nan=False), encoding='utf-8')
    return summary
