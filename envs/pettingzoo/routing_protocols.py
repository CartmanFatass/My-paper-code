import abc
import numpy as np
import heapq
import collections
from typing import Dict, List, Tuple, Optional, Any

class BaseRoutingProtocol(abc.ABC):
    """
    抽象基类，定义所有路由协议必须实现的接口
    """
    def __init__(self, env):
        self.env = env  # 访问环境状态的引用
        self.routing_overhead = 0  # 当前步骤产生的路由开销（数据包数量）
        self.protocol_name = "base"
        
    @abc.abstractmethod
    def compute_routing_paths(self):
        """
        主要方法，由环境在每个步骤中调用。
        该方法应更新 env.routing_paths 字典。
        """
        raise NotImplementedError
        
    def get_and_reset_overhead(self) -> int:
        """返回上一步生成的开销并重置计数器"""
        overhead = self.routing_overhead
        self.routing_overhead = 0
        return overhead
        
    def reset(self):
        """重置协议状态（在环境重置时调用）"""
        self.routing_overhead = 0

class HGGRProtocol(BaseRoutingProtocol):
    """
    分层地理贪婪路由协议实现
    """
    def __init__(self, env):
        super().__init__(env)
        self.protocol_name = "HGGR"
        self.hggr_update_interval = getattr(env, 'hggr_update_interval', 10)
        self.hop_map = {}
        
    def compute_routing_paths(self):
        # 高层决策：周期性更新全局hop_map
        if self.env.current_step % self.hggr_update_interval == 0:
            self.hop_map = self._calculate_hop_map()
            # 全局更新是HGGR的主要路由开销来源
            # 建模为每个UAV接收一个控制数据包来获取地图
            self.routing_overhead += self.env.n_uavs
            
        # 低层决策：基于当前地图重建所有路径
        self._reconstruct_all_hggr_paths()
        
    def _calculate_hop_map(self) -> Dict[int, float]:
        """动态计算跳数地图（全局BFS）"""
        q = collections.deque()
        hop_map = {i: float('inf') for i in range(self.env.n_uavs)}
        
        # 1. 将所有直连到基站的无人机作为第一层（跳数为1）
        for uav_idx in range(self.env.n_uavs):
            for bs_idx in range(self.env.n_ground_bs):
                if self.env.uav_bs_connections[uav_idx, bs_idx]:
                    if hop_map[uav_idx] == float('inf'):
                        hop_map[uav_idx] = 1
                        q.append(uav_idx)
                    break
                    
        # 2. 从第一层开始，通过BFS计算其他无人机的跳数
        while q:
            current_uav = q.popleft()
            current_hop = hop_map[current_uav]
            
            for neighbor_idx in range(self.env.n_uavs):
                if self.env.uav_connections[current_uav, neighbor_idx]:
                    if hop_map[neighbor_idx] == float('inf'):
                        hop_map[neighbor_idx] = current_hop + 1
                        q.append(neighbor_idx)
                        
        return hop_map
        
    def _reconstruct_all_hggr_paths(self):
        """重建所有HGGR路径"""
        self.env.routing_paths = {}
        for uav_idx in range(self.env.n_uavs):
            path, bottleneck_capacity = self._reconstruct_hggr_path(uav_idx)
            if path and bottleneck_capacity > 0:
                self.env.routing_paths[uav_idx] = (path, bottleneck_capacity)
                
    def _reconstruct_hggr_path(self, start_uav_idx) -> Tuple[Optional[List], float]:
        """从指定的无人机开始，沿着跳数梯度重建到基站的完整路径"""
        path = [("uav", start_uav_idx)]
        bottleneck_capacity = float('inf')
        
        current_node_idx = start_uav_idx
        
        # 循环构建路径，直到到达基站或无法继续
        for _ in range(self.env.max_hops + 1):
            current_hop = self.hop_map.get(current_node_idx, float('inf'))
            if current_hop == float('inf'):
                return None, 0  # 当前节点不可达
                
            # --- 寻找最优的下一跳 ---
            best_next_hop_node = None
            max_link_capacity = 0.0
            
            # 候选1：其他无人机
            for neighbor_idx in range(self.env.n_uavs):
                if current_node_idx == neighbor_idx or not self.env.uav_connections[current_node_idx, neighbor_idx]:
                    continue
                    
                neighbor_hop = self.hop_map.get(neighbor_idx, float('inf'))
                if neighbor_hop < current_hop:
                    capacity = self.env._get_link_capacity("uav", current_node_idx, "uav", neighbor_idx)
                    if capacity > max_link_capacity:
                        max_link_capacity = capacity
                        best_next_hop_node = ("uav", neighbor_idx)
                        
            # 候选2：地面基站 (跳数为0)
            for bs_idx in range(self.env.n_ground_bs):
                if self.env.uav_bs_connections[current_node_idx, bs_idx]:
                    if 0 < current_hop:
                        capacity = self.env._get_link_capacity("uav", current_node_idx, "ground_bs", bs_idx)
                        if capacity > max_link_capacity:
                            max_link_capacity = capacity
                            best_next_hop_node = ("ground_bs", bs_idx)
                            
            # --- 更新路径和瓶颈 ---
            if best_next_hop_node:
                path.append(best_next_hop_node)
                bottleneck_capacity = min(bottleneck_capacity, max_link_capacity)
                
                # 如果下一跳是基站，路径构建完成
                if best_next_hop_node[0] == "ground_bs":
                    return path, bottleneck_capacity
                    
                # 更新当前节点以继续构建路径
                current_node_idx = best_next_hop_node[1]
            else:
                # 找不到下一跳，路径中断
                return None, 0
                
        # 如果超出最大跳数仍未到达基站，则路径无效
        return None, 0

