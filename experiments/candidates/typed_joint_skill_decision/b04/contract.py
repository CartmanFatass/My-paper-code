"""Fixed, effect-free B04 addresses, interfaces and numerical topology."""
from __future__ import annotations
import os
import sys
import uuid as uuid_module

KINDS = ('kmeans_plain', 'subset_relay', 'subset_flat')
TRAIN_START, TRAIN_COUNT, FRESH_START, FRESH_COUNT = 109400000, 16000, 109420000, 512
FITS = (
 {'id':'R1000s0','n':1000,'stream':0,'model_seed':109491001,'order_seed':109492001,'subset_seed':109493001},
 {'id':'R4000s1','n':4000,'stream':1,'model_seed':109491002,'order_seed':109492002,'subset_seed':109493002},
 {'id':'R16000s0','n':16000,'stream':0,'model_seed':109491001,'order_seed':109492001,'subset_seed':109493001},
 {'id':'R1000s1','n':1000,'stream':1,'model_seed':109491002,'order_seed':109492002,'subset_seed':109493002},
 {'id':'R4000s0','n':4000,'stream':0,'model_seed':109491001,'order_seed':109492001,'subset_seed':109493001},
 {'id':'R16000s1','n':16000,'stream':1,'model_seed':109491002,'order_seed':109492002,'subset_seed':109493002})
ARMS = tuple(f['id'] for f in FITS) + ('Raw8J','RawJ','P')
SHAPES = {'U':(6,9),'Y':(50,52),'B':(3,),'M':(6,),'E_UY':(6,50,4),'E_UU':(6,5,4),'E_UB':(6,4)}
FEATURE_KEYS = {'users_xy','bs_xyz','layouts_xyz','kinds','ks'}
PARAMETERS, UPDATES, BATCH, SUBSET, CHUNK = 205441, 4096, 32, 16, 64
TOLERANCES = {'scorer':{'atol':1e-6,'rtol':1e-5},'radio':{'atol':1e-10,'rtol':1e-10},'position_atol':1e-8,'discrete':'exact'}


def gpu_uuid(value):
    """Normalize CUDA's string, UUID object or sixteen raw UUID bytes explicitly."""
    if isinstance(value,bytes):
        value = str(uuid_module.UUID(bytes=value)) if len(value)==16 else value.decode('ascii')
    value = str(value).removeprefix('GPU-')
    return 'GPU-'+str(uuid_module.UUID(value))


def threads():
    env = {k:'1' for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS')}
    os.environ.update(env)
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    sys.dont_write_bytecode = True
    return env


def configure(cuda=False, expected=None):
    import platform
    import numpy as np
    import torch
    torch.set_default_dtype(torch.float32)
    torch.set_num_threads(1)
    if not globals().get("_CONFIGURED", False):
        torch.set_num_interop_threads(1)
        globals()["_CONFIGURED"] = True
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.set_float32_matmul_precision('highest')
    values = {'python':platform.python_version(),'numpy':np.__version__,'torch':torch.__version__,
              'dtype':'float32','tf32':False,'cpu_intra_threads':1,'cpu_inter_threads':1}
    if expected is not None and (values['python'] != expected['python_version'] or values['numpy'] != expected['numpy_version']
                               or values['torch'] != expected['torch_version']):
        raise RuntimeError('declared Python/NumPy/Torch runtime identity mismatch')
    if cuda:
        if not torch.cuda.is_available():
            raise RuntimeError('fixed CUDA device unavailable; no fallback')
        torch.cuda.set_device(0)
        properties = torch.cuda.get_device_properties(0)
        uuid = gpu_uuid(properties.uuid)
        values.update(device='cuda:0',gpu_uuid=uuid,gpu_name=properties.name)
        if expected is not None and uuid != gpu_uuid(expected['gpu_uuid']):
            raise RuntimeError('physical GPU UUID mismatch')
    return values


def validate_features(f):
    import numpy as np
    if set(f) != FEATURE_KEYS:
        raise ValueError('exact outcome-free feature whitelist required')
    layouts = np.asarray(f['layouts_xyz'],dtype=np.float64)
    m = len(layouts)
    if (not 1 <= m <= 221 or layouts.shape != (m,6,3)
        or np.asarray(f['users_xy']).shape != (50,2) or np.asarray(f['bs_xyz']).shape != (3,)
        or len(f['kinds']) != m or len(f['ks']) != m):
        raise ValueError('fixed lawful feature shapes required')
    if any(k not in KINDS for k in f['kinds']) or any(type(k) is not int or k not in (4,5,6) for k in f['ks']):
        raise ValueError('fixed kind/k encoding required')
    if not all(np.isfinite(np.asarray(f[k],dtype=float)).all() for k in ('users_xy','bs_xyz','layouts_xyz')):
        raise ValueError('finite geometry required')
    if (np.any(layouts[...,:2]<0) or np.any(layouts[...,:2]>5000)
        or np.any(layouts[...,2]<50) or np.any(layouts[...,2]>150)):
        raise ValueError('illegal raw target')
    return m
