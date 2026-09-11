"""Synthetic bounded repairs, inspired by inspected current HMASD boundaries.

These are NOT recovered historical bugs. Private fixes/checks stay on the host.
"""
from textwrap import dedent

TASKS, SOURCES, REFERENCES, HIDDEN, WRONG = {}, {}, {}, {}, {}
SOURCE_REVISION = "1385b56b6a0761d4064dcafbce0c66c590ecc5a2"


def add(task, kind, family, title, difficulty, reason, brief, provenance,
        modules, fixes, public, hidden, wrong):
    package = "cm_" + task
    owned = [f"{package}/{name}.py" for name in modules if name != "api"]
    facts = dedent(brief).strip()
    facts += ("\n\nInterface: `" + package + ".api` is the caller. Repair only "
              + ", ".join(f"`{p}`" for p in owned) + ". Preserve public signatures. "
              "All inputs described here are supported; no other input validation is required. "
              "Use only Python stdlib, NumPy 1.26.3 and torch 2.7.0+cpu. "
              "This is a bounded coding repair: no training runs, dependencies or external services. "
              "Public checks are examples; acceptance covers the stated behavior on additional inputs.")
    TASKS[task] = dict(kind=kind, family=family, title=title, brief=facts,
                       difficulty=difficulty, difficulty_reason=reason,
                       owned_paths=owned, public_command=["-B", "-m", package + ".public"],
                       provenance=provenance + " Inspected source revision: " + SOURCE_REVISION + ".",
                       source_revision=SOURCE_REVISION)
    src = {f"{package}/{name}.py": dedent(code).lstrip() for name, code in modules.items()}
    src[f"{package}/__init__.py"] = ""
    src[f"{package}/public.py"] = "from . import api\n" + dedent(public).lstrip()
    src[f"{package}/TASK.md"] = f"# {title}\n\n{facts}\n"
    SOURCES[task] = src
    REFERENCES[task] = {f"{package}/{name}.py": dedent(code).lstrip() for name, code in fixes.items()}
    HIDDEN[task] = dedent(hidden).lstrip()
    WRONG[task] = {f"{package}/{name}.py": dedent(code).lstrip() for name, code in wrong.items()}


LOSS_PROVENANCE = ("Synthetic reconstitution of an actor-credit reduction boundary; inspired by "
                   "experiments/candidates/ucope/uav_motion_prefix_b01/learner.py:clipped_policy_loss "
                   "and experiments/candidates/ucope/paired_training.py:_update actor advantage construction. "
                   "PPO ratios/clipping, environment and optimizer are removed; the benchmark states its "
                   "own scalar objective and injects reduction/gradient bugs. Neither the original algorithm "
                   "nor a historical prebug snapshot is reproduced.")
TIME_PROVENANCE = ("Synthetic transition adapter; inspired by the observation/terminal collection boundary in "
                   "experiments/candidates/vap_folr_core/public_lifecycle_b01/collection.py:collect. "
                   "The timeout semantics are invented for this benchmark, not attributed to that source.")
RNG_PROVENANCE = ("Synthetic evaluation fixture; inspired by paired-support evaluation in "
                  "experiments/candidates/ucope/crossed_evaluation.py:crossed_support. Seed law and bug are benchmark inventions.")

