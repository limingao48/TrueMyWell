#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""独立的 PSO 井轨迹优化模块。"""

import random
import time
from typing import List, Tuple, Optional, Dict, Any

import numpy as np

from well_trajectory_objective import (
    WellTrajectoryConfig,
    create_multiple_well_obstacles,
    create_objective_function,
)


class PSOWellTrajectoryOptimizer:
    """粒子群井轨迹优化器（固定轮数运行，不保存CSV/收敛图）。"""

    def __init__(self,
                 target_e: float,
                 target_n: float,
                 target_d: float,
                 wellhead_position: Optional[Tuple[float, float, float]] = None,
                 excel_files: Optional[List[str]] = None,
                 wellhead_positions: Optional[List[Tuple[float, float, float]]] = None,
                 population_size: int = 40,
                 max_iterations: int = 500,
                 w: float = 0.72,
                 c1: float = 1.49,
                 c2: float = 1.49,
                 random_seed: Optional[int] = None,
                 hit_threshold: float = 1e5):
        if wellhead_position is None:
            wellhead_position = (0.0, 0.0, 0.0)

        self.target_e = float(target_e)
        self.target_n = float(target_n)
        self.target_d = float(target_d)
        self.wellhead_position = tuple(wellhead_position)

        self.relative_target_e = self.target_e - self.wellhead_position[0]
        self.relative_target_n = self.target_n - self.wellhead_position[1]
        self.relative_target_d = self.target_d - self.wellhead_position[2]

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

        self.config = WellTrajectoryConfig(
            E_target=self.relative_target_e,
            N_target=self.relative_target_n,
            D_target=self.relative_target_d,
        )

        self.well_obstacles = []
        if excel_files and wellhead_positions:
            self.well_obstacles = create_multiple_well_obstacles(
                excel_files,
                wellhead_positions=wellhead_positions,
                safety_radius=10.0,
                segment_length=150.0,
            )

        self.objective = create_objective_function(
            config=self.config,
            well_obstacles=self.well_obstacles,
            objective_mode="seven_segment_weighted",
            objective_weights={
                "hit_threshold": float(hit_threshold),
                "w_target": 1e5,
                "w_length": 1.0,
                "w_collision_soft": 0.0,
                "w_collision_hard": 1e8,
                "collision_buffer_factor": 1.0,
                "hard_collision_penalty": 1e24,
                "depth_step": 10.0,
            },
        )

        bounds = self.config.get_seven_segment_parameter_bounds()
        self.lower = bounds[:, 0].astype(float)
        self.upper = bounds[:, 1].astype(float)
        self.dimension = len(self.lower)

    def optimize(self) -> Dict[str, Any]:
        start_time = time.time()

        X = np.random.uniform(self.lower, self.upper, size=(self.population_size, self.dimension))
        v_span = (self.upper - self.lower)
        V = np.random.uniform(-0.1 * v_span, 0.1 * v_span, size=(self.population_size, self.dimension))

        P = X.copy()
        P_fit = np.array([self.objective.calculate_objective(x) for x in X], dtype=float)

        g_idx = int(np.argmin(P_fit))
        G = P[g_idx].copy()
        G_fit = float(P_fit[g_idx])

        fitness_history: List[float] = [G_fit]
        first_hit_time = None
        first_hit_iter = None

        if G_fit < self.hit_threshold:
            first_hit_time = 0.0
            first_hit_iter = 0

        # 固定轮数运行，不提前停止
        for it in range(1, self.max_iterations + 1):
            r1 = np.random.rand(self.population_size, self.dimension)
            r2 = np.random.rand(self.population_size, self.dimension)

            V = self.w * V + self.c1 * r1 * (P - X) + self.c2 * r2 * (G - X)
            X = X + V
            X = np.clip(X, self.lower, self.upper)

            fit = np.array([self.objective.calculate_objective(x) for x in X], dtype=float)
            improved = fit < P_fit
            P[improved] = X[improved]
            P_fit[improved] = fit[improved]

            g_idx = int(np.argmin(P_fit))
            if float(P_fit[g_idx]) < G_fit:
                G = P[g_idx].copy()
                G_fit = float(P_fit[g_idx])

            fitness_history.append(G_fit)

            if first_hit_time is None and G_fit < self.hit_threshold:
                first_hit_time = time.time() - start_time
                first_hit_iter = it

            if it % 10 == 0:
                print(f"PSO Iter {it}: Best Fitness = {G_fit:.6f}")

        elapsed = time.time() - start_time

        result = {
            'best_solution': G,
            'best_fitness': G_fit,
            'total_iterations': len(fitness_history) - 1,
            'optimization_time': elapsed,
            'time_to_target_seconds': first_hit_time,
            'hit_threshold': self.hit_threshold,
            'hit_iteration': first_hit_iter,
            'fitness_history': fitness_history,
            'config': self.config,
        }

        info = self.objective.get_trajectory_info(G)
        if info.get('success', False):
            result['trajectory_info'] = info

        return result


def optimize_well_trajectory_pso(target_e, target_n, target_d,
                                 wellhead_position=(0, 0, 0),
                                 excel_files=None, wellhead_positions=None,
                                 population_size=40, max_iterations=500,
                                 w=0.72, c1=1.49, c2=1.49,
                                 random_seed=42,
                                 hit_threshold=1e5):
    optimizer = PSOWellTrajectoryOptimizer(
        target_e=target_e,
        target_n=target_n,
        target_d=target_d,
        wellhead_position=wellhead_position,
        excel_files=excel_files,
        wellhead_positions=wellhead_positions,
        population_size=population_size,
        max_iterations=max_iterations,
        w=w,
        c1=c1,
        c2=c2,
        random_seed=random_seed,
        hit_threshold=hit_threshold,
    )
    return optimizer.optimize()
