"""
井轨迹目标函数
Well Trajectory Objective Function

提供CPU和GPU版本的目标函数计算
"""

import numpy as np
from typing import Tuple, Optional, List, Dict, Any
from .config import WellTrajectoryConfig
from .well_calculator import WellPathCalculator
from .obstacle_detection import WellObstacleDetector, WellDataReader

def calculate_vector_angle(v1, v2):
    """
    计算两个三维向量的夹角（度）
    参数：
        v1 (np.ndarray): 第一个向量 [ΔN1, ΔE1, ΔV1]
        v2 (np.ndarray): 第二个向量 [ΔN2, ΔE2, ΔV2]
    返回：
        angle_deg (float): 向量夹角（度，0~180°）
        angle_rad (float): 向量夹角（弧度）
    """
    # 计算向量点积
    dot_product = np.dot(v1, v2)
    # 计算向量的模（避免除以0）
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)

    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0, 0.0  # 向量为零，夹角为0

    # 计算余弦值（限制在[-1,1]，避免浮点误差导致nan）
    cos_theta = np.clip(dot_product / (norm_v1 * norm_v2), -1.0, 1.0)
    # 计算弧度，再转换为度
    angle_rad = np.arccos(cos_theta)
    angle_deg = np.degrees(angle_rad)

    return angle_deg, angle_rad
def detect_direction_jump(points, threshold_deg=10.0):
    N, E, V = points
    """检测方向突变，新增零向量（重复点）过滤"""
    N = np.array(N, dtype=np.float64)
    E = np.array(E, dtype=np.float64)
    V = np.array(V, dtype=np.float64)
    # 输入校验
    if not (len(N) == len(E) == len(V)):
        raise ValueError("N、E、V数组长度必须相同！")
    n_points = len(N)
    if n_points < 3:
        raise ValueError("至少需要3个点（两段向量）！")

    # 第一步：计算方向向量，过滤零向量
    valid_vectors = []  # 存储非零向量
    duplicate_points = []  # 存储重复点信息

    for i in range(n_points - 1):
        ΔN = N[i + 1] - N[i]
        ΔE = E[i + 1] - E[i]
        ΔV = V[i + 1] - V[i]
        vec = np.array([ΔN, ΔE, ΔV])
        vec_norm = np.linalg.norm(vec)
        label = f"P{i + 1}→P{i + 2}"

        # 判断是否为零向量（重复点）
        if vec_norm < 1e-8:  # 浮点精度容错
            duplicate_points.append(label)
        else:
            valid_vectors.append(vec)

    # 检查过滤后是否有足够的有效向量
    valid_vector_count = len(valid_vectors)
    if valid_vector_count < 2:
        return 0, duplicate_points, valid_vector_count  # 突变个数为0

    # 第二步：计算有效向量的夹角，统计突变个数
    jump_count = 0  # 初始化突变个数
    for i in range(valid_vector_count - 1):
        v1 = valid_vectors[i]
        v2 = valid_vectors[i + 1]
        v1_label = f"P{[idx+1 for idx in range(n_points-1) if (N[idx+1]-N[idx], E[idx+1]-E[idx], V[idx+1]-V[idx]) == (v1[0],v1[1],v1[2])][0]}→P{[idx+2 for idx in range(n_points-1) if (N[idx+1]-N[idx], E[idx+1]-E[idx], V[idx+1]-V[idx]) == (v1[0],v1[1],v1[2])][0]}"
        v2_label = f"P{[idx+1 for idx in range(n_points-1) if (N[idx+1]-N[idx], E[idx+1]-E[idx], V[idx+1]-V[idx]) == (v2[0],v2[1],v2[2])][0]}→P{[idx+2 for idx in range(n_points-1) if (N[idx+1]-N[idx], E[idx+1]-E[idx], V[idx+1]-V[idx]) == (v2[0],v2[1],v2[2])][0]}"

        # 计算夹角
        angle_deg, _ = calculate_vector_angle(v1, v2)
        is_jump = angle_deg > threshold_deg

        # 统计突变个数
        if is_jump:
            jump_count += 1
            jump_level = "严重突变" if angle_deg > 20 else "轻微突变"
        # else:

    # 打印汇总信息


    return jump_count
