#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
七段式井眼轨迹统一优化入口（已彻底放弃原先五段式/8参数流程）。

说明：
- 当前仓库内稳定可用的七段式优化器为 PSO：
  optimize_seven_segment_well_trajectory_pso
- 若后续新增 CMA-ES/L-SHADE/SA 的七段式版本，可按同一接口继续扩展。
"""

import time
import random
from typing import Dict, Any, Optional

from pso_well_trajectory import optimize_seven_segment_well_trajectory_pso
from optimize_well_trajectory_b2opt import optimize_well_trajectory_b2opt
from optimize_well_trajectory_ga_optigan import optimize_well_trajectory_ga_optigan
from optimization_workflow import run_optimization_workflow, quick_visualize_seven_segment


def optimize_well_trajectory(
    target_e: float,
    target_n: float,
    target_d: float,
    wellhead_position=(0, 0, 0),
    excel_files=None,
    wellhead_positions=None,
    optimizer_fn=optimize_seven_segment_well_trajectory_pso,
    optimizer_kwargs: Optional[Dict[str, Any]] = None,
):
    """七段式统一优化调用（仅七段式优化器）。"""
    if optimizer_kwargs is None:
        optimizer_kwargs = {}

    return run_optimization_workflow(
        target_e=target_e,
        target_n=target_n,
        target_d=target_d,
        wellhead_position=wellhead_position,
        excel_files=excel_files,
        wellhead_positions=wellhead_positions,
        optimizer_fn=optimizer_fn,
        optimizer_kwargs=optimizer_kwargs,
        auto_plot=False,
        plot_save_path="../ga_population_boxplot_from_csv.png",
    )


def main():
    print("七段式井轨迹优化示例（统一七段式，含邻井避障）")
    print("=" * 56)

    # ===== 场景配置 =====
    target_e, target_n, target_d =502.64, 2790.71, 2636.06
    wellhead_position = (222, 2030, 0)
    # target_e, target_n, target_d = -216.87, 3883.71, 2536.06
    # wellhead_position = (222, 2030, 0)
# DEFAULT_TARGET = (502.64, 790.71, 2636.06)
# DEFAULT_WELLHEAD = (254.0, 2030.0, 0.0)
    # 邻井数据（用于防碰）
    excel_files = ["41-37YH3.xlsx", "41-37YH5.xlsx"]
    wellhead_positions = [(208, 2015, 0.0), (209, 2000, 0.0)]

    # ===== 优化器开关（七段式）：PSO / B2OPT / GA-optiGAN =====
    # 可选：  optimize_seven_segment_well_trajectory_pso / optimize_well_trajectory_b2opt / optimize_well_trajectory_ga_optigan
    optimizer_fn = optimize_seven_segment_well_trajectory_pso
    rand_seed = random.randint(1, 99)
    print("random_seed:", rand_seed)

    if optimizer_fn is optimize_seven_segment_well_trajectory_pso:
        optimizer_kwargs = {
            # PSO主参数
            "population_size": 100,
            "max_iterations": 100,
            "w": 1.10,
            "c1": 1.49,
            "c2": 0.49,
            "random_seed": rand_seed,

            # 七段式目标函数权重（先入靶、后井深、硬防碰）
            "hit_threshold": 30.0,
            "w_target": 1e5,
            "w_length": 1.0,
            "w_collision_hard": 1e8,
            "hard_collision_penalty": 1e24,

            # 防碰扫描配置
            "safety_radius": 10.0,
            "segment_length": 150.0,
            "depth_step": 10.0,
        }
    elif optimizer_fn is optimize_well_trajectory_ga_optigan:
        optimizer_kwargs = {
            # GA-optiGAN 主参数（可按资源调节）
            "max_evaluations": 30000,
            "population_size": 100,
            "opt_size": 300,
            "gamma": 1.2,
            "lambda2": 0.3,
            "pretrain": 1,
            "epochs": 150,
            "d_iter": 4,
            "gen_n": 10,
            "elite_ratio": 0.5,
            "random_seed": rand_seed,
            "train_every": 3,
            "random_injection_ratio": 0.10,
            "stagnation_patience": 30,
            "reheat_factor": 1.5,
            "refine_mode": True,
            "residual_strength": 0.08,
            # 与七段式 PSO 一致的目标函数权重与防碰配置
            "hit_threshold": 30.0,
            "w_target": 1e5,
            "w_length": 1.0,
            "w_collision_hard": 1e8,
            "hard_collision_penalty": 1e24,
            "safety_radius": 10.0,
            "segment_length": 150.0,
            "depth_step": 10.0,
        }
    elif optimizer_fn is optimize_well_trajectory_b2opt:
        optimizer_kwargs = {
            # B2OPT主参数（可按机器资源调节）
            "b2opt_project_dir": "/home/lma/aaa/12/MLROpt",
            "checkpoint": "/home/lma/aaa/12/MLROpt/ckpt/well_traj_b2opt_diversity_ems_50_ws_True_d12_20260306_181522.pth",
            "hidden_dim": 200,
            "population_size": 100,
            "ems": 50,
            "max_evaluations": 10000,
            "print_interval": 10,
            "random_seed": rand_seed,
            "use_normalization": True,
            # "mode": "hybrid",

            # 与七段式PSO一致的目标函数权重模板
            "hit_threshold": 30,
            "w_target": 1e5,
            "w_length": 1.0,
            "w_collision_hard": 1e8,
            "hard_collision_penalty": 1e24,

            # 防碰扫描配置（与PSO保持一致）
            "safety_radius": 10.0,
            "segment_length": 150.0,
            "depth_step": 10.0,
        }
    else:
        raise ValueError("仅支持七段式 PSO、B2OPT 或 GA-optiGAN")

    total_start = time.time()
    result = optimize_well_trajectory(
        target_e=target_e,
        target_n=target_n,
        target_d=target_d,
        wellhead_position=wellhead_position,
        excel_files=excel_files,
        wellhead_positions=wellhead_positions,
        optimizer_fn=optimizer_fn,
        optimizer_kwargs=optimizer_kwargs,
    )

    print("\n" + "=" * 56)
    print(f"最佳适应度: {result['best_fitness']:.6f}")
    print(f"最佳参数: {result.get('best_solution_dict', result['best_solution'])}")
    if result.get("final_deviation") is not None:
        print(f"终点偏差: {result['final_deviation']:.3f} m")
    if result.get("time_to_target_seconds") is not None:
        print(f"达到入靶阈值({optimizer_kwargs['hit_threshold']}m)用时: {result['time_to_target_seconds']:.3f} 秒")
    else:
        print(f"达到入靶阈值({optimizer_kwargs['hit_threshold']}m)用时: 未入靶")
    if result.get("optimization_time") is not None:
        print(f"优化阶段总耗时: {result['optimization_time']:.3f} 秒")

    # 七段式结果可视化（叠加邻井）
    quick_visualize_seven_segment(
        custom_params=result["best_solution_dict"],
        target=(target_e, target_n, target_d),
        wellhead_position=wellhead_position,
        excel_files=excel_files,
        wellhead_positions=wellhead_positions,
        safety_radius=optimizer_kwargs["safety_radius"],
        save_filename="seven_segment_minimal_result.png",
        ds=10.0,
    )

    total_elapsed = time.time() - total_start
    print(f"流程总耗时(优化+可视化): {total_elapsed:.3f} 秒")
    print("=" * 56)


if __name__ == "__main__":
    main()
