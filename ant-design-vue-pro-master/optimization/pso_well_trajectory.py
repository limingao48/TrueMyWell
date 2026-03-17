#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""七段式井眼轨迹 PSO 优化入口。"""

import random
import time
from typing import Dict, Any, Optional, Tuple, List

import numpy as np

from optimization_workflow import (
    generate_seven_segment_trajectory,
    quick_visualize_seven_segment,
)
from well_trajectory_objective import (
    WellTrajectoryConfig,
    create_multiple_well_obstacles,
    create_objective_function,
)


SEVEN_SEG_PARAM_NAMES = ["L0", "DLS1", "alpha3", "L3", "DLS_turn", "L4", "L5", "DLS6", "alpha_e", "L7", "phi_init", "phi_target"]

SPATIAL_SEVEN_SEG_DEFAULT = {
    "L0": 900.0,
    "DLS1": 2.4,
    "alpha3": 42.0,
    "L3": 750.0,
    "DLS_turn": 2.0,
    "L4": 600.0,
    "L5": 600.0,
    "DLS6": 1.5,
    "alpha_e": 35.0,
    "L7": 900.0,
    "phi_init": 65.0,
    "phi_target": 95.0,
}


class SevenSegmentPSO:
    """七段式井轨迹参数 PSO（对接 well_trajectory_objective 的权重目标函数）。"""

    def __init__(self,
                 target_e: float,
                 target_n: float,
                 target_d: float,
                 wellhead_position: Tuple[float, float, float] = (0, 0, 0),
                 excel_files: Optional[List[str]] = None,
                 wellhead_positions: Optional[List[Tuple[float, float, float]]] = None,
                 safety_radius: float = 10.0,
                 segment_length: float = 150.0,
                 population_size: int = 60,
                 max_iterations: int = 400,
                 w: float = 0.72,
                 c1: float = 1.49,
                 c2: float = 1.49,
                 random_seed: Optional[int] = None,
                 hit_threshold: float = 30.0,
                 w_target: float = 1e5,
                 w_length: float = 1.0,
                 w_collision_hard: float = 1e8,
                 hard_collision_penalty: float = 1e24,
                 depth_step: float = 10.0):
        self.target_e = float(target_e)
        self.target_n = float(target_n)
        self.target_d = float(target_d)
        self.wellhead_position = tuple(float(v) for v in wellhead_position)

        self.rel_target_e = self.target_e - self.wellhead_position[0]
        self.rel_target_n = self.target_n - self.wellhead_position[1]
        self.rel_target_d = self.target_d - self.wellhead_position[2]

        self.population_size = int(population_size)
        self.max_iterations = int(max_iterations)
        self.w = float(w)
        self.c1 = float(c1)
        self.c2 = float(c2)
        self.random_seed = random_seed
        self.hit_threshold = float(hit_threshold)

        if random_seed is not None:
            random.seed(random_seed)
            np.random.seed(random_seed)

        # 对接 objective_function：七段式权重目标（先入靶、后最小井深、硬防碰）
        self.config = WellTrajectoryConfig(
            E_target=self.rel_target_e,
            N_target=self.rel_target_n,
            D_target=self.rel_target_d,
            E_wellhead=0.0,
            N_wellhead=0.0,
            D_wellhead=0.0,
            safety_radius=float(safety_radius),
            target_deviation_threshold=float(hit_threshold),
        )

        self.well_obstacles = []
        if excel_files and wellhead_positions:
            try:
                self.well_obstacles = create_multiple_well_obstacles(
                    excel_files=excel_files,
                    wellhead_positions=wellhead_positions,
                    safety_radius=float(safety_radius),
                    segment_length=float(segment_length),
                )
            except Exception as e:
                print(f"加载已有井轨迹失败，继续无障碍优化: {e}")
                self.well_obstacles = []

        self.objective = create_objective_function(
            config=self.config,
            well_obstacles=self.well_obstacles,
            objective_mode="seven_segment_weighted",
            objective_weights={
                "hit_threshold": float(hit_threshold),
                "w_target": float(w_target),
                "w_length": float(w_length),
                "w_collision_soft": 0.0,
                "w_collision_hard": float(w_collision_hard),
                "collision_buffer_factor": 1.0,
                "hard_collision_penalty": float(hard_collision_penalty),
                "depth_step": float(depth_step),
            },
        )
        bounds = self.config.get_seven_segment_parameter_bounds()
        self.lower = bounds[:, 0].astype(float)
        self.upper = bounds[:, 1].astype(float)
        self.dim = len(self.config.SEVEN_SEG_PARAM_NAMES)

        # 初始中心可用默认参数，提升稳定性
        self.default_vec = np.array([float(SPATIAL_SEVEN_SEG_DEFAULT[n]) for n in SEVEN_SEG_PARAM_NAMES], dtype=float)

    @staticmethod
    def _vec_to_params(vec: np.ndarray) -> Dict[str, float]:
        return {k: float(v) for k, v in zip(SEVEN_SEG_PARAM_NAMES, vec)}

    def _objective(self, vec: np.ndarray) -> float:
        p = self._vec_to_params(vec)
        return float(self.objective.calculate_objective(p))

    def optimize(self) -> Dict[str, Any]:
        start = time.time()

        X = np.random.uniform(self.lower, self.upper, size=(self.population_size, self.dim))
        # 用默认参数替换第一个粒子，作为稳定初值
        X[0] = np.clip(self.default_vec, self.lower, self.upper)

        span = self.upper - self.lower
        V = np.random.uniform(-0.1 * span, 0.1 * span, size=(self.population_size, self.dim))

        P = X.copy()
        P_fit = np.array([self._objective(x) for x in X], dtype=float)

        g_idx = int(np.argmin(P_fit))
        G = P[g_idx].copy()
        G_fit = float(P_fit[g_idx])

        fitness_history: List[float] = [G_fit]
        first_hit_time = None
        first_hit_iter = None

        # 用几何偏差判定是否入靶（与目标函数口径一致）
        g_traj = generate_seven_segment_trajectory(custom_params=self._vec_to_params(G), ds=10.0)
        g_dev = float(np.sqrt(
            (g_traj["E"][-1] - self.rel_target_e) ** 2 +
            (g_traj["N"][-1] - self.rel_target_n) ** 2 +
            (g_traj["D"][-1] - self.rel_target_d) ** 2
        ))
        if g_dev <= self.hit_threshold:
            first_hit_time = 0.0
            first_hit_iter = 0

        for it in range(1, self.max_iterations + 1):
            r1 = np.random.rand(self.population_size, self.dim)
            r2 = np.random.rand(self.population_size, self.dim)

            V = self.w * V + self.c1 * r1 * (P - X) + self.c2 * r2 * (G - X)
            X = np.clip(X + V, self.lower, self.upper)

            fit = np.array([self._objective(x) for x in X], dtype=float)
            improved = fit < P_fit
            P[improved] = X[improved]
            P_fit[improved] = fit[improved]

            g_idx = int(np.argmin(P_fit))
            if float(P_fit[g_idx]) < G_fit:
                G = P[g_idx].copy()
                G_fit = float(P_fit[g_idx])

            fitness_history.append(G_fit)

            if first_hit_time is None:
                g_traj = generate_seven_segment_trajectory(custom_params=self._vec_to_params(G), ds=10.0)
                g_dev = float(np.sqrt(
                    (g_traj["E"][-1] - self.rel_target_e) ** 2 +
                    (g_traj["N"][-1] - self.rel_target_n) ** 2 +
                    (g_traj["D"][-1] - self.rel_target_d) ** 2
                ))
                if g_dev <= self.hit_threshold:
                    first_hit_time = time.time() - start
                    first_hit_iter = it

            if it % 20 == 0:
                print(f"Seven-Segment PSO Iter {it}: best={G_fit:.4f}")

        elapsed = time.time() - start

        best_params = self._vec_to_params(G)
        best_traj = generate_seven_segment_trajectory(custom_params=best_params, ds=10.0)
        end_dev = float(np.sqrt(
            (best_traj["E"][-1] - self.rel_target_e) ** 2 +
            (best_traj["N"][-1] - self.rel_target_n) ** 2 +
            (best_traj["D"][-1] - self.rel_target_d) ** 2
        ))

        return {
            "best_solution": G,
            "best_solution_dict": best_params,
            "best_fitness": float(G_fit),
            "total_iterations": self.max_iterations,
            "optimization_time": float(elapsed),
            "time_to_target_seconds": first_hit_time,
            "hit_iteration": first_hit_iter,
            "fitness_history": fitness_history,
            "final_deviation": end_dev,
            "segment_lengths": best_traj["segment_lengths"],
            "total_length": best_traj["total_length"],
        }


