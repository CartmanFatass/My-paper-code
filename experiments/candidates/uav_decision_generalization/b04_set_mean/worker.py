"""One agent per endpoint; the inherited collector owns native traces and failures."""
import gc
from experiments.candidates.uav_decision_generalization.b03_joint_window import evidence as e, independent as i, worker as old
from . import bindings as b, contract as c


class Store(old.Store):
    def __init__(self, out, args, meter, config):
        super().__init__(out, args, meter, config)
        self.manifest = {'schema': 1, 'object': c.OBJECT, 'inference_mode': c.MODE, 'frozen': [], 'checkpoints': c.CHECKPOINTS}
        self.summary.update(object=c.OBJECT, inference_mode=c.MODE, new_native_steps=0, new_fits=0, optimizer_steps=0)

    def publish(self):
        b.check_counts(self.meter, 'worker')
        self.summary.update(new_native_steps=self.meter.counts.get('native_steps', 0),
                            actual_neural_agent_rows=b.neural_rows(self.meter), cost=self.meter.report())
        e.write_json(self.out / 'manifest.json', self.manifest)
        e.write_json(self.out / 'summary.json', self.summary)


def load_endpoint(ancestor, endpoint, out, programme, meter):
    identity = c.CHECKPOINTS[endpoint]
    checkpoint = i.checked_file(ancestor['worker_root'], identity)
    agent, _, payload = e.load_agent(checkpoint, 'SET', 1, out / 'logs' / programme, meter)
    if payload['arm'] != 'SET' or payload['endpoint'] != endpoint or payload['launch_sha'] != ancestor['worker_config']['launch_sha']:
        raise ValueError('original checkpoint arm/endpoint/launch identity')
    return agent, payload


def run(root, out, args, context):
    meter = context['meter']
    store = Store(out, args, meter, context['config'])
    store.publish()
    for programme in c.PROGRAMMES:
        endpoint = c.ENDPOINTS[programme]
        b.check_counts(meter, 'worker')
        agent, payload = load_endpoint(context['ancestor'], endpoint, out, programme, meter)
        try:
            for world, phase in [(w, 'main') for w in c.WORLDS] + [(c.AUDIT_WORLD, 'audit')]:
                b.check_counts(meter, 'worker')
                old.frozen_mission(store, programme, world, phase, agent, c.CHECKPOINTS[endpoint], deterministic=True)
                if e.digest_agent(agent) != payload['state_digest']:
                    raise AssertionError('checkpoint full state changed after mission')
                # Host counters are finalized by the inherited collector's finally.
                store.publish()
        finally:
            del agent
            gc.collect()
    b.validate_roster(store.manifest['frozen'])
    b.check_counts(meter, 'worker', terminal=True)
    b.neural_rows(meter, terminal=True)
    store.summary.update(status='COMPLETE', inflight=None)
    store.publish()
