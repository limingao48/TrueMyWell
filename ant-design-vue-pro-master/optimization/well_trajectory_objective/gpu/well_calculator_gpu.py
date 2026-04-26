"""
GPU版本的井轨迹计算器
使用PyTorch在GPU上批量并行计算多个井眼轨迹

支持：
- 批量计算多个井眼轨迹
- 完整的轨迹坐标计算（垂直段、造斜段、切线段、转向段）
- 完整的目标函数计算（轨迹长度、目标偏差、碰撞检测等）
"""

import torch
import numpy as np
from typing import Tuple, Optional, List, Dict, Any
from ..config import WellTrajectoryConfig


class WellPathCalculatorGPU:
    """GPU版本的井轨迹计算器，支持批量计算"""
    
    def __init__(self, config: WellTrajectoryConfig, device: torch.device = None, n_points: int = 50):
        """
        初始化GPU计算器
        
        Args:
            config: 井轨迹配置对象
            device: GPU设备，如果为None则自动选择
            n_points: 每段的轨迹点数（默认50）
        """
        self.config = config
        self.n_points = n_points
        
        # 设备设置
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = device
        
        # 将配置参数移到GPU
        self.E_target = torch.tensor(config.E_target, device=self.device, dtype=torch.float32)
        self.N_target = torch.tensor(config.N_target, device=self.device, dtype=torch.float32)
        self.D_target = torch.tensor(config.D_target, device=self.device, dtype=torch.float32)
        self.E_wellhead = torch.tensor(config.E_wellhead, device=self.device, dtype=torch.float32)
        self.N_wellhead = torch.tensor(config.N_wellhead, device=self.device, dtype=torch.float32)
        self.TOLERANCE = config.TOLERANCE
        
        print(f"✅ GPU计算器已初始化，设备: {self.device}, 每段{n_points}个点")
    
    def calculate_lengths_batch(self, 
                                D_kop: torch.Tensor,
                                alpha_1: torch.Tensor,
                                alpha_2: torch.Tensor,
                                phi_1: torch.Tensor,
                                phi_2: torch.Tensor,
                                R_1: torch.Tensor,
                                R_2: torch.Tensor,
                                D_turn_kop: torch.Tensor) -> Tuple[Dict[str, torch.Tensor], torch.Tensor]:
        """
        批量计算各段长度
        
        Args:
            D_kop: (batch_size,) 造斜点深度
            alpha_1: (batch_size,) 第一造斜角（弧度）
            alpha_2: (batch_size,) 第二造斜角（弧度）
            phi_1: (batch_size,) 第一方位角（弧度）
            phi_2: (batch_size,) 第二方位角（弧度）
            R_1: (batch_size,) 第一造斜半径
            R_2: (batch_size,) 第二造斜半径
            D_turn_kop: (batch_size,) 转向点深度
            
        Returns:
            Tuple[长度字典, 损失值]
        """
        batch_size = D_kop.shape[0]
        
        # 计算转向角 gamma
        cos_gamma = (torch.cos(alpha_1) * torch.cos(alpha_2) + 
                    torch.sin(alpha_1) * torch.sin(alpha_2) * torch.cos(phi_2 - phi_1))
        cos_gamma = torch.clamp(cos_gamma, -1.0, 1.0)
        gamma = torch.acos(cos_gamma)
        gamma_half = gamma / 2
        
        # 计算各段长度
        delta_D_build = R_1 * (1 - torch.cos(alpha_1))
        remaining_D = D_turn_kop - D_kop - delta_D_build
        
        # 计算RF因子
        RF = torch.where(gamma != 0, 2 * torch.tan(gamma_half) / gamma, torch.ones_like(gamma))
        delta_D_turn = R_2 * (torch.cos(alpha_1) + torch.cos(alpha_2)) * RF / 2
        
        # 第一切线段长度（迭代求解）
        cos_alpha1 = torch.cos(alpha_1)
        length_tangent1 = remaining_D / torch.clamp(cos_alpha1, min=1e-6)
        
        # 快速迭代（最多10次）
        max_iterations = 10
        for _ in range(max_iterations):
            final_D = D_kop + delta_D_build + length_tangent1 * cos_alpha1
            depth_error = final_D - D_turn_kop
            
            # 检查是否收敛
            if torch.all(torch.abs(depth_error) < self.TOLERANCE):
                break
            
            # 更新长度
            length_tangent1 = length_tangent1 - depth_error / torch.clamp(cos_alpha1, min=1e-6)
            length_tangent1 = torch.clamp(length_tangent1, min=0.0)
        
        # 第二切线段长度
        remaining_to_target = self.D_target - D_turn_kop - delta_D_turn
        cos_alpha2 = torch.cos(alpha_2)
        length_tangent2 = remaining_to_target / torch.clamp(cos_alpha2, min=1e-6)
        
        lengths = {
            'vertical': D_kop,
            'build': R_1 * alpha_1,
            'tangent1': length_tangent1,
            'turn': R_2 * gamma,
            'tangent2': length_tangent2
        }
        
        # 计算损失值（无效情况）
        loss = torch.zeros(batch_size, device=self.device, dtype=torch.float32)
        invalid_mask = (remaining_D < 0) | (remaining_to_target < 0) | (length_tangent1 < 0) | (length_tangent2 < 0)
        loss = torch.where(invalid_mask, torch.tensor(1e6, device=self.device), loss)
        
        return lengths, loss
    
    def calculate_build_coords_batch(self,
                                    alpha_start: torch.Tensor,
                                    alpha_end: torch.Tensor,
                                    phi: torch.Tensor,
                                    R: torch.Tensor,
                                    length: torch.Tensor,
                                    start_pos: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        批量计算造斜段坐标
        
        Args:
            alpha_start: (batch_size,) 起始造斜角（弧度）
            alpha_end: (batch_size,) 结束造斜角（弧度）
            phi: (batch_size,) 方位角（弧度）
            R: (batch_size,) 造斜半径
            length: (batch_size,) 段长度
            start_pos: (batch_size, 3) 起始位置 [E, N, D]
            
        Returns:
            Tuple[x, y, z] 每个都是 (batch_size, n_points) 形状
        """
        batch_size = alpha_start.shape[0]
        
        # 生成角度序列 (batch_size, n_points)
        alpha = torch.linspace(0, 1, self.n_points, device=self.device).unsqueeze(0)  # (1, n_points)
        alpha = alpha_start.unsqueeze(1) + alpha * (alpha_end - alpha_start).unsqueeze(1)  # (batch_size, n_points)
        
        # 计算增量（向量化）
        cos_alpha_prev = torch.cos(alpha[:, :-1])  # (batch_size, n_points-1)
        cos_alpha_curr = torch.cos(alpha[:, 1:])
        sin_alpha_prev = torch.sin(alpha[:, :-1])
        sin_alpha_curr = torch.sin(alpha[:, 1:])
        
        # 广播phi和R
        cos_phi = torch.cos(phi).unsqueeze(1)  # (batch_size, 1)
        sin_phi = torch.sin(phi).unsqueeze(1)
        R_expanded = R.unsqueeze(1)  # (batch_size, 1)
        
        # 计算增量
        delta_N = R_expanded * (cos_alpha_prev - cos_alpha_curr) * cos_phi  # (batch_size, n_points-1)
        delta_E = R_expanded * (cos_alpha_prev - cos_alpha_curr) * sin_phi
        delta_V = R_expanded * (sin_alpha_curr - sin_alpha_prev)
        
        # 累积求和
        x = torch.zeros(batch_size, self.n_points, device=self.device, dtype=torch.float32)
        y = torch.zeros(batch_size, self.n_points, device=self.device, dtype=torch.float32)
        z = torch.zeros(batch_size, self.n_points, device=self.device, dtype=torch.float32)
        
        x[:, 1:] = torch.cumsum(delta_E, dim=1)
        y[:, 1:] = torch.cumsum(delta_N, dim=1)
        z[:, 1:] = torch.cumsum(delta_V, dim=1)
        
        # 加上起始位置
        x = x + start_pos[:, 0:1]  # (batch_size, n_points)
        y = y + start_pos[:, 1:2]
        z = z + start_pos[:, 2:3]
        
        return x, y, z
    
    def calculate_tangent_coords_batch(self,
                                      alpha: torch.Tensor,
                                      phi: torch.Tensor,
                                      length: torch.Tensor,
                                      start_pos: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        批量计算切线段坐标
        
        Args:
            alpha: (batch_size,) 造斜角（弧度）
            phi: (batch_size,) 方位角（弧度）
            length: (batch_size,) 段长度
            start_pos: (batch_size, 3) 起始位置 [E, N, D]
            
        Returns:
            Tuple[x, y, z] 每个都是 (batch_size, n_points) 形状
        """
        batch_size = alpha.shape[0]
        
        # 计算单位增量
        dl = length.unsqueeze(1) / (self.n_points - 1)  # (batch_size, 1)
        
        # 计算增量分量
        sin_alpha = torch.sin(alpha).unsqueeze(1)  # (batch_size, 1)
        cos_alpha = torch.cos(alpha).unsqueeze(1)
        sin_phi = torch.sin(phi).unsqueeze(1)
        cos_phi = torch.cos(phi).unsqueeze(1)
        
        delta_N = dl * sin_alpha * cos_phi  # (batch_size, 1)
        delta_E = dl * sin_alpha * sin_phi
        delta_V = dl * cos_alpha
        
        # 生成坐标序列
        indices = torch.arange(self.n_points, device=self.device, dtype=torch.float32).unsqueeze(0)  # (1, n_points)
        
        x = indices * delta_E + start_pos[:, 0:1]  # (batch_size, n_points)
        y = indices * delta_N + start_pos[:, 1:2]
        z = indices * delta_V + start_pos[:, 2:3]
        
        return x, y, z
    
    def calculate_turn_coords_batch(self,
                                   alpha_start: torch.Tensor,
                                   alpha_end: torch.Tensor,
                                   phi_start: torch.Tensor,
                                   phi_end: torch.Tensor,
                                   R: torch.Tensor,
                                   length: torch.Tensor,
                                   start_pos: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        批量计算转向段坐标
        
        Args:
            alpha_start: (batch_size,) 起始造斜角（弧度）
            alpha_end: (batch_size,) 结束造斜角（弧度）
            phi_start: (batch_size,) 起始方位角（弧度）
            phi_end: (batch_size,) 结束方位角（弧度）
            R: (batch_size,) 转向半径
            length: (batch_size,) 段长度
            start_pos: (batch_size, 3) 起始位置 [E, N, D]
            
        Returns:
            Tuple[x, y, z] 每个都是 (batch_size, n_points) 形状
        """
        batch_size = alpha_start.shape[0]
        
        # 生成角度序列
        t = torch.linspace(0, 1, self.n_points, device=self.device).unsqueeze(0)  # (1, n_points)
        alpha = alpha_start.unsqueeze(1) + t * (alpha_end - alpha_start).unsqueeze(1)  # (batch_size, n_points)
        phi = phi_start.unsqueeze(1) + t * (phi_end - phi_start).unsqueeze(1)
        
        # 计算增量
        dl = length.unsqueeze(1) / (self.n_points - 1)  # (batch_size, 1)
        
        # 平均角度
        alpha_avg = 0.5 * (alpha[:, :-1] + alpha[:, 1:])  # (batch_size, n_points-1)
        phi_avg = 0.5 * (phi[:, :-1] + phi[:, 1:])
        
        # 计算增量
        delta_N = dl * torch.sin(alpha_avg) * torch.cos(phi_avg)  # (batch_size, n_points-1)
        delta_E = dl * torch.sin(alpha_avg) * torch.sin(phi_avg)
        delta_V = dl * torch.cos(alpha_avg)
        
        # 累积求和
        x = torch.zeros(batch_size, self.n_points, device=self.device, dtype=torch.float32)
        y = torch.zeros(batch_size, self.n_points, device=self.device, dtype=torch.float32)
        z = torch.zeros(batch_size, self.n_points, device=self.device, dtype=torch.float32)
        
        x[:, 1:] = torch.cumsum(delta_E, dim=1)
        y[:, 1:] = torch.cumsum(delta_N, dim=1)
        z[:, 1:] = torch.cumsum(delta_V, dim=1)
        
        # 加上起始位置
        x = x + start_pos[:, 0:1]
        y = y + start_pos[:, 1:2]
        z = z + start_pos[:, 2:3]
        
        return x, y, z
    
    def calculate_coordinates_batch(self, params: torch.Tensor) -> Tuple[Optional[Tuple[torch.Tensor, torch.Tensor, torch.Tensor]], 
                                                                        torch.Tensor, 
                                                                        torch.Tensor, 
                                                                        torch.Tensor]:
        """
        批量计算完整井轨迹坐标
        
        Args:
            params: (batch_size, 8) 参数张量 [D_kop, alpha1, alpha2, phi1, phi2, R1, R2, D_turn_kop]
                   角度单位为度
            
        Returns:
            Tuple[坐标元组(x,y,z), 总长度, 是否成功标志, 损失值]
            - x, y, z: 每个都是 (batch_size, total_points) 形状
            - total_length: (batch_size,)
            - flag: (batch_size,) bool类型
            - loss: (batch_size,)
        """
        batch_size = params.shape[0]
        
        # 参数提取并转换为弧度
        D_kop = params[:, 0]
        alpha1 = torch.deg2rad(params[:, 1])
        alpha2 = torch.deg2rad(params[:, 2])
        phi1 = torch.deg2rad(params[:, 3])
        phi2 = torch.deg2rad(params[:, 4])
        R1 = params[:, 5]
        R2 = params[:, 6]
        D_turn_kop = params[:, 7]
        
        # 计算各段长度
        lengths, loss = self.calculate_lengths_batch(D_kop, alpha1, alpha2, phi1, phi2, R1, R2, D_turn_kop)
        
        # 检查无效情况
        invalid_mask = loss > 0
        if torch.all(invalid_mask):
            # 所有都无效，返回空结果
            total_points = self.n_points * 5  # 5段
            x = torch.zeros(batch_size, total_points, device=self.device, dtype=torch.float32)
            y = torch.zeros(batch_size, total_points, device=self.device, dtype=torch.float32)
            z = torch.zeros(batch_size, total_points, device=self.device, dtype=torch.float32)
            total_length = torch.zeros(batch_size, device=self.device, dtype=torch.float32)
            flag = torch.zeros(batch_size, dtype=torch.bool, device=self.device)
            return (x, y, z), total_length, flag, loss
        
        # 垂直段
        z_vertical = torch.linspace(0, 1, self.n_points, device=self.device).unsqueeze(0)  # (1, n_points)
        z_vertical = z_vertical * D_kop.unsqueeze(1)  # (batch_size, n_points)
        x_vertical = torch.full((batch_size, self.n_points), self.E_wellhead.item(), device=self.device, dtype=torch.float32)
        y_vertical = torch.full((batch_size, self.n_points), self.N_wellhead.item(), device=self.device, dtype=torch.float32)
        
        # 垂直段结束位置
        vertical_end = torch.stack([
            x_vertical[:, -1],
            y_vertical[:, -1],
            z_vertical[:, -1]
        ], dim=1)  # (batch_size, 3)
        
        # 造斜段
        length_build = lengths['build']
        x_build, y_build, z_build = self.calculate_build_coords_batch(
            torch.zeros_like(alpha1), alpha1, phi1, R1, length_build, vertical_end
        )
        
        # 造斜段结束位置
        build_end = torch.stack([
            x_build[:, -1],
            y_build[:, -1],
            z_build[:, -1]
        ], dim=1)  # (batch_size, 3)
        
        # 第一切线段
        length_tangent1 = lengths['tangent1']
        x_tangent, y_tangent, z_tangent = self.calculate_tangent_coords_batch(
            alpha1, phi1, length_tangent1, build_end
        )
        
        # 第一切线段结束位置
        tangent1_end = torch.stack([
            x_tangent[:, -1],
            y_tangent[:, -1],
            z_tangent[:, -1]
        ], dim=1)  # (batch_size, 3)
        
        # 转向段
        length_turn = lengths['turn']
        x_turn, y_turn, z_turn = self.calculate_turn_coords_batch(
            alpha1, alpha2, phi1, phi2, R2, length_turn, tangent1_end
        )
        
        # 转向段结束位置
        turn_end = torch.stack([
            x_turn[:, -1],
            y_turn[:, -1],
            z_turn[:, -1]
        ], dim=1)  # (batch_size, 3)
        
        # 第二切线段
        length_tangent2 = lengths['tangent2']
        x_tangent2, y_tangent2, z_tangent2 = self.calculate_tangent_coords_batch(
            alpha2, phi2, length_tangent2, turn_end
        )
        
        # 合并所有段
        x = torch.cat([x_vertical, x_build, x_tangent, x_turn, x_tangent2], dim=1)  # (batch_size, total_points)
        y = torch.cat([y_vertical, y_build, y_tangent, y_turn, y_tangent2], dim=1)
        z = torch.cat([z_vertical, z_build, z_tangent, z_turn, z_tangent2], dim=1)
        
        # 计算总长度
        total_length = (lengths['vertical'] + lengths['build'] + 
                       lengths['tangent1'] + lengths['turn'] + lengths['tangent2'])
        
        # 成功标志
        flag = ~invalid_mask
        
        return (x, y, z), total_length, flag, loss