add("masked_credit", "classic", "01_loss_credit", "Masked actor credit", "medium",
    "Two boundaries: reduction units and actor-to-critic gradient isolation.",
    """
    Repair `api.loss(logp, values, returns, active)`. All four tensors have identical nonempty
    [time, agent] shape, CPU float64 except boolean active, and finite entries. The actor objective
    is the negative sum of active log-probabilities times (returns - values) within each time row,
    then the mean over ALL time rows, including rows with no active agents. Equivalently, divide
    the total active credit by the time dimension T, not the active count or T*agents.
    Inactive entries contribute zero. An all-inactive batch has scalar zero
    loss and zero logp gradient. The actor loss must not create gradients on values or returns.
    Preserve float64 and autograd on logp, including the all-inactive case.
    """, LOSS_PROVENANCE,
    dict(api="""
        from .adapter import actor_loss
        def loss(logp, values, returns, active):
            return actor_loss(logp, values, returns, active)
        """, adapter="""
        from .reduction import reduce_credit
        def actor_loss(logp, values, returns, active):
            advantage = returns - values
            return reduce_credit(logp, advantage, active)
        """, reduction="""
        def reduce_credit(logp, advantage, active):
            return -(logp * advantage * active).mean()
        """),
    dict(adapter="""
        from .reduction import reduce_credit
        def actor_loss(logp, values, returns, active):
            advantage = (returns - values).detach()
            return reduce_credit(logp, advantage, active)
        """, reduction="""
        def reduce_credit(logp, advantage, active):
            return -(logp * advantage * active).sum(dim=-1).mean()
        """),
    """
    import torch
    x = torch.tensor([[1., 3., 2.], [5., 7., 9.]], dtype=torch.float64, requires_grad=True)
    v = torch.zeros_like(x, requires_grad=True)
    y = api.loss(x, v, torch.ones_like(x), torch.tensor([[True, True, True], [False, False, False]]))
    assert y.item() == -3.
    y.backward()
    assert v.grad is None
    print('public checks passed')
    """,
    """
    import torch
    for mask in ([[1,0,1],[0,1,0]], [[1,0,1],[0,0,0]], [[0,0,0],[0,0,0]], [[1,1,1],[1,1,1]]):
        x = torch.tensor([[.5,-2.,3.],[4.,1.,-1.]], dtype=torch.float64, requires_grad=True)
        v = torch.tensor([[1.,2.,3.],[4.,5.,6.]], dtype=torch.float64, requires_grad=True)
        r = torch.tensor([[4.,1.,7.],[2.,8.,9.]], dtype=torch.float64, requires_grad=True)
        m = torch.tensor(mask, dtype=torch.bool)
        y = api.loss(x,v,r,m)
        denominator = len(mask)
        expected = -sum(float(x[i,j]) * float(r[i,j]-v[i,j]) for i in range(2) for j in range(3) if mask[i][j]) / denominator
        assert y.dtype == torch.float64 and abs(y.item()-expected) < 1e-12
        y.backward()
        assert torch.equal(x.grad, -(r.detach()-v.detach()) * m / denominator)
        assert v.grad is None and r.grad is None
    """,
    dict(reduction="""
        def reduce_credit(logp, advantage, active):
            return -(logp * advantage * active).sum() / active.sum().clamp_min(1)
        """))

add("timeout_bootstrap", "classic", "02_time_state", "Auto-reset timeout target", "hard",
    "Final-observation selection and bootstrap masking interact with reset state and simultaneous flags.",
    """
    Repair `api.target(transition, gamma, value)`. transition has reward (float), terminated and
    truncated (bool), next_obs (scalar float), final_obs (scalar float), hidden (NumPy vector).
    next_obs is the auto-reset observation on either end flag; final_obs is the last observation
    before reset. Truncation is an external collection timeout in a continuing task, so its target
    includes the final state's value. True termination has no bootstrap, even if truncated too.
    Ordinary transitions bootstrap from next_obs. gamma is in [0,1]. Return (scalar TD target,
    next_hidden): hidden is zeroed on either flag, otherwise an equal independent copy. Do not
    mutate transition or call value on terminated transitions. value accepts a scalar and returns
    a scalar. Target and recurrent reset have deliberately different end conditions.
    """, TIME_PROVENANCE,
    dict(api="""
        from .adapter import prepare
        from .target import finish
        def target(transition, gamma, value):
            return finish(prepare(transition), gamma, value)
        """, adapter="""
        import numpy as np
        def prepare(t):
            done = t['terminated'] or t['truncated']
            return t['reward'], done, t['next_obs'], np.zeros_like(t['hidden']) if done else t['hidden']
        """, target="""
        def finish(row, gamma, value):
            reward, done, obs, hidden = row
            return reward + gamma * value(obs), hidden
        """),
    dict(adapter="""
        import numpy as np
        def prepare(t):
            ended = t['terminated'] or t['truncated']
            obs = t['final_obs'] if ended else t['next_obs']
            hidden = np.zeros_like(t['hidden']) if ended else t['hidden'].copy()
            return t['reward'], t['terminated'], obs, hidden
        """, target="""
        def finish(row, gamma, value):
            reward, terminated, obs, hidden = row
            return reward if terminated else reward + gamma * value(obs), hidden
        """),
    """
    import numpy as np
    t = dict(reward=2., terminated=False, truncated=True, next_obs=100., final_obs=4., hidden=np.array([3.]))
    y,h = api.target(t, .5, lambda x: x*2)
    assert y == 6. and h.tolist() == [0.]
    print('public checks passed')
    """,
    """
    import numpy as np
    for terminated,truncated in [(False,False),(False,True),(True,False),(True,True)]:
        t = dict(reward=-3.,terminated=terminated,truncated=truncated,next_obs=19.,final_obs=-5.,hidden=np.array([2.,7.]))
        calls=[]
        def value(x):
            calls.append(x)
            return x*3
        y,h = api.target(t,.8,value)
        expected = -3. if terminated else -3.+.8*3*(-5. if truncated else 19.)
        assert abs(y-expected)<1e-12
        assert calls == ([] if terminated else [-5. if truncated else 19.])
        assert np.array_equal(h, [0.,0.] if terminated or truncated else [2.,7.])
        h[0]=99.
        assert t['hidden'].tolist()==[2.,7.]
    """,
    dict(adapter="""
        import numpy as np
        def prepare(t):
            ended = t['terminated'] or t['truncated']
            obs = t['final_obs'] if ended else t['next_obs']
            hidden = np.zeros_like(t['hidden']) if ended else t['hidden'].copy()
            return t['reward'], ended, obs, hidden
        """))

