#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""轨迹设计：GA-optiGAN 命令行入口（供 Java 后端调用）。"""

import argparse
import json
import os
import sys
import time
import traceback
from typing import Any, Dict, List, Optional, Tuple

# 保证 optimization 目录在 path 中
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from well_trajectory_objective.objective_function import SEVEN_SEG_PARAM_NAMES


def _write_progress(progress_path: Optional[str], payload: Dict[str, Any]) -> None:
    if not progress_path:
        return
    try:
        with open(progress_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
    except OSError:
        pass


def _apply_design_constraints(config, payload: Dict[str, Any]) -> None:
    """与 Java OptimizationTaskManager 对齐的七段式边界约束。"""
    algo = payload.get("algorithm") or {}
    landing = payload.get("landingRequirement") or {}

    min_kop = algo.get("minKickoffDepth")
    if min_kop is not None:
        lo, hi = config.seven_L0_range
        config.seven_L0_range = (max(0.0, float(min_kop)), hi)

    dogleg_min = algo.get("doglegMin")
    dogleg_max = algo.get("doglegMax")
    if dogleg_min is not None:
        dmin = max(0.1, float(dogleg_min))
        config.seven_DLS1_range = (dmin, config.seven_DLS1_range[1])
        config.seven_DLS_turn_range = (dmin, config.seven_DLS_turn_range[1])
        config.seven_DLS6_range = (dmin, config.seven_DLS6_range[1])
    if dogleg_max is not None:
        dmax = float(dogleg_max)
        config.seven_DLS1_range = (config.seven_DLS1_range[0], max(config.seven_DLS1_range[0], dmax))
        config.seven_DLS_turn_range = (config.seven_DLS_turn_range[0], max(config.seven_DLS_turn_range[0], dmax))
        config.seven_DLS6_range = (config.seven_DLS6_range[0], max(config.seven_DLS6_range[0], dmax))

    inc_min = landing.get("inclinationMin")
    inc_max = landing.get("inclinationMax")
    if inc_min is not None and inc_max is not None:
        a, b = float(inc_min), float(inc_max)
        if a > b:
            a, b = b, a
        config.seven_alpha_e_range = (a, b)

    azi_min = landing.get("azimuthMin")
    azi_max = landing.get("azimuthMax")
    if azi_min is not None and azi_max is not None:
        az0, az1 = float(azi_min), float(azi_max)
        if az0 <= az1:
            config.seven_phi_target_range = (az0, az1)
        else:
            config.seven_phi_target_range = (0.0, 360.0)

    if landing.get("verticalTolerance") is not None:
        config.vertical_tolerance = float(landing["verticalTolerance"])
    if landing.get("horizontalTolerance") is not None:
        config.horizontal_tolerance = float(landing["horizontalTolerance"])

    lo, hi = config.seven_L0_range
    config.seven_L0_range = (lo, max(hi, lo + 1.0))


def _trajectory_to_points(
    trajectory_info: Dict[str, Any],
    wellhead: Tuple[float, float, float],
) -> List[Dict[str, float]]:
    traj = trajectory_info.get("trajectory")
    if traj is None:
        return []
    if isinstance(traj, dict):
        x = traj.get("x") or traj.get("E")
        y = traj.get("y") or traj.get("N")
        z = traj.get("z") or traj.get("D")
    else:
        x, y, z = traj[0], traj[1], traj[2]
    we, wn, wd = wellhead
    points = []
    n = min(len(x), len(y), len(z))
    for i in range(n):
        # Python 目标函数使用相对井口坐标，返回前端/库表需加井口偏移为绝对 E/N/D
        points.append({
            "x": float(x[i]) + we,
            "y": float(y[i]) + wn,
            "z": float(z[i]) + wd,
        })
    return points


def run_design(payload: Dict[str, Any], progress_path: Optional[str] = None) -> Dict[str, Any]:
    target = payload.get("target") or {}
    wellhead = payload.get("wellhead") or {}
    algo = payload.get("algorithm") or {}

    target_e = float(target.get("e", 0))
    target_n = float(target.get("n", 0))
    target_d = float(target.get("d", 0))
    wh = (
        float(wellhead.get("e", 0)),
        float(wellhead.get("n", 0)),
        float(wellhead.get("d", 0)),
    )

    excel_files: List[str] = []
    wellhead_positions: List[Tuple[float, float, float]] = []
    for nb in payload.get("neighborWells") or []:
        path = nb.get("excelPath")
        if path and os.path.isfile(path):
            excel_files.append(path)
            wh_nb = nb.get("wellhead") or {}
            wellhead_positions.append(
                (
                    float(wh_nb.get("e", 0)),
                    float(wh_nb.get("n", 0)),
                    float(wh_nb.get("d", 0)),
                )
            )

    population = int(algo.get("population") or 100)
    max_evaluations = int(algo.get("maxEvaluations") or 30000)
    opt_size = int(algo.get("optSize") or min(300, max_evaluations // 2))
    progress_total = max(100, min(max_evaluations, 100000))

    _write_progress(
        progress_path,
        {
            "iteration": 0,
            "totalIterations": progress_total,
            "currentBest": None,
            "progressPercent": 2.0,
            "message": "GA-optiGAN 初始化中（加载 PyTorch 与邻井数据）...",
        },
    )

    start = time.time()
    try:
        from optimize_well_trajectory_ga_optigan import GAOptiGANWellTrajectoryOptimizer

        optimizer = GAOptiGANWellTrajectoryOptimizer(
            target_e=target_e,
            target_n=target_n,
            target_d=target_d,
            wellhead_position=wh,
            excel_files=excel_files or None,
            wellhead_positions=wellhead_positions or None,
            safety_radius=float(algo.get("safeRadius") or 10.0),
            hit_threshold=float(algo.get("hitThreshold") or 30.0),
            max_evaluations=max_evaluations,
            population_size=population,
            opt_size=opt_size,
            random_seed=int(algo.get("randomSeed") or 42),
            optigan_dir=algo.get("optiganDir"),
        )
        _apply_design_constraints(optimizer.config, payload)
        bounds = optimizer.config.get_seven_segment_parameter_bounds()
        optimizer.lower = bounds[:, 0].astype(float)
        optimizer.upper = bounds[:, 1].astype(float)
        optimizer.dimension = len(optimizer.lower)

        _write_progress(
            progress_path,
            {
                "iteration": 1,
                "totalIterations": progress_total,
                "currentBest": None,
                "progressPercent": 8.0,
                "message": f"GA-optiGAN 优化运行中（最大评估 {max_evaluations} 次，含 GAN 预训练）...",
            },
        )

        raw = optimizer.optimize()
    except Exception:
        traceback.print_exc()
        raise

    elapsed = time.time() - start
    best_solution_dict = raw.get("best_solution_dict")
    final_deviation = raw.get("final_deviation")
    trajectory_points: List[Dict[str, float]] = []
    traj_info = raw.get("trajectory_info")
    if isinstance(traj_info, dict):
        trajectory_points = _trajectory_to_points(traj_info, wh)

    if best_solution_dict is None and raw.get("best_solution") is not None:
        sol = raw["best_solution"]
        best_solution_dict = {
            k: float(v) for k, v in zip(SEVEN_SEG_PARAM_NAMES, list(sol))
        }

    best_fitness = raw.get("best_fitness")
    _write_progress(
        progress_path,
        {
            "iteration": progress_total,
            "totalIterations": progress_total,
            "currentBest": float(best_fitness) if best_fitness is not None else None,
            "progressPercent": 100.0,
            "message": "GA-optiGAN 优化完成",
            "completed": True,
        },
    )

    return {
        "success": best_solution_dict is not None,
        "best_solution_dict": best_solution_dict,
        "final_deviation": final_deviation,
        "optimization_time": float(raw.get("optimization_time") or elapsed),
        "best_fitness": best_fitness,
        "total_evaluations": raw.get("total_evaluations"),
        "trajectory_points": trajectory_points,
        "error": None if best_solution_dict else "未得到有效最优解",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="GA-optiGAN trajectory design CLI")
    parser.add_argument("--input", required=True, help="输入 JSON 路径")
    parser.add_argument("--output", required=True, help="输出 JSON 路径")
    parser.add_argument("--progress", default=None, help="进度 JSON 路径（可选）")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        payload = json.load(f)

    try:
        result = run_design(payload, progress_path=args.progress)
        result["success"] = bool(result.get("success"))
    except Exception as exc:
        result = {
            "success": False,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }
        _write_progress(
            args.progress,
            {
                "message": "GA-optiGAN 失败: " + str(exc),
                "progressPercent": 100.0,
                "completed": True,
                "failed": True,
            },
        )

    os.makedirs(os.path.dirname(os.path.abspath(args.output)) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return 0 if result.get("success") else 1


if __name__ == "__main__":
    sys.exit(main())
