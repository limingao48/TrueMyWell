"""井轨迹目标函数计算库（GA-optiGAN 独立项目版）。"""

__version__ = "1.0.0"

from .well_calculator import WellPathCalculator
from .obstacle_detection import WellObstacleDetector, WellDataReader
from .objective_function import (
    WellTrajectoryObjective,
    SevenSegmentWeightedObjective,
    create_well_obstacle_from_excel,
    create_multiple_well_obstacles,
    create_well_obstacles_from_directory,
    create_objective_function,
    SEVEN_SEG_PARAM_NAMES,
)
from .config import WellTrajectoryConfig

__all__ = [
    "WellPathCalculator",
    "WellObstacleDetector",
    "WellDataReader",
    "WellTrajectoryObjective",
    "SevenSegmentWeightedObjective",
    "WellTrajectoryConfig",
    "create_well_obstacle_from_excel",
    "create_multiple_well_obstacles",
    "create_well_obstacles_from_directory",
    "create_objective_function",
    "SEVEN_SEG_PARAM_NAMES",
]
