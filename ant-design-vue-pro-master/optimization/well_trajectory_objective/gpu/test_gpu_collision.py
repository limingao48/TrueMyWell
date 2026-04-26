"""
GPU 版分离系数测试脚本

运行前请准备：
1. `excel_files`: 现有井的井斜数据文件路径列表（可为空，示例中给出占位）
2. `wellhead_positions`: 每口井的井口坐标 (E, N, D)，长度需与 excel_files 对应
3. `params_tensor`: (batch_size, 8) 的候选井参数张量，顺序是
   [D_kop, alpha1, alpha2, phi1, phi2, R1, R2, D_turn_kop]，角度单位为“度”

脚本会构建 GPU 目标函数，批量计算目标值，并输出每个个体的最小分离系数是否低于 1。
"""

import torch
import numpy as np

from well_trajectory_objective import (
    WellTrajectoryConfig,
    create_multiple_well_obstacles,
)
from well_trajectory_objective.gpu import create_gpu_objective_function


def build_obstacles() -> list:
    """
    根据实际项目填写 Excel 路径和井口坐标。
    返回值：WellObstacleDetector 列表，可为空。
    """
    # 示例：请替换成真实文件与井口位置
    excel_files = [
        # r"D:\data\wells\well_A.xlsx",
        # r"D:\data\wells\well_B.xlsx",
    ]
    wellhead_positions = [
        # (E, N, D)
        # (100.0, 200.0, 0.0),
        # (150.0, 250.0, 0.0),
    ]

    if not excel_files:
        print("未提供障碍井，默认不进行分离系数检查。")
        return []

    obstacles = create_multiple_well_obstacles(
        excel_files=excel_files,
        wellhead_positions=wellhead_positions,
        safety_radius=15.0,
        segment_length=50.0,
    )
    return obstacles


def build_params_tensor(device: torch.device) -> torch.Tensor:
    """
    示例参数：生成 4 条随机井轨迹。
    实际使用时请替换成优化算法传入的 (batch_size, 8) 数组/张量。
    """
    batch_size = 4
    # 参数范围示例，可根据 config.BOUNDS 来生成
    params = np.array(
        [
            [950, 70, 90, 200, 90, 1200, 400, 2450],
            [960, 72, 91, 210, 88, 1100, 380, 2440],
            [930, 68, 89, 190, 92, 1250, 450, 2460],
            [970, 75, 92, 205, 89, 1180, 420, 2470],
        ],
        dtype=np.float32,
    )
    print(f"参数张量形状: {params.shape} (batch_size={batch_size}, dim=8)")
    return torch.tensor(params, device=device, dtype=torch.float32)


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"当前设备: {device}")

    config = WellTrajectoryConfig(
        E_target=1500.0,
        N_target=1200.0,
        D_target=2950.0,
        E_wellhead=0.0,
        N_wellhead=0.0,
    )

    well_obstacles = build_obstacles()

    objective_gpu = create_gpu_objective_function(
        config=config,
        well_obstacles=well_obstacles,
        device=device,
        n_points=50,
    )

    params_tensor = build_params_tensor(device)

    fitness = objective_gpu.calculate_objective_batch(params_tensor)
    print("适应度：", fitness.cpu().numpy())

    info = objective_gpu.calculate_objective_batch_with_info(params_tensor)
    if "collision_penalty" in info:
        print("碰撞惩罚：", info["collision_penalty"].cpu().numpy())
    print("是否有效：", info["is_valid"].cpu().numpy())


if __name__ == "__main__":
    main()

