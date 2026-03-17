"""
井轨迹配置类
Well Trajectory Configuration
"""

import numpy as np
from typing import Tuple, Optional

class WellTrajectoryConfig:
    """井轨迹计算配置类"""
    
    def __init__(self, 
                 E_target: float = 1500.64,
                 N_target: float = 1200.71,
                 D_target: float = 2936.06,
                 E_wellhead: float = 30.0,
                 N_wellhead: float = 15.0,
                 D_wellhead: float = 0.0,
                 tolerance: float = 10.0,
                 obstacle_count: int = 0,
                 obstacle_min_radius: float = 50.0,
                 obstacle_max_radius: float = 50.0,
                 obstacle_x_range: Tuple[float, float] = (0, 1500),
                 obstacle_y_range: Tuple[float, float] = (0, 1500),
                 obstacle_z_range: Tuple[float, float] = (1600, 3000),
                 safety_radius: float = 10.0,
                 target_deviation_threshold: float = 30.0,
                 target_deviation_penalty: float = 100000.0,
                 # ===== 简化空间七段式参数范围（DLS统一为 °/30m） =====
                 # 1) seven_L0_range: 第1段直井段长度范围（m）
                 #    含义：从井口垂直向下钻进的长度；越大说明越晚开始偏斜。
                 seven_L0_range: Tuple[float, float] = (500.0, 2500.0),
                 # 2) seven_DLS1_range: 第2段增斜段狗腿度范围（°/30m）
                 #    含义：井斜从0°提升到 alpha3 的快慢；DLS越大，达到目标井斜所需段长越短。
                 seven_DLS1_range: Tuple[float, float] = (1, 6.0),
                 # 3) seven_alpha3_range: 第3段稳斜井斜角范围（°）
                 #    含义：扭方位前主稳斜角，决定水平位移推进能力。
                 seven_alpha3_range: Tuple[float, float] = (5.0, 85.0),
                 # 4) seven_L3_range: 第3段稳斜段长度范围（m）
                 #    含义：在初始方位 phi_init 上持续推进的长度（扭方位前）。
                 seven_L3_range: Tuple[float, float] = (0.0, 2500.0),
                 # 5) seven_DLS_turn_range: 第4段扭方位弧段狗腿度范围（°/30m）
                 #    含义：扭方位段的曲率能力上限；与 L4 一起决定可实现的方位变化幅度。
                 seven_DLS_turn_range: Tuple[float, float] = (1, 6.0),
                 # 6) seven_L4_range: 第4段扭方位弧段长度范围（m）
                 #    含义：专用扭方位段长度；越长可实现的总扭方位角通常越大。
                 seven_L4_range: Tuple[float, float] = (0, 2000.0),
                 # 7) seven_phi_target_range: 显式末端目标方位角范围（°）
                 #    含义：轨迹末端希望达到的方位方向（这里限制在355°~360°，即接近正北）。
                 # 0是东 270是南 180的西 90是北
                 #90 东
                 seven_phi_target_range: Tuple[float, float] = (0,0.5),
                 # 8) seven_L5_range: 第5段扭方位后稳斜段长度范围（m）
                 #    含义：完成扭方位后，保持当前井斜与方位继续推进的长度。
                 seven_L5_range: Tuple[float, float] = (0.0, 2500.0),
                 # 9) seven_DLS6_range: 第6段井斜调整段狗腿度范围（°/30m）
                 #    含义：将井斜从 alpha3 调整到 alpha_e 的速率（可增可降）。
                 seven_DLS6_range: Tuple[float, float] = (1, 6.0),
                 # 10) seven_alpha_e_range: 第7段末端井斜角范围（°）
                 #     含义：末端稳斜目标井斜（85°~90°表示接近水平井）。
                 seven_alpha_e_range: Tuple[float, float] = (85, 90),
                 # 11) seven_L7_range: 第7段末端稳斜段长度范围（m）
                 #     含义：在目标井斜与目标方位附近向靶区推进的末端长度。
                 seven_L7_range: Tuple[float, float] = (200, 2500.0),
                 # 12) seven_phi_init_range: 初始方位角范围（°）
                 #     含义：从“进入斜井”开始生效的参考方位（直井段井斜=0°时方位不产生水平位移）。
                 seven_phi_init_range: Tuple[float, float] = (0, 360),
                 ):
        """
       seven_L0_range: 第1段直井长度范围（m）
        #    含义：井眼从井口垂直向下钻进的长度。
        # 2) seven_K1_range: 第2段第一增斜段造斜率范围（°/m）
        #    含义：井斜从0°增到 alpha3 的快慢；值越大，达到目标井斜所需长度越短。
        # 3) seven_alpha3_range: 第3段稳斜段井斜角范围（°）
        #    含义：前半段主稳斜角，影响水平位移增长速度与后续扭方位段几何。
        # 4) seven_L3_range: 第3段稳斜段长度范围（m）
        #    含义：扭方位前沿当前方位持续推进的段长。
        # 5) seven_R_turn_range: 第4段扭方位圆弧半径范围（m）
        #    含义：专门“扭方位”的空间圆弧半径；半径越小，扭方位越急。
        # 6) seven_dphi_turn_range: 第4段扭方位角增量范围（°）
        #    含义：在扭方位段内总共改变多少方位角（0~360°）。

        # 7) seven_L5_range: 第5段扭方位后稳斜段长度范围（m）
        #    含义：完成扭方位后，保持当前井斜/方位继续推进的段长。
        # 8) seven_K6_range: 第6段末次井斜调整段造斜率范围（°/m）
        #    含义：将井斜从 alpha3 调整到 alpha_e 的速率（可增可降）。
        # 9) seven_alpha_e_range: 第7段目标末端井斜角范围（°）
        #    你这设置(88~92°)表示目标接近水平井（约90°）。
        # 10) seven_L7_range: 第7段末端稳斜段长度范围（m）
        #     含义：末端保持目标井斜与方位向靶区推进的长度。
        # 11) seven_phi_init_range: 初始方位角范围（°）
        #     含义：从“开始偏斜”起生效的参考方位（直井段井斜=0时方位不产生水平位移）。
        """
        # 目标点坐标
        self.E_target = E_target
        self.N_target = N_target
        self.D_target = D_target
        
        # 井口坐标
        self.E_wellhead = E_wellhead
        self.N_wellhead = N_wellhead
        self.D_wellhead = D_wellhead
        
        # 计算参数
        self.TOLERANCE = tolerance
        
        # 障碍物参数
        self.obstacle_count = obstacle_count
        self.obstacle_min_radius = obstacle_min_radius
        self.obstacle_max_radius = obstacle_max_radius
        self.obstacle_x_range = obstacle_x_range
        self.obstacle_y_range = obstacle_y_range
        self.obstacle_z_range = obstacle_z_range
        
        # 安全参数
        self.safety_radius = safety_radius
        self.target_deviation_threshold = target_deviation_threshold
        self.target_deviation_penalty = target_deviation_penalty

        # 简化空间七段式参数范围（直-增-稳-扭方位弧-稳-调斜-稳）
        self.seven_L0_range = seven_L0_range
        self.seven_DLS1_range = seven_DLS1_range
        self.seven_alpha3_range = seven_alpha3_range
        self.seven_L3_range = seven_L3_range
        self.seven_DLS_turn_range = seven_DLS_turn_range
        self.seven_L4_range = seven_L4_range
        self.seven_L5_range = seven_L5_range
        self.seven_DLS6_range = seven_DLS6_range
        self.seven_alpha_e_range = seven_alpha_e_range
        self.seven_L7_range = seven_L7_range
        self.seven_phi_init_range = seven_phi_init_range
        self.seven_phi_target_range = seven_phi_target_range

        self.SEVEN_SEG_PARAM_NAMES = [
            "L0", "DLS1", "alpha3", "L3", "DLS_turn", "L4", "L5", "DLS6", "alpha_e", "L7", "phi_init", "phi_target"
        ]
        self.SEVEN_SEG_BOUNDS_DICT = {
            "L0": self.seven_L0_range,
            "DLS1": self.seven_DLS1_range,
            "alpha3": self.seven_alpha3_range,
            "L3": self.seven_L3_range,
            "DLS_turn": self.seven_DLS_turn_range,
            "L4": self.seven_L4_range,
            "L5": self.seven_L5_range,
            "DLS6": self.seven_DLS6_range,
            "alpha_e": self.seven_alpha_e_range,
            "L7": self.seven_L7_range,
            "phi_init": self.seven_phi_init_range,
            "phi_target": self.seven_phi_target_range,
        }
        self.SEVEN_SEG_BOUNDS = np.array([
            self.SEVEN_SEG_BOUNDS_DICT[name] for name in self.SEVEN_SEG_PARAM_NAMES
        ], dtype=float)
        
        # 井轨迹参数边界
        self.D_kop_min = 500  # 最小造斜点深度
        self.D_kop_max = 1500  # 最大造斜点深度
        self.alpha_1_min = 10  # 最小造斜角
        self.alpha_1_max = 60  # 最大造斜角
        self.alpha_2_min = 88  # 最小第二造斜角
        self.alpha_2_max = 92  # 最大第二造斜角
        self.phi_1_min = 0  # 最小方位角
        self.phi_1_max = 360  # 最大方位角
        self.phi_2_min = 355  # 最小第二方位角
        self.phi_2_max = 360  # 最大第二方位角
        self.R_1_min = 286  # 最小造斜半径 2°/30m
        self.R_1_max = 			1145  # 最大造斜半径 1°/30m
        self.R_2_min = 286  # 最小第二造斜半径 5°/30m
        self.R_2_max = 			1145  # 最大第二造斜半径 3°/30m
        self.D_turn_kop_min = 1500  # 最小转向点深度
        self.D_turn_kop_max = 2400  # 最大转向点深度
        
        # 参数边界矩阵
        self.BOUNDS = np.array([
            [self.D_kop_min, self.D_kop_max],
            [self.alpha_1_min, self.alpha_1_max],
            [self.alpha_2_min, self.alpha_2_max],
            [self.phi_1_min, self.phi_1_max],
            [self.phi_2_min, self.phi_2_max],
            [self.R_1_min, self.R_1_max],
            [self.R_2_min, self.R_2_max],
            [self.D_turn_kop_min, self.D_turn_kop_max]
        ])
    
    def validate_parameters(self, position_tuple: list) -> bool:
        """
        验证参数是否在有效范围内
        
        Args:
            position_tuple: 位置参数元组 [D_kop, alpha1, alpha2, phi1, phi2, R1, R2, D_turn_kop]
            
        Returns:
            bool: 参数是否有效
        """
        if len(position_tuple) != 8:
            return False
            
        for i, param in enumerate(position_tuple):
            if not (self.BOUNDS[i, 0] <= param <= self.BOUNDS[i, 1]):
                return False
                
        # 检查造斜点深度不能大于转向点深度
        if position_tuple[0] > position_tuple[7]:
            return False
            
        return True
    
    def get_parameter_bounds(self) -> np.ndarray:
        """获取参数边界"""
        return self.BOUNDS.copy()
    
    def get_target_point(self) -> Tuple[float, float, float]:
        """获取目标点坐标"""
        return (self.E_target, self.N_target, self.D_target)

    def get_wellhead_point(self) -> Tuple[float, float, float]:
        """获取井口坐标"""
        return (self.E_wellhead, self.N_wellhead, self.D_wellhead)

    def get_seven_segment_parameter_bounds(self) -> np.ndarray:
        """获取七段式参数边界矩阵（按固定顺序）。"""
        return self.SEVEN_SEG_BOUNDS.copy()

    def get_seven_segment_bounds_dict(self) -> dict:
        """获取七段式参数边界字典。"""
        return dict(self.SEVEN_SEG_BOUNDS_DICT)

    def validate_seven_segment_parameters(self, params) -> bool:
        """
        验证七段式参数是否有效。

        支持:
            - dict: {"L0":..., "K1":..., ...}
            - list/tuple/np.ndarray: 按 SEVEN_SEG_PARAM_NAMES 顺序
        """
        if isinstance(params, dict):
            for name in self.SEVEN_SEG_PARAM_NAMES:
                if name not in params:
                    return False
                lo, hi = self.SEVEN_SEG_BOUNDS_DICT[name]
                if not (lo <= float(params[name]) <= hi):
                    return False
            alpha3 = float(params["alpha3"])
            alpha_e = float(params["alpha_e"])
            if not (0.0 <= alpha3 <= 89.0 and 0.0 <= alpha_e <= 89.0):
                return False
            return True

        if isinstance(params, (list, tuple, np.ndarray)):
            if len(params) != len(self.SEVEN_SEG_PARAM_NAMES):
                return False
            for i, v in enumerate(params):
                lo, hi = self.SEVEN_SEG_BOUNDS[i]
                if not (lo <= float(v) <= hi):
                    return False
            alpha3 = float(params[self.SEVEN_SEG_PARAM_NAMES.index("alpha3")])
            alpha_e = float(params[self.SEVEN_SEG_PARAM_NAMES.index("alpha_e")])
            if not (0.0 <= alpha3 <= 89.0 and 0.0 <= alpha_e <= 89.0):
                return False
            return True

        return False