class WellTrajectoryObjective:
    """CPU版本的井轨迹目标函数"""
    
    def __init__(self, config: WellTrajectoryConfig, 
                 well_obstacle: Optional[WellObstacleDetector] = None,
                 well_obstacles: Optional[List[WellObstacleDetector]] = None):
        """
        初始化目标函数
        
        Args:
            config: 井轨迹配置对象
            well_obstacle: 单个井轨迹障碍物检测器（可选，向后兼容）
            well_obstacles: 多个井轨迹障碍物检测器列表（可选）
        """
        self.config = config
        self.calculator = WellPathCalculator(config)

        # 处理井轨迹障碍物
        if well_obstacles is not None:
            self.well_obstacles = well_obstacles
        elif well_obstacle is not None:
            self.well_obstacles = [well_obstacle]
        else:
            self.well_obstacles = []
    
    def calculate_objective(self, position_tuple: List[float]) -> float:
        """
        计算目标函数值
        
        Args:
            position_tuple: 位置参数 [D_kop, alpha1, alpha2, phi1, phi2, R1, R2, D_turn_kop]
            
        Returns:
            float: 目标函数值
        """
        # # 参数验证
        # if not self.config.validate_parameters(position_tuple):
        #     return 1e20
        # 检查造斜点深度不能大于转向点深度
        if position_tuple[0] > position_tuple[7]:
            return 1e20
        
        # 检查特殊情况 - 在计算轨迹坐标之前
        special_case_check = self._check_special_cases(position_tuple)
        if special_case_check:
            return 1e20
        
        # 计算井轨迹坐标
        result = self.calculator.calculate_coordinates(position_tuple)
        points, total_length, flag, loss = result
        # tubian = 0
        # tubian = detect_direction_jump(points)
        # if tubian > 0:
        #     return tubian * self.config.target_deviation_penalty
        if points is None or not flag:
            return 1e20
        
        penalty = 0
        
        # 检查损失值
        if loss > 0:
            penalty += 1e20
            return penalty
        
        # # 检查与球形障碍物的碰撞
        # is_collision = self.obstacle_detector.check_collision(points)
        # if is_collision:
        #     penalty += 1e20
        #     return penalty
        
        # 检查与多个井轨迹的碰撞
        for well_obstacle in self.well_obstacles:
            if well_obstacle is not None:
                well_collision_penalty = well_obstacle.get_collision_penalty(points)
                penalty += well_collision_penalty
                if well_collision_penalty >= 1e20:
                    return penalty
        
        # 计算目标偏差
        final_point = (points[0][-1], points[1][-1], points[2][-1])
        target_deviation = np.sqrt(
            (final_point[0] - self.config.E_target)**2 +
            (final_point[1] - self.config.N_target)**2 +
            (final_point[2] - self.config.D_target)**2
        )
        
        # 目标偏差惩罚
        if target_deviation > self.config.target_deviation_threshold:
            target_deviation = target_deviation * self.config.target_deviation_penalty
        
        # 总目标函数值
        objective_value = target_deviation + total_length + penalty
        
        return objective_value
    
    def get_trajectory_info(self, position_tuple: List[float]) -> Dict[str, Any]:
        """
        获取轨迹详细信息
        
        Args:
            position_tuple: 位置参数
            
        Returns:
            Dict: 轨迹信息
        """
        result = self.calculator.calculate_coordinates(position_tuple)
        points, total_length, flag, loss = result
        
        if points is None or not flag:
            return {
                'success': False,
                'error': 'Invalid parameters or calculation failed',
                'loss': loss
            }
        
        x, y, z = points
        final_point = (x[-1], y[-1], z[-1])
        target_deviation = np.sqrt(
            (final_point[0] - self.config.E_target)**2 +
            (final_point[1] - self.config.N_target)**2 +
            (final_point[2] - self.config.D_target)**2
        )
        
        # 检查碰撞
        well_collision = False
        for well_obstacle in self.well_obstacles:
            if well_obstacle is not None:
                if well_obstacle.check_horizontal_collision((x, y, z), depth_step=10.0):
                    well_collision = True
                    break
        
        return {
            'success': True,
            'trajectory': points,
            'total_length': total_length,
            'final_point': final_point,
            'target_deviation': target_deviation,
            'well_collision': well_collision,
            'loss': loss
        }
    
    def _check_special_cases(self, position_tuple: List[float]) -> bool:
        """
        检查特殊情况，如果存在特殊情况返回True
        只检查可以客观计算出来说明参数不合理的特殊情况
        
        Args:
            position_tuple: 位置参数 [D_kop, alpha1, alpha2, phi1, phi2, R1, R2, D_turn_kop]
            
        Returns:
            bool: 如果存在特殊情况返回True，否则返回False
        """
        D_kop, alpha1, alpha2, phi1, phi2, R1, R2, D_turn_kop = position_tuple
        
        # 转换为弧度
        alpha1_rad = np.radians(alpha1)
        alpha2_rad = np.radians(alpha2)
        phi1_rad = np.radians(phi1)
        phi2_rad = np.radians(phi2)
        
        # 1. 检查数值稳定性 - cos_gamma是否在有效范围内
        cos_gamma = (np.cos(alpha1_rad) * np.cos(alpha2_rad) + 
                    np.sin(alpha1_rad) * np.sin(alpha2_rad) * np.cos(phi2_rad - phi1_rad))
        
        if abs(cos_gamma) > 1.0:
            return True  # 数值不稳定，无法计算转向角
        
        cos_gamma = np.clip(cos_gamma, -1.0, 1.0)
        gamma = np.arccos(cos_gamma)
        
        # 2. 检查第二切线段长度是否为负值（客观的几何约束）
        # 计算转向段垂直投影
        gamma_half = gamma / 2
        RF = 2 * np.tan(gamma_half) / gamma if gamma != 0 else 1
        delta_D_turn = R2 * (np.cos(alpha1_rad) + np.cos(alpha2_rad)) * RF / 2
        
        # 计算第二切线段长度
        remaining_to_target = self.config.D_target - D_turn_kop - delta_D_turn
        if remaining_to_target < 0:
            return True  # 第二切线段长度为负值，几何上不可能
        
        # 3. 检查几何空间约束 - 第一造斜段空间是否足够
        delta_D_build = R1 * (1 - np.cos(alpha1_rad))
        available_space = D_turn_kop - D_kop
        if available_space < delta_D_build:
            return True  # 空间不足，第一造斜段无法完成
        
        # 4. 检查第一切线段长度是否为负值
        # 第一切线段长度 = (D_turn_kop - D_kop - delta_D_build) / cos(alpha1)
        first_tangent_length = (D_turn_kop - D_kop - delta_D_build) / np.cos(alpha1_rad)
        if first_tangent_length < 0:
            return True  # 第一切线段长度为负值，几何上不可能
        
        # 5. 检查转向段长度是否为负值或零
        turn_length = R2 * gamma
        if turn_length <= 0:
            return True  # 转向段长度必须为正
        
        # 6. 检查第二切线段长度计算是否合理
        second_tangent_length = remaining_to_target / np.cos(alpha2_rad)
        if second_tangent_length < 0:
            return True  # 第二切线段长度为负值，几何上不可能
        
        # 7. 检查总长度是否为负值
        total_length = D_kop + R1 * alpha1_rad + first_tangent_length + turn_length + second_tangent_length
        if total_length <= 0:
            return True  # 总长度必须为正
        
        # 8. 检查转向角是否为NaN或无穷大
        if not np.isfinite(gamma):
            return True  # 转向角计算异常
        
        # 9. 检查关键角度是否为NaN或无穷大
        if not np.isfinite(alpha1_rad) or not np.isfinite(alpha2_rad):
            return True  # 角度计算异常
        
        # 10. 检查关键长度是否为NaN或无穷大
        if not np.isfinite(turn_length) or not np.isfinite(first_tangent_length) or not np.isfinite(second_tangent_length):
            return True  # 长度计算异常
        
        return False  # 没有特殊情况