add("evaluation_stream", "classic", "03_rng_evaluation", "Private evaluation stream", "medium",
    "Seed forwarding crosses sampler/evaluator while global RNG and model mode remain unchanged.",
    """
    Repair `api.evaluate(model, seed, n)`. model is a CPU torch module producing two logits from
    a float32 observation tensor of shape [n,1], with n a positive integer. Evaluate under eval
    mode and without autograd. Every observation is 1. Sample exactly n actions using one
    torch.multinomial call on the row-wise softmax, using a private CPU torch.Generator initialized
    to the supplied nonnegative seed. Return a detached int64 tensor [n]. Calls repeat exactly
    for the same seed/model. Do not advance or reseed global torch RNG. Restore the model's original
    train/eval flag, including when forward raises. Supported models have uniformly inherited mode
    (no mixed child modes); model forward in eval mode does not itself draw randomness.
    """, RNG_PROVENANCE,
    dict(api="""
        from .evaluator import evaluate
        """, evaluator="""
        import torch
        from .sampler import actions
        def evaluate(model, seed, n):
            model.eval()
            with torch.no_grad():
                logits = model(torch.ones((n,1), dtype=torch.float32))
                return actions(logits, seed)
        """, sampler="""
        import torch
        def actions(logits, seed):
            torch.manual_seed(seed)
            return torch.multinomial(logits.softmax(-1), 1).squeeze(-1)
        """),
    dict(evaluator="""
        import torch
        from .sampler import actions
        def evaluate(model, seed, n):
            training = model.training
            try:
                model.eval()
                with torch.no_grad():
                    logits = model(torch.ones((n,1), dtype=torch.float32))
                    return actions(logits, seed)
            finally:
                model.train(training)
        """, sampler="""
        import torch
        def actions(logits, seed):
            rng = torch.Generator(device='cpu').manual_seed(seed)
            return torch.multinomial(logits.softmax(-1), 1, generator=rng).squeeze(-1)
        """),
    """
    import torch
    model = torch.nn.Linear(1,2)
    before = torch.get_rng_state().clone()
    a = api.evaluate(model, 31, 5)
    assert torch.equal(before, torch.get_rng_state()) and model.training
    assert torch.equal(a, api.evaluate(model,31,5))
    print('public checks passed')
    """,
    """
    import torch
    class Model(torch.nn.Module):
        def forward(self,x):
            assert not self.training and not torch.is_grad_enabled()
            return torch.cat([x*.3, -x*.2], -1)
    for training in (True,False):
        m=Model().train(training)
        for seed,n in [(2,1),(119,37),(5,64)]:
            state=torch.get_rng_state().clone()
            y=api.evaluate(m,seed,n)
            p=torch.tensor([[.3,-.2]]).expand(n,2).softmax(-1)
            expected=torch.multinomial(p,1,generator=torch.Generator().manual_seed(seed)).squeeze(-1)
            assert torch.equal(y,expected) and y.dtype==torch.int64 and not y.requires_grad
            assert m.training==training and torch.equal(state,torch.get_rng_state())
    class Broken(Model):
        def forward(self,x):
            raise ValueError('forward failed')
    m=Broken().train()
    try:
        api.evaluate(m,11,3)
        raise AssertionError('exception swallowed')
    except ValueError:
        pass
    assert m.training
    """,
    dict(evaluator="""
        import torch
        from .sampler import actions
        def evaluate(model, seed, n):
            training = model.training
            model.eval()
            with torch.no_grad():
                logits = model(torch.ones((n,1), dtype=torch.float32))
                result = actions(logits, seed)
            model.train(training)
            return result
        """))

