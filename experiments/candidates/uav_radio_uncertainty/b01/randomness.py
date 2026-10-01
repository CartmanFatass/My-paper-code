"""Independent, addressed Philox blocks; neither helper owns persistent RNG state."""

import numpy as np

from . import contract as c


def _identifier(value, name):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) or value < 0:
        raise ValueError(name + ' must be a nonnegative integer')
    return int(value)


def _addressed(namespace, root, world, tick, shape):
    world, tick = _identifier(world, 'world'), _identifier(tick, 'tick')
    if np.__version__ != c.NUMPY_VERSION:
        raise RuntimeError('addressed normals require NumPy ' + c.NUMPY_VERSION)
    generator = np.random.Generator(np.random.Philox(np.random.SeedSequence([namespace, root, world, tick])))
    return generator.standard_normal(size=shape, dtype=np.float64)


def physical_normals(world, tick):
    return _addressed(c.PHYSICAL_NAMESPACE, c.PHYSICAL_ROOT, world, tick, (c.N_UAVS, c.N_USERS))


def model_normals(world, report_tick):
    tick = _identifier(report_tick, 'report_tick')
    if tick % c.HOLD:
        raise ValueError('model report tick must be a multiple of4')
    return _addressed(c.MODEL_NAMESPACE, c.MODEL_ROOT, world, tick,
                      (c.BASE_PARTICLES, c.MODEL_STEPS, c.N_UAVS, c.N_USERS))
