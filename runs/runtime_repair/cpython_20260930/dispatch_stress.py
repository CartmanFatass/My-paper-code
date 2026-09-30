"""Bounded engineering probe; no HMASD environment, policy, or result episode."""
import argparse
import faulthandler
import hashlib
import json
import os
from pathlib import Path
import resource
import sys
import time
import traceback

faulthandler.enable()
parser = argparse.ArgumentParser()
parser.add_argument('--mode', choices=('python', 'numpy'), required=True)
parser.add_argument('--seconds', type=float, default=180)
parser.add_argument('--out', required=True)
args = parser.parse_args()
output = Path(args.out)
assert not output.exists(), output
start = time.monotonic()
cpu_start = time.process_time()
record = {
    'scope': 'engineering dispatch stress; zero environments, transitions or fits',
    'mode': args.mode, 'python': sys.version, 'executable': os.path.realpath(sys.executable),
    'executable_sha256': hashlib.sha256(Path(sys.executable).resolve().read_bytes()).hexdigest(),
    'pid': os.getpid(), 'seconds_limit': args.seconds,
    'allocator': os.environ.get('PYTHONMALLOC'), 'dev_mode': sys.flags.dev_mode,
}
iterations = 0
calls = 0
next_report = 30

def python_dispatch(a, axis=None, out=None, keepdims=False, where=True):
    return a, where, out

def emit(status):
    record.update(status=status, iterations=iterations, checked_calls=calls,
                  wall_seconds=time.monotonic()-start,
                  cpu_seconds=time.process_time()-cpu_start,
                  peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    output.write_text(json.dumps(record, indent=2)+'\n')

try:
    if args.mode == 'numpy':
        import numpy as np
        from numpy.core import fromnumeric
        record['numpy'] = np.__version__
        code = fromnumeric._all_dispatcher.__code__.co_code
        mask = np.array([True, False, True, True, False], dtype=np.bool_)
        connections = np.arange(250).reshape(5, 50) % 7 == 0
        expected = [any(bool(connections[i, u]) for i in range(5)) for u in range(50)]
        while iterations < 1000 or time.monotonic()-start < args.seconds:
            for _ in range(1000):
                u = iterations % 50
                assert not bool(np.all(mask))
                assert bool(np.any(connections[:, u])) == expected[u]
                value = (iterations % 101-50)/17.
                assert float(np.clip(value, -.7, .8)) == min(.8, max(-.7, value))
                result = np.clip(np.array([value, -value]), -.7, .8)
                assert result.tolist() == [min(.8, max(-.7, x)) for x in (value, -value)]
                dispatched = fromnumeric._all_dispatcher(mask, where=True)
                assert dispatched[0] is mask and dispatched[1] is True and dispatched[2] is None
                iterations += 1
                calls += 5
            assert fromnumeric._all_dispatcher.__code__.co_code == code
            payload = {'iteration': iterations, 'mask': mask.tolist(), 'means': result.tolist()}
            assert json.loads(json.dumps(payload)) == payload
            if time.monotonic()-start >= next_report:
                emit('RUNNING')
                print(json.dumps(record), flush=True)
                next_report += 30
    else:
        original_code = python_dispatch.__code__.co_code
        while iterations < 10000 or time.monotonic()-start < args.seconds:
            for _ in range(10000):
                a = (iterations, True, None)
                assert python_dispatch(a) == (a, True, None)
                data = {'a': [iterations, str(iterations), None], 'b': {'x': iterations % 7}}
                assert json.loads(json.dumps(data)) == data
                assert tuple([a, data]) == (a, data)
                assert all([True, True]) and any([False, True])
                iterations += 1
                calls += 5
            assert python_dispatch.__code__.co_code == original_code
            if time.monotonic()-start >= next_report:
                emit('RUNNING')
                print(json.dumps(record), flush=True)
                next_report += 30
    emit('PASS')
except BaseException:
    record['exception'] = traceback.format_exc()
    emit('FAIL')
    raise
finally:
    print(json.dumps(record), flush=True)
