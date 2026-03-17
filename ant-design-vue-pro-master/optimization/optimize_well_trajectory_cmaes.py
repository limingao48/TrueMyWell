#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""独立的 CMA-ES 井轨迹优化模块。"""

import random
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from well_trajectory_objective import (
    WellTrajectoryConfig,
    create_multiple_well_obstacles,
    create_objective_function,
)


class CMAESWellTrajectoryOptimizer:
    """CMA-ES 井轨迹优化器（固定轮数运行，不保存CSV/收敛图）。"""

    def __init__(
        self,
        target_e: float,
        target_n: float,
        target_d: float,
        wellhead_position: Optional[Tuple[float, float, float]] = None,
        excel_files: Optional[List[str]] = None,
        wellhead_positions: Optional[List[Tuple[float, float, float]]] = None,
        population_size: Optional[int] = None,
        max_iterations: int = 500,
        sigma0: float = 0.3,
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
        self.sigma0 = float(sigma0)
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

        if population_size is None:
            population_size = 4 + int(3 * np.log(self.dimension))
        self.population_size = int(max(4, population_size))

    def optimize(self) -> Dict[str, Any]:
        start_time = time.time()

        n = self.dimension
        lam = self.population_size
        mu = lam // 2

        # Recombination weights
        weights = np.log(mu + 0.5) - np.log(np.arange(1, mu + 1))
        weights = weights / np.sum(weights)
        mu_eff = 1.0 / np.sum(weights**2)

        # Strategy parameter setting: Adaptation
        c_sigma = (mu_eff + 2) / (n + mu_eff + 5)
        d_sigma = 1 + 2 * max(0.0, np.sqrt((mu_eff - 1) / (n + 1)) - 1) + c_sigma
        c_c = (4 + mu_eff / n) / (n + 4 + 2 * mu_eff / n)
        c1 = 2 / ((n + 1.3) ** 2 + mu_eff)
        c_mu = min(1 - c1, 2 * (mu_eff - 2 + 1 / mu_eff) / ((n + 2) ** 2 + mu_eff))

        # Init
        x_mean = (self.lower + self.upper) / 2.0
        sigma = self.sigma0 * float(np.mean(self.upper - self.lower))
        sigma = max(1e-12, sigma)

        C = np.eye(n)
        p_c = np.zeros(n)
        p_sigma = np.zeros(n)
        chi_n = np.sqrt(n) * (1 - 1 / (4 * n) + 1 / (21 * n**2))

        B = np.eye(n)
        D = np.ones(n)

        best_solution = x_mean.copy()
        best_fitness = float(self.objective.calculate_objective(best_solution))
        fitness_history: List[float] = [best_fitness]

        first_hit_time = None
        first_hit_iter = None
        if best_fitness < self.hit_threshold:
            first_hit_time = 0.0
            first_hit_iter = 0

        for it in range(1, self.max_iterations + 1):
            # Sample offspring
            Z = np.random.randn(lam, n)
            Y = Z @ (B * D).T
            X = x_mean + sigma * Y
            X = np.clip(X, self.lower, self.upper)

            fit = np.array([self.objective.calculate_objective(x) for x in X], dtype=float)
            idx = np.argsort(fit)

            if float(fit[idx[0]]) < best_fitness:
                best_fitness = float(fit[idx[0]])
                best_solution = X[idx[0]].copy()

            # Recombination
            X_sel = X[idx[:mu]]
            old_mean = x_mean.copy()
            x_mean = np.sum(X_sel * weights[:, None], axis=0)
            x_mean = np.clip(x_mean, self.lower, self.upper)

            y_w = (x_mean - old_mean) / sigma

            # Update evolution path for sigma
            C_inv_sqrt = B @ np.diag(1.0 / np.maximum(D, 1e-20)) @ B.T
            p_sigma = (
                (1 - c_sigma) * p_sigma
                + np.sqrt(c_sigma * (2 - c_sigma) * mu_eff) * (C_inv_sqrt @ y_w)
            )

            # h_sig
            p_sigma_norm = np.linalg.norm(p_sigma)
            h_sig_cond = (
                p_sigma_norm / np.sqrt(1 - (1 - c_sigma) ** (2 * it))
                < (1.4 + 2 / (n + 1)) * chi_n
            )
            h_sig = 1.0 if h_sig_cond else 0.0

            # Update evolution path for covariance
            p_c = (1 - c_c) * p_c + h_sig * np.sqrt(c_c * (2 - c_c) * mu_eff) * y_w

            # Rank-mu update
            Y_sel = (X_sel - old_mean) / sigma
            rank_mu = np.zeros((n, n))
            for k in range(mu):
                rank_mu += weights[k] * np.outer(Y_sel[k], Y_sel[k])

            C = (
                (1 - c1 - c_mu) * C
                + c1 * (np.outer(p_c, p_c) + (1 - h_sig) * c_c * (2 - c_c) * C)
                + c_mu * rank_mu
            )

            # Keep numerical stability
            C = 0.5 * (C + C.T)
            eigvals, B = np.linalg.eigh(C)
            eigvals = np.maximum(eigvals, 1e-20)
            D = np.sqrt(eigvals)
            C = B @ np.diag(eigvals) @ B.T

            # Step size control
            sigma *= np.exp((c_sigma / d_sigma) * (p_sigma_norm / chi_n - 1.0))
            sigma = max(1e-12, sigma)

            fitness_history.append(best_fitness)

            if first_hit_time is None and best_fitness < self.hit_threshold:
                first_hit_time = time.time() - start_time
                first_hit_iter = it

            if it % 10 == 0:
                print(f"CMA-ES Iter {it}: Best Fitness = {best_fitness:.6f}")

        elapsed = time.time() - start_time

        result = {
            "best_solution": best_solution,
            "best_fitness": best_fitness,
            "total_iterations": len(fitness_history) - 1,
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


def optimize_well_trajectory_cmaes(
    target_e,
    target_n,
    target_d,
    wellhead_position=(0, 0, 0),
    excel_files=None,
    wellhead_positions=None,
    population_size=None,
    max_iterations=500,
    sigma0=0.3,
    random_seed=42,
    hit_threshold=1e5,
):
    optimizer = CMAESWellTrajectoryOptimizer(
        target_e=target_e,
        target_n=target_n,
        target_d=target_d,
        wellhead_position=wellhead_position,
        excel_files=excel_files,
        wellhead_positions=wellhead_positions,
        population_size=population_size,
        max_iterations=max_iterations,
        sigma0=sigma0,
        random_seed=random_seed,
        hit_threshold=hit_threshold,
    )
    return optimizer.optimize()
