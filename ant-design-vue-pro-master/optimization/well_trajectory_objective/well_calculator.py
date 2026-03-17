"""
井轨迹计算器
Well Path Calculator

提供CPU和GPU版本的井轨迹计算功能
"""

import numpy as np
import math
from typing import Tuple, Optional, Dict, List
from .config import WellTrajectoryConfig


class WellPathCalculator:
    """CPU版本的井轨迹计算器"""

    def __init__(self, config: WellTrajectoryConfig):
        print("dadasdsda")
        self.config = config

    def calculate_lengths(self, D_kop: float, alpha_1: float, alpha_2: float,
                          phi_1: float, phi_2: float, R_1: float, R_2: float,
                          D_turn_kop: float) -> Tuple[Optional[Dict[str, float]], float]:
        """计算各段长度。"""
        cos_gamma = math.cos(alpha_1) * math.cos(alpha_2) + \
                    math.sin(alpha_1) * math.sin(alpha_2) * math.cos(phi_2 - phi_1)
        cos_gamma = max(-1.0, min(1.0, cos_gamma))
        gamma = math.acos(cos_gamma)
        gamma_half = gamma / 2.0

        lengths = {
            'vertical': float(D_kop),
            'build': float(R_1 * alpha_1),
            'tangent1': 0.0,
            'turn': float(R_2 * gamma),
        }

        delta_D_build = R_1 * (1.0 - math.cos(alpha_1))
        remaining_D = D_turn_kop - D_kop - delta_D_build
        if remaining_D < 0:
            return None, remaining_D * (-1000)

        RF = 2.0 * math.tan(gamma_half) / gamma if gamma != 0 else 1.0
        delta_D_turn = R_2 * (math.cos(alpha_1) + math.cos(alpha_2)) * RF / 2.0

        lengths['tangent1'] = remaining_D / math.cos(alpha_1)

        # 小迭代修正第一切线长度
        for _ in range(20):
            final_D = D_kop + delta_D_build + lengths['tangent1'] * math.cos(alpha_1)
            depth_error = final_D - D_turn_kop
            if abs(depth_error) < self.config.TOLERANCE:
                break
            lengths['tangent1'] -= depth_error / math.cos(alpha_1)
            if lengths['tangent1'] < 0:
                lengths['tangent1'] = 0.0

        remaining_to_target = self.config.D_target - D_turn_kop - delta_D_turn
        if remaining_to_target < 0:
            return None, remaining_to_target * (-1000)

        lengths['tangent2'] = remaining_to_target / math.cos(alpha_2)
        return lengths, 0.0

    def calculate_build_coords(self, alpha_start: float, alpha_end: float,
                               phi: float, R: float, length: float,
                               n_points: int = 50) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """计算造斜段相对坐标。"""
        alpha = np.linspace(alpha_start, alpha_end, n_points)

        cos_alpha_prev = np.cos(alpha[:-1])
        cos_alpha_curr = np.cos(alpha[1:])
        sin_alpha_prev = np.sin(alpha[:-1])
        sin_alpha_curr = np.sin(alpha[1:])

        delta_N = R * (cos_alpha_prev - cos_alpha_curr) * np.cos(phi)
        delta_E = R * (cos_alpha_prev - cos_alpha_curr) * np.sin(phi)
        delta_V = R * (sin_alpha_curr - sin_alpha_prev)

        x = np.zeros(n_points)
        y = np.zeros(n_points)
        z = np.zeros(n_points)
        x[1:] = np.cumsum(delta_E)
        y[1:] = np.cumsum(delta_N)
        z[1:] = np.cumsum(delta_V)
        return x, y, z

    def calculate_tangent_coords(self, alpha: float, phi: float, length: float,
                                 n_points: int = 50) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """计算切线段相对坐标。"""
        dl = length / (n_points - 1)
        delta_N = dl * np.sin(alpha) * np.cos(phi)
        delta_E = dl * np.sin(alpha) * np.sin(phi)
        delta_V = dl * np.cos(alpha)

        x = np.arange(n_points, dtype=np.float64) * delta_E
        y = np.arange(n_points, dtype=np.float64) * delta_N
        z = np.arange(n_points, dtype=np.float64) * delta_V
        return x, y, z

    def calculate_turn_coords(self, alpha_start: float, alpha_end: float,
                              phi_start: float, phi_end: float, R: float,
                              length: float, n_points: int = 50) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """计算转向段相对坐标。"""
        alpha = np.linspace(alpha_start, alpha_end, n_points)
        phi = np.linspace(phi_start, phi_end, n_points)
        dl = length / (n_points - 1)

        alpha_avg = 0.5 * (alpha[:-1] + alpha[1:])
        phi_avg = 0.5 * (phi[:-1] + phi[1:])

        delta_N = dl * np.sin(alpha_avg) * np.cos(phi_avg)
        delta_E = dl * np.sin(alpha_avg) * np.sin(phi_avg)
        delta_V = dl * np.cos(alpha_avg)

        x = np.zeros(n_points)
        y = np.zeros(n_points)
        z = np.zeros(n_points)
        x[1:] = np.cumsum(delta_E)
        y[1:] = np.cumsum(delta_N)
        z[1:] = np.cumsum(delta_V)
        return x, y, z

    @staticmethod
    def calculate_vector_angle(v1: np.ndarray, v2: np.ndarray) -> Tuple[float, float]:
        dot_product = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0, 0.0
        cos_theta = np.clip(dot_product / (norm_v1 * norm_v2), -1.0, 1.0)
        angle_rad = np.arccos(cos_theta)
        angle_deg = np.degrees(angle_rad)
        return float(angle_deg), float(angle_rad)

    def detect_direction_jump(self, points: Tuple[np.ndarray, np.ndarray, np.ndarray], threshold_deg: float = 10.0) -> int:
        """检测方向突变，points 顺序为 (N, E, V)。"""
        N, E, V = points
        N = np.array(N, dtype=np.float64)
        E = np.array(E, dtype=np.float64)
        V = np.array(V, dtype=np.float64)

        if not (len(N) == len(E) == len(V)):
            raise ValueError("N、E、V数组长度必须相同！")
        if len(N) < 3:
            return 0

        valid_vectors = []
        for i in range(len(N) - 1):
            vec = np.array([N[i + 1] - N[i], E[i + 1] - E[i], V[i + 1] - V[i]], dtype=np.float64)
            if np.linalg.norm(vec) >= 1e-8:
                valid_vectors.append(vec)

        if len(valid_vectors) < 2:
            return 0

        jump_count = 0
        for i in range(len(valid_vectors) - 1):
            angle_deg, _ = self.calculate_vector_angle(valid_vectors[i], valid_vectors[i + 1])
            if angle_deg > threshold_deg:
                jump_count += 1
        return jump_count

    def calculate_coordinates(self, position_tuple: list) -> Tuple[Optional[Tuple[np.ndarray, np.ndarray, np.ndarray]],
                                                                   float, bool, float]:
        """
        计算完整井轨迹坐标（干净重写版）：
        - 先统一计算段长
        - 再按段相对坐标累加为绝对坐标
        - 段拼接时移除重复端点，保证连续平滑
        """
        D_kop, alpha1, alpha2, phi1, phi2, R1, R2, D_turn_kop = position_tuple
        alpha1_rad = np.radians(alpha1)
        alpha2_rad = np.radians(alpha2)
        phi1_rad = np.radians(phi1)
        phi2_rad = np.radians(phi2)

        lengths, loss = self.calculate_lengths(D_kop, alpha1_rad, alpha2_rad, phi1_rad, phi2_rad, R1, R2, D_turn_kop)
        if lengths is None:
            return None, 10000, False, loss * 1000

        n_points = 50

        x_all: List[float] = []
        y_all: List[float] = []
        z_all: List[float] = []

        def append_segment(x_seg: np.ndarray, y_seg: np.ndarray, z_seg: np.ndarray):
            if not x_all:
                x_all.extend(x_seg.tolist())
                y_all.extend(y_seg.tolist())
                z_all.extend(z_seg.tolist())
            else:
                x_all.extend(x_seg[1:].tolist())
                y_all.extend(y_seg[1:].tolist())
                z_all.extend(z_seg[1:].tolist())

        # 1) 垂直段
        x0 = float(self.config.E_wellhead)
        y0 = float(self.config.N_wellhead)
        x_vertical = np.full(n_points, x0, dtype=np.float64)
        y_vertical = np.full(n_points, y0, dtype=np.float64)
        z_vertical = np.linspace(0.0, float(D_kop), n_points)
        append_segment(x_vertical, y_vertical, z_vertical)

        # 2) 第一造斜段
        L2 = lengths.get('build', R1 * alpha1_rad)
        xb, yb, zb = self.calculate_build_coords(0.0, alpha1_rad, phi1_rad, R1, L2, n_points)
        x_build = x_vertical[-1] + xb
        y_build = y_vertical[-1] + yb
        z_build = z_vertical[-1] + zb
        append_segment(x_build, y_build, z_build)

        # 3) 第一切线段
        L3 = lengths.get('tangent1', 0.0)
        xt1, yt1, zt1 = self.calculate_tangent_coords(alpha1_rad, phi1_rad, L3, n_points)
        x_t1 = x_build[-1] + xt1
        y_t1 = y_build[-1] + yt1
        z_t1 = z_build[-1] + zt1
        append_segment(x_t1, y_t1, z_t1)

        # 4) 转向段
        L4 = lengths.get('turn', 0.0)
        xtr, ytr, ztr = self.calculate_turn_coords(alpha1_rad, alpha2_rad, phi1_rad, phi2_rad, R2, L4, n_points)
        x_turn = x_t1[-1] + xtr
        y_turn = y_t1[-1] + ytr
        z_turn = z_t1[-1] + ztr
        append_segment(x_turn, y_turn, z_turn)

        # 5) 第二切线段
        L5 = lengths.get('tangent2', 0.0)
        xt2, yt2, zt2 = self.calculate_tangent_coords(alpha2_rad, phi2_rad, L5, n_points)
        x_t2 = x_turn[-1] + xt2
        y_t2 = y_turn[-1] + yt2
        z_t2 = z_turn[-1] + zt2
        append_segment(x_t2, y_t2, z_t2)

        x = np.array(x_all, dtype=np.float64)
        y = np.array(y_all, dtype=np.float64)
        z = np.array(z_all, dtype=np.float64)

        total_length = float(sum(lengths.values()))

        # 方向突变惩罚（按 N,E,V）
        jump_count = self.detect_direction_jump((y, x, z), threshold_deg=10.0)
        loss_jump = float(jump_count * 100000.0) if jump_count > 0 else 0.0

        return (x, y, z), total_length, True, loss_jump