def optimize_seven_segment_well_trajectory_pso(target_e,
                                               target_n,
                                               target_d,
                                               wellhead_position=(0, 0, 0),
                                               excel_files=None,
                                               wellhead_positions=None,
                                               safety_radius=10.0,
                                               segment_length=150.0,
                                               population_size=60,
                                               max_iterations=400,
                                               w=0.72,
                                               c1=1.49,
                                               c2=1.49,
                                               random_seed=45,
                                               hit_threshold=30.0,
                                               w_target=1e5,
                                               w_length=1.0,
                                               w_collision_hard=1e8,
                                               hard_collision_penalty=1e24,
                                               depth_step=10.0):
    """统一接口：对接 well_trajectory_objective 七段式权重目标函数。"""
    optimizer = SevenSegmentPSO(
        target_e=target_e,
        target_n=target_n,
        target_d=target_d,
        wellhead_position=wellhead_position,
        excel_files=excel_files,
        wellhead_positions=wellhead_positions,
        safety_radius=safety_radius,
        segment_length=segment_length,
        population_size=population_size,
        max_iterations=max_iterations,
        w=w,
        c1=c1,
        c2=c2,
        random_seed=random_seed,
        hit_threshold=hit_threshold,
        w_target=w_target,
        w_length=w_length,
        w_collision_hard=w_collision_hard,
        hard_collision_penalty=hard_collision_penalty,
        depth_step=depth_step,
    )
    return optimizer.optimize()


def main():
    target_e, target_n, target_d = 1500.64, 1200.71, 2936.06
    wellhead_position = (0, 0, 0)

    result = optimize_seven_segment_well_trajectory_pso(
        target_e=target_e,
        target_n=target_n,
        target_d=target_d,
        wellhead_position=wellhead_position,
        population_size=60,
        max_iterations=300,
        w=0.72,
        c1=1.49,
        c2=1.49,
        random_seed=45,
        hit_threshold=30.0,
    )

    print("=" * 60)
    print(f"七段式PSO最佳适应度: {result['best_fitness']:.6f}")
    print(f"七段式PSO终点偏差: {result['final_deviation']:.3f} m")
    print("七段式PSO最佳参数:")
    for k, v in result["best_solution_dict"].items():
        print(f"  {k}: {v:.4f}")
    print("=" * 60)

    quick_visualize_seven_segment(
        custom_params=result["best_solution_dict"],
        target=(target_e, target_n, target_d),
        wellhead_position=wellhead_position,
        save_filename="seven_segment_pso_result.png",
        ds=10.0,
    )


if __name__ == "__main__":
    main()