def create_well_obstacle_from_excel(excel_file_path: str, 
                                   safety_radius: float = 15.0,
                                   segment_length: float = 30.0,
                                   wellhead_position: tuple = (0.0, 0.0, 0.0)) -> Optional[WellObstacleDetector]:
    """
    从Excel文件创建井轨迹障碍物检测器 - 优化版本
    
    Args:
        excel_file_path: Excel文件路径
        safety_radius: 安全半径 (m)
        segment_length: 段长度 (m)
        wellhead_position: 井口位置 (E, N, D)，默认为原点
        
    Returns:
        WellObstacleDetector: 井轨迹障碍物检测器
    """
    try:
        reader = WellDataReader(excel_file_path)
        if reader.read_well_data() and reader.process_well_trajectory(wellhead_position=wellhead_position):
            # 检测器内部会按深度步长自建 well_segments，只需传入 well_trajectory
            return WellObstacleDetector(
                well_trajectory=reader.well_trajectory,
                safety_radius=safety_radius
            )
    except Exception as e:
        print(f"创建井轨迹障碍物失败: {e}")
    return None


def create_multiple_well_obstacles(excel_files: List[str],
                                  wellhead_positions: List[tuple],
                                  safety_radius: float = 15.0,
                                  segment_length: float = 30.0) -> List[WellObstacleDetector]:
    """
    从多个Excel文件创建多个井轨迹障碍物检测器
    
    Args:
        excel_files: Excel文件路径列表
        wellhead_positions: 对应的井口位置列表 [(E1, N1, D1), (E2, N2, D2), ...]
        safety_radius: 安全半径 (m)
        segment_length: 段长度 (m)
        
    Returns:
        List[WellObstacleDetector]: 井轨迹障碍物检测器列表
    """
    import os
    
    well_obstacles = []
    successful_wells = []
    failed_wells = []
    
    # 验证输入参数
    if len(excel_files) != len(wellhead_positions):
        print(f"❌ 错误：Excel文件数量({len(excel_files)})与井口位置数量({len(wellhead_positions)})不匹配")
        return well_obstacles
    
    # 根据Excel文件名自动生成井名称
    well_names = []
    for excel_file in excel_files:
        # 提取文件名（不含路径和扩展名）
        filename = os.path.basename(excel_file)
        well_name = os.path.splitext(filename)[0]
        well_names.append(well_name)
    
    print(f"开始创建 {len(excel_files)} 个井轨迹障碍物...")
    print("=" * 60)
    
    for i, (excel_file, wellhead_position) in enumerate(zip(excel_files, wellhead_positions)):
        well_name = well_names[i] if well_names else f"井{i+1}"
        
        print(f"\n[{i+1}/{len(excel_files)}] 创建井轨迹障碍物: {well_name}")
        print(f"  Excel文件: {excel_file}")
        print(f"  井口位置: E={wellhead_position[0]}, N={wellhead_position[1]}, D={wellhead_position[2]}")
        
        # 检查文件是否存在
        if not os.path.exists(excel_file):
            print(f"  ❌ 文件不存在: {excel_file}")
            failed_wells.append((well_name, excel_file, "文件不存在"))
            continue
        
        try:
            well_obstacle = create_well_obstacle_from_excel(
                excel_file,
                safety_radius=safety_radius,
                segment_length=segment_length,
                wellhead_position=wellhead_position
            )
            
            if well_obstacle is not None:
                well_obstacles.append(well_obstacle)
                successful_wells.append(well_name)
                print(f"  ✓ 成功创建井轨迹障碍物: {well_name}")
                
                # 显示井轨迹信息
                if well_obstacle.well_trajectory is not None:
                    traj = well_obstacle.well_trajectory
                    print(f"    轨迹点数: {len(traj)}")
                    print(f"    轨迹范围: X({traj[:, 0].min():.1f}~{traj[:, 0].max():.1f}), "
                          f"Y({traj[:, 1].min():.1f}~{traj[:, 1].max():.1f}), "
                          f"Z({traj[:, 2].min():.1f}~{traj[:, 2].max():.1f})")
            else:
                print(f"  ❌ 创建失败: {well_name}")
                failed_wells.append((well_name, excel_file, "井轨迹处理失败"))
                
        except Exception as e:
            print(f"  ❌ 创建异常: {well_name} - {str(e)}")
            failed_wells.append((well_name, excel_file, f"异常: {str(e)}"))
    
    # 输出总结
    print("\n" + "=" * 60)
    print("井轨迹障碍物创建总结")
    print("=" * 60)
    print(f"成功创建: {len(successful_wells)} 个")
    if successful_wells:
        print(f"  成功列表: {', '.join(successful_wells)}")
    
    print(f"创建失败: {len(failed_wells)} 个")
    if failed_wells:
        print("  失败详情:")
        for well_name, excel_file, reason in failed_wells:
            print(f"    {well_name}: {excel_file} - {reason}")
    
    print(f"\n总共创建了 {len(well_obstacles)} 个井轨迹障碍物")
    return well_obstacles


