import torch
import networkx as nx
import community as community_louvain
from logger import main_logger

class LouvainSkillHierarchy:
    """
    使用Louvain算法构建和管理多层次技能树。
    这个类负责:
    1. 从环境交互轨迹构建状态转换图。
    2. 应用Louvain算法来识别多层次的社区结构。
    3. 将社区层次结构转换为可用的技能树。
    4. 提供查询接口，例如查找一个状态属于哪个社区。
    """
    def __init__(self, resolution=0.05, min_cluster_size=4):
        """
        初始化Louvain技能层次结构。

        参数:
            resolution (float): Louvain算法的分辨率参数。
            min_cluster_size (int): 过滤掉过小社区的阈值。
        """
        self.graph = nx.DiGraph()
        self.partitions = []  # 存储由Louvain算法生成的多层分区
        self.skill_tree = {}  # 存储最终的技能层次结构
        self.resolution = resolution
        self.min_cluster_size = min_cluster_size
        self.state_to_node = {} # 状态到图节点的映射
        self.node_counter = 0

    def _get_or_create_node(self, state):
        """
        获取或创建与状态对应的图节点。
        为了处理非哈希able的状态（如numpy数组），我们将状态转换为唯一的ID。
        """
        # 将状态（可能是numpy数组）转换为一个可哈希的元组
        state_tuple = tuple(state.flatten())
        if state_tuple not in self.state_to_node:
            self.state_to_node[state_tuple] = self.node_counter
            self.graph.add_node(self.node_counter, state=state)
            self.node_counter += 1
        return self.state_to_node[state_tuple]

    def build_graph_from_trajectories(self, trajectories):
        """
        从轨迹数据构建状态转换图。

        参数:
            trajectories (list): 轨迹数据列表，每个元素是 (s_t, a_t, s_{t+1})。
        """
        main_logger.info("从轨迹构建状态转换图...")
        for state, _, next_state in trajectories:
            u = self._get_or_create_node(state)
            v = self._get_or_create_node(next_state)
            if self.graph.has_edge(u, v):
                self.graph[u][v]['weight'] += 1
            else:
                self.graph.add_edge(u, v, weight=1)
        main_logger.info(f"图构建完成。节点数: {self.graph.number_of_nodes()}, 边数: {self.graph.number_of_edges()}")

    def generate_skill_hierarchy(self):
        """
        在构建的图上运行Louvain算法并生成技能层次结构。
        """
        if self.graph.number_of_nodes() == 0:
            main_logger.warning("图为空，无法生成技能层次结构。")
            return

        main_logger.info("开始生成技能层次结构...")
        # Louvain算法需要无向图，我们将其转换为无向图进行社区检测
        # 保留权重信息
        undirected_graph = self.graph.to_undirected()
        
        # 使用 best_partition 函数来获取多层次的社区结构
        # dendrogram 是一个列表，每个元素是一个字典，表示一层的社区划分
        dendrogram = community_louvain.generate_dendrogram(undirected_graph, 
                                                           resolution=self.resolution,
                                                           weight='weight')
        
        # dendrogram 的层级是从细到粗，我们将其反转为从粗到细
        self.partitions = [community_louvain.partition_at_level(dendrogram, level) for level in range(len(dendrogram))]
        self.partitions.reverse() # 从最高层(L)到最低层(1)

        # 过滤掉过小的社区层级
        self.partitions = [p for p in self.partitions if self._get_mean_cluster_size(p) >= self.min_cluster_size]

        main_logger.info(f"技能层次结构生成完毕，共 {len(self.partitions)} 层。")
        self._build_skill_tree()

    def _get_mean_cluster_size(self, partition):
        """计算一个分区中社区的平均大小。"""
        if not partition:
            return 0
        num_clusters = len(set(partition.values()))
        if num_clusters == 0:
            return 0
        return len(partition) / num_clusters

    def _build_skill_tree(self):
        """
        将Louvain分区转换为一个明确的技能树结构。
        技能被定义为在某一层级中，从一个社区导航到另一个相邻社区。
        """
        self.skill_tree = {}
        for level, partition in enumerate(self.partitions):
            level_id = len(self.partitions) - level # L, L-1, ..., 1
            self.skill_tree[level_id] = {}
            
            # 找出该层级的所有社区
            clusters = {}
            for node, cluster_id in partition.items():
                if cluster_id not in clusters:
                    clusters[cluster_id] = []
                clusters[cluster_id].append(node)
            
            # 对于每个社区，找出其邻居社区，并定义技能
            for cluster_id, nodes in clusters.items():
                neighbors = self._get_cluster_neighbors(nodes, partition)
                self.skill_tree[level_id][cluster_id] = {
                    'nodes': nodes,
                    'neighbors': neighbors,
                    'skills': {neighbor_id: f"Z_{level_id}_({cluster_id}->{neighbor_id})" for neighbor_id in neighbors}
                }
        main_logger.info("技能树构建完成。")

    def _get_cluster_neighbors(self, cluster_nodes, partition):
        """找到一个社区的所有邻居社区。"""
        neighbors = set()
        for node in cluster_nodes:
            for neighbor in self.graph.neighbors(node):
                if neighbor in partition and partition[neighbor] != partition[node]:
                    neighbors.add(partition[neighbor])
        return list(neighbors)

    def find_community(self, state, level):
        """
        找到一个状态在指定层级所属的社区ID。

        参数:
            state: 全局状态。
            level (int): 技能层级 (从L到1)。

        返回:
            int: 社区ID，如果找不到则返回None。
        """
        state_tuple = tuple(state.flatten())
        if state_tuple not in self.state_to_node:
            return None # 该状态未在图中出现
        
        node_id = self.state_to_node[state_tuple]
        
        # level 是从 L 到 1, self.partitions 的索引是从 0 到 L-1
        partition_index = len(self.partitions) - level
        if 0 <= partition_index < len(self.partitions):
            partition = self.partitions[partition_index]
            if node_id in partition:
                return partition[node_id]
        
        return None

    def get_available_skills(self, state, level):
        """
        获取在当前状态和层级下可用的技能。

        参数:
            state: 全局状态。
            level (int): 技能层级。

        返回:
            dict: 可用技能的字典 {neighbor_id: skill_name}。
        """
        community_id = self.find_community(state, level)
        if community_id is not None and level in self.skill_tree and community_id in self.skill_tree[level]:
            return self.skill_tree[level][community_id]['skills']
        return {}
