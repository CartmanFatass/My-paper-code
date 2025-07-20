import gym
from gym import spaces
import numpy as np
from .core import World, UAV, GroundBaseStation, UserEquipment
from .utils.simplified_channel_model import SimplifiedChannelModel

class UAVCommEnv(gym.Env):
    """
    无人机通信环境类，继承自gym.Env
    实现了多个无人机作为智能体，既作为基站又作为中继，为用户提供通信服务
    """
    metadata = {
        'render.modes': ['human', 'rgb_array']
    }

    def __init__(self, world, reset_callback=None, reward_callback=None,
                 observation_callback=None, info_callback=None,
                 done_callback=None, shared_viewer=True):
        """
        初始化环境
        
        Args:
            world: World对象
            reset_callback: 重置世界的回调函数
            reward_callback: 计算奖励的回调函数
            observation_callback: 生成观测的回调函数
            info_callback: 生成info字典的回调函数
            done_callback: 判断是否结束的回调函数
            shared_viewer: 是否共享视图
        """
        self.world = world
        self.uavs = self.world.policy_agents
        self.n = len(world.policy_agents)
        
        # 场景回调函数
        self.reset_callback = reset_callback
        self.reward_callback = reward_callback
        self.observation_callback = observation_callback
        self.info_callback = info_callback
        self.done_callback = done_callback
        
        # 信道模型
        self.channel_model = SimplifiedChannelModel()
        
        # 当前步数
        self.current_step = 0
        
        # 环境参数
        self.shared_reward = False  # 是否所有智能体共享奖励
        
        # 配置空间
        self.action_space = []
        self.observation_space = []
        self.share_observation_space = []
        
        share_obs_dim = 0
        
        # 为每个UAV配置动作和观测空间
        for uav in self.uavs:
            # 动作空间：3D速度调整 [delta_vx, delta_vy, delta_vz]
            # 每个维度的范围是 [-1, 1]，会根据UAV的max_speed进行缩放
            self.action_space.append(spaces.Box(
                low=-1.0, high=1.0, shape=(3,), dtype=np.float32))
            
            # 计算观测空间维度
            # 自身状态：3D位置、3D速度、电池电量、是否服务用户、是否中继、回程链路质量
            # 1（电池电量）+ 3（位置）+ 3（速度）+ 1（是否服务）+ 1（是否中继）+ 1（回程链路质量）= 10
            # 每个观测到的UAV：3D相对位置、3D相对速度、是否服务用户、是否中继 = 8
            # 每个观测到的GBS：3D相对位置 = 3
            # 每个观测到的UE：3D相对位置、是否请求服务 = 4
            
            # 假设最多能观测到 n_uav 个 UAVs, n_gbs 个 GBSs, n_ue 个 UEs
            n_uav = self.n - 1  # 除自己外的所有UAV
            n_gbs = len(self.world.ground_base_stations)
            n_ue = len(self.world.user_equipments)
            
            obs_dim = 10 + n_uav * 8 + n_gbs * 3 + n_ue * 4
            
            self.observation_space.append(spaces.Box(
                low=-np.inf, high=+np.inf, shape=(obs_dim,), dtype=np.float32))
            
            share_obs_dim += obs_dim
        
        # 共享观测空间
        self.share_observation_space = [spaces.Box(
            low=-np.inf, high=+np.inf, shape=(share_obs_dim,), dtype=np.float32) for _ in range(self.n)]
        
        # 渲染
        self.shared_viewer = shared_viewer
        if self.shared_viewer:
            self.viewers = [None]
        else:
            self.viewers = [None] * self.n
        self._reset_render()
    
    def step(self, action_n):
        """
        环境步进
        
        Args:
            action_n: 所有UAV的动作列表
            
        Returns:
            obs_n: 所有UAV的观测列表
            reward_n: 所有UAV的奖励列表
            done_n: 所有UAV的结束标志列表
            info_n: 所有UAV的信息字典列表
        """
        self.current_step += 1
        
        # 设置每个UAV的动作
        for i, uav in enumerate(self.uavs):
            self._set_action(action_n[i], uav)
        
        # 更新世界状态
        self.world.step(self.channel_model)
        
        # 记录每个UAV的观测、奖励、结束标志和信息
        obs_n = []
        reward_n = []
        done_n = []
        info_n = []
        
        for i, uav in enumerate(self.uavs):
            obs_n.append(self._get_obs(uav))
            reward_n.append([self._get_reward(uav)])
            done_n.append(self._get_done(uav))
            
            info = {'individual_reward': self._get_reward(uav)}
            # 添加其他信息
            if self.info_callback is not None:
                env_info = self.info_callback(uav, self.world)
                info.update(env_info)
            info_n.append(info)
        
        # 如果设置了共享奖励，则所有UAV获得相同的奖励
        if self.shared_reward:
            reward = np.sum(reward_n)
            reward_n = [[reward]] * self.n
        
        return obs_n, reward_n, done_n, info_n
    
    def reset(self):
        """
        重置环境
        
        Returns:
            obs_n: 所有UAV的初始观测列表
        """
        self.current_step = 0
        
        # 重置世界
        self.reset_callback(self.world)
        
        # 重置渲染器
        self._reset_render()
        
        # 记录每个UAV的初始观测
        obs_n = []
        for uav in self.uavs:
            obs_n.append(self._get_obs(uav))
        
        return obs_n
    
    def _get_obs(self, uav):
        """
        获取单个UAV的观测
        
        Args:
            uav: UAV对象
            
        Returns:
            obs: UAV的观测
        """
        if self.observation_callback is None:
            return np.zeros(0)
        return self.observation_callback(uav, self.world)
    
    def _get_reward(self, uav):
        """
        获取单个UAV的奖励
        
        Args:
            uav: UAV对象
            
        Returns:
            reward: UAV的奖励
        """
        if self.reward_callback is None:
            return 0.0
        return self.reward_callback(uav, self.world)
    
    def _get_done(self, uav):
        """
        判断单个UAV是否结束
        
        Args:
            uav: UAV对象
            
        Returns:
            done: 是否结束
        """
        if self.done_callback is None:
            # 如果没有提供回调函数，则根据最大步数判断
            if self.current_step >= self.world.world_length:
                return True
            return False
        return self.done_callback(uav, self.world)
    
    def _set_action(self, action, uav):
        """
        设置单个UAV的动作
        
        Args:
            action: UAV的动作
            uav: UAV对象
        """
        # 将动作范围（-1,1）映射到实际速度调整值
        uav.action.u = action * uav.max_speed
    
    def _reset_render(self):
        """
        重置渲染器
        """
        self.render_geoms = None
        self.render_geoms_xform = None
    
    def render(self, mode='human'):
        """
        渲染环境
        
        Args:
            mode: 渲染模式
        
        Returns:
            结果：根据不同的模式返回不同的结果
        """
        # 实现渲染逻辑，可参考MPE的渲染代码
        # 由于3D渲染较复杂，这里可以先简单实现或返回None
        return None

def make_uav_comm_env(scenario_name, args, benchmark=False):
    """
    创建UAV通信环境的工厂函数
    
    Args:
        scenario_name: 场景名称
        args: 参数
        benchmark: 是否为基准测试
        
    Returns:
        env: UAV通信环境
    """
    from .scenarios.load import load
    
    # 加载场景
    scenario = load(scenario_name + ".py").Scenario()
    
    # 创建世界
    world = scenario.make_world(args)
    
    # 创建多智能体环境
    env = UAVCommEnv(world, 
                     scenario.reset_world,
                     scenario.reward,
                     scenario.observation,
                     scenario.info if hasattr(scenario, 'info') else None,
                     scenario.done if hasattr(scenario, 'done') else None)
    
    return env