class AODVProtocol(BaseRoutingProtocol):
    """
    AODV (Ad-hoc On-Demand Distance Vector) 反应式路由协议
    """
    def __init__(self, env):
        super().__init__(env)
        self.protocol_name = "AODV"
        # 每个UAV的路由表: {dest_id: (next_hop_id, expiry_time, seq_num)}
        self.routing_tables = {i: {} for i in range(self.env.n_uavs)}
        # 跟踪进行中的路由发现，避免请求风暴: {(source_id, dest_id): request_id}
        self.rreq_cache = {}
        self.route_expiry_time = 30  # 路由有效期（步数）
        self.sequence_numbers = {i: 0 for i in range(self.env.n_uavs)}  # 序列号
        
    def reset(self):
        """重置AODV协议状态"""
        super().reset()
        self.routing_tables = {i: {} for i in range(self.env.n_uavs)}
        self.rreq_cache = {}
        self.sequence_numbers = {i: 0 for i in range(self.env.n_uavs)}
        
    def compute_routing_paths(self):
        # 1. 使过期的路由失效
        for uav_id, table in self.routing_tables.items():
            expired_dests = [dest for dest, (_, expiry, _) in table.items() if self.env.current_step > expiry]
            for dest in expired_dests:
                del table[dest]
                
        # 2. 对于每个UAV，如果它需要到BS的路径，检查其表。如果不存在，启动RREQ。
        self.env.routing_paths = {}
        for uav_idx in range(self.env.n_uavs):
            path_found, path, capacity = self._get_path_from_table(uav_idx)
            if path_found:
                self.env.routing_paths[uav_idx] = (path, capacity)
            else:
                # 启动路由发现（RREQ）
                self._initiate_rreq(uav_idx)
                
    def _initiate_rreq(self, source_uav_id):
        """启动路由请求"""
        # 检查是否已经有正在进行的请求
        cache_key = (source_uav_id, "BS")  # 简化：所有请求都是到基站的
        if cache_key in self.rreq_cache:
            return  # 避免重复请求
            
        # 模拟RREQ泛洪。这是主要的开销来源。
        # 成本与转发请求的UAV数量成正比。
        # 简化模型：假设所有可达的UAV都转发一次。
        self.routing_overhead += self.env.n_uavs  # 简化开销成本
        
        # 在真实仿真中，路径会在延迟后建立。
        # 我们可以通过在模拟延迟（例如2-3步）后才将路径添加到路由表来模拟这一点。
        # 为了简化，这里我们立即找到并建立路径。
        path, capacity = self._find_shortest_path_to_bs(source_uav_id)
        if path:
            self._establish_path_in_tables(path)
            self.rreq_cache[cache_key] = self.env.current_step
            
        # 清理旧的缓存条目
        old_cache_keys = [key for key, timestamp in self.rreq_cache.items() 
                         if self.env.current_step - timestamp > 10]
        for key in old_cache_keys:
            del self.rreq_cache[key]
            
    def _find_shortest_path_to_bs(self, source_uav) -> Tuple[Optional[List], float]:
        """使用BFS找到到基站的最短路径"""
        from collections import deque
        
        queue = deque([(("uav", source_uav), [("uav", source_uav)], float('inf'))])
        visited = {("uav", source_uav)}
        
        while queue:
            current_node, path, capacity = queue.popleft()
            current_type, current_idx = current_node
            
            if current_type == "uav":
                # 检查到基站的直连
                for bs_idx in range(self.env.n_ground_bs):
                    if self.env.uav_bs_connections[current_idx, bs_idx]:
                        bs_node = ("ground_bs", bs_idx)
                        link_capacity = self.env._get_link_capacity("uav", current_idx, "ground_bs", bs_idx)
                        if link_capacity > 0:
                            final_path = path + [bs_node]
                            final_capacity = min(capacity, link_capacity)
                            return final_path, final_capacity
                            
                # 添加UAV邻居到队列
                for neighbor_idx in range(self.env.n_uavs):
                    neighbor_node = ("uav", neighbor_idx)
                    if (neighbor_idx != current_idx and 
                        self.env.uav_connections[current_idx, neighbor_idx] and
                        neighbor_node not in visited and
                        len(path) < self.env.max_hops):
                        
                        link_capacity = self.env._get_link_capacity("uav", current_idx, "uav", neighbor_idx)
                        if link_capacity > 0:
                            new_path = path + [neighbor_node]
                            new_capacity = min(capacity, link_capacity)
                            queue.append((neighbor_node, new_path, new_capacity))
                            visited.add(neighbor_node)
                            
        return None, 0
        
    def _establish_path_in_tables(self, path):
        """在找到路径时，更新路径上所有UAV的路由表"""
        expiry_time = self.env.current_step + self.route_expiry_time
        
        # 更新序列号
        for _, node_idx in path:
            if _ == "uav":
                self.sequence_numbers[node_idx] += 1
                
        for i in range(len(path) - 1):
            source_node, source_idx = path[i]
            next_hop_node, next_hop_idx = path[i+1]
            dest_node, dest_idx = path[-1]
            
            if source_node == "uav" and dest_node == "ground_bs":
                # 路径到基站 - 使用特殊标识符
                dest_key = f"BS_{dest_idx}"
                seq_num = self.sequence_numbers.get(dest_idx, 0)
                self.routing_tables[source_idx][dest_key] = (next_hop_idx, expiry_time, seq_num)
                
    def _get_path_from_table(self, uav_idx) -> Tuple[bool, Optional[List], float]:
        """从表中重建路径（如果存在）"""
        table = self.routing_tables[uav_idx]
        
        # 寻找到任何基站的路由
        for dest_key, (next_hop_idx, expiry, seq_num) in table.items():
            if dest_key.startswith("BS_") and expiry > self.env.current_step:
                bs_idx = int(dest_key.split("_")[1])
                
                # 重建路径（简化版本）
                path = [("uav", uav_idx)]
                capacity = float('inf')
                current_idx = uav_idx
                
                # 跟随下一跳链接，最多跳跃max_hops次
                for _ in range(self.env.max_hops):
                    if next_hop_idx in range(self.env.n_uavs):
                        # 下一跳是UAV
                        link_capacity = self.env._get_link_capacity("uav", current_idx, "uav", next_hop_idx)
                        if link_capacity <= 0:
                            break  # 链路失效
                            
                        capacity = min(capacity, link_capacity)
                        path.append(("uav", next_hop_idx))
                        current_idx = next_hop_idx
                        
                        # 检查这个UAV是否有到基站的直连
                        if self.env.uav_bs_connections[current_idx, bs_idx]:
                            bs_link_capacity = self.env._get_link_capacity("uav", current_idx, "ground_bs", bs_idx)
                            if bs_link_capacity > 0:
                                capacity = min(capacity, bs_link_capacity)
                                path.append(("ground_bs", bs_idx))
                                return True, path, capacity
                                
                        # 检查当前UAV的路由表以获取下一跳
                        if dest_key in self.routing_tables[current_idx]:
                            next_hop_idx, expiry, _ = self.routing_tables[current_idx][dest_key]
                            if expiry <= self.env.current_step:
                                break  # 路由过期
                        else:
                            break  # 没有进一步的路由信息
                    else:
                        break  # 无效的下一跳
                        
        return False, None, 0

