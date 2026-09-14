"""Verify the frozen final panel from recorded bytes; no model, RNG or environment."""
import argparse
import collections
import hashlib
import json
import math
from pathlib import Path
import statistics


def analyze(root):
    summary = json.loads((root / 'summary.json').read_text())
    episodes = [json.loads(line) for line in (root / 'episodes.jsonl').read_text().splitlines()]
    updates = [json.loads(line) for line in (root / 'updates.jsonl').read_text().splitlines()]
    assert summary['object'] == 'ACVC_CLUSTER_DEPLOYMENT_B01'
    assert summary['master'] == 21457 and summary['evaluation_namespace'] == 31457
    assert summary['launch_sha'] == 'e06b3d63f7e9f77c13fd327dba0270d80e74d819'
    assert summary['status'] == 'complete' and summary['fit_complete'] and summary['checkpoint_complete']
    assert summary['scientific_invocations'] == 1 and not summary['limits']
    cfg = summary['configuration']
    for key, value in dict(horizon=256, training_episodes=512, episodes_per_rollout=2,
                           ppo_epochs_per_rollout=4, chunk=32, evaluation_episodes_per_arm=64,
                           evaluation_order=['C','F','dwell'], device='cpu', dtype='float32',
                           intraop_threads=1, interop_threads=1, user_distribution='cluster',
                           training_rule='C').items():
        assert cfg[key] == value, key
    expected = dict(environment_constructors=4, explicit_resets=704, train_episodes=512,
                    eval_episodes=192, rollouts=256, optimizer_steps=1024, backward_calls=1024,
                    update_records=1024, train_team_steps=131072, eval_team_steps=49152,
                    team_steps=180224, fresh_dense_initializations=1, post_fit_loads=3,
                    final_checkpoints=1, new_fits=1, gate_constructions=0,
                    duration_heads=0, selector_updates=0, evaluation_updates=0)
    for key, value in expected.items():
        assert summary['counts'][key] == value, key
    assert len(episodes) == 704 and len(updates) == 1024
    training = [row for row in episodes if row['phase'] == 'train']
    evaluation = [row for row in episodes if row['phase'] == 'eval']
    assert len(training) == 512 and len(evaluation) == 192
    for i, row in enumerate(training):
        assert row['episode'] == i and row['master'] == row['base'] == 21457
        assert row['arm'] == 'DENSE' and row['rule'] == 'DENSE_fit'
        assert row['reset_seed'] == 21457*100000+1000+i
        assert row['duration_decisions'] == row['d4'] == 0
        assert row['velocity_decisions'] == 5*256
    for row in episodes:
        assert row['steps'] == 256 and math.isfinite(row['S']) and math.isfinite(row['J'])
        assert row['J'] == row['S']/256
    for index, row in enumerate(updates):
        rollout, epoch = divmod(index, 4)
        assert row['master'] == 21457 and row['rollout'] == rollout and row['epoch'] == epoch
        assert row['episodes'] == [rollout*2,rollout*2+1]
        assert all(math.isfinite(row[key]) for key in ('loss','policy_loss','value_loss','entropy','grad_norm'))
    assert sum(row['steps'] for row in episodes) == 180224
    by_arm = {}
    for position, arm in enumerate(('C','F','dwell')):
        rows = evaluation[position*64:(position+1)*64]
        assert len(rows) == 64
        for i, row in enumerate(rows):
            assert row['arm'] == row['rule'] == arm and row['base'] == 21457
            assert row['evaluation_namespace'] == 31457 and row['episode'] == i
            assert row['reset_seed'] == 31457*100000+2000+i
        by_arm[arm] = rows
        native = summary['primary']['arms'][arm]
        assert native['complete'] and native['available_episodes'] == 64
        assert math.isclose(native['mean_J'], statistics.fmean(row['J'] for row in rows), abs_tol=1e-14)
        assert math.isclose(native['mean_S'], statistics.fmean(row['S'] for row in rows), abs_tol=1e-12)
    contrasts = {}
    for name, (left,right) in {'F-C':('F','C'),'F-dwell':('F','dwell'),'dwell-C':('dwell','C')}.items():
        values = [a['J']-b['J'] for a,b in zip(by_arm[left],by_arm[right])]
        mean = statistics.fmean(values)
        sd = statistics.stdev(values)
        reading = 'UP' if mean > .01 else 'DOWN' if mean < -.01 else 'WITHIN'
        result = dict(mean_J=mean, sample_SD_J=sd, conditional_SE_J=sd/8,
                      minimum_J=min(values), maximum_J=max(values),
                      adverse=sum(v<0 for v in values), favorable=sum(v>0 for v in values),
                      zero=sum(v==0 for v in values), reading=reading)
        native = summary['primary']['contrasts'][name]
        assert native['complete'] and native['n_joint_episodes'] == 64
        assert native['episode_ids'] == list(range(64)) and native['paired_differences_J'] == values
        for key, value in result.items():
            assert (math.isclose(native[key], value, rel_tol=1e-13, abs_tol=1e-14)
                    if isinstance(value,float) else native[key] == value), (name,key)
        result.update(adverse_episode_ids=[i for i,v in enumerate(values) if v<0], paired_differences_J=values)
        contrasts[name] = result
    exposure = summary['exposure']
    for group in ('common_actor','critic','total'):
        assert exposure[group]['parameters'] > 0
        assert all(math.isfinite(exposure[group][key]) and exposure[group][key] > 0
                   for key in ('initial_norm','final_norm','displacement','relative_displacement'))
    forecasts = {'F-C':[.55,.25,.20], 'F-dwell':[.45,.30,.25]}
    brier = {name: sum((p-float(label==contrasts[name]['reading']))**2
                      for p,label in zip(probs,('UP','WITHIN','DOWN')))
             for name,probs in forecasts.items()}
    return dict(accepted=True, evidence_class='B/EXPLORE', independent_training_units=1,
                rule='strictly >+0.01 J is UP; inclusive [-0.01,+0.01] is WITHIN, retaining its sign and without equivalence; strictly <-0.01 is DOWN',
                uncertainty='64 paired initial-world differences conditional on the one fitted endpoint; no training-population or joint confidence',
                verification='All704 episode rows and1024 ordered update rows; literal source/master/namespace/config; native published primary checked against scalar recorded-byte arithmetic with absolute tolerance1e-14 for J moments. No new scientific exposure.',
                expected_counts=expected, arm_means=summary['primary']['arms'], contrasts=contrasts,
                exposure=exposure, forecast_brier_sum=brier, completion_forecast_brier=(.95-1)**2,
                native_resources=summary['resources'], raw_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in root.iterdir() if p.is_file()})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.root)
    args.out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key:value for key,value in result.items() if key not in ('exposure','raw_sha256','contrasts')}))
    print(json.dumps({name:{key:value for key,value in result.items() if key!='paired_differences_J'} for name,result in result['contrasts'].items()}))
