import importlib
import os.path

def load(name):
    """
    加载场景模块
    
    Args:
        name: 场景文件名，如 "multi_role_uav.py"
    
    Returns:
        module: 加载的场景模块
    """
    pathname = os.path.join(os.path.dirname(__file__), name)
    if not os.path.exists(pathname):
        raise Exception("场景文件 {} 不存在".format(pathname))
    return importlib.import_module('mat.envs.uav_communication.scenarios.' + name[:-3])