add("publish_count", "classic", "04_runner_publication", "Episode count reaches publication", "easy",
    "Straight configuration forwarding and one summary count, with a short deterministic producer.",
    """
    Repair `api.run(argv, output)` where argv includes `--episodes N`, N >= 1, and output is a
    pathlib.Path to an existing empty directory. The deterministic producer yields score 2*i+1
    for episode index i starting at zero. Produce exactly the requested episodes; write
    summary.json with keys requested, completed, mean. requested is N, completed is the actual
    number of produced scores, mean is their arithmetic mean. Return the same dictionary as
    the JSON file. `--episodes` defaults to 2. No other files are required.

    Also preserve the existing helper `publication.publish(requested, scores, output)` as a
    supported entry point. requested is a positive integer; scores is a nonempty supplied list
    of finite numeric scores whose length MAY DIFFER from requested (partial producer output).
    output is a pathlib.Path to an existing empty directory. The helper writes summary.json
    and returns that same dictionary: requested is unchanged, completed is len(scores), and
    mean is the arithmetic mean of the supplied scores. No other helper inputs are required.
    """, "Synthetic wiring bug inspired by producer/publication separation in experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_metrics_artifact.py:publish_metrics_only_complete; producers, tables and validations are replaced by a deterministic score list and three-field JSON; no historical failure is reproduced.",
    dict(api="""
        import argparse
        from .runner import execute
        def run(argv, output):
            parser=argparse.ArgumentParser()
            parser.add_argument('--episodes', type=int, default=2)
            return execute(parser.parse_args(argv).episodes, output)
        """, runner="""
        from .publication import publish
        def execute(episodes, output):
            scores=[2*i+1 for i in range(2)]
            return publish(episodes, scores, output)
        """, publication="""
        import json
        def publish(requested, scores, output):
            result=dict(requested=requested, completed=requested, mean=sum(scores)/len(scores))
            (output/'summary.json').write_text(json.dumps(result), encoding='utf-8')
            return result
        """),
    dict(runner="""
        from .publication import publish
        def execute(episodes, output):
            scores=[2*i+1 for i in range(episodes)]
            return publish(episodes, scores, output)
        """, publication="""
        import json
        def publish(requested, scores, output):
            result=dict(requested=requested, completed=len(scores), mean=sum(scores)/len(scores))
            (output/'summary.json').write_text(json.dumps(result), encoding='utf-8')
            return result
        """),
    """
    import tempfile
    from pathlib import Path
    Path('temp').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir='temp') as d:
        assert api.run(['--episodes','3'],Path(d)) == dict(requested=3,completed=3,mean=3.)
    print('public checks passed')
    """,
    """
    import json, tempfile
    from pathlib import Path
    from importlib import import_module
    pub=import_module(api.__package__+'.publication')
    Path('temp').mkdir(exist_ok=True)
    for argv,n in [([],2),(['--episodes','1'],1),(['--episodes','7'],7)]:
        with tempfile.TemporaryDirectory(dir='temp') as d:
            p=Path(d)
            r=api.run(argv,p)
            assert r == dict(requested=n,completed=n,mean=float(n))
            assert json.loads((p/'summary.json').read_text())==r
    with tempfile.TemporaryDirectory(dir='temp') as d:
        assert pub.publish(5,[2.,8.],Path(d))==dict(requested=5,completed=2,mean=5.)
    """,
    dict(publication="""
        import json
        def publish(requested, scores, output):
            result=dict(requested=requested, completed=requested, mean=sum(scores)/len(scores))
            (output/'summary.json').write_text(json.dumps(result), encoding='utf-8')
            return result
        """))

