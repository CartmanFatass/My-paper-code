
import socket
from absl import flags
FLAGS = flags.FLAGS
FLAGS(['train_sc.py'])

# 注册UAV通信环境
from mat.envs.uav_communication import UAVCommEnv
