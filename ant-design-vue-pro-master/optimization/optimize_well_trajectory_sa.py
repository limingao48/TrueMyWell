#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""独立的 SA（模拟退火）井轨迹优化模块。"""

import random
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from well_trajectory_objective import (
    WellTrajectoryConfig,
    create_multiple_well_obstacles,
    create_objective_function,
)


class SAWellTrajectoryOptimizer:
    """模拟退火井轨迹优化器。"""

    def __init__(
        self,
        target_e: float,
        target_n: float,
        target_d: float,
        wellhead_position: Optional[Tuple[float, float, float]] = None,
        excel_files: Optional[List[str]] = None,
        wellhead_positions: Optional[List[Tuple[float, float, float]]] = None,
        max_iterations: int = 5000,
        initial_temperature: float = 1000.0,
        cooling_rate: float = 0.995,
        min_temperature: float = 1e-6,
        step_scale: float = 0.08,
        random_seed: Optional[int] = None,
        hit_threshold: float = 1e5,
    ):
        if wellhead_position is None:
            wellhead_position = (0.0, 0.0, 0.0)

        self.target_e = float(target_e)
        self.target_n = float(target_n)
        self.target_d = float(target_d)
        self.wellhead_position = tuple(wellhead_position)

        self.relative_target_e = self.target_e - self.wellhead_position[0]
        self.relative_target_n = self.target_n - self.wellhead_position[1]
        self.relative_target_d = self.target_d - self.wellhead_position[2]

        self.max_iterations = int(max_iterations)
        self.initial_temperature = float(initial_temperature)
        self.cooling_rate = float(cooling_rate)
        self.min_temperature = float(min_temperature)
        self.step_scale = float(step_scale)
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
        self.span = self.upper - self.lower

    def _random_solution(self) -> np.ndarray:
        return np.random.uniform(self.lower, self.upper, size=self.dimension)

    def _neighbor(self, x: np.ndarray, temperature: float) -> np.ndarray:
        # 随温度下降逐步减小扰动步长，提升后期微调能力
        temp_ratio = max(temperature / max(self.initial_temperature, 1e-12), 1e-4)
        sigma = self.step_scale * self.span * temp_ratio
        step = np.random.normal(loc=0.0, scale=sigma, size=self.dimension)
        y = x + step
        return np.clip(y, self.lower, self.upper)

    def optimize(self) -> Dict[str, Any]:
        start_time = time.time()

        current = self._random_solution()
        current_fit = float(self.objective.calculate_objective(current))

        best_solution = current.copy()
        best_fitness = current_fit

        temperature = self.initial_temperature
        fitness_history: List[float] = [best_fitness]

        first_hit_time = None
        first_hit_iter = None
        if best_fitness < self.hit_threshold:
            first_hit_time = 0.0
            first_hit_iter = 0

        total_iterations = 0
        for it in range(1, self.max_iterations + 1):
            total_iterations = it

            candidate = self._neighbor(current, temperature)
            candidate_fit = float(self.objective.calculate_objective(candidate))

            delta = candidate_fit - current_fit
            if delta <= 0:
                accept = True
            else:
                prob = np.exp(-delta / max(temperature, 1e-12))
                accept = np.random.rand() < prob

            if accept:
                current = candidate
                current_fit = candidate_fit

            if current_fit < best_fitness:
                best_fitness = current_fit
                best_solution = current.copy()

            fitness_history.append(best_fitness)

            if first_hit_time is None and best_fitness < self.hit_threshold:
                first_hit_time = time.time() - start_time
                first_hit_iter = it

            if it % 50 == 0:
                print(
                    f"SA Iter {it}: Best Fitness = {best_fitness:.6f}, "
                    f"Current Temp = {temperature:.6e}"
                )

            temperature *= self.cooling_rate
            if temperature < self.min_temperature:
                break

        elapsed = time.time() - start_time

        result = {
            "best_solution": best_solution,
            "best_fitness": best_fitness,
            "total_iterations": total_iterations,
            "optimization_time": elapsed,
            "time_to_target_seconds": first_hit_time,
            "hit_threshold": self.hit_threshold,
            "hit_iteration": first_hit_iter,
            "fitness_history": fitness_history,
            "config": self.config,
        }

        info = self.objective.get_trajectory_info(best_solution)
        if info.get("success", False):
            result["trajectory_info"] = info

        return result


def optimize_well_trajectory_sa(
    target_e,
    target_n,
    target_d,
    wellhead_position=(0, 0, 0),
    excel_files=None,
    wellhead_positions=None,
    max_iterations=5000,
    initial_temperature=1000.0,
    cooling_rate=0.995,
    min_temperature=1e-6,
    step_scale=0.08,
    random_seed=42,
    hit_threshold=1e5,
):
    optimizer = SAWellTrajectoryOptimizer(
        target_e=target_e,
        target_n=target_n,
        target_d=target_d,
        wellhead_position=wellhead_position,
        excel_files=excel_files,
        wellhead_positions=wellhead_positions,
        max_iterations=max_iterations,
        initial_temperature=initial_temperature,
        cooling_rate=cooling_rate,
        min_temperature=min_temperature,
        step_scale=step_scale,
        random_seed=random_seed,
        hit_threshold=hit_threshold,
    )
    return optimizer.optimize()