add("replay_snapshot", "classic", "05_integration_performance", "Replay owns batched observations", "medium",
    "Mutable environment buffer lifetime meets indexed batching and duplicate/order semantics.",
    """
    Repair `api.collect_and_batch(env, steps, indices)`. Each env.step() returns the SAME writable
    NumPy float32 array [agents,features], mutated at each step. steps >= 1; indices is a nonempty
    list of valid integer step indices, possibly repeated or out of order. Capture one observation
    per step, then return a CPU float32 torch tensor [len(indices),agents,features] in exactly the
    requested index order. Earlier observations and returned tensors must not change when the
    environment buffer or replay input changes later. `replay.capture(rows, obs)` appends an owned
    snapshot; `batching.batch(rows, indices)` returns independent batched storage. Preserve array
    values, including non-contiguous input layouts; do not change env.step call count or draw RNG.
    """, "Synthetic ownership/batching bug inspired by collect/sample in experiments/candidates/vap_folr_core/public_lifecycle_b01/collection.py. That source is not claimed to contain this bug.",
    dict(api="""
        from .replay import capture
        from .batching import batch
        def collect_and_batch(env, steps, indices):
            rows=[]
            for _ in range(steps):
                capture(rows, env.step())
            return batch(rows, indices)
        """, replay="""
        def capture(rows, obs):
            rows.append(obs)
        """, batching="""
        import numpy as np
        import torch
        def batch(rows, indices):
            return torch.from_numpy(np.stack([rows[i] for i in sorted(set(indices))]))
        """),
    dict(replay="""
        def capture(rows, obs):
            rows.append(obs.copy())
        """, batching="""
        import numpy as np
        import torch
        def batch(rows, indices):
            return torch.from_numpy(np.stack([rows[i] for i in indices]))
        """),
    """
    import numpy as np
    class Env:
        def __init__(self): self.x=np.zeros((1,2),dtype=np.float32)
        def step(self):
            self.x += 1
            return self.x
    y=api.collect_and_batch(Env(),3,[2,0,2])
    assert y[:,0,0].tolist()==[3.,1.,3.]
    print('public checks passed')
    """,
    """
    import numpy as np, torch
    from importlib import import_module
    class Env:
        def __init__(self):
            self.x=np.arange(12,dtype=np.float32).reshape(3,4)[:,::2]
            self.n=0
        def step(self):
            self.n+=1
            self.x += self.n
            return self.x
    env=Env(); base=env.x.copy()
    y=api.collect_and_batch(env,4,[3,1,1,0])
    assert env.n==4 and y.dtype==torch.float32 and y.shape==(4,3,2)
    expected=np.stack([base+10,base+3,base+3,base+1])
    assert np.array_equal(y.numpy(),expected)
    env.x.fill(-10)
    assert np.array_equal(y.numpy(),expected)
    replay=import_module(api.__package__+'.replay')
    batching=import_module(api.__package__+'.batching')
    rows=[]; x=np.ones((2,2),dtype=np.float32)
    replay.capture(rows,x); x.fill(9)
    assert np.array_equal(rows[0],np.ones((2,2)))
    z=batching.batch(rows,[0,0]); rows[0].fill(5)
    assert torch.equal(z,torch.ones((2,2,2)))
    """,
    dict(batching="""
        import numpy as np
        import torch
        def batch(rows, indices):
            return torch.from_numpy(np.stack([rows[i] for i in sorted(set(indices))]))
        """))

