#!/usr/bin/env python3
"""
修复scenario4.py中的路由算法问题
确保所有能够直连基站的UAV都能建立路由路径
"""

import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_fixed_routing_method():
    """
    创建修复后的路由计算方法
    
    修复策略：
    1. 优先为能直连基站的UAV建立直连路径
    2. 为无法直连的UAV寻找多跳路径
    3. 确保所有有连接用户的UAV都有回程路径
    """
    
    routing_code = '''
    def _compute_routing_paths(self):
        """
        修复后的路由路径计算方法
        
        改进策略：
        1. 优先建立直连路径（1跳）
        2. 为无法直连的UAV建立多跳路径
        3. 确保所有连接了用户的UAV都有回程路径
        """
        self.routing_paths = {}
        
        # 第一步：为所有能直连基站的UAV建立直连路径
        for uav_idx in range(self.n_uavs):
            # 检查是否有用户连接到这个UAV
            has_users = np.sum(self.connections[uav_idx]) > 0
            if not has_users:
                continue  # 跳过没有用户连接的UAV
            
            # 检查能否直连任何基站
            best_bs_capacity = 0
            best_bs_idx = -1
            
            for bs_idx in range(self.n_ground_bs):
                capacity = self._get_link_capacity("uav", uav_idx, "ground_bs", bs_idx)
                if capacity > best_bs_capacity:
                    best_bs_capacity = capacity
                    best_bs_idx = bs_idx
            
            # 如果能直连基站，建立直连路径
            if best_bs_capacity > 0:
                direct_path = [("uav", uav_idx), ("ground_bs", best_bs_idx)]
                self.routing_paths[uav_idx] = (direct_path, best_bs_capacity)
        
        # 第二步：为无法直连的UAV寻找多跳路径
        for uav_idx in range(self.n_uavs):
            # 跳过已有路径的UAV
            if uav_idx in self.routing_paths:
                continue
            
            # 检查是否有用户连接到这个UAV
            has_users = np.sum(self.connections[uav_idx]) > 0
            if not has_users:
                continue
            
            # 使用原有的最宽路径算法寻找多跳路径
            path, capacity = self._find_widest_path_to_ground_bs(uav_idx)
            if path and capacity > 0 and len(path) <= self.max_hops + 1:
                self.routing_paths[uav_idx] = (path, capacity)
        
        # 第三步：验证和统计
        connected_uavs_with_users = sum(1 for i in range(self.n_uavs) if np.sum(self.connections[i]) > 0)
        uavs_with_routes = len(self.routing_paths)
        
        # 如果仍有UAV没有路径，尝试降低标准
        if uavs_with_routes < connected_uavs_with_users:
            for uav_idx in range(self.n_uavs):
                if uav_idx in self.routing_paths:
                    continue
                
                has_users = np.sum(self.connections[uav_idx]) > 0
                if not has_users:
                    continue
                
                # 尝试通过任何有路径的UAV中继
                best_relay_capacity = 0
                best_relay_path = None
                
                for relay_uav in self.routing_paths:
                    # 计算到中继UAV的容量
                    relay_capacity = self._get_link_capacity("uav", uav_idx, "uav", relay_uav)
                    if relay_capacity > 0:
                        # 构建通过中继的路径
                        relay_path = [("uav", uav_idx), ("uav", relay_uav)]
                        # 添加中继UAV到基站的路径
                        original_path = self.routing_paths[relay_uav][0]
                        for node in original_path[1:]:  # 跳过中继UAV自身
                            relay_path.append(node)
                        
                        # 计算瓶颈容量
                        bottleneck = min(relay_capacity, self.routing_paths[relay_uav][1])
                        
                        if bottleneck > best_relay_capacity:
                            best_relay_capacity = bottleneck
                            best_relay_path = relay_path
                
                if best_relay_path and best_relay_capacity > 0:
                    self.routing_paths[uav_idx] = (best_relay_path, best_relay_capacity)
    '''
    
    return routing_code

def test_fixed_routing():
    """测试修复后的路由算法"""
    print("=" * 60)
    print("测试修复后的路由算法")
    print("=" * 60)
    
    # 读取原始文件
    with open('envs/pettingzoo/scenario4.py', 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    # 创建修复后的代码
    fixed_routing_code = create_fixed_routing_method()
    
    # 找到原始方法的位置并替换
    import re
    
    # 匹配原始的_compute_routing_paths方法
    pattern = r'def _compute_routing_paths\(self\):.*?(?=\n    def |\n\nclass |\Z)'
    
    if re.search(pattern, original_content, re.DOTALL):
        # 替换方法
        fixed_content = re.sub(pattern, fixed_routing_code.strip(), original_content, flags=re.DOTALL)
        
        # 保存修复后的文件
        backup_file = 'envs/pettingzoo/scenario4_backup.py'
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(original_content)
        print(f"原始文件已备份到: {backup_file}")
        
        with open('envs/pettingzoo/scenario4.py', 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        print("已应用路由算法修复")
        
        # 测试修复效果
        print("\n测试修复效果:")
        from envs.pettingzoo.scenario4 import UAVForcedRelayEnv
        
        # 重新导入模块以获取修复后的版本
        import importlib
        import envs.pettingzoo.scenario4
        importlib.reload(envs.pettingzoo.scenario4)
        from envs.pettingzoo.scenario4 import UAVForcedRelayEnv
        
        seeds = [42, 123, 456]
        results = []
        
        for seed in seeds:
            env = UAVForcedRelayEnv(
                n_uavs=12, n_users=80, area_size=2500,
                seed=seed,
                randomize_bs=True, randomize_users=True, randomize_uav_start=True
            )
            
            obs, info = env.reset(seed=seed)
            
            # 统计结果
            total_connections = np.sum(env.connections)
            connected_uavs = len(env.routing_paths) if hasattr(env, 'routing_paths') else 0
            
            effective_users = 0
            if hasattr(env, 'routing_paths'):
                for i in range(env.n_uavs):
                    if i in env.routing_paths and env.routing_paths[i][0]:
                        effective_users += np.sum(env.connections[i])
            
            coverage_ratio = effective_users / env.n_users
            results.append(coverage_ratio)
            
            print(f"种子 {seed:3d}: 连接 {total_connections:2d}, 有路径UAV {connected_uavs:2d}, 覆盖率 {coverage_ratio*100:5.1f}%")
        
        avg_coverage = np.mean(results)
        print(f"\n修复后平均覆盖率: {avg_coverage*100:.1f}%")
        
        if avg_coverage > 0.8:
            print("✅ 路由算法修复成功！覆盖率显著提升")
        else:
            print("⚠️ 修复效果有限，可能需要进一步调整")
            
    else:
        print("❌ 未找到_compute_routing_paths方法，无法应用修复")

if __name__ == "__main__":
    test_fixed_routing()
