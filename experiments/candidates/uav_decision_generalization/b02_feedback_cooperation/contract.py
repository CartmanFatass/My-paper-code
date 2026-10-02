"""Fixed B02 science, canonical actors and frozen import identities."""
import hashlib
import json

DIRECTION='uav_decision_generalization'
OBJECT='UAV-FEEDBACK-COOPERATION-B02'
MASTER=108311000
HORIZON=256
ARMS=('C','G','ZG','SL0','ZSL0','SL1','ZSL1','Bstar0')
PARENTS={'ZG':'G','ZSL0':'SL0','ZSL1':'SL1'}
OLD_ARMS={'C':'C','G':'G','SL0':'S_L0','SL1':'S_L1','Bstar0':'Bstar_L0'}
WORLDS=tuple(range(108310000,108310032))
AUDIT_WORLDS=(108310900,108310901)
SAMPLING_ROOTS=(108311001,108311002)
AUDIT_ROOT=108319001
ACTOR_SEEDS=(108311011,108311012)
BOOTSTRAP_SEED=108311091
MAX_CPU_SECONDS=3600
SYNTHETIC_LIMITS={'original_C_calls':256,'frozen_actor_rows':256,'count_decodes':10000}


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def initial_state_digest(positions,users,sinr,uav_sinr,connections):
    """Bind every saved reset radio field that can affect an original local row."""
    from experiments.candidates.uav_fleet_adaptation.b02.contract import array_digest
    return array_digest(positions,users,sinr,uav_sinr,connections)


def contract():
    return {'object':OBJECT,'worlds':WORLDS,'audit_worlds':AUDIT_WORLDS,'arms':ARMS,'horizon':HORIZON,
            'sampling_roots':SAMPLING_ROOTS,'audit_root':AUDIT_ROOT,'actor_seeds':ACTOR_SEEDS,
            'bootstrap_seed':BOOTSTRAP_SEED,'bootstrap_resamples':10000,'assets':ASSETS,
            'calibration':CALIBRATION,'sources':SOURCE_SHA256,'master':MASTER,
            'gate':'t0 parent; at t>=4 grid boundaries all q(t-3..t)==0 selects C; one actual nav',
            'cache':'episode-agent-source private; first103 FP32 row values and nav byte',
            'max_cpu_seconds':MAX_CPU_SECONDS,'synthetic_limits':SYNTHETIC_LIMITS}


def episode_order(phase):
    worlds=AUDIT_WORLDS if phase=='audit' else WORLDS if phase=='main' else ()
    if not worlds:raise ValueError('unknown fixed phase')
    for wi,world in enumerate(worlds):
        cells=[(arm,tape) for arm in ARMS for tape in ((-1,) if arm=='C' else (0,) if phase=='audit' else (0,1))]
        offset=0 if phase=='audit' else wi%15
        for arm,tape in cells[offset:]+cells[:offset]:
            yield {'phase':phase,'world':world,'arm':arm,'tape':tape,
                   'sampling_root':None if arm=='C' else AUDIT_ROOT if phase=='audit' else SAMPLING_ROOTS[tape]}


def expected_counts(phase,m,g):
    if phase=='main':
        episodes,slots,c,s,draws,gprob,decodes,gates=480,153600,51200,102400,143360,40960,245760,60480
        mmax,gmax=40320,20160
    elif phase=='audit':
        episodes,slots,c,s,draws,gprob,decodes,gates=16,5120,1920,3200,4480,1280,7680,1890
        mmax,gmax=1260,630
    else:raise ValueError('unknown fixed phase')
    if not 0<=m<=mmax or not 0<=g<=gmax:raise ValueError('takeover counts outside fixed bounds')
    return {'episodes':episodes,'native_steps':episodes*256,'constructor_resets':1,'explicit_resets':episodes,
            'decision_slots':slots,'worker_C_requests':c+m,'worker_S_requests':s-m,
            'worker_draws':draws-m-g,'worker_G_probabilities':gprob-g,'online_count_decodes':decodes,
            'online_gate_checks':gates,'reader_C_calls':c+m,'reader_S_rows':s,
            'reader_draws':draws,'reader_G_probabilities':gprob,'reader_count_decodes':episodes*257*5}