add("fixed_slot_credit", "non_example", "01_loss_credit", "Fixed-slot exposure objective", "easy",
    "A single reduction correction; the mask is exposure weighting, not a sample-selection denominator.",
    """
    Repair `api.loss(logp, advantage, exposure)`. All inputs are same-shaped nonempty CPU float64
    tensors [time,slot] with finite entries; exposure is in [0,1]. This objective measures credit
    PER ALLOCATED SLOT, including absent slots. Required loss is the negative sum of logp times
    advantage times exposure divided by the total number of allocated entries. Fractional exposure
    is meaningful. There is no renormalization by observed exposure. advantage is externally
    supplied fixed data (requires_grad=False). Preserve logp autograd and zero gradient where
    exposure is zero, including all-zero exposure.
    """, LOSS_PROVENANCE + " The fixed-slot denominator is a distinct invented objective.",
    dict(api="""
        from .adapter import objective
        def loss(logp, advantage, exposure):
            return objective(logp, advantage, exposure)
        """, adapter="""
        from .reduction import average
        def objective(logp, advantage, exposure):
            return -average(logp * advantage * exposure, exposure)
        """, reduction="""
        def average(credit, exposure):
            return credit.sum() / exposure.sum().clamp_min(1)
        """),
    dict(reduction="""
        def average(credit, exposure):
            return credit.mean()
        """),
    """
    import torch
    x=torch.tensor([[2.,8.]],dtype=torch.float64,requires_grad=True)
    y=api.loss(x,torch.ones_like(x),torch.tensor([[1.,0.]],dtype=torch.float64))
    assert y.item()==-1.
    print('public checks passed')
    """,
    """
    import torch
    for e in ([[.2,0.,.7],[1.,.1,0.]], [[0.,0.,0.],[0.,0.,0.]]):
        x=torch.tensor([[1.,2.,3.],[4.,5.,6.]],dtype=torch.float64,requires_grad=True)
        a=torch.tensor([[2.,-3.,4.],[1.,2.,3.]],dtype=torch.float64)
        exposure=torch.tensor(e,dtype=torch.float64)
        y=api.loss(x,a,exposure)
        expected=-sum(float(x[i,j])*float(a[i,j])*e[i][j] for i in range(2) for j in range(3))/6
        assert abs(y.item()-expected)<1e-12 and y.dtype==torch.float64
        y.backward()
        assert torch.allclose(x.grad,-a*exposure/6,atol=1e-15,rtol=0)
    """,
    dict(reduction="""
        def average(credit, exposure):
            return credit.sum() / (exposure > 0).sum().clamp_min(1)
        """))

add("finite_horizon", "non_example", "02_time_state", "Task horizon ends value", "medium",
    "Time-limit flag has task-terminal meaning, while ordinary continuation still requires a value call.",
    """
    Repair `api.target(t, gamma, value)` for a FINITE-HORIZON task. The wrapper uses the field
    truncated to report exhaustion of the task's remaining time; it is a true objective endpoint,
    not an external collection cut. terminated also ends the objective. On either flag, return
    reward without calling value and reset hidden. Otherwise return reward + gamma*value(next_obs)
    and an equal independent copy of hidden. t has reward float, terminated/truncated bool,
    next_obs/final_obs scalar floats, and NumPy hidden vector. final_obs exists for logging only
    at ended transitions. gamma is in [0,1]. Never mutate t. Return (target,next_hidden).
    """, TIME_PROVENANCE + " Finite-horizon interpretation intentionally differs from the classic task.",
    dict(api="""
        from .adapter import row
        from .target import compute
        def target(t, gamma, value):
            return compute(row(t),gamma,value)
        """, adapter="""
        import numpy as np
        def row(t):
            ended=t['terminated'] or t['truncated']
            obs=t['final_obs'] if ended else t['next_obs']
            h=np.zeros_like(t['hidden']) if ended else t['hidden']
            return t['reward'], t['terminated'], obs, h
        """, target="""
        def compute(row,gamma,value):
            r,terminal,obs,h=row
            return r if terminal else r+gamma*value(obs), h
        """),
    dict(adapter="""
        import numpy as np
        def row(t):
            ended=t['terminated'] or t['truncated']
            h=np.zeros_like(t['hidden']) if ended else t['hidden'].copy()
            return t['reward'], ended, t['next_obs'], h
        """),
    """
    import numpy as np
    t=dict(reward=1.,terminated=False,truncated=True,next_obs=20.,final_obs=7.,hidden=np.ones(2))
    y,h=api.target(t,.9,lambda x: x)
    assert y==1. and h.tolist()==[0.,0.]
    print('public checks passed')
    """,
    """
    import numpy as np
    for term,trunc in [(False,False),(False,True),(True,False),(True,True)]:
        t=dict(reward=3.,terminated=term,truncated=trunc,next_obs=4.,final_obs=11.,hidden=np.array([1.,5.]))
        calls=[]
        def value(x):
            calls.append(x)
            return -x
        y,h=api.target(t,.25,value)
        assert y==(3. if term or trunc else 2.)
        assert calls==([] if term or trunc else [4.])
        assert h.tolist()==([0.,0.] if term or trunc else [1.,5.])
        h[1]=9.
        assert t['hidden'].tolist()==[1.,5.]
    """,
    dict(adapter="""
        import numpy as np
        def row(t):
            ended=t['terminated'] or t['truncated']
            h=np.zeros_like(t['hidden']) if ended else t['hidden'].copy()
            return t['reward'], t['terminated'], t['final_obs'] if ended else t['next_obs'], h
        """))

