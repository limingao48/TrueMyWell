#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
井轨迹几何体转换器
Well Trajectory Geometry Converter

将Excel格式的井轨迹数据转换为直线段和圆弧段的基本几何体
"""

import numpy as np
import pandas as pd
import math
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from .geometric_obstacle_detector import LineSegment, CircularArc, GeometricObstacleDetector

@dataclass
class WellTrajectoryPoint:
    """井轨迹点数据结构"""
    depth: float          # 测深 (m)
    inclination: float    # 井斜角 (度)
    azimuth: float        # 网格方位角 (度)
    vertical_depth: float # 垂深 (m)
    north_coord: float    # 北坐标 (m)
    east_coord: float     # 东坐标 (m)
    displacement: float   # 视平移 (m)
    dogleg_severity: float # 全角变化率 (度/30m)

class WellTrajectoryGeometryConverter:
    """井轨迹几何体转换器"""
    
    def __init__(self, safety_radius: float = 15.0):
        """
        初始化转换器
        
        Args:
            safety_radius: 安全半径 (m)
        """
        self.safety_radius = safety_radius
        self.geometric_detector = GeometricObstacleDetector()
        
    def read_excel_data(self, excel_file_path: str) -> Optional[pd.DataFrame]:
        """
        读取Excel数据
        
        Args:
            excel_file_path: Excel文件路径
            
        Returns:
            pd.DataFrame: 井轨迹数据
        """
        try:
            df = pd.read_excel(excel_file_path)
            print(f"成功读取Excel文件: {excel_file_path}")
            print(f"数据形状: {df.shape}")
            print(f"列名: {df.columns.tolist()}")
            return df
        except Exception as e:
            print(f"读取Excel文件失败: {e}")
            return None
    
    def parse_well_data(self, df: pd.DataFrame) -> List[WellTrajectoryPoint]:
        """
        解析井轨迹数据
        
        Args:
            df: 井轨迹数据DataFrame
            
        Returns:
            List[WellTrajectoryPoint]: 井轨迹点列表
        """
        points = []
        
        # 根据列名映射数据
        column_mapping = {
            'depth': ['测深（m）', '测深(m)', '测深', 'Depth'],
            'inclination': ['井斜（deg）', '井斜(deg)', '井斜', 'Inclination'],
            'azimuth': ['网格方位（deg）', '网格方位(deg)', '网格方位', 'Azimuth'],
            'vertical_depth': ['垂深（m）', '垂深(m)', '垂深', 'Vertical Depth'],
            'north_coord': ['北坐标（m）', '北坐标(m)', '北坐标', 'North'],
            'east_coord': ['东坐标（m）', '东坐标(m)', '东坐标', 'East'],
            'displacement': ['视平移（m）', '视平移(m)', '视平移', 'Displacement'],
            'dogleg_severity': ['全角变化率(deg/30m)', '全角变化率', 'Dogleg Severity']
        }
        
        # 查找对应的列名
        actual_columns = {}
        for key, possible_names in column_mapping.items():
            for name in possible_names:
                if name in df.columns:
                    actual_columns[key] = name
                    break
        
        print(f"找到的列映射: {actual_columns}")
        
        # 解析数据点
        for index, row in df.iterrows():
            try:
                point = WellTrajectoryPoint(
                    depth=float(row[actual_columns['depth']]),
                    inclination=float(row[actual_columns['inclination']]),
                    azimuth=float(row[actual_columns['azimuth']]),
                    vertical_depth=float(row[actual_columns['vertical_depth']]),
                    north_coord=float(row[actual_columns['north_coord']]),
                    east_coord=float(row[actual_columns['east_coord']]),
                    displacement=float(row[actual_columns['displacement']]),
                    dogleg_severity=float(row[actual_columns['dogleg_severity']])
                )
                points.append(point)
            except Exception as e:
                print(f"解析第{index+1}行数据失败: {e}")
                continue
        
        print(f"成功解析 {len(points)} 个井轨迹点")
        return points
    
    def calculate_3d_coordinates(self, points: List[WellTrajectoryPoint]) -> np.ndarray:
        """
        计算3D坐标
        
        Args:
            points: 井轨迹点列表
            
        Returns:
            np.ndarray: 3D坐标数组 (N, 3)
        """
        coordinates = []
        
        for point in points:
            # 使用已有的北坐标、东坐标和垂深
            x = point.east_coord    # 东坐标
            y = point.north_coord   # 北坐标
            z = point.vertical_depth # 垂深
            coordinates.append([x, y, z])
        
        return np.array(coordinates)
    
    def analyze_trajectory_segments(self, points: List[WellTrajectoryPoint]) -> List[Dict[str, Any]]:
        """
        分析井轨迹段类型
        
        Args:
            points: 井轨迹点列表
            
        Returns:
            List[Dict]: 段信息列表
        """
        segments = []
        
        for i in range(len(points) - 1):
            current_point = points[i]
            next_point = points[i + 1]
            
            # 计算段长度
            current_coord = np.array([current_point.east_coord, current_point.north_coord, current_point.vertical_depth])
            next_coord = np.array([next_point.east_coord, next_point.north_coord, next_point.vertical_depth])
            segment_length = np.linalg.norm(next_coord - current_coord)
            
            # 计算角度变化
            incl_change = abs(next_point.inclination - current_point.inclination)
            azi_change = abs(next_point.azimuth - current_point.azimuth)
            
            # 处理方位角跨越0度的情况
            if azi_change > 180:
                azi_change = 360 - azi_change
            
            # 计算全角变化率
            dogleg_severity = current_point.dogleg_severity
            
            # 判断段类型
            if dogleg_severity < 0.1:  # 全角变化率小于0.1度/30m认为是直线段
                segment_type = "直线段"
            else:  # 否则认为是圆弧段
                segment_type = "圆弧段"
            
            segment_info = {
                'index': i,
                'type': segment_type,
                'start_point': current_coord,
                'end_point': next_coord,
                'length': segment_length,
                'inclination_change': incl_change,
                'azimuth_change': azi_change,
                'dogleg_severity': dogleg_severity,
                'start_inclination': current_point.inclination,
                'end_inclination': next_point.inclination,
                'start_azimuth': current_point.azimuth,
                'end_azimuth': next_point.azimuth
            }
            
            segments.append(segment_info)
        
        return segments
    
    def create_line_segments(self, segments: List[Dict[str, Any]]) -> List[LineSegment]:
        """
        创建直线段几何体
        
        Args:
            segments: 段信息列表
            
        Returns:
            List[LineSegment]: 直线段列表
        """
        line_segments = []
        
        for segment in segments:
            if segment['type'] == "直线段":
                line_seg = LineSegment(
                    start_point=segment['start_point'],
                    end_point=segment['end_point'],
                    radius=self.safety_radius
                )
                line_segments.append(line_seg)
        
        print(f"创建了 {len(line_segments)} 个直线段")
        return line_segments
    
    def create_circular_arcs(self, segments: List[Dict[str, Any]]) -> List[CircularArc]:
        """
        创建圆弧段几何体
        
        Args:
            segments: 段信息列表
            
        Returns:
            List[CircularArc]: 圆弧段列表
        """
        circular_arcs = []
        
        for segment in segments:
            if segment['type'] == "圆弧段":
                # 计算圆弧参数
                arc_params = self._calculate_arc_parameters(segment)
                if arc_params is not None:
                    circular_arc = CircularArc(
                        center=arc_params['center'],
                        radius=arc_params['radius'],
                        normal=arc_params['normal'],
                        start_angle=arc_params['start_angle'],
                        end_angle=arc_params['end_angle'],
                        safety_radius=self.safety_radius
                    )
                    circular_arcs.append(circular_arc)
        
        print(f"创建了 {len(circular_arcs)} 个圆弧段")
        return circular_arcs
    
    def _calculate_arc_parameters(self, segment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        计算圆弧参数
        
        Args:
            segment: 段信息
            
        Returns:
            Dict: 圆弧参数字典
        """
        try:
            start_point = segment['start_point']
            end_point = segment['end_point']
            start_incl = math.radians(segment['start_inclination'])
            end_incl = math.radians(segment['end_inclination'])
            start_azi = math.radians(segment['start_azimuth'])
            end_azi = math.radians(segment['end_azimuth'])
            
            # 计算圆弧半径（使用全角变化率）
            dogleg_severity = segment['dogleg_severity']  # 度/30m
            if dogleg_severity > 0:
                # 转换为弧度/米
                dogleg_rad_per_m = math.radians(dogleg_severity) / 30.0
                radius = 1.0 / dogleg_rad_per_m if dogleg_rad_per_m > 0 else 1000.0
            else:
                # 使用段长度作为半径
                radius = segment['length'] / 2.0
            
            # 计算圆弧中心（简化处理）
            # 这里使用段的中点作为圆弧中心
            center = (start_point + end_point) / 2.0
            
            # 计算圆弧所在平面的法向量
            # 使用井斜角和方位角计算方向向量
            start_dir = np.array([
                math.sin(start_incl) * math.cos(math.radians(90 - segment['start_azimuth'])),
                math.sin(start_incl) * math.sin(math.radians(90 - segment['start_azimuth'])),
                math.cos(start_incl)
            ])
            
            end_dir = np.array([
                math.sin(end_incl) * math.cos(math.radians(90 - segment['end_azimuth'])),
                math.sin(end_incl) * math.sin(math.radians(90 - segment['end_azimuth'])),
                math.cos(end_incl)
            ])
            
            # 计算法向量
            normal = np.cross(start_dir, end_dir)
            if np.linalg.norm(normal) > 0:
                normal = normal / np.linalg.norm(normal)
            else:
                normal = np.array([0, 0, 1])  # 默认垂直方向
            
            # 计算起始和结束角度
            start_angle = 0.0
            end_angle = math.radians(segment['inclination_change'] + segment['azimuth_change'])
            
            return {
                'center': center,
                'radius': radius,
                'normal': normal,
                'start_angle': start_angle,
                'end_angle': end_angle
            }
            
        except Exception as e:
            print(f"计算圆弧参数失败: {e}")
            return None
    
    def convert_well_trajectory(self, excel_file_path: str) -> GeometricObstacleDetector:
        """
        转换井轨迹为几何体
        
        Args:
            excel_file_path: Excel文件路径
            
        Returns:
            GeometricObstacleDetector: 几何障碍物检测器
        """
        print("=" * 60)
        print("开始转换井轨迹为几何体")
        print("=" * 60)
        
        # 1. 读取Excel数据
        df = self.read_excel_data(excel_file_path)
        if df is None:
            return self.geometric_detector
        
        # 2. 解析井轨迹数据
        points = self.parse_well_data(df)
        if not points:
            return self.geometric_detector
        
        # 3. 计算3D坐标
        coordinates = self.calculate_3d_coordinates(points)
        print(f"3D坐标范围:")
        print(f"  X: {coordinates[:, 0].min():.2f} ~ {coordinates[:, 0].max():.2f}")
        print(f"  Y: {coordinates[:, 1].min():.2f} ~ {coordinates[:, 1].max():.2f}")
        print(f"  Z: {coordinates[:, 2].min():.2f} ~ {coordinates[:, 2].max():.2f}")
        
        # 4. 分析井轨迹段
        segments = self.analyze_trajectory_segments(points)
        
        # 统计段类型
        line_count = sum(1 for seg in segments if seg['type'] == "直线段")
        arc_count = sum(1 for seg in segments if seg['type'] == "圆弧段")
        
        print(f"\n段类型统计:")
        print(f"  直线段: {line_count} 个")
        print(f"  圆弧段: {arc_count} 个")
        print(f"  总段数: {len(segments)} 个")
        
        # 5. 创建几何体
        line_segments = self.create_line_segments(segments)
        circular_arcs = self.create_circular_arcs(segments)
        
        # 6. 添加到检测器
        for line_seg in line_segments:
            self.geometric_detector.add_line_segment(
                line_seg.start_point,
                line_seg.end_point,
                line_seg.radius
            )
        
        for arc in circular_arcs:
            self.geometric_detector.add_circular_arc(
                arc.center,
                arc.radius,
                arc.normal,
                arc.start_angle,
                arc.end_angle,
                arc.safety_radius
            )
        
        print(f"\n转换完成!")
        print(f"  直线段: {len(line_segments)} 个")
        print(f"  圆弧段: {len(circular_arcs)} 个")
        print(f"  总几何体: {len(line_segments) + len(circular_arcs)} 个")
        
        return self.geometric_detector
    
    def visualize_trajectory_segments(self, segments: List[Dict[str, Any]], 
                                    coordinates: np.ndarray) -> None:
        """
        可视化井轨迹段
        
        Args:
            segments: 段信息列表
            coordinates: 3D坐标数组
        """
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import Axes3D
        
        fig = plt.figure(figsize=(15, 5))
        
        # 3D轨迹图
        ax1 = fig.add_subplot(131, projection='3d')
        ax1.plot(coordinates[:, 0], coordinates[:, 1], coordinates[:, 2], 'b-', linewidth=2, label='井轨迹')
        ax1.scatter(coordinates[0, 0], coordinates[0, 1], coordinates[0, 2], color='green', s=100, label='起点')
        ax1.scatter(coordinates[-1, 0], coordinates[-1, 1], coordinates[-1, 2], color='red', s=100, label='终点')
        ax1.set_xlabel('东坐标 (m)')
        ax1.set_ylabel('北坐标 (m)')
        ax1.set_zlabel('垂深 (m)')
        ax1.set_title('井轨迹3D视图')
        ax1.legend()
        
        # 段类型分布
        ax2 = fig.add_subplot(132)
        segment_types = [seg['type'] for seg in segments]
        type_counts = {'直线段': segment_types.count('直线段'), '圆弧段': segment_types.count('圆弧段')}
        ax2.bar(type_counts.keys(), type_counts.values(), color=['blue', 'orange'])
        ax2.set_ylabel('段数量')
        ax2.set_title('段类型分布')
        
        # 全角变化率分布
        ax3 = fig.add_subplot(133)
        dogleg_severities = [seg['dogleg_severity'] for seg in segments]
        ax3.plot(range(len(dogleg_severities)), dogleg_severities, 'o-', color='red')
        ax3.set_xlabel('段索引')
        ax3.set_ylabel('全角变化率 (度/30m)')
        ax3.set_title('全角变化率分布')
        ax3.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig("well_trajectory_analysis.png", dpi=300, bbox_inches='tight')
        plt.show()
        
        print("井轨迹分析图已保存: well_trajectory_analysis.png")

def create_well_geometry_converter(safety_radius: float = 15.0) -> WellTrajectoryGeometryConverter:
    """创建井轨迹几何体转换器"""
    return WellTrajectoryGeometryConverter(safety_radius)

def convert_excel_to_geometric_obstacles(excel_file_path: str, 
                                       safety_radius: float = 15.0) -> GeometricObstacleDetector:
    """从Excel文件创建几何障碍物检测器"""
    converter = create_well_geometry_converter(safety_radius)
    return converter.convert_well_trajectory(excel_file_path)

# 示例使用
if __name__ == "__main__":
    # 创建转换器
    converter = create_well_geometry_converter(safety_radius=15.0)
    
    # 转换井轨迹（需要提供实际的Excel文件路径）
    # geometric_detector = converter.convert_well_trajectory("米41-37YH3.xlsx")
    
    print("井轨迹几何体转换器已准备就绪")
    print("使用方法:")
    print("1. converter = create_well_geometry_converter(safety_radius=15.0)")
    print("2. geometric_detector = converter.convert_well_trajectory('your_file.xlsx')")
    print("3. 使用geometric_detector进行障碍物检测")
