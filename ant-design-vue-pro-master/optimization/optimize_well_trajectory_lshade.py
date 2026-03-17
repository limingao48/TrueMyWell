#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""独立的 L-SHADE 井轨迹优化模块。"""

import random
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from well_trajectory_objective import (
    WellTrajectoryConfig,
    create_multiple_well_obstacles,
    create_objective_function,
)


def _weighted_lehmer_mean(values: np.ndarray, weights: np.ndarray) -> float:
    denom = np.sum(weights * values)
    if denom <= 1e-20:
        return float(np.mean(values))
    return float(np.sum(weights * (values ** 2)) / denom)


class LSHADEWellTrajectoryOptimizer:
    """L-SHADE 井轨迹优化器（线性种群缩减 + 成功历史参数记忆）。"""

    def __init__(
        self,
        target_e: float,
        target_n: float,
        target_d: float,
        wellhead_position: Optional[Tuple[float, float, float]] = None,
        excel_files: Optional[List[str]] = None,
        wellhead_positions: Optional[List[Tuple[float, float, float]]] = None,
        population_size: int = 100,
        max_evaluations: int = 40000,
        memory_size: int = 6,
        p_best_rate: float = 0.11,
        min_population_size: int = 4,
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

        self.initial_population_size = int(population_size)
        self.max_evaluations = int(max_evaluations)
        self.memory_size = int(memory_size)
        self.p_best_rate = float(p_best_rate)
        self.min_population_size = int(min_population_size)
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

        if self.initial_population_size < self.min_population_size:
            raise ValueError("population_size 不能小于 min_population_size")

    def _sample_cr_f(self, m_cr: np.ndarray, m_f: np.ndarray, mem_idx: int) -> Tuple[float, float]:
        # CR ~ N(M_CR[k], 0.1)
        cr = np.random.normal(loc=m_cr[mem_idx], scale=0.1)
        cr = float(np.clip(cr, 0.0, 1.0))

        # F ~ Cauchy(M_F[k], 0.1), 重采样直到 F>0
        f = -1.0
        while f <= 0.0:
            f = np.random.standard_cauchy() * 0.1 + m_f[mem_idx]
        f = float(min(f, 1.0))

        return cr, f

    def _current_to_pbest_1_bin(
        self,
        i: int,
        X: np.ndarray,
        A: np.ndarray,
        F: float,
        CR: float,
        pbest_index: int,
    ) -> np.ndarray:
        npop = X.shape[0]

        # r1 from population, r1 != i
        r1 = i
        while r1 == i:
            r1 = np.random.randint(0, npop)

        # r2 from population union archive, and != i, != r1
        U = np.vstack([X, A]) if len(A) > 0 else X
        total_u = U.shape[0]
        r2 = np.random.randint(0, total_u)

        # ensure different vectors for mutation sources
        retry = 0
        while (
            np.array_equal(U[r2], X[i])
            or np.array_equal(U[r2], X[r1])
            or np.array_equal(U[r2], X[pbest_index])
        ) and retry < 50:
            r2 = np.random.randint(0, total_u)
            retry += 1

        v = X[i] + F * (X[pbest_index] - X[i]) + F * (X[r1] - U[r2])

        # binomial crossover
        j_rand = np.random.randint(0, self.dimension)
        u = X[i].copy()
        cross_mask = np.random.rand(self.dimension) < CR
        cross_mask[j_rand] = True
        u[cross_mask] = v[cross_mask]

        # boundary handling: clip
        u = np.clip(u, self.lower, self.upper)
        return u

    def optimize(self) -> Dict[str, Any]:
        start_time = time.time()

        npop = self.initial_population_size
        X = np.random.uniform(self.lower, self.upper, size=(npop, self.dimension))
        fit = np.array([self.objective.calculate_objective(x) for x in X], dtype=float)
        evaluations = int(npop)

        best_idx = int(np.argmin(fit))
        best_solution = X[best_idx].copy()
        best_fitness = float(fit[best_idx])

        fitness_history: List[float] = [best_fitness]
        first_hit_time = None
        first_hit_eval = None
        if best_fitness < self.hit_threshold:
            first_hit_time = 0.0
            first_hit_eval = evaluations

        # Success-history memory
        H = self.memory_size
        m_cr = np.full(H, 0.5, dtype=float)
        m_f = np.full(H, 0.5, dtype=float)
        k_mem = 0

        archive = np.empty((0, self.dimension), dtype=float)

        generation = 0
        while evaluations < self.max_evaluations and npop >= self.min_population_size:
            generation += 1

            # rank population for p-best selection
            rank_idx = np.argsort(fit)
            p_num = max(2, int(np.ceil(self.p_best_rate * npop)))

            trial = np.empty_like(X)
            cr_list = np.zeros(npop, dtype=float)
            f_list = np.zeros(npop, dtype=float)
            delta_f = np.zeros(npop, dtype=float)

            for i in range(npop):
                mem_idx = np.random.randint(0, H)
                cr_i, f_i = self._sample_cr_f(m_cr, m_f, mem_idx)
                cr_list[i] = cr_i
                f_list[i] = f_i

                pbest_index = rank_idx[np.random.randint(0, p_num)]
                trial[i] = self._current_to_pbest_1_bin(
                    i=i,
                    X=X,
                    A=archive,
                    F=f_i,
                    CR=cr_i,
                    pbest_index=int(pbest_index),
                )

            trial_fit = np.array([self.objective.calculate_objective(x) for x in trial], dtype=float)
            evaluations += npop

            # Selection + archive update
            improved = trial_fit < fit
            if np.any(improved):
                # add replaced parents into archive
                replaced = X[improved]
                archive = np.vstack([archive, replaced]) if len(archive) > 0 else replaced.copy()

                # success statistics for memory update
                delta_f[improved] = fit[improved] - trial_fit[improved]
                s_cr = cr_list[improved]
                s_f = f_list[improved]
                w = delta_f[improved]

                if np.sum(w) > 0:
                    w = w / np.sum(w)
                    m_cr[k_mem] = float(np.sum(w * s_cr))
                    m_f[k_mem] = _weighted_lehmer_mean(s_f, w)
                    k_mem = (k_mem + 1) % H

                X[improved] = trial[improved]
                fit[improved] = trial_fit[improved]

            # archive truncation
            if archive.shape[0] > npop:
                sel = np.random.choice(archive.shape[0], size=npop, replace=False)
                archive = archive[sel]

            # update best
            current_best_idx = int(np.argmin(fit))
            if float(fit[current_best_idx]) < best_fitness:
                best_fitness = float(fit[current_best_idx])
                best_solution = X[current_best_idx].copy()

            fitness_history.append(best_fitness)

            if first_hit_time is None and best_fitness < self.hit_threshold:
                first_hit_time = time.time() - start_time
                first_hit_eval = evaluations

            # Linear population size reduction
            target_npop = int(
                round(
                    self.min_population_size
                    + (self.initial_population_size - self.min_population_size)
                    * (1.0 - evaluations / self.max_evaluations)
                )
            )
            target_npop = max(self.min_population_size, min(target_npop, npop))

            if target_npop < npop:
                keep_idx = np.argsort(fit)[:target_npop]
                X = X[keep_idx]
                fit = fit[keep_idx]
                npop = target_npop
                if archive.shape[0] > npop:
                    sel = np.random.choice(archive.shape[0], size=npop, replace=False)
                    archive = archive[sel]

            if generation % 10 == 0:
                print(
                    f"L-SHADE Gen {generation}: Best Fitness = {best_fitness:.6f}, "
                    f"Pop = {npop}, Eval = {evaluations}"
                )

        elapsed = time.time() - start_time

        result = {
            "best_solution": best_solution,
            "best_fitness": best_fitness,
            "total_iterations": generation,
            "total_evaluations": evaluations,
            "optimization_time": elapsed,
            "time_to_target_seconds": first_hit_time,
            "hit_threshold": self.hit_threshold,
            "hit_evaluations": first_hit_eval,
            "fitness_history": fitness_history,
            "config": self.config,
        }

        info = self.objective.get_trajectory_info(best_solution)
        if info.get("success", False):
            result["trajectory_info"] = info

        return result


def optimize_well_trajectory_lshade(
    target_e,
    target_n,
    target_d,
    wellhead_position=(0, 0, 0),
    excel_files=None,
    wellhead_positions=None,
    population_size=100,
    max_evaluations=40000,
    memory_size=6,
    p_best_rate=0.11,
    min_population_size=4,
    random_seed=42,
    hit_threshold=1e5,
):
    optimizer = LSHADEWellTrajectoryOptimizer(
        target_e=target_e,
        target_n=target_n,
        target_d=target_d,
        wellhead_position=wellhead_position,
        excel_files=excel_files,
        wellhead_positions=wellhead_positions,
        population_size=population_size,
        max_evaluations=max_evaluations,
        memory_size=memory_size,
        p_best_rate=p_best_rate,
        min_population_size=min_population_size,
        random_seed=random_seed,
        hit_threshold=hit_threshold,
    )
    return optimizer.optimize()