def create_well_obstacles_from_directory(directory_path: str,
                                       wellhead_positions: List[tuple],
                                       safety_radius: float = 15.0,
                                       segment_length: float = 30.0,
                                       file_pattern: str = "*.xls") -> List[WellObstacleDetector]:
    """
    从目录中的Excel文件创建多个井轨迹障碍物检测器
    
    Args:
        directory_path: 包含Excel文件的目录路径
        wellhead_positions: 对应的井口位置列表 [(E1, N1, D1), (E2, N2, D2), ...]
        safety_radius: 安全半径 (m)
        segment_length: 段长度 (m)
        file_pattern: 文件匹配模式，默认为 "*.xls"
        
    Returns:
        List[WellObstacleDetector]: 井轨迹障碍物检测器列表
    """
    import os
    import glob
    
    # 查找Excel文件
    search_pattern = os.path.join(directory_path, file_pattern)
    excel_files = glob.glob(search_pattern)
    
    if not excel_files:
        print(f"❌ 在目录 {directory_path} 中未找到匹配 {file_pattern} 的文件")
        return []
    
    # 按文件名排序
    excel_files.sort()
    
    print(f"在目录 {directory_path} 中找到 {len(excel_files)} 个Excel文件:")
    for i, file in enumerate(excel_files):
        print(f"  {i+1}. {os.path.basename(file)}")
    
    # 检查井口位置数量
    if len(excel_files) != len(wellhead_positions):
        print(f"⚠ 警告：找到 {len(excel_files)} 个文件，但提供了 {len(wellhead_positions)} 个井口位置")
        if len(wellhead_positions) < len(excel_files):
            print("  将使用默认井口位置 (0, 0, 0) 填充缺失的位置")
            # 填充缺失的井口位置
            while len(wellhead_positions) < len(excel_files):
                wellhead_positions.append((0.0, 0.0, 0.0))
        else:
            print("  将截取前几个井口位置")
            wellhead_positions = wellhead_positions[:len(excel_files)]
    
    # 创建井名称列表
    well_names = [os.path.splitext(os.path.basename(f))[0] for f in excel_files]
    
    return create_multiple_well_obstacles(
        excel_files, 
        wellhead_positions, 
        safety_radius, 
        segment_length
    )


