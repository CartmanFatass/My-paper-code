"""Selected finite exposure and immutable external evidence addresses."""
from experiments.candidates.uav_decision_generalization.b03_joint_window import contract as b03

DIRECTION = b03.DIRECTION
OBJECT = 'UAV-SET-MEAN-B04'
MASTER = b03.MASTER
PROGRAMMES = ('SET-initial-mean', 'SET-final-mean')
ENDPOINTS = dict(zip(PROGRAMMES, ('initial', 'final')))
WORLDS = b03.WORLDS
AUDIT_WORLD = b03.AUDIT_WORLD
MODE = 'deterministic_mean'
ANCESTOR = {
    'schema': 1, 'root': '/home/wu/projects/HMASD/runs/uav_decision_generalization/b03_joint_window_a01',
    'config_sha256': '0bc410effb3e254ea38f5f23186e5ed975a5492251f333ad059c56932e228e88',
    'summary_sha256': '2fe984bf5c203b2b450237c1304a0b074f24c604e7adfe7153f02f1a9a263ae9',
    'manifest_sha256': '6d572b218c091ccd5ca2b8e305c0b1dc074f45efdd24c51029d4edbaa5ac1c95'}
READING = {
    'path': '/home/wu/projects/HMASD/runs/uav_decision_generalization/b03_joint_window_read_a02/reading.json',
    'sha256': 'eab3cdeff541f4849f6086e5752d0ea9ad59b6e29ab7765a9b047bce5d356c69'}
CHECKPOINTS = {
    'initial': {'path': 'checkpoints/SET/initial.pt', 'bytes': 21418427,
                'sha256': 'ba2eb18a78abfbe4383d105292a53d81d777d71d6549dfa279c9ab30ff765586'},
    'final': {'path': 'checkpoints/SET/final.pt', 'bytes': 21418155,
              'sha256': '9be9c88f867b2dc6a8749bda099429a471731ee041fd01b878486139a407f463'}}
BASELINES = ('SET-initial', 'SET-final', 'O', 'B')
EXCEPTIONS = {'experiments/candidates/uav_decision_generalization/b03_joint_window/' + name
              for name in ('worker.py', 'independent.py')}
WORKER_COUNTS = {'native_step_attempts': 33000, 'native_steps': 33000,
                 'frozen_native_steps': 33000, 'frozen_model_steps': 33000, 'model_constructions': 2}
READER_COUNTS = {'reader_ledger_updates': 33000, 'reader_user_indicator_reads': 1650000,
                 'reader_movement_uav_ticks': 198000, 'reader_physical_states': 33066,
                 'reader_distance_relations': 10614186, 'reader_model_team_steps': 33000,
                 'reader_actor_agent_rows': 198000, 'reader_critic_agent_rows': 198000, 'model_constructions': 2}


def roster(programmes=PROGRAMMES):
    return [(p, w, 'main') for p in programmes for w in WORLDS] + [(p, AUDIT_WORLD, 'audit') for p in programmes]


def frozen_contract():
    return {'schema': 1, 'object': OBJECT, 'master': MASTER, 'inference_mode': MODE,
            'programmes': list(PROGRAMMES), 'worlds': list(WORLDS), 'audit_world': AUDIT_WORLD,
            'horizon': 500, 'missions': 66, 'native_steps': 33000, 'fits': 0, 'optimizer_steps': 0,
            'checkpoint_map': CHECKPOINTS, 'worker_counts': WORKER_COUNTS, 'reader_counts': READER_COUNTS,
            'cpu_watchdog_seconds': 7200, 'operation_wall_watchdog_seconds': 7200,
            'development_exposed': True, 'baseline_sampled_W_gain': .0625,
            'action': 'original Gaussian mean; inherited copied-vector projection and native motion',
            'inference_seed': 'world+51 after construction and reset'}
