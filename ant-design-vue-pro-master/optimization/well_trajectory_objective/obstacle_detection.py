"""
障碍物检测系统
Obstacle Detection System

仅保留井轨迹障碍物检测功能（水平距离扫描）
"""

import numpy as np
import math
from typing import List, Tuple, Optional, Dict, Any
from .config import WellTrajectoryConfig

class WellObstacleDetector:
    """井轨迹障碍物检测器 - 优化版本，简化碰撞计算"""
    
    def __init__(self, well_trajectory: Optional[np.ndarray] = None, 
                 trajectory_segments: Optional[List[Dict]] = None,
                 safety_radius: float = 15.0):
        """
        初始化井轨迹障碍物检测器
        
        Args:
            well_trajectory: 井轨迹数据 (N, 3) 数组
            trajectory_segments: 轨迹段列表（可选，用于简化计算）
            safety_radius: 安全半径 (m)
        """
        self.well_trajectory = well_trajectory
        self.trajectory_segments = trajectory_segments
        self.safety_radius = safety_radius
        self.well_segments = None
        self.segment_bounds = None  # 存储每个段的边界框，用于快速碰撞检测
        
        if well_trajectory is not None:
            # 默认每 10m 垂深做一次水平距离扫描段划分
            self.create_well_segments(depth_step=10.0)
            self.calculate_segment_bounds()
    
    def create_well_segments(self, depth_step: float = 10.0) -> bool:
        """
        按垂深步长生成“水平距离扫描”用的井轨迹段。

        说明：
        - 不再按空间线段长度切分
        - 统一按垂深(TVD) z 间隔进行重采样（默认 10m）
        - 每一小段仍保存 start/end，便于兼容现有边界框逻辑

        Args:
            depth_step: 垂深扫描步长 (m)

        Returns:
            bool: 是否成功创建段
        """
        if self.well_trajectory is None:
            return False

        if depth_step <= 0:
            raise ValueError("depth_step 必须为正数")

        z_obs, x_obs, y_obs = self._prepare_xy_interpolator_from_trajectory(self.well_trajectory)
        if z_obs.size < 2:
            self.well_segments = []
            return False

        z_min = float(z_obs.min())
        z_max = float(z_obs.max())
        if z_max <= z_min:
            self.well_segments = []
            return False

        depths = np.arange(z_min, z_max + 1e-9, depth_step, dtype=float)
        if depths.size == 0:
            self.well_segments = []
            return False

        # 确保最后一个采样点覆盖到最大深度
        if depths[-1] < z_max:
            depths = np.append(depths, z_max)

        x_i = np.interp(depths, z_obs, x_obs)
        y_i = np.interp(depths, z_obs, y_obs)

        segments: List[Dict[str, Any]] = []
        for i in range(len(depths) - 1):
            start_point = np.array([x_i[i], y_i[i], depths[i]], dtype=float)
            end_point = np.array([x_i[i + 1], y_i[i + 1], depths[i + 1]], dtype=float)

            dx = float(end_point[0] - start_point[0])
            dy = float(end_point[1] - start_point[1])
            horizontal_length = float(np.hypot(dx, dy))

            segments.append({
                'start': start_point,
                'end': end_point,
                'length': float(np.linalg.norm(end_point - start_point)),
                'horizontal_length': horizontal_length,
                'segment_type': 'horizontal_scan',
            })

        self.well_segments = segments
        return True
    
    def calculate_segment_bounds(self):
        """计算每个轨迹段的边界框，用于快速碰撞检测"""
        if self.well_segments is None:
            return
            
        self.segment_bounds = []
        for segment in self.well_segments:
            start = segment['start']
            end = segment['end']
            
            # 计算边界框（包含安全半径）
            min_coords = np.minimum(start, end) - self.safety_radius
            max_coords = np.maximum(start, end) + self.safety_radius
            
            self.segment_bounds.append({
                'min': min_coords,
                'max': max_coords,
                'center': (min_coords + max_coords) / 2,
                'size': max_coords - min_coords,
                'segment': segment
            })
    
    def distance_to_well_segment(self, point: np.ndarray, segment: Dict[str, Any]) -> float:
        """
        计算点到井轨迹段的最短距离
        
        Args:
            point: 点坐标 [x, y, z]
            segment: 井轨迹段
            
        Returns:
            float: 最短距离
        """
        start = segment['start']
        end = segment['end']
        
        # 计算点到线段的距离
        line_vec = end - start
        point_vec = point - start
        
        line_len = np.linalg.norm(line_vec)
        if line_len == 0:
            return np.linalg.norm(point - start)
        
        # 投影参数
        t = np.dot(point_vec, line_vec) / (line_len ** 2)
        t = np.clip(t, 0, 1)
        
        # 最近点
        closest_point = start + t * line_vec
        
        # 距离
        distance = np.linalg.norm(point - closest_point)
        
        return distance

    @staticmethod
    def _prepare_xy_interpolator_from_trajectory(traj: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        将轨迹整理为按垂深单调递增的 (z, x, y)，用于按垂深插值。
        约定：traj 每行为 [E, N, D]（东、北、垂深TVD），x=E、y=N、z=D，垂深向下为正。
        """
        if traj.size == 0:
            return np.array([]), np.array([]), np.array([])

        x = traj[:, 0].astype(float, copy=False)   # E (东)
        y = traj[:, 1].astype(float, copy=False)   # N (北)
        z = traj[:, 2].astype(float, copy=False)   # D 垂深 TVD，向下为正

        order = np.argsort(z)
        z_sorted = z[order]
        x_sorted = x[order]
        y_sorted = y[order]

        # 去掉重复深度点（np.interp 需要严格递增/非递减；重复会导致数值不稳定）
        z_unique, unique_idx = np.unique(z_sorted, return_index=True)
        x_unique = x_sorted[unique_idx]
        y_unique = y_sorted[unique_idx]
        return z_unique, x_unique, y_unique

    @staticmethod
    def _prepare_xy_interpolator_from_xyz(x: np.ndarray, y: np.ndarray, z: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """把 (x,y,z) 轨迹整理为按 z 递增的 (z, x, y)。"""
        if x.size == 0:
            return np.array([]), np.array([]), np.array([])

        x = x.astype(float, copy=False)
        y = y.astype(float, copy=False)
        z = z.astype(float, copy=False)

        order = np.argsort(z)
        z_sorted = z[order]
        x_sorted = x[order]
        y_sorted = y[order]

        z_unique, unique_idx = np.unique(z_sorted, return_index=True)
        x_unique = x_sorted[unique_idx]
        y_unique = y_sorted[unique_idx]
        return z_unique, x_unique, y_unique

    def _min_horizontal_distance_scan(self,
                                      trajectory: Tuple[np.ndarray, np.ndarray, np.ndarray],
                                      horizontal_threshold: Optional[float] = None,
                                      depth_step: float = 10.0) -> float:
        """
        按垂深间隔扫描，计算新井轨迹与障碍井轨迹的最小水平距离（EN 平面）。

        - 只使用水平距离，不包含垂深方向
        - 在同一垂深 D 上对两口井的 (E, N) 做线性插值后比较

        Args:
            trajectory: 新井轨迹 (E, N, D) 三个一维数组，D 为垂深(TVD)，与 objective 中 traj["E"], traj["N"], traj["D"] 一致
            horizontal_threshold: 水平距离阈值（m），为 None 时使用 self.safety_radius
            depth_step: 垂深扫描步长（m），默认 10m

        Returns:
            min_horizontal_distance: 最小水平距离（m），若无重叠深度或数据不足返回 +inf
        """
        if self.well_trajectory is None:
            return float('inf')

        if depth_step <= 0:
            raise ValueError("depth_step 必须为正数")

        x_new, y_new, z_new = trajectory
        if x_new is None or y_new is None or z_new is None:
            return float('inf')

        z_obs, x_obs, y_obs = self._prepare_xy_interpolator_from_trajectory(self.well_trajectory)
        z_new_s, x_new_s, y_new_s = self._prepare_xy_interpolator_from_xyz(x_new, y_new, z_new)

        if z_obs.size < 2 or z_new_s.size < 2:
            return float('inf')

        z_min = max(float(z_obs.min()), float(z_new_s.min()))
        z_max = min(float(z_obs.max()), float(z_new_s.max()))
        if z_max <= z_min:
            return float('inf')

        depths = np.arange(z_min, z_max + 1e-9, depth_step, dtype=float)
        if depths.size == 0:
            return float('inf')

        x_obs_i = np.interp(depths, z_obs, x_obs)
        y_obs_i = np.interp(depths, z_obs, y_obs)
        x_new_i = np.interp(depths, z_new_s, x_new_s)
        y_new_i = np.interp(depths, z_new_s, y_new_s)

        dx = x_new_i - x_obs_i
        dy = y_new_i - y_obs_i
        horiz_dist = np.sqrt(dx * dx + dy * dy)

        # 返回最小水平距离
        return float(np.min(horiz_dist))
    
    def distance_to_well_trajectory(self, point: np.ndarray) -> float:
        """
        计算点到整个井轨迹的最短距离
        
        Args:
            point: 点坐标 [x, y, z]
            
        Returns:
            float: 最短距离
        """
        if self.well_segments is None:
            return float('inf')
        
        min_distance = float('inf')
        for segment in self.well_segments:
            dist = self.distance_to_well_segment(point, segment)
            min_distance = min(min_distance, dist)
        
        return min_distance
    
    def check_collision_with_well(self, trajectory_points: List[np.ndarray]) -> bool:
        """
        检查轨迹是否与井碰撞 - 简化版本，使用边界框快速检测
        
        Args:
            trajectory_points: 轨迹点列表
            
        Returns:
            bool: 是否发生碰撞
        """
        if self.segment_bounds is None:
            return False
        
        # 首先进行边界框快速检测
        for point in trajectory_points:
            for bounds in self.segment_bounds:
                # 检查点是否在边界框内
                if (bounds['min'][0] <= point[0] <= bounds['max'][0] and
                    bounds['min'][1] <= point[1] <= bounds['max'][1] and
                    bounds['min'][2] <= point[2] <= bounds['max'][2]):
                    
                    # 如果在边界框内，进行精确距离计算
                    distance = self.distance_to_well_segment(point, bounds['segment'])
                    if distance < self.safety_radius:
                        return True
        
        return False

    def check_horizontal_collision(self,
                                   trajectory: Tuple[np.ndarray, np.ndarray, np.ndarray],
                                   horizontal_threshold: Optional[float] = None,
                                   depth_step: float = 10.0) -> bool:
        """
        仅使用“水平距离扫描”判断是否与障碍井发生碰撞。

        Args:
            trajectory: 新井轨迹 (x, y, z)
            horizontal_threshold: 水平距离阈值（m），为 None 时使用 self.safety_radius
            depth_step: 深度扫描步长（m），默认 10m
        """
        if horizontal_threshold is None:
            horizontal_threshold = self.safety_radius
        d_min = self._min_horizontal_distance_scan(
            trajectory=trajectory,
            horizontal_threshold=horizontal_threshold,
            depth_step=depth_step,
        )
        return d_min < float(horizontal_threshold)
    
    def check_collision_with_well_segments(self, trajectory_segments: List[Dict]) -> bool:
        """
        检查轨迹段是否与井轨迹段碰撞 - 最高效的检测方法
        
        Args:
            trajectory_segments: 目标轨迹段列表
            
        Returns:
            bool: 是否发生碰撞
        """
        if self.segment_bounds is None:
            return False
        
        # 对每个目标轨迹段进行检测
        for target_segment in trajectory_segments:
            target_start = target_segment['start']
            target_end = target_segment['end']
            
            # 计算目标段的边界框
            target_min = np.minimum(target_start, target_end) - self.safety_radius
            target_max = np.maximum(target_start, target_end) + self.safety_radius
            
            # 与每个井轨迹段进行边界框检测
            for bounds in self.segment_bounds:
                # 检查边界框是否相交
                if (target_max[0] >= bounds['min'][0] and target_min[0] <= bounds['max'][0] and
                    target_max[1] >= bounds['min'][1] and target_min[1] <= bounds['max'][1] and
                    target_max[2] >= bounds['min'][2] and target_min[2] <= bounds['max'][2]):
                    
                    # 如果边界框相交，进行精确的线段距离计算
                    if self.segment_to_segment_distance(target_segment, bounds['segment']) < self.safety_radius * 2:
                        return True
        
        return False
    
    def segment_to_segment_distance(self, seg1: Dict, seg2: Dict) -> float:
        """
        计算两个线段之间的最短距离
        
        Args:
            seg1: 第一个线段
            seg2: 第二个线段
            
        Returns:
            float: 最短距离
        """
        p1, p2 = seg1['start'], seg1['end']
        p3, p4 = seg2['start'], seg2['end']
        
        # 计算两个线段的最短距离
        # 使用向量方法计算
        d1 = p2 - p1
        d2 = p4 - p3
        w = p1 - p3
        
        a = np.dot(d1, d1)
        b = np.dot(d1, d2)
        c = np.dot(d2, d2)
        d = np.dot(d1, w)
        e = np.dot(d2, w)
        
        denom = a * c - b * b
        if denom < 1e-10:  # 线段平行
            # 计算点到线段的距离
            t1 = np.clip(d / a, 0, 1) if a > 1e-10 else 0
            t2 = np.clip(e / c, 0, 1) if c > 1e-10 else 0
        else:
            t1 = np.clip((b * e - c * d) / denom, 0, 1)
            t2 = np.clip((a * e - b * d) / denom, 0, 1)
        
        # 计算最近点
        closest1 = p1 + t1 * d1
        closest2 = p3 + t2 * d2
        
        # 返回距离
        return np.linalg.norm(closest1 - closest2)
    
    def get_collision_penalty(self, trajectory: Tuple[np.ndarray, np.ndarray, np.ndarray]) -> float:
        """
        计算与井碰撞的惩罚值 - 优化版本
        
        Args:
            trajectory: 轨迹坐标 (x, y, z)
            
        Returns:
            float: 惩罚值
        """
        # 采用“水平距离扫描”：
        # - 水平距离 < safety_radius → 视为碰撞，罚 1e20
        # - safety_radius ≤ 水平距离 < 2*safety_radius → 线性接近惩罚（可选）
        d_min = self._min_horizontal_distance_scan(trajectory, depth_step=10.0)
        if not np.isfinite(d_min):
            return 0.0

        if d_min < self.safety_radius:
            return 1e20

        if d_min < self.safety_radius * 2:
            return (self.safety_radius * 2 - d_min) * 1000.0

        return 0.0
    
    def get_well_bounds(self) -> Optional[Dict[str, np.ndarray]]:
        """
        获取井轨迹的边界框
        
        Returns:
            Dict: 边界框信息
        """
        if self.well_trajectory is None:
            return None
            
        min_coords = np.min(self.well_trajectory, axis=0)
        max_coords = np.max(self.well_trajectory, axis=0)
        
        return {
            'min': min_coords,
            'max': max_coords,
            'center': (min_coords + max_coords) / 2,
            'size': max_coords - min_coords
        }


class WellDataReader:
    """井斜数据读取器 - 优化版本，参照well_trajectory.py的处理方法"""
    
    def __init__(self, excel_file_path: str):
        """
        初始化井数据读取器
        
        Args:
            excel_file_path: Excel文件路径
        """
        self.excel_file_path = excel_file_path
        self.well_data = None
        self.trajectory_points = []
        self.trajectory_segments = []
        self.well_trajectory = None
        self.well_segments = None
        
    def read_well_data(self) -> bool:
        """
        读取井斜数据表（按 测深、井斜角、方位角 传入）
        
        测深(MD)=沿井眼轨迹的测量长度，不是垂深(TVD)；垂深由 MD/Inc/Az 计算得到。
        支持两种输入：
        1) 新格式（推荐）：测深(MD)、井斜(Inc)、方位角(Az) 三列，可有表头
           - 测深：沿井眼累计长度 (m)
           - 井斜：相对竖直向下，0°=垂直向下，单位度
           - 方位：从北顺时针，N=0°、E=90°，单位度
        2) 旧格式（向后兼容）：含 垂深/北坐标/东坐标 等列，可无表头
        
        Returns:
            bool: 是否成功读取
        """
        try:
            import pandas as pd

            # 读取表格（csv/tsv/txt 或 Excel）
            file_lower = str(self.excel_file_path).lower()
            df = None
            if file_lower.endswith((".csv", ".tsv", ".txt")):
                # 尝试自动分隔（逗号/制表符/空格）
                df = pd.read_csv(self.excel_file_path, sep=r"[\t,\s]+", engine="python")
                print("成功读取文本格式数据")
            else:
                df = pd.read_excel(self.excel_file_path)
                print("成功读取Excel格式数据")

            # 统一列名（去空格）
            df.columns = [str(c).strip() for c in df.columns]

            # 允许无表头的格式：列名为 0,1,2... 时按实际列数赋默认列名（3 列=MD/Inc/Az，8 列=旧格式）
            if all(isinstance(c, int) or str(c).isdigit() for c in df.columns):
                df = pd.read_csv(self.excel_file_path, sep=r"[\t,\s]+", engine="python", header=None)
                ncol = len(df.columns)
                if ncol >= 8:
                    df.columns = ['测深', '井斜', '网格方位', '垂深', '北坐标', '东坐标', '视平移', '全角变化率'] + [f'_c{i}' for i in range(8, ncol)]
                elif ncol >= 3:
                    df.columns = ['测深', '井斜', '网格方位'] + [f'_c{i}' for i in range(3, ncol)]
                # 否则列数<3，后面 pick_col 会报错

            # 新格式列名别名
            def pick_col(candidates: List[str]) -> Optional[str]:
                for name in candidates:
                    if name in df.columns:
                        return name
                return None

            col_md = pick_col(["测深", "MD", "md", "MeasuredDepth", "measured_depth"])
            col_inc = pick_col(["井斜", "Inclination", "inc", "INC", "inclination"])
            col_az = pick_col(["方位角", "网格方位", "Azimuth", "az", "AZ", "azimuth"])

            col_tvd = pick_col(["垂深", "TVD", "tvd", "true_vertical_depth"])
            col_n = pick_col(["北坐标", "North", "N", "north_coord"])
            col_e = pick_col(["东坐标", "East", "E", "east_coord"])

            if col_md is None or col_inc is None or col_az is None:
                raise ValueError("已有井数据至少需要三列：测深(MD)、井斜(Inc)、方位角(Az)")

            # 清空旧数据
            self.trajectory_points = []

            # 逐行读取：优先新格式；若存在 E/N/TVD 则一并保存用于旧式直接坐标
            for i, row in df.iterrows():
                if pd.isna(row[col_md]):
                    continue

                md = float(row[col_md])
                inc = float(row[col_inc])
                az = float(row[col_az])

                point: Dict[str, Any] = {
                    'index': int(i),
                    'measured_depth': md,
                    'inclination': inc,
                    'azimuth': az,
                }

                # 旧格式附加列（可选）
                if col_tvd is not None and col_n is not None and col_e is not None:
                    if not (pd.isna(row[col_tvd]) or pd.isna(row[col_n]) or pd.isna(row[col_e])):
                        point['true_vertical_depth'] = float(row[col_tvd])
                        point['north_coord'] = float(row[col_n])
                        point['east_coord'] = float(row[col_e])

                self.trajectory_points.append(point)

            if len(self.trajectory_points) < 2:
                raise ValueError("轨迹点数不足（至少需要2行测点）")

            # 基本检查：MD 单调递增
            md_list = [p['measured_depth'] for p in self.trajectory_points]
            if any((md_list[i + 1] - md_list[i]) <= 0 for i in range(len(md_list) - 1)):
                raise ValueError("测深(MD)必须严格递增（不能重复/倒序）")

            print(f"成功读取 {len(self.trajectory_points)} 个轨迹点（MD/Inc/Az）")
            return True
            
        except Exception as e:
            print(f"读取井斜数据表失败: {e}")
            return False
    
    
    def calculate_3d_coordinates(self, wellhead_position: tuple = (0.0, 0.0, 0.0)):
        """
        基于起点 + 测深(MD)/井斜/方位角 计算井眼三维坐标（E, N, 垂深），采用最小曲率法。

        输入为测深(MD)不是垂深：测深=沿井眼轨迹的累计长度，垂深=竖直方向深度。
        输出 D 为垂深(TVD)，向下为正。

        约定：
        - 测深 MD：沿井眼测量长度 (m)，仅作输入
        - 井斜角 Inclination：相对竖直向下（0°=垂直向下）
        - 方位角 Azimuth：从北顺时针（N=0°, E=90°）
        - 输出 D：垂深 TVD，向下为正
        """
        if not self.trajectory_points:
            return

        x0, y0, z0 = wellhead_position

        # 起点
        self.trajectory_points[0]['x'] = float(x0)
        self.trajectory_points[0]['y'] = float(y0)
        self.trajectory_points[0]['z'] = float(z0)

        for i in range(1, len(self.trajectory_points)):
            p1 = self.trajectory_points[i - 1]
            p2 = self.trajectory_points[i]

            md1 = float(p1['measured_depth'])
            md2 = float(p2['measured_depth'])
            dmd = md2 - md1
            if dmd <= 0:
                raise ValueError("测深(MD)必须严格递增")

            inc1 = math.radians(float(p1['inclination']))
            inc2 = math.radians(float(p2['inclination']))
            az1 = math.radians(float(p1['azimuth']))
            az2 = math.radians(float(p2['azimuth']))

            # 圆柱螺线法（与最小曲率法一致形式）：
            # 先计算狗腿角，再用比例因子 RF 修正弧段积分
            cos_dogleg = (
                math.cos(inc1) * math.cos(inc2)
                + math.sin(inc1) * math.sin(inc2) * math.cos(az2 - az1)
            )
            cos_dogleg = max(-1.0, min(1.0, cos_dogleg))
            dogleg = math.acos(cos_dogleg)
            rf = 1.0 if dogleg < 1e-12 else (2.0 / dogleg) * math.tan(dogleg / 2.0)

            dN = 0.5 * dmd * (
                math.sin(inc1) * math.cos(az1) + math.sin(inc2) * math.cos(az2)
            ) * rf
            dE = 0.5 * dmd * (
                math.sin(inc1) * math.sin(az1) + math.sin(inc2) * math.sin(az2)
            ) * rf
            dD = 0.5 * dmd * (
                math.cos(inc1) + math.cos(inc2)
            ) * rf

            p2['x'] = float(p1['x']) + dE
            p2['y'] = float(p1['y']) + dN
            p2['z'] = float(p1['z']) + dD
    
    def process_well_trajectory(self, wellhead_position: tuple = (0.0, 0.0, 0.0)) -> bool:
        """
        由 测深(MD)/井斜/方位角 计算井眼三维坐标（E, N, 垂深），最小曲率法。
        注意：输入是测深(MD)，输出第三列是垂深(TVD)，二者不同。

        Args:
            wellhead_position: 井口位置 (E, N, D)，D 为井口垂深，向下为正

        Returns:
            bool: 是否成功处理。成功后 self.well_trajectory 为 (N_pt, 3)，每行 [E, N, 垂深TVD]
        """
        if not self.trajectory_points:
            print("请先读取井斜数据表")
            return False

        try:
            # 仅计算3D坐标
            self.calculate_3d_coordinates(wellhead_position)

            # 生成numpy数组格式的轨迹数据
            trajectory_array = []
            for point in self.trajectory_points:
                trajectory_array.append([point['x'], point['y'], point['z']])
            self.well_trajectory = np.array(trajectory_array)

            # 清空轨迹段参数（不再计算）
            self.trajectory_segments = []

            print(f"处理完成，轨迹点数: {len(self.trajectory_points)}")
            print(f"井口位置: E={wellhead_position[0]:.2f}, N={wellhead_position[1]:.2f}, D={wellhead_position[2]:.2f}")
            print(f"轨迹范围:")
            print(f"  X (East): {np.min(self.well_trajectory[:, 0]):.2f} ~ {np.max(self.well_trajectory[:, 0]):.2f}")
            print(f"  Y (North): {np.min(self.well_trajectory[:, 1]):.2f} ~ {np.max(self.well_trajectory[:, 1]):.2f}")
            print(f"  垂深 TVD: {np.min(self.well_trajectory[:, 2]):.2f} ~ {np.max(self.well_trajectory[:, 2]):.2f} m (向下为正)")

            return True

        except Exception as e:
            print(f"处理井轨迹数据失败: {e}")
            return False
    
    def create_well_segments(self, segment_length: float = 50.0) -> bool:
        """
        将井轨迹分割成小段，用于碰撞检测
        
        Args:
            segment_length: 段长度 (m)
            
        Returns:
            bool: 是否成功创建段
        """
        if self.well_trajectory is None:
            print("请先处理井轨迹数据")
            return False
            
        segments = []
        for i in range(len(self.well_trajectory) - 1):
            start_point = self.well_trajectory[i]
            end_point = self.well_trajectory[i + 1]
            
            # 计算段长度
            segment_len = np.linalg.norm(end_point - start_point)
            
            # 如果段太长，进一步分割
            if segment_len > segment_length:
                num_sub_segments = int(segment_len / segment_length) + 1
                for j in range(num_sub_segments):
                    t = j / num_sub_segments
                    sub_start = start_point + t * (end_point - start_point)
                    sub_end = start_point + min(1, (j + 1) / num_sub_segments) * (end_point - start_point)
                    segments.append({
                        'start': sub_start,
                        'end': sub_end,
                        'length': np.linalg.norm(sub_end - sub_start)
                    })
            else:
                segments.append({
                    'start': start_point,
                    'end': end_point,
                    'length': segment_len
                })
        
        self.well_segments = segments
        print(f"创建了 {len(segments)} 个井轨迹段")
        return True