SEVEN_SEG_PARAM_NAMES = [
    "L0", "DLS1", "alpha3", "L3", "DLS_turn", "L4", "L5", "DLS6", "alpha_e", "L7", "phi_init", "phi_target"
]


def _build_seven_segment_trajectory(params: Dict[str, float], ds: float = 10.0) -> Dict[str, Any]:
    """生成简化空间七段式轨迹（含1段专用扭方位圆弧段）。"""
    p = {
        "L0": float(max(0.0, params.get("L0", 900.0))),
        "DLS1": float(max(1e-6, params.get("DLS1", 2.4))),
        "alpha3": float(np.clip(params.get("alpha3", 42.0), 0.0, 89.0)),
        "L3": float(max(0.0, params.get("L3", 750.0))),
        "DLS_turn": float(max(1e-6, params.get("DLS_turn", 2.0))),
        "L4": float(max(0.0, params.get("L4", 600.0))),
        "L5": float(max(0.0, params.get("L5", 650.0))),
        "DLS6": float(max(1e-6, params.get("DLS6", 1.5))),
        "alpha_e": float(np.clip(params.get("alpha_e", 35.0), 0.0, 89.0)),
        "L7": float(max(0.0, params.get("L7", 900.0))),
        "phi_init": float(params.get("phi_init", 65.0) % 360.0),
        "phi_target": float(params.get("phi_target", 95.0) % 360.0),
    }

    alpha3 = p["alpha3"]
    alpha_e = p["alpha_e"]

    # DLS(°/30m) -> 角度变化率(°/m)
    k1 = p["DLS1"] / 30.0
    k_turn = p["DLS_turn"] / 30.0
    k6 = p["DLS6"] / 30.0

    # 第2段增斜长度
    L1 = abs(alpha3 - 0.0) / k1

    # 第4段扭方位：与井斜对称——目标角自由，段长由目标推导（井斜是 L6=|alpha_e-alpha3|/k6，这里是 L4_used）
    # 目标总扭角 = phi_target - phi_init（取[-180, 180)最短方向）
    dphi_target = (p["phi_target"] - p["phi_init"] + 180.0) % 360.0 - 180.0

    sin_alpha = max(np.sin(np.radians(max(alpha3, 1e-3))), 1e-3)
    # 与井斜完全对称：段长仅由目标角推导，无上限。井斜没有 L6_max，这里也不再用 L4 截断
    L4_needed = abs(dphi_target) * sin_alpha / abs(k_turn) if abs(k_turn) > 1e-9 else 0.0
    L4_used = min(L4_needed, 1e6) if L4_needed < 1e9 else 0.0  # 仅防数值爆炸，不依赖 L4
    dphi_turn = float(dphi_target)  # 直接用目标扭角，末端方位 = phi_target

    # 第6段井斜调整长度（增/降皆可）
    L6 = abs(alpha_e - alpha3) / k6

    E, N, D, MD = [0.0], [0.0], [0.0], [0.0]
    md = 0.0

    def append_step(step_len: float, inc_deg: float, azi_deg: float):
        nonlocal md
        inc = np.radians(inc_deg)
        azi = np.radians(azi_deg)
        dN = step_len * np.sin(inc) * np.cos(azi)
        dE = step_len * np.sin(inc) * np.sin(azi)
        dD = step_len * np.cos(inc)
        N.append(N[-1] + dN)
        E.append(E[-1] + dE)
        D.append(D[-1] + dD)
        md += step_len
        MD.append(md)
    # 1) 直井段
    n = max(1, int(np.ceil(p["L0"] / ds)))
    for _ in range(n):
        append_step(p["L0"] / n, 0.0, p["phi_init"])

    # 2) 增斜段（方位固定）
    n = max(1, int(np.ceil(L1 / ds)))
    for k in range(1, n + 1):
        frac = k / n
        inc = 0.0 + (alpha3 - 0.0) * frac
        append_step(L1 / n, inc, p["phi_init"])

    # 3) 稳斜段
    n = max(1, int(np.ceil(p["L3"] / ds)))
    for _ in range(n):
        append_step(p["L3"] / n, alpha3, p["phi_init"])

    # 4) 专用扭方位圆弧段（井斜保持 alpha3），长度 L4_used（由目标方位推导，与第6段 L6 由 alpha_e 推导对称）
    n = max(1, int(np.ceil(L4_used / ds)))
    for k in range(1, n + 1):
        frac = k / n
        azi = p["phi_init"] + dphi_turn * frac
        append_step(L4_used / n, alpha3, azi)

    phi_after_turn = p["phi_init"] + dphi_turn

    # 5) 稳斜段
    n = max(1, int(np.ceil(p["L5"] / ds)))
    for _ in range(n):
        append_step(p["L5"] / n, alpha3, phi_after_turn)

    # 6) 井斜调整段（方位固定）
    n = max(1, int(np.ceil(L6 / ds)))
    for k in range(1, n + 1):
        frac = k / n
        inc = alpha3 + (alpha_e - alpha3) * frac
        append_step(L6 / n, inc, phi_after_turn)

    # 7) 末端稳斜段
    n = max(1, int(np.ceil(p["L7"] / ds)))
    for _ in range(n):
        append_step(p["L7"] / n, alpha_e, phi_after_turn)
    seg1_len = p["L0"]          # 直井段
    seg2_len = L1               # 增斜段
    seg3_len = p["L3"]          # 稳斜段1
    seg4_len = L4_used          # 扭方位段（实际使用长度，由 phi_target 推导）
    seg5_len = p["L5"]          # 稳斜段2
    seg6_len = L6               # 井斜调整段
    seg7_len = p["L7"]          # 末端稳斜段
    # 轨迹末端方位角（第4段扭方位后的方位，在第5/6/7段保持不变）
    return {
        "E": np.asarray(E, dtype=float),
        "N": np.asarray(N, dtype=float),
        "D": np.asarray(D, dtype=float),
        "total_length": float(MD[-1]),
        "phi_end": float(phi_after_turn),
    }


