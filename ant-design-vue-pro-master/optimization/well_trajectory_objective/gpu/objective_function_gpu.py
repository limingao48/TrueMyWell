"""
GPU版本的井轨迹目标函数
支持批量并行计算多个井眼轨迹的目标函数值

使用PyTorch在GPU上实现，充分利用并行计算能力
"""

import torch
import numpy as np
from typing import Tuple, Optional, List, Dict, Any
from ..config import WellTrajectoryConfig
from .well_calculator_gpu import WellPathCalculatorGPU
from ..obstacle_detection import WellObstacleDetector


class WellTrajectoryObjectiveGPU:
    """GPU版本的井轨迹目标函数，支持批量计算"""
    
    def __init__(self, 
                 config: WellTrajectoryConfig,
                 well_obstacles: Optional[List[WellObstacleDetector]] = None,
                 device: torch.device = None,
                 n_points: int = 50):
        """
        初始化GPU目标函数
        
        Args:
            config: 井轨迹配置对象
            well_obstacles: 多个井轨迹障碍物检测器列表（可选）
            device: GPU设备，如果为None则自动选择
            n_points: 每段的轨迹点数（默认50）
        """
        self.config = config
        # 原始的障碍井检测器（CPU 版本对象列表）
        self.well_obstacles = well_obstacles or []
        self.n_points = n_points
        
        # 设备设置
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = device
        
        # 创建GPU计算器
        self.calculator = WellPathCalculatorGPU(config, device=self.device, n_points=n_points)
        
        # 将配置参数移到GPU
        self.E_target = torch.tensor(config.E_target, device=self.device, dtype=torch.float32)
        self.N_target = torch.tensor(config.N_target, device=self.device, dtype=torch.float32)
        self.D_target = torch.tensor(config.D_target, device=self.device, dtype=torch.float32)
        self.target_deviation_threshold = config.target_deviation_threshold
        self.target_deviation_penalty = config.target_deviation_penalty

        # 预处理障碍井数据到 GPU，用于分离系数计算
        # self.obstacle_points: (n_wells, max_len, 3)
        # self.obstacle_mask:   (n_wells, max_len)  True 表示有效点
        # self.obstacle_safety_radius: (n_wells,)
        self.obstacle_points: Optional[torch.Tensor] = None
        self.obstacle_mask: Optional[torch.Tensor] = None
        self.obstacle_safety_radius: Optional[torch.Tensor] = None

        if self.well_obstacles:
            obstacle_arrays: List[np.ndarray] = []
            safety_radii: List[float] = []

            for obs in self.well_obstacles:
                if obs is None:
                    continue

                pts: Optional[np.ndarray] = None

                # 优先使用处理后的井轨迹点 (N, 3)
                if getattr(obs, "well_trajectory", None) is not None:
                    pts = np.asarray(obs.well_trajectory, dtype=np.float32)
                # 其次尝试由井段还原为点集
                elif getattr(obs, "well_segments", None) is not None and obs.well_segments:
                    seg_points: List[np.ndarray] = []
                    for seg in obs.well_segments:
                        seg_points.append(np.asarray(seg["start"], dtype=np.float32))
                    # 补上最后一个 end 点
                    seg_points.append(np.asarray(obs.well_segments[-1]["end"], dtype=np.float32))
                    pts = np.stack(seg_points, axis=0).astype(np.float32)

                if pts is None or pts.size == 0:
                    continue

                obstacle_arrays.append(pts)
                safety_radii.append(float(getattr(obs, "safety_radius", 10.0)))

            if obstacle_arrays:
                max_len = max(arr.shape[0] for arr in obstacle_arrays)
                n_wells = len(obstacle_arrays)
                padded = np.zeros((n_wells, max_len, 3), dtype=np.float32)
                mask = np.zeros((n_wells, max_len), dtype=bool)

                for i, arr in enumerate(obstacle_arrays):
                    length = arr.shape[0]
                    padded[i, :length, :] = arr
                    mask[i, :length] = True

                self.obstacle_points = torch.tensor(padded, device=self.device, dtype=torch.float32)
                self.obstacle_mask = torch.tensor(mask, device=self.device, dtype=torch.bool)
                self.obstacle_safety_radius = torch.tensor(
                    safety_radii, device=self.device, dtype=torch.float32
                )
        
        print(f"✅ GPU目标函数已初始化，设备: {self.device}")
        if self.obstacle_points is not None:
            print(f"   包含 {self.obstacle_points.shape[0]} 个井轨迹障碍物（用于GPU分离系数计算）")
    
    def calculate_objective_batch(self, params: torch.Tensor) -> torch.Tensor:
        """
        批量计算目标函数值（GPU版本）
        
        Args:
            params: (batch_size, 8) 参数张量，已在GPU上
                   [D_kop, alpha1, alpha2, phi1, phi2, R1, R2, D_turn_kop]
                   角度单位为度
            
        Returns:
            fitness: (batch_size,) 目标函数值（适应度值）
        """
        batch_size = params.shape[0]
        
        # 快速验证：检查造斜点深度不能大于转向点深度
        invalid_mask = params[:, 0] > params[:, 7]
        
        # 计算井轨迹坐标
        result = self.calculator.calculate_coordinates_batch(params)
        points, total_length, flag, loss = result
        
        if points is None:
            return torch.full((batch_size,), 1e20, device=self.device, dtype=torch.float32)
        
        x, y, z = points
        
        # 更新无效标志
        invalid_mask = invalid_mask | ~flag | (loss > 0)
        
        # 计算目标偏差（使用终点）
        final_E = x[:, -1]  # (batch_size,)
        final_N = y[:, -1]
        final_D = z[:, -1]
        
        target_deviation = torch.sqrt(
            (final_E - self.E_target) ** 2 +
            (final_N - self.N_target) ** 2 +
            (final_D - self.D_target) ** 2
        )
        
        # 目标偏差惩罚
        target_deviation = torch.where(
            target_deviation > self.target_deviation_threshold,
            target_deviation * self.target_deviation_penalty,
            target_deviation
        )
        
        # 碰撞检测惩罚（简化版本，批量检测）
        collision_penalty = self._calculate_collision_penalty_batch(x, y, z)
        
        # 总目标函数值
        fitness = target_deviation + total_length + collision_penalty
        
        # 设置无效解的适应度
        fitness = torch.where(invalid_mask, torch.tensor(1e20, device=self.device, dtype=torch.float32), fitness)
        
        return fitness
    
    def _calculate_collision_penalty_batch(self, 
                                          x: torch.Tensor,
                                          y: torch.Tensor,
                                          z: torch.Tensor) -> torch.Tensor:
        """
        批量计算碰撞惩罚（GPU 版本，基于井间分离系数）
        
        思路：
        - 对每个候选井轨迹（batch 内一条井），计算到每一口障碍井轨迹的最小距离 d_min
        - 使用安全半径 safety_radius 计算分离系数 SF = d_min / safety_radius
        - 如果任意一口井的 SF < 1，则认为发生碰撞，惩罚设为 1e20
        
        说明：
        - 为控制显存，障碍井在 __init__ 中预处理为固定长度的点集，并使用 mask 标记有效点
        - 这里使用“点到点”近似距离来估计井间最小距离，对 10 口以内的障碍井是可行的
        
        Args:
            x, y, z: (batch_size, n_points) 轨迹坐标（当前优化井）
            
        Returns:
            penalty: (batch_size,) 碰撞惩罚值
        """
        batch_size = x.shape[0]
        penalty = torch.zeros(batch_size, device=self.device, dtype=torch.float32)

        # 没有障碍井，直接返回 0 惩罚
        if self.obstacle_points is None or self.obstacle_safety_radius is None:
            return penalty

        # 当前井轨迹点 (batch_size, n_points, 3)
        points = torch.stack([x, y, z], dim=2)  # (B, P, 3)

        # 障碍井点集 (W, Q, 3)，mask (W, Q)
        obs_pts = self.obstacle_points        # (W, Q, 3)
        obs_mask = self.obstacle_mask         # (W, Q)
        safety_r = self.obstacle_safety_radius  # (W,)

        B, P, _ = points.shape
        W, Q, _ = obs_pts.shape

        # 扩展维度以便广播：
        # points_bw: (B, W, P, 1, 3)
        # obs_bw:    (B, W, 1, Q, 3)
        points_bw = points.unsqueeze(1).unsqueeze(3)      # (B, 1, P, 1, 3)
        points_bw = points_bw.expand(-1, W, -1, 1, -1)    # (B, W, P, 1, 3)
        obs_bw = obs_pts.unsqueeze(0).unsqueeze(2)        # (1, W, 1, Q, 3)
        obs_bw = obs_bw.expand(B, -1, P, -1, -1)          # (B, W, P, Q, 3)

        # 计算点对点欧氏距离
        diff = points_bw - obs_bw                        # (B, W, P, Q, 3)
        dist_sq = (diff * diff).sum(dim=-1)              # (B, W, P, Q)
        dist = torch.sqrt(dist_sq + 1e-9)                # 避免 sqrt(0)

        # 应用障碍点 mask：无效点距离设为一个很大值
        obs_mask_bw = obs_mask.unsqueeze(0).unsqueeze(2)  # (1, W, 1, Q)
        obs_mask_bw = obs_mask_bw.expand(B, -1, P, -1)    # (B, W, P, Q)

        large_val = torch.tensor(1e9, device=self.device, dtype=torch.float32)
        dist = torch.where(obs_mask_bw, dist, large_val)

        # 对每个 (B, W) 取最小距离：在 P, Q 维度上取最小值
        # min_dist_bw: (B, W) 每条候选井对每口障碍井的最小距离
        min_dist_bw, _ = dist.view(B, W, -1).min(dim=-1)

        # 分离系数 SF = d_min / safety_radius
        # safety_r: (W,) -> (1, W)
        sf = min_dist_bw / safety_r.view(1, W)           # (B, W)

        # 对每条井，取最小分离系数
        sf_min, _ = sf.min(dim=1)                        # (B,)

        # 如果最小分离系数 < 1，认为发生碰撞，惩罚设为 1e20
        collision_mask = sf_min < 1.0
        penalty = torch.where(collision_mask, torch.tensor(1e20, device=self.device, dtype=torch.float32), penalty)

        return penalty
    
    def calculate_objective(self, position_tuple: List[float]) -> float:
        """
        单个参数计算（兼容接口）
        
        注意：对于单个计算，建议使用CPU版本以获得完整功能（包括精确碰撞检测）
        批量计算时使用 calculate_objective_batch
        
        Args:
            position_tuple: 位置参数 [D_kop, alpha1, alpha2, phi1, phi2, R1, R2, D_turn_kop]
            
        Returns:
            float: 目标函数值
        """
        # 转换为张量并移到GPU
        params = torch.tensor([position_tuple], device=self.device, dtype=torch.float32)
        fitness = self.calculate_objective_batch(params)
        return fitness.item()
    
    def calculate_objective_batch_with_info(self, 
                                           params: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        批量计算目标函数值并返回详细信息
        
        Args:
            params: (batch_size, 8) 参数张量
            
        Returns:
            Dict包含:
                - fitness: (batch_size,) 目标函数值
                - total_length: (batch_size,) 总长度
                - target_deviation: (batch_size,) 目标偏差
                - collision_penalty: (batch_size,) 碰撞惩罚
                - is_valid: (batch_size,) 是否有效
                - final_points: (batch_size, 3) 终点坐标
        """
        batch_size = params.shape[0]
        
        # 计算轨迹
        result = self.calculator.calculate_coordinates_batch(params)
        points, total_length, flag, loss = result
        
        if points is None:
            return {
                'fitness': torch.full((batch_size,), 1e20, device=self.device, dtype=torch.float32),
                'total_length': torch.zeros(batch_size, device=self.device, dtype=torch.float32),
                'target_deviation': torch.full((batch_size,), 1e20, device=self.device, dtype=torch.float32),
                'collision_penalty': torch.zeros(batch_size, device=self.device, dtype=torch.float32),
                'is_valid': torch.zeros(batch_size, dtype=torch.bool, device=self.device),
                'final_points': torch.zeros(batch_size, 3, device=self.device, dtype=torch.float32)
            }
        
        x, y, z = points
        
        # 检查无效情况
        invalid_mask = (params[:, 0] > params[:, 7]) | ~flag | (loss > 0)
        
        # 计算目标偏差
        final_E = x[:, -1]
        final_N = y[:, -1]
        final_D = z[:, -1]
        
        final_points = torch.stack([final_E, final_N, final_D], dim=1)  # (batch_size, 3)
        
        target_deviation = torch.sqrt(
            (final_E - self.E_target) ** 2 +
            (final_N - self.N_target) ** 2 +
            (final_D - self.D_target) ** 2
        )
        
        # 目标偏差惩罚
        target_deviation_penalized = torch.where(
            target_deviation > self.target_deviation_threshold,
            target_deviation * self.target_deviation_penalty,
            target_deviation
        )
        
        # 碰撞惩罚
        collision_penalty = self._calculate_collision_penalty_batch(x, y, z)
        
        # 总适应度
        fitness = target_deviation_penalized + total_length + collision_penalty
        fitness = torch.where(invalid_mask, torch.tensor(1e20, device=self.device, dtype=torch.float32), fitness)
        
        return {
            'fitness': fitness,
            'total_length': total_length,
            'target_deviation': target_deviation,
            'collision_penalty': collision_penalty,
            'is_valid': ~invalid_mask,
            'final_points': final_points
        }
    
    def get_trajectory_info_batch(self, params: torch.Tensor) -> List[Dict[str, Any]]:
        """
        批量获取轨迹详细信息
        
        Args:
            params: (batch_size, 8) 参数张量
            
        Returns:
            List[Dict]: 每个轨迹的详细信息列表
        """
        batch_size = params.shape[0]
        info_list = []
        
        # 计算轨迹
        result = self.calculator.calculate_coordinates_batch(params)
        points, total_length, flag, loss = result
        
        if points is None:
            return [{'success': False, 'error': 'Calculation failed'} for _ in range(batch_size)]
        
        x, y, z = points
        
        # 转换为numpy以便处理
        x_np = x.detach().cpu().numpy()
        y_np = y.detach().cpu().numpy()
        z_np = z.detach().cpu().numpy()
        total_length_np = total_length.detach().cpu().numpy()
        flag_np = flag.detach().cpu().numpy()
        
        for i in range(batch_size):
            if not flag_np[i]:
                info_list.append({
                    'success': False,
                    'error': 'Invalid parameters or calculation failed',
                    'loss': loss[i].item() if isinstance(loss, torch.Tensor) else loss
                })
                continue
            
            final_point = (x_np[i, -1], y_np[i, -1], z_np[i, -1])
            target_deviation = np.sqrt(
                (final_point[0] - self.config.E_target) ** 2 +
                (final_point[1] - self.config.N_target) ** 2 +
                (final_point[2] - self.config.D_target) ** 2
            )
            
            info_list.append({
                'success': True,
                'trajectory': (x_np[i], y_np[i], z_np[i]),
                'total_length': float(total_length_np[i]),
                'final_point': final_point,
                'target_deviation': float(target_deviation),
                'loss': loss[i].item() if isinstance(loss, torch.Tensor) else loss
            })
        
        return info_list


def create_gpu_objective_function(config: WellTrajectoryConfig,
                                  well_obstacles: Optional[List[WellObstacleDetector]] = None,
                                  device: torch.device = None,
                                  n_points: int = 50) -> WellTrajectoryObjectiveGPU:
    """
    创建GPU目标函数实例
    
    Args:
        config: 井轨迹配置对象
        well_obstacles: 多个井轨迹障碍物检测器列表（可选）
        device: GPU设备，如果为None则自动选择
        n_points: 每段的轨迹点数（默认50）
        
    Returns:
        WellTrajectoryObjectiveGPU: GPU目标函数实例
    """
    return WellTrajectoryObjectiveGPU(config, well_obstacles, device, n_points)

