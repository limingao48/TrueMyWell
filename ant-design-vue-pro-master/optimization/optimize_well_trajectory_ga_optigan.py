#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""兼容层：从独立项目 gaoptgan 重新导出优化器 API。"""

import os
import sys

_GAOPTGAN = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "gaoptgan")
)
if _GAOPTGAN not in sys.path:
    sys.path.insert(0, _GAOPTGAN)

from optimize_well_trajectory_ga_optigan import (  # noqa: F401
    GAOptiGANWellTrajectoryOptimizer,
    optimize_well_trajectory_ga_optigan,
)

__all__ = ["GAOptiGANWellTrajectoryOptimizer", "optimize_well_trajectory_ga_optigan"]