class SevenSegmentWeightedObjective:
    """七段式目标函数：先入靶，再最小化总井深，并考虑相邻井防碰。

    入靶定义：轨迹末端点 (E,N,D) 与靶点 (E_target, N_target, D_target) 的三维欧氏距离
    dev <= hit_threshold 时视为入靶；未入靶时目标值为 w_target * dev^2 + 防碰项，入靶后为井深 + 防碰项。
    若优化结果仍离靶点较远，可：增大 w_target、适当增大 hit_threshold、检查参数边界与初值。
    """

    def __init__(self,
                 config: WellTrajectoryConfig,
                 well_obstacle: Optional[WellObstacleDetector] = None,
                 well_obstacles: Optional[List[WellObstacleDetector]] = None,
                 hit_threshold: float = 30.0,
                 w_target: float = 1e5,
                 w_length: float = 1.0,
                 w_azimuth: float = 1.0,
                 azimuth_as_free_parameter: bool = True,
                 w_collision_soft: float = 0.0,
                 w_collision_hard: float = 1e8,
                 collision_buffer_factor: float = 1.0,
                 hard_collision_penalty: float = 1e24,
                 depth_step: float = 10.0):
        self.config = config
        if well_obstacles is not None:
            self.well_obstacles = well_obstacles
        elif well_obstacle is not None:
            self.well_obstacles = [well_obstacle]
        else:
            self.well_obstacles = []

        self.hit_threshold = float(hit_threshold)
        self.w_target = float(w_target)
        self.w_length = float(w_length)
        self.w_azimuth = float(w_azimuth)  # 末端方位与 phi_target 偏差的权重（仅在 azimuth_as_free_parameter=False 时生效）
        self.azimuth_as_free_parameter = bool(azimuth_as_free_parameter)  # True：方位角同井斜角，作为自由参数，不可行则拒绝
        self.w_collision_soft = float(w_collision_soft)
        self.w_collision_hard = float(w_collision_hard)
        self.collision_buffer_factor = float(max(1.0, collision_buffer_factor))
        self.hard_collision_penalty = float(hard_collision_penalty)
        self.depth_step = float(depth_step)

    @staticmethod
    def _to_param_dict(position_tuple: Any) -> Dict[str, float]:
        if isinstance(position_tuple, dict):
            return {k: float(v) for k, v in position_tuple.items()}
        if isinstance(position_tuple, (list, tuple, np.ndarray)) and len(position_tuple) == len(SEVEN_SEG_PARAM_NAMES):
            return {k: float(v) for k, v in zip(SEVEN_SEG_PARAM_NAMES, position_tuple)}
        raise ValueError("七段式参数必须是 dict 或长度为12的序列")

    def _collision_penalty(self, trajectory: Tuple[np.ndarray, np.ndarray, np.ndarray]) -> float:
        total_penalty = 0.0
        for well_obstacle in self.well_obstacles:
            if well_obstacle is None:
                continue
            d_min = well_obstacle._min_horizontal_distance_scan(
                trajectory=trajectory,
                horizontal_threshold=well_obstacle.safety_radius,
                depth_step=self.depth_step,
            )
            if not np.isfinite(d_min):
                continue

            safe = float(well_obstacle.safety_radius)

            if d_min < safe:
                # 仅硬约束：发生碰撞直接重罚
                total_penalty += self.hard_collision_penalty + self.w_collision_hard * (safe - d_min + 1.0) ** 2

        return float(total_penalty)

    def calculate_objective(self, position_tuple: Any) -> float:
        try:
            params = self._to_param_dict(position_tuple)
        except Exception:
            return 1e20

        # 空间七段式参数有效性校验
        if hasattr(self.config, "validate_seven_segment_parameters"):
            if not self.config.validate_seven_segment_parameters(params):
                return 1e20

        traj = _build_seven_segment_trajectory(params, ds=self.depth_step)

        e_end = float(traj["E"][-1])
        n_end = float(traj["N"][-1])
        d_end = float(traj["D"][-1])

        # 入靶判定：轨迹末端点 (e_end, n_end, d_end) 与靶点 (E_target, N_target, D_target) 的三维欧氏距离
        # dev <= hit_threshold 即视为入靶；单位与坐标一致（通常为 m）
        dev = float(np.sqrt(
            (e_end - self.config.E_target) ** 2 +
            (n_end - self.config.N_target) ** 2 +
            (d_end - self.config.D_target) ** 2
        ))

        collision_term = self._collision_penalty((traj["E"], traj["N"], traj["D"]))

        # 方位与井斜一致：段长由目标角推导，末端方位恒为 phi_target，无需任何方位约束或惩罚
        azimuth_term = 0.0

        # 两阶段目标：先入靶，入靶后最小化井深（并保持防碰）
        if dev > self.hit_threshold:
            # 未入靶：惩罚与到靶点距离相关。用 dev^2 使远距离时梯度更大，便于优化器靠近靶点
            return float(self.w_target * (dev ** 2) + collision_term + azimuth_term)

        length_term = self.w_length * float(traj["total_length"])
        return float(length_term + collision_term + azimuth_term)

    def get_trajectory_info(self, position_tuple: Any) -> Dict[str, Any]:
        params = self._to_param_dict(position_tuple)
        traj = _build_seven_segment_trajectory(params, ds=self.depth_step)

        end_point = (float(traj["E"][-1]), float(traj["N"][-1]), float(traj["D"][-1]))
        dev = float(np.sqrt(
            (end_point[0] - self.config.E_target) ** 2 +
            (end_point[1] - self.config.N_target) ** 2 +
            (end_point[2] - self.config.D_target) ** 2
        ))
        collision_penalty = self._collision_penalty((traj["E"], traj["N"], traj["D"]))

        # 末端方位角：优先用轨迹返回的 phi_end，否则用最后一段水平增量估算
        azi_end = traj.get("phi_end")
        if azi_end is None and len(traj["E"]) >= 2:
            dE = float(traj["E"][-1] - traj["E"][-2])
            dN = float(traj["N"][-1] - traj["N"][-2])
            if abs(dE) + abs(dN) > 1e-9:
                azi_end = float((np.degrees(np.arctan2(dE, dN)) + 360.0) % 360.0)

        return {
            "success": True,
            "trajectory": (traj["E"], traj["N"], traj["D"]),
            "total_length": float(traj["total_length"]),
            "final_point": end_point,
            "target_deviation": dev,
            "hit_threshold": float(self.hit_threshold),
            "is_target_hit": bool(dev <= self.hit_threshold),
            "final_azimuth": float(azi_end) if azi_end is not None else None,
            "phi_target": float(params.get("phi_target", 0.0) % 360.0),
            "well_collision": collision_penalty >= self.hard_collision_penalty,
            "collision_penalty": float(collision_penalty),
        }


