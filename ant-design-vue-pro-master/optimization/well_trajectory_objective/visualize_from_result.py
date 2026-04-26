"""
从B2OPT推理结果文件读取最优参数并可视化
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from typing import Tuple, List, Dict, Any, Optional
import argparse
import sys
import os
import json

# 添加路径
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GA_DIR = os.path.join(ROOT_DIR, "GA")
if GA_DIR not in sys.path:
    sys.path.append(GA_DIR)

from well_trajectory_objective import (
    WellTrajectoryConfig,
    WellTrajectoryObjective,
    create_multiple_well_obstacles,
)
from visualize_optimization_result import visualize_optimization_result, parse_triplet, PARAM_NAMES


def load_result_from_file(result_file: str) -> Dict:
    """
    从结果文件加载最优参数
    
    支持格式：
    1. JSON文件: {"best_solution": [...], "best_fitness": ...}
    2. 文本文件: 每行一个参数值
    3. CSV文件: 包含参数列
    """
    if not os.path.exists(result_file):
        raise FileNotFoundError(f"结果文件不存在: {result_file}")
    
    ext = os.path.splitext(result_file)[1].lower()
    
    if ext == '.json':
        with open(result_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if 'best_solution' in data:
            return {
                'optimal_params': data['best_solution'],
                'best_fitness': data.get('best_fitness', None),
                'trajectory_info': data.get('trajectory_info', None),
            }
        else:
            raise ValueError("JSON文件中未找到 'best_solution' 字段")
    
    elif ext == '.txt':
        with open(result_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        params = [float(line) for line in lines[:8]]
        if len(params) != 8:
            raise ValueError(f"文本文件应包含8个参数值，找到{len(params)}个")
        return {'optimal_params': params}
    
    elif ext == '.csv':
        import pandas as pd
        df = pd.read_csv(result_file)
        if len(df) == 0:
            raise ValueError("CSV文件为空")
        # 尝试从列名或第一行读取参数
        param_cols = [col for col in df.columns if col in PARAM_NAMES]
        if len(param_cols) == 8:
            params = df.iloc[0][param_cols].values.tolist()
        else:
            # 假设前8列是参数
            params = df.iloc[0, :8].values.tolist()
        return {'optimal_params': params}
    
    else:
        raise ValueError(f"不支持的文件格式: {ext}")


def main():
    parser = argparse.ArgumentParser(description="从结果文件可视化井轨迹优化结果")
    
    # 结果文件
    parser.add_argument("--result-file", type=str, required=True,
                       help="结果文件路径（JSON/TXT/CSV）")
    
    # 目标点和井口
    parser.add_argument("--target-e", type=float, default=502.64)
    parser.add_argument("--target-n", type=float, default=790.71)
    parser.add_argument("--target-d", type=float, default=2636.06)
    parser.add_argument("--wellhead", type=str, default="254.0,2030.0,0.0")
    
    # 已有井
    parser.add_argument("--excel-files", nargs="*", default=None)
    parser.add_argument("--wellhead-positions", nargs="*", default=None)
    
    # 输出选项
    parser.add_argument("--save-path", type=str, default=None)
    parser.add_argument("--no-show", action="store_true")
    parser.add_argument("--no-param-info", action="store_true")
    
    args = parser.parse_args()
    
    # 加载结果
    print(f"📂 加载结果文件: {args.result_file}")
    result_data = load_result_from_file(args.result_file)
    optimal_params = result_data['optimal_params']
    
    print(f"\n✅ 成功加载最优参数:")
    for name, value in zip(PARAM_NAMES, optimal_params):
        print(f"  {name}: {value:.6f}")
    
    if 'best_fitness' in result_data and result_data['best_fitness'] is not None:
        print(f"\n最佳适应度: {result_data['best_fitness']:.6e}")
    
    # 解析井口位置
    wellhead = parse_triplet(args.wellhead)
    
    # 计算相对目标点
    relative_target = (
        args.target_e - wellhead[0],
        args.target_n - wellhead[1],
        args.target_d - wellhead[2],
    )
    
    # 创建配置
    config = WellTrajectoryConfig(
        E_target=relative_target[0],
        N_target=relative_target[1],
        D_target=relative_target[2],
        E_wellhead=wellhead[0],
        N_wellhead=wellhead[1],
        D_wellhead=wellhead[2],
    )
    
    # 创建已有井障碍物
    well_obstacles = []
    if args.excel_files and args.wellhead_positions:
        obstacle_wellheads = [parse_triplet(pos) for pos in args.wellhead_positions]
        well_obstacles = create_multiple_well_obstacles(
            args.excel_files,
            wellhead_positions=obstacle_wellheads,
            safety_radius=10.0,
            segment_length=150.0,
        )
        print(f"✅ 加载了 {len(well_obstacles)} 个已有井")
    
    # 可视化
    visualize_optimization_result(
        optimal_params=optimal_params,
        config=config,
        well_obstacles=well_obstacles,
        wellhead_position=wellhead,
        save_path=args.save_path,
        show=not args.no_show,
        show_parameter_info=not args.no_param_info,
    )


if __name__ == "__main__":
    main()