add("paired_tape", "non_example", "03_rng_evaluation", "Common exogenous evaluation tape", "hard",
    "One shared exogenous tape must survive arm reordering, mutation, and unequal private policy draws.",
    """
    Repair `api.compare(policies, seed, n)`. policies is an insertion-ordered dict of named
    callables; n >= 1. Every callable receives (weather, rng) and returns a float. weather must
    contain the SAME n NumPy float64 standard-normal draws for every arm, from a fresh
    np.random.default_rng(seed). Each arm separately receives its own private action generator
    initialized to seed+1. Weather and action streams are distinct. An arm may modify its weather
    array and consume any number of action draws. Neither action consumption, array modification,
    nor dictionary order may affect another arm's inputs or outputs. Preserve input key order in
    the result dict. Do not mutate global NumPy RNG state. Return each callable's score unchanged.
    Common weather is an intentional paired-comparison design, not accidental RNG sharing.
    """, RNG_PROVENANCE + " Common weather and independent action streams are a synthetic contrast fixture.",
    dict(api="""
        from .evaluator import compare
        """, evaluator="""
        from .streams import weather, actions
        def compare(policies, seed, n):
            tape=weather(seed,n)
            rng=actions(seed)
            return {name: policy(tape,rng) for name,policy in policies.items()}
        """, streams="""
        import numpy as np
        def weather(seed,n):
            return np.random.default_rng(seed+1).standard_normal(n)
        def actions(seed):
            return np.random.default_rng(seed+1)
        """),
    dict(evaluator="""
        from .streams import weather, actions
        def compare(policies, seed, n):
            tape=weather(seed,n)
            return {name: policy(tape.copy(),actions(seed)) for name,policy in policies.items()}
        """, streams="""
        import numpy as np
        def weather(seed,n):
            return np.random.default_rng(seed).standard_normal(n)
        def actions(seed):
            return np.random.default_rng(seed+1)
        """),
    """
    import numpy as np
    def score(w,r): return float(w.sum()+r.random())
    y=api.compare({'a':score,'b':score},17,4)
    expected=float(np.random.default_rng(17).standard_normal(4).sum()+np.random.default_rng(18).random())
    assert y=={'a':expected,'b':expected}
    print('public checks passed')
    """,
    """
    import numpy as np
    for seed,n in [(0,1),(4,13),(99,8)]:
        seen={}
        def first(w,r):
            seen['first']=w.copy()
            v=float(w.sum()+r.random(19)[-1])
            w.fill(999.)
            return v
        def second(w,r):
            seen['second']=w.copy()
            return float(w.sum()+r.random())
        state=np.random.get_state()
        a=api.compare({'first':first,'second':second},seed,n)
        b=api.compare({'second':second,'first':first},seed,n)
        tape=np.random.default_rng(seed).standard_normal(n)
        assert list(a)==['first','second'] and list(b)==['second','first'] and a==b
        assert np.array_equal(seen['first'],tape) and np.array_equal(seen['second'],tape)
        assert a['first']==float(tape.sum()+np.random.default_rng(seed+1).random(19)[-1])
        assert a['second']==float(tape.sum()+np.random.default_rng(seed+1).random())
        after=np.random.get_state()
        assert state[0]==after[0] and np.array_equal(state[1],after[1]) and state[2:]==after[2:]
    """,
    dict(evaluator="""
        from .streams import weather, actions
        def compare(policies, seed, n):
            return {name: policy(weather(seed+i,n),actions(seed+i)) for i,(name,policy) in enumerate(policies.items())}
        """))