ASSETS=({'path': '/home/wu/projects/HMASD/runs/uav_fleet_adaptation/b02_inheritance_a01/assets/S.pt', 'bytes': 424487, 'sha256': 'b9e25fca68109bb50fa64fadfc90939ad6a4669058c1c0ccd1351c8bbcefe12a', 'state_sha256': '6fa2eddc542d8f5293f5daf6a989b97a9d7d5f56f484f1eb6bddc6a87d27de0c', 'launch_sha': 'e945483b85c7f8ddfc315c57f36938d6c14201c7'}, {'path': '/home/wu/projects/HMASD/runs/uav_fleet_adaptation/b03_inheritance_recurrence_a01/assets/S.pt', 'bytes': 424487, 'sha256': 'cb67a3d46fe9628e1dfef1ef081b89091a13fde3a92295fe198f27555c67364d', 'state_sha256': 'c6286dd32097d37b2c2c3039e487a24b756398e3ddffa9dc9e1ec3ef66170699', 'launch_sha': '4909c9553300a4a4de6eb79476e818d7b1ceab53'})
CALIBRATION={'launch_sha': '98307b0c5cb6e42763458d780568d105d3f631af', 'evidence_commit': '978c622c37207067dd673247cf6729d786383304', 'reading_path': 'runs/uav_fleet_adaptation/b04_native_development_a01/reading.json', 'reading_sha256': '93c681eba38f8fcd7fd9059eb9eaa75142771d085bf645e831099bed63b25a50', 'winners': ['S_T2', 'S_T1'], 'new_calibrations': 0}
SOURCE_SHA256={'envs/pettingzoo/__init__.py': 'd247e986e573c70196b7674d05a28ae229028d858ca4fb9c7ddf684c8c6d12c3', 'envs/pettingzoo/env_adapter.py': '8b42c1c3e7ef44cb814f79225b4af944b1018ad764dfeb17e9e1cc294df79d40', 'envs/pettingzoo/scenario1.py': 'e5b3eb7d755a7d7866cc7cd01531383bee821f0c6d72a81a3d4fa9cb5954939e', 'envs/pettingzoo/scenario2.py': '277374f365e8eeda882de53d53cc051c1534fe210622fee74d7b5a8f9d2cf2f2', 'envs/pettingzoo/uav_env.py': 'fb67554cf911adc9d3260a2a7f16d1773921c295646cb46beb4ba1247fec599e', 'envs/pettingzoo/uav_radio.py': 'db3464803b1a5aa9c9504096810dc971266a6bd7eba1c31dfe79e7d8d903f3cc', 'experiments/candidates/uav_fleet_adaptation/__init__.py': '52d21d8e90cb93167c8a2ced54f3d977f1b3edc569b0d61d69495d258be4a488', 'experiments/candidates/uav_fleet_adaptation/b02/__init__.py': 'acb5ecf84dabf7c006af3c2658d6ee8ef587cf3338d15898df75011c4c0a0970', 'experiments/candidates/uav_fleet_adaptation/b02/contract.py': '4f312ecbbe653c1d00632be4cd2f1ea6d48f7f98ce50eb28cf405f06e9fbe1a3', 'experiments/candidates/uav_fleet_adaptation/b02/controllers.py': 'a2bbbdb877bd988590472a41c336d934a0431b5c560c7e80225cbb630fc3d522', 'experiments/candidates/uav_fleet_adaptation/b02/model.py': 'c9b95b6718262c65591ed106ca81da0abb15b48ef6a8439438618365efc39934', 'experiments/candidates/uav_fleet_adaptation/b02/policies.py': 'fba732164b07d80fc2f901e6545e6ca281c7db39cd89f9e61cc49bdb40ba4efd', 'experiments/candidates/uav_fleet_transmission/__init__.py': 'd221f06bef6a96f8bbbf3a272c89bddb023f6926f8b6349e58a5965ef90ce5c6', 'experiments/candidates/uav_fleet_transmission/b05_score_sampling/__init__.py': '3c02b8ff4fc28f2fae70cb815d89fc58a180537d172899316da5c8a81a1f388f', 'experiments/candidates/uav_fleet_transmission/b05_score_sampling/policies.py': 'b6a018614df3ee4e32d41d6fd5550850deb8bfe0ec02cf53b6b5efd1291bb986', 'experiments/candidates/uav_fleet_transmission/b06_cadence/__init__.py': '9b03455561d8d223ca0f09c59800baaafc33d98ebd6a243532288dc17423bc03', 'experiments/candidates/uav_fleet_transmission/b06_cadence/gate.py': '22fbc4d955c17afb95341fcca9aef8bce334f0f78d1a947c0c2ab3abb46d181c', 'experiments/candidates/uav_local_history/b01/__init__.py': '2e9325183add31dc3fdaf705b71ecf2b79a6c99cd0ad285e809b365edade511c', 'experiments/candidates/uav_local_history/b01/controller.py': 'b5fdfbfe2718ee693c9ed1d7aeb8bbb6c5c59964ec6c56c5bb35be8b685f23d2', 'experiments/candidates/uav_local_history/b01/study.py': '5fb3a1538a29bc5dd613a49fdd469d351876e8b070794171956a290651cdb8ec', 'experiments/candidates/ucope/uav_motion_prefix_b01/__init__.py': '9ac022e8f48f07e80a45cb3ff30d499dcf9285b5d97ccbdf6601ee08b40eb84d', 'experiments/candidates/ucope/uav_motion_prefix_b01/environment.py': 'fb25e48857cc8531ac9b80f13243ccd6ca88fa5bf2b194a43dffed21c80690e6'}
