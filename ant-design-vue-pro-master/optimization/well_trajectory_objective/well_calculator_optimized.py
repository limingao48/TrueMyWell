"""
优化版本的井轨迹计算器
使用向量化计算和Numba JIT加速
"""

import numpy as np
from typing import Tuple, Optional, Dict, Any
from .config import WellTrajectoryConfig

# 尝试导入Numba，如果没有则使用纯numpy
try:
    from numba import jit, prange
    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False
    print("⚠️  Numba未安装，将使用纯numpy版本（速度较慢）")


class WellPathCalculatorOptimized:
    """优化版本的井轨迹计算器"""
    
    def __init__(self, config: WellTrajectoryConfig, use_numba: bool = True, n_points: int = 50):
        """
        初始化优化计算器
        
        Args:
            config: 井轨迹配置对象
            use_numba: 是否使用Numba加速（如果可用）
            n_points: 每段的轨迹点数（默认50，比原来的100少一半）
        """
        self.config = config
        self.use_numba = use_numba and HAS_NUMBA
        self.n_points = n_points
        
        if self.use_numba:
            print(f"✅ 使用Numba加速，每段{n_points}个点")
        else:
            print(f"⚠️  使用纯numpy版本，每段{n_points}个点")
    
    def calculate_lengths(self, D_kop: float, alpha_1: float, alpha_2: float, 
                         phi_1: float, phi_2: float, R_1: float, R_2: float, 
                         D_turn_kop: float) -> Tuple[Optional[Dict[str, float]], float]:
        """
        计算各段长度（优化版本：减少迭代次数）
        """
        gamma = np.arccos(
            np.clip(
                np.cos(alpha_1) * np.cos(alpha_2) +
                np.sin(alpha_1) * np.sin(alpha_2) * np.cos(phi_2 - phi_1),
                -1.0, 1.0
            )
        )
        gamma_half = gamma / 2

        delta_D_build = R_1 * (1 - np.cos(alpha_1))
        remaining_D = D_turn_kop - D_kop - delta_D_build

        if remaining_D < 0:
            return None, remaining_D * (-1000)

        RF = 2 * np.tan(gamma_half) / gamma if gamma != 0 else 1.0
        delta_D_turn = R_2 * (np.cos(alpha_1) + np.cos(alpha_2)) * RF / 2

        # 优化：直接计算，减少迭代
        # 第一切线段长度的精确计算
        cos_alpha1 = np.cos(alpha_1)
        if cos_alpha1 <= 0:
            return None, -1000
        
        # 使用解析解而非迭代（如果可能）
        lengths = {
            'vertical': D_kop,
            'build': R_1 * alpha_1,
            'tangent1': remaining_D / cos_alpha1,
            'turn': R_2 * gamma
        }
        
        # 快速迭代（最多10次，而非500次）
        max_iterations = 10
        for _ in range(max_iterations):
            final_D = D_kop + delta_D_build + lengths['tangent1'] * cos_alpha1
            depth_error = final_D - D_turn_kop

            if abs(depth_error) < self.config.TOLERANCE:
                break

            lengths['tangent1'] -= depth_error / cos_alpha1
            if lengths['tangent1'] < 0:
                lengths['tangent1'] = 0
                break

        remaining_to_target = self.config.D_target - D_turn_kop - delta_D_turn
        if remaining_to_target < 0:
            return None, remaining_to_target * (-1000)

        lengths['tangent2'] = remaining_to_target / np.cos(alpha_2)

        return lengths, 0
    
    def calculate_build_coords_vectorized(self, alpha_start: float, alpha_end: float, 
                                         phi: float, R: float, length: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """向量化版本的造斜段坐标计算"""
        n_points = self.n_points
        alpha = np.linspace(alpha_start, alpha_end, n_points)
        
        # 向量化计算所有增量
        cos_alpha_prev = np.cos(alpha[:-1])
        cos_alpha_curr = np.cos(alpha[1:])
        sin_alpha_prev = np.sin(alpha[:-1])
        sin_alpha_curr = np.sin(alpha[1:])
        
        delta_N = R * (cos_alpha_prev - cos_alpha_curr) * np.cos(phi)
        delta_E = R * (cos_alpha_prev - cos_alpha_curr) * np.sin(phi)
        delta_V = R * (sin_alpha_curr - sin_alpha_prev)
        
        # 累积求和
        x = np.zeros(n_points)
        y = np.zeros(n_points)
        z = np.zeros(n_points)
        x[1:] = np.cumsum(delta_E)
        y[1:] = np.cumsum(delta_N)
        z[1:] = np.cumsum(delta_V)
        
        return x, y, z
    
    def calculate_tangent_coords_vectorized(self, alpha: float, phi: float, length: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """向量化版本的切线段坐标计算"""
        n_points = self.n_points
        dl = length / (n_points - 1)
        
        # 一次性计算所有增量
        delta_N = dl * np.sin(alpha) * np.cos(phi)
        delta_E = dl * np.sin(alpha) * np.sin(phi)
        delta_V = dl * np.cos(alpha)
        
        # 创建坐标数组
        x = np.arange(n_points, dtype=np.float64) * delta_E
        y = np.arange(n_points, dtype=np.float64) * delta_N
        z = np.arange(n_points, dtype=np.float64) * delta_V
        
        return x, y, z
    
    def calculate_turn_coords_vectorized(self, alpha_start: float, alpha_end: float, 
                                        phi_start: float, phi_end: float, R: float, 
                                        length: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """向量化版本的转向段坐标计算"""
        n_points = self.n_points
        alpha = np.linspace(alpha_start, alpha_end, n_points)
        phi = np.linspace(phi_start, phi_end, n_points)
        dl = length / (n_points - 1)
        
        # 计算平均角度（向量化）
        alpha_avg = 0.5 * (alpha[:-1] + alpha[1:])
        phi_avg = 0.5 * (phi[:-1] + phi[1:])
        
        # 向量化计算增量
        delta_N = dl * np.sin(alpha_avg) * np.cos(phi_avg)
        delta_E = dl * np.sin(alpha_avg) * np.sin(phi_avg)
        delta_V = dl * np.cos(alpha_avg)
        
        # 累积求和
        x = np.zeros(n_points)
        y = np.zeros(n_points)
        z = np.zeros(n_points)
        x[1:] = np.cumsum(delta_E)
        y[1:] = np.cumsum(delta_N)
        z[1:] = np.cumsum(delta_V)
        
        return x, y, z
    
    def calculate_coordinates(self, position_tuple: list) -> Tuple[Optional[Tuple[np.ndarray, np.ndarray, np.ndarray]], 
                                                                   float, bool, float]:
        """
        计算完整井轨迹坐标（优化版本）
        """
        D_kop, alpha1, alpha2, phi1, phi2, R1, R2, D_turn_kop = position_tuple
        alpha1_rad = np.radians(alpha1)
        alpha2_rad = np.radians(alpha2)
        phi1_rad = np.radians(phi1)
        phi2_rad = np.radians(phi2)

        n_points = self.n_points

        # 垂直段（向量化）
        z_vertical = np.linspace(0, D_kop, n_points)
        x_vertical = np.full(n_points, self.config.E_wellhead)
        y_vertical = np.full(n_points, self.config.N_wellhead)

        # 造斜段（向量化）
        length_build = R1 * alpha1_rad
        x_build, y_build, z_build = self.calculate_build_coords_vectorized(
            0, alpha1_rad, phi1_rad, R1, length_build
        )
        x_build += x_vertical[-1]
        y_build += y_vertical[-1]
        z_build += D_kop
        
        delta_D_build = R1 * (1 - np.cos(alpha1_rad))
        remaining_D = D_turn_kop - D_kop - delta_D_build
        if remaining_D < 0:
            return None, 10000, False, remaining_D * (-1000)

        # 第一切线段（向量化）
        L3 = remaining_D / np.cos(alpha1_rad)
        x_tangent, y_tangent, z_tangent = self.calculate_tangent_coords_vectorized(
            alpha1_rad, phi1_rad, L3
        )
        x_tangent += x_build[-1]
        y_tangent += y_build[-1]
        z_tangent += z_build[-1]
        
        # 快速修正（只修正一次，而非重新计算）
        if abs(z_tangent[-1] - D_turn_kop) > self.config.TOLERANCE:
            length_error = D_turn_kop - z_tangent[-1]
            L3 += length_error / np.cos(alpha1_rad)
            x_tangent, y_tangent, z_tangent = self.calculate_tangent_coords_vectorized(
                alpha1_rad, phi1_rad, L3
            )
            x_tangent += x_build[-1]
            y_tangent += y_build[-1]
            z_tangent += z_build[-1]

        # 转向段（向量化）
        z_turn_start = z_tangent[-1]
        x_turn_start = x_tangent[-1]
        y_turn_start = y_tangent[-1]

        cos_gamma = np.clip(
            np.cos(alpha1_rad) * np.cos(alpha2_rad) +
            np.sin(alpha1_rad) * np.sin(alpha2_rad) * np.cos(phi2_rad - phi1_rad),
            -1.0, 1.0
        )
        gamma = np.arccos(cos_gamma)
        L4 = R2 * gamma

        x_turn, y_turn, z_turn = self.calculate_turn_coords_vectorized(
            alpha1_rad, alpha2_rad, phi1_rad, phi2_rad, R2, L4
        )
        z_turn += z_turn_start
        x_turn += x_turn_start
        y_turn += y_turn_start
        
        # 计算长度（只计算一次）
        lengths, loss = self.calculate_lengths(
            D_kop, alpha1_rad, alpha2_rad, phi1_rad, phi2_rad, R1, R2, D_turn_kop
        )
        if lengths is None:
            return None, 10000, False, loss * 1000
            
        # 第二切线段（向量化）
        L5 = lengths.get('tangent2', 0)
        x_tangent2, y_tangent2, z_tangent2 = self.calculate_tangent_coords_vectorized(
            alpha2_rad, phi2_rad, L5
        )
        x_tangent2 += x_turn[-1]
        y_tangent2 += y_turn[-1]
        z_tangent2 += z_turn[-1]

        # 合并所有段（使用concatenate，已经很快）
        x = np.concatenate([x_vertical, x_build, x_tangent, x_turn, x_tangent2])
        y = np.concatenate([y_vertical, y_build, y_tangent, y_turn, y_tangent2])
        z = np.concatenate([z_vertical, z_build, z_tangent, z_turn, z_tangent2])
        
        # 计算总长度
        total_length = sum(lengths.values())
        
        return (x, y, z), total_length, True, 0


# 如果使用Numba，创建JIT编译版本
if HAS_NUMBA:
    @jit(nopython=True, cache=True)
    def _calculate_build_coords_numba(alpha_start, alpha_end, phi, R, length, n_points):
        """Numba加速的造斜段计算"""
        alpha = np.linspace(alpha_start, alpha_end, n_points)
        x = np.zeros(n_points)
        y = np.zeros(n_points)
        z = np.zeros(n_points)
        
        for i in range(1, n_points):
            delta_N = R * (np.cos(alpha[i-1]) - np.cos(alpha[i])) * np.cos(phi)
            delta_E = R * (np.cos(alpha[i-1]) - np.cos(alpha[i])) * np.sin(phi)
            delta_V = R * (np.sin(alpha[i]) - np.sin(alpha[i-1]))
            x[i] = x[i-1] + delta_E
            y[i] = y[i-1] + delta_N
            z[i] = z[i-1] + delta_V
        
        return x, y, z
    
    @jit(nopython=True, cache=True)
    def _calculate_tangent_coords_numba(alpha, phi, length, n_points):
        """Numba加速的切线段计算"""
        dl = length / (n_points - 1)
        x = np.zeros(n_points)
        y = np.zeros(n_points)
        z = np.zeros(n_points)
        
        delta_N = dl * np.sin(alpha) * np.cos(phi)
        delta_E = dl * np.sin(alpha) * np.sin(phi)
        delta_V = dl * np.cos(alpha)
        
        for i in range(1, n_points):
            x[i] = x[i-1] + delta_E
            y[i] = y[i-1] + delta_N
            z[i] = z[i-1] + delta_V
        
        return x, y, z
    
    @jit(nopython=True, cache=True)
    def _calculate_turn_coords_numba(alpha_start, alpha_end, phi_start, phi_end, R, length, n_points):
        """Numba加速的转向段计算"""
        alpha = np.linspace(alpha_start, alpha_end, n_points)
        phi = np.linspace(phi_start, phi_end, n_points)
        dl = length / (n_points - 1)
        x = np.zeros(n_points)
        y = np.zeros(n_points)
        z = np.zeros(n_points)
        
        for i in range(1, n_points):
            alpha_avg = 0.5 * (alpha[i-1] + alpha[i])
            phi_avg = 0.5 * (phi[i-1] + phi[i])
            delta_N = dl * np.sin(alpha_avg) * np.cos(phi_avg)
            delta_E = dl * np.sin(alpha_avg) * np.sin(phi_avg)
            delta_V = dl * np.cos(alpha_avg)
            x[i] = x[i-1] + delta_E
            y[i] = y[i-1] + delta_N
            z[i] = z[i-1] + delta_V
        
        return x, y, z