class DSDVProtocol(BaseRoutingProtocol):
    """
    DSDV (Destination-Sequenced Distance Vector) 主动式路由协议
    """
    def __init__(self, env):
        super().__init__(env)
        self.protocol_name = "DSDV"
        self.update_interval = 10  # 每10步广播更新
        # 每个UAV的完整路由表: {dest_id: (next_hop_id, distance, seq_num)}
        self.routing_tables = {i: {} for i in range(self.env.n_uavs)}
        self.sequence_numbers = {i: 0 for i in range(self.env.n_uavs)}
        
    def reset(self):
        """重置DSDV协议状态"""
        super().reset()
        self.routing_tables = {i: {} for i in range(self.env.n_uavs)}
        self.sequence_numbers = {i: 0 for i in range(self.env.n_uavs)}
        
    def compute_routing_paths(self):
        # 1. 周期性广播并更新路由表
        if self.env.current_step % self.update_interval == 0:
            self._broadcast_and_update_all_tables()
            
        # 2. 路径计算只是表查找（非常快）
        self.env.routing_paths = {}
        for uav_idx in range(self.env.n_uavs):
            path, capacity = self._reconstruct_path_from_table(uav_idx)
            if path:
                self.env.routing_paths[uav_idx] = (path, capacity)
                
    def _broadcast_and_update_all_tables(self):
        """模拟每个UAV向其直接邻居广播其表"""
        # 这是DSDV的主要开销来源
        self.routing_overhead += self.env.n_uavs * (self.env.n_uavs // 2)  # 高开销模型
        
        # 实际更新逻辑将涉及Bellman-Ford或类似算法
        # 来基于邻居的表找到最短路径。
        # 简化：只是重新计算所有对最短路径。
        # （这在计算上很重，但模拟了DSDV的结果）
        self._update_all_routing_tables()
        
    def _update_all_routing_tables(self):
        """更新所有路由表（简化的全对最短路径）"""
        # 为每个UAV计算到基站的最短路径
        for uav_idx in range(self.env.n_uavs):
            # 增加序列号
            self.sequence_numbers[uav_idx] += 1
            
            # 使用Dijkstra算法计算最短路径
            distances, predecessors = self._dijkstra_shortest_paths(uav_idx)
            
            # 更新到基站的路由
            for bs_idx in range(self.env.n_ground_bs):
                bs_key = f"BS_{bs_idx}"
                if bs_key in distances and distances[bs_key] < float('inf'):
                    # 找到下一跳
                    next_hop = self._get_next_hop(uav_idx, bs_key, predecessors)
                    if next_hop is not None:
                        self.routing_tables[uav_idx][bs_key] = (
                            next_hop, 
                            distances[bs_key], 
                            self.sequence_numbers[uav_idx]
                        )
                        
    def _dijkstra_shortest_paths(self, source_uav) -> Tuple[Dict, Dict]:
        """为源UAV计算到所有目标的最短路径"""
        distances = {}
        predecessors = {}
        visited = set()
        pq = []
        
        # 初始化
        source_key = f"UAV_{source_uav}"
        distances[source_key] = 0
        heapq.heappush(pq, (0, source_key))
        
        while pq:
            current_dist, current_key = heapq.heappop(pq)
            
            if current_key in visited:
                continue
            visited.add(current_key)
            
            current_type, current_idx = current_key.split("_")
            current_idx = int(current_idx)
            
            if current_type == "UAV":
                # 探索UAV邻居
                for neighbor_idx in range(self.env.n_uavs):
                    if (neighbor_idx != current_idx and 
                        self.env.uav_connections[current_idx, neighbor_idx]):
                        
                        neighbor_key = f"UAV_{neighbor_idx}"
                        link_cost = 1  # 简化：所有UAV链路成本为1
                        new_dist = current_dist + link_cost
                        
                        if neighbor_key not in distances or new_dist < distances[neighbor_key]:
                            distances[neighbor_key] = new_dist
                            predecessors[neighbor_key] = current_key
                            heapq.heappush(pq, (new_dist, neighbor_key))
                            
                # 探索基站邻居
                for bs_idx in range(self.env.n_ground_bs):
                    if self.env.uav_bs_connections[current_idx, bs_idx]:
                        bs_key = f"BS_{bs_idx}"
                        link_cost = 1  # 简化：到基站的链路成本为1
                        new_dist = current_dist + link_cost
                        
                        if bs_key not in distances or new_dist < distances[bs_key]:
                            distances[bs_key] = new_dist
                            predecessors[bs_key] = current_key
                            heapq.heappush(pq, (new_dist, bs_key))
                            
        return distances, predecessors
        
    def _get_next_hop(self, source_uav, dest_key, predecessors) -> Optional[int]:
        """从前驱字典中获取下一跳"""
        if dest_key not in predecessors:
            return None
            
        current = dest_key
        path = []
        
        while current is not None:
            path.append(current)
            current = predecessors.get(current)
            
        path.reverse()
        
        # 路径格式：["UAV_source", ..., "dest"]
        if len(path) >= 2:
            next_node_key = path[1]  # 第二个节点是下一跳
            node_type, node_idx = next_node_key.split("_")
            return int(node_idx)
            
        return None
        
    def _reconstruct_path_from_table(self, uav_idx) -> Tuple[Optional[List], float]:
        """从路由表重建路径"""
        table = self.routing_tables[uav_idx]
        
        # 寻找到任何基站的最短路由
        best_path = None
        best_capacity = 0
        
        for dest_key, (next_hop_idx, distance, seq_num) in table.items():
            if dest_key.startswith("BS_"):
                bs_idx = int(dest_key.split("_")[1])
                
                # 重建路径
                path = [("uav", uav_idx)]
                capacity = float('inf')
                current_idx = uav_idx
                
                # 跟随路由表重建路径
                for _ in range(int(distance) + 1):
                    if current_idx == next_hop_idx:
                        # 直接连接到基站
                        link_capacity = self.env._get_link_capacity("uav", current_idx, "ground_bs", bs_idx)
                        if link_capacity > 0:
                            capacity = min(capacity, link_capacity)
                            path.append(("ground_bs", bs_idx))
                            break
                    else:
                        # 下一跳是另一个UAV
                        link_capacity = self.env._get_link_capacity("uav", current_idx, "uav", next_hop_idx)
                        if link_capacity <= 0:
                            break  # 链路失效
                            
                        capacity = min(capacity, link_capacity)
                        path.append(("uav", next_hop_idx))
                        current_idx = next_hop_idx
                        
                        # 查找当前UAV的下一跳
                        if dest_key in self.routing_tables[current_idx]:
                            next_hop_idx, _, _ = self.routing_tables[current_idx][dest_key]
                        else:
                            break  # 没有进一步的路由信息
                            
                if len(path) > 1 and path[-1][0] == "ground_bs":
                    if capacity > best_capacity:
                        best_capacity = capacity
                        best_path = path
                        
        return best_path, best_capacity

class GPSRProtocol(BaseRoutingProtocol):
    """
    GPSR (Greedy Perimeter Stateless Routing) 地理位置路由协议
    """
    def __init__(self, env):
        super().__init__(env)
        self.protocol_name = "GPSR"
        
    def compute_routing_paths(self):
        # 地理路由是无状态的，所以开销很小（或者为零）
        # 它依赖于一跳"hello"消息来了解邻居，
        # 这可以建模为每步的小的、恒定的开销。
        self.routing_overhead += self.env.n_uavs
        
        # 使用贪婪地理路由逻辑
        self._compute_geographic_routing_paths()
        
    def _compute_geographic_routing_paths(self):
        """使用简化的地理路由算法计算路由路径"""
        self.env.routing_paths = {}
        
        # 预先计算所有无人机到最近基站的物理距离
        uav_dist_to_bs = {}
        for i in range(self.env.n_uavs):
            min_dist = float('inf')
            for bs_pos in self.env.ground_bs_positions:
                dist = np.linalg.norm(self.env.uav_positions[i] - bs_pos)
                min_dist = min(min_dist, dist)
            uav_dist_to_bs[i] = min_dist
            
        for uav_idx in range(self.env.n_uavs):
            path = [("uav", uav_idx)]
            bottleneck_capacity = float('inf')
            current_node_idx = uav_idx
            
            # 迭代构建路径
            for _ in range(self.env.max_hops + 1):
                own_dist = uav_dist_to_bs.get(current_node_idx, float('inf'))
                if own_dist == float('inf'):
                    break
                    
                best_next_hop_node = None
                max_link_capacity = 0.0
                
                # 候选1：寻找距离基站更近的无人机邻居
                for neighbor_idx in range(self.env.n_uavs):
                    if (current_node_idx == neighbor_idx or 
                        not self.env.uav_connections[current_node_idx, neighbor_idx]):
                        continue
                        
                    neighbor_dist = uav_dist_to_bs.get(neighbor_idx, float('inf'))
                    if neighbor_dist < own_dist:
                        capacity = self.env._get_link_capacity("uav", current_node_idx, "uav", neighbor_idx)
                        if capacity > max_link_capacity:
                            max_link_capacity = capacity
                            best_next_hop_node = ("uav", neighbor_idx)
                
                # 候选2：检查到基站的直连
                for bs_idx in range(self.env.n_ground_bs):
                    if self.env.uav_bs_connections[current_node_idx, bs_idx]:
                        capacity = self.env._get_link_capacity("uav", current_node_idx, "ground_bs", bs_idx)
                        if capacity > max_link_capacity:
                            max_link_capacity = capacity
                            best_next_hop_node = ("ground_bs", bs_idx)
                
                # 更新路径
                if best_next_hop_node:
                    path.append(best_next_hop_node)
                    bottleneck_capacity = min(bottleneck_capacity, max_link_capacity)
                    
                    if best_next_hop_node[0] == "ground_bs":
                        # 成功到达基站
                        self.env.routing_paths[uav_idx] = (path, bottleneck_capacity)
                        break
                    
                    current_node_idx = best_next_hop_node[1]
                else:
                    # 路径中断
                    break
            # 如果循环结束仍未设置路径，则说明失败

class WidestPathProtocol(BaseRoutingProtocol):
    """
    最宽路径路由协议（原始实现）
    """
    def __init__(self, env):
        super().__init__(env)
        self.protocol_name = "Widest Path"
        
    def compute_routing_paths(self):
        # 最宽路径算法的开销相对较小，主要是链路状态信息的交换
        self.routing_overhead += self.env.n_uavs // 2  # 中等开销
        
        self.env.routing_paths = {}
        for uav_idx in range(self.env.n_uavs):
            path, capacity = self.env._find_widest_path_to_ground_bs(uav_idx)
            if path and capacity > 0 and len(path) - 1 <= self.env.max_hops:
                self.env.routing_paths[uav_idx] = (path, capacity)