def create_objective_function(config: WellTrajectoryConfig,
                            well_obstacle: Optional[WellObstacleDetector] = None,
                            well_obstacles: Optional[List[WellObstacleDetector]] = None,
                            use_gpu: bool = False,
                            objective_mode: str = "legacy8",
                            objective_weights: Optional[Dict[str, float]] = None):
    """
    创建目标函数实例

    Args:
        config: 井轨迹配置对象
        well_obstacle: 单个井轨迹障碍物检测器（可选，向后兼容）
        well_obstacles: 多个井轨迹障碍物检测器列表（可选）
        use_gpu: 是否使用GPU（当前保留参数）
        objective_mode: "legacy8"(原8参数) 或 "seven_segment_weighted"
        objective_weights: 七段式权重配置字典
    """
    _ = use_gpu

    if objective_mode == "seven_segment_weighted":
        weights = objective_weights or {}
        # 支持从 weights 传入布尔：0/1.0 视为 False/True
        ap = weights.get("azimuth_as_free_parameter", True)
        azimuth_as_free = bool(ap) if isinstance(ap, (bool, int)) else bool(float(ap))
        return SevenSegmentWeightedObjective(
            config=config,
            well_obstacle=well_obstacle,
            well_obstacles=well_obstacles,
            hit_threshold=float(weights.get("hit_threshold", 30.0)),
            w_target=float(weights.get("w_target", 1e5)),
            w_length=float(weights.get("w_length", 1.0)),
            w_azimuth=float(weights.get("w_azimuth", 1.0)),
            azimuth_as_free_parameter=azimuth_as_free,
            w_collision_soft=float(weights.get("w_collision_soft", 0.0)),
            w_collision_hard=float(weights.get("w_collision_hard", 1e8)),
            collision_buffer_factor=float(weights.get("collision_buffer_factor", 1.0)),
            hard_collision_penalty=float(weights.get("hard_collision_penalty", 1e24)),
            depth_step=float(weights.get("depth_step", 10.0)),
        )

    return WellTrajectoryObjective(config, well_obstacle, well_obstacles)
