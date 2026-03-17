"""
井轨迹目标函数计算库
Well Trajectory Objective Function Library

一个专门用于井眼轨迹优化目标函数计算的独立库
"""

__version__ = "1.0.0"
__author__ = "Well Trajectory Optimization Team"

from .well_calculator import WellPathCalculator
from .obstacle_detection import WellObstacleDetector, WellDataReader
from .objective_function import (
    WellTrajectoryObjective,
    SevenSegmentWeightedObjective,
    create_well_obstacle_from_excel,
    create_multiple_well_obstacles,
    create_well_obstacles_from_directory,
    create_objective_function
)
from .config import WellTrajectoryConfig

# GPU版本（可选，需要PyTorch）
try:
    from .gpu import WellPathCalculatorGPU, WellTrajectoryObjectiveGPU, create_gpu_objective_function
    HAS_GPU = True
except ImportError:
    HAS_GPU = False
    WellPathCalculatorGPU = None
    WellTrajectoryObjectiveGPU = None
    create_gpu_objective_function = None
from .visualization import (
    plot_trajectory_3d,
    plot_trajectory_multiple_views,
    plot_fitness_evolution,
    plot_parameter_analysis,
    plot_well_comparison_3d,
    plot_well_comparison_interactive,
    create_visualization_report
)

__all__ = [
    'WellPathCalculator',
    'WellObstacleDetector',
    'WellDataReader',
    'WellTrajectoryObjective',
    'SevenSegmentWeightedObjective',
    'WellTrajectoryConfig',
    'create_well_obstacle_from_excel',
    'create_multiple_well_obstacles',
    'create_well_obstacles_from_directory',
    'create_objective_function',
    'plot_trajectory_3d',
    'plot_trajectory_multiple_views',
    'plot_fitness_evolution',
    'plot_parameter_analysis',
    'plot_well_comparison_3d',
    'plot_well_comparison_interactive',
    'create_visualization_report',
    'HAS_GPU',
]

# 如果GPU版本可用，添加到__all__
if HAS_GPU:
    __all__.extend([
        'WellPathCalculatorGPU',
        'WellTrajectoryObjectiveGPU',
        'create_gpu_objective_function'
    ])
