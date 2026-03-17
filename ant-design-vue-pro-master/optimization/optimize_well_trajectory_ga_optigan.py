#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GA-optiGAN 井轨迹优化封装模块。"""

import os
import random
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from well_trajectory_objective import (
    WellTrajectoryConfig,
    create_multiple_well_obstacles,
    create_objective_function,
)


class GAOptiGANWellTrajectoryOptimizer:
    """基于 GA-optiGAN 的井轨迹优化器。"""

    def __init__(
        self,
        target_e: float,
        target_n: float,
        target_d: float,
        wellhead_position: Optional[Tuple[float, float, float]] = None,
        excel_files: Optional[List[str]] = None,
        wellhead_positions: Optional[List[Tuple[float, float, float]]] = None,
        # 七段式目标与防碰（与 PSO/B2OPT 一致）
        safety_radius: float = 10.0,
        segment_length: float = 150.0,
        depth_step: float = 10.0,
        hit_threshold: float = 30.0,
        w_target: float = 1e5,
        w_length: float = 1.0,
        w_collision_hard: float = 1e8,
        hard_collision_penalty: float = 1e24,
        # GA-optiGAN 关键参数
        max_evaluations: int = 300000,
        population_size: int = 100,
        opt_size: int = 300,
        gamma: float = 1.2,
        lambda2: float = 0.3,
        pretrain: int = 1,
        epochs: int = 150,
        d_iter: int = 4,
        gen_n: int = 10,
        elite_ratio: float = 0.5,
        random_seed: Optional[int] = None,
        # Hybrid/refiner controls
        train_every: int = 3,
        random_injection_ratio: float = 0.10,
        stagnation_patience: int = 30,
        reheat_factor: float = 1.5,
        refine_mode: bool = True,
        residual_strength: float = 0.08,
        optigan_dir: Optional[str] = None,
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

        self.safety_radius = float(safety_radius)
        self.segment_length = float(segment_length)
        self.depth_step = float(depth_step)
        self.hit_threshold = float(hit_threshold)
        self.w_target = float(w_target)
        self.w_length = float(w_length)
        self.w_collision_hard = float(w_collision_hard)
        self.hard_collision_penalty = float(hard_collision_penalty)

        self.max_evaluations = int(max_evaluations)
        self.population_size = int(population_size)
        self.opt_size = int(opt_size)
        self.gamma = float(gamma)
        self.lambda2 = float(lambda2)
        self.pretrain = int(pretrain)
        self.epochs = int(epochs)
        self.d_iter = int(d_iter)
        self.gen_n = int(gen_n)
        self.elite_ratio = float(elite_ratio)
        self.random_seed = random_seed
        self.hit_threshold = float(hit_threshold)

        self.train_every = int(train_every)
        self.random_injection_ratio = float(random_injection_ratio)
        self.stagnation_patience = int(stagnation_patience)
        self.reheat_factor = float(reheat_factor)
        self.refine_mode = bool(refine_mode)
        self.residual_strength = float(residual_strength)

        if random_seed is not None:
            random.seed(random_seed)
            np.random.seed(random_seed)

        self.config = WellTrajectoryConfig(
            E_target=self.relative_target_e,
            N_target=self.relative_target_n,
            D_target=self.relative_target_d,
            safety_radius=self.safety_radius,
            target_deviation_threshold=self.hit_threshold,
        )

        self.well_obstacles = []
        if excel_files and wellhead_positions:
            self.well_obstacles = create_multiple_well_obstacles(
                excel_files,
                wellhead_positions=wellhead_positions,
                safety_radius=self.safety_radius,
                segment_length=self.segment_length,
            )

        self.objective = create_objective_function(
            self.config,
            well_obstacles=self.well_obstacles,
            objective_mode="seven_segment_weighted",
            objective_weights={
                "hit_threshold": self.hit_threshold,
                "w_target": self.w_target,
                "w_length": self.w_length,
                "w_collision_hard": self.w_collision_hard,
                "hard_collision_penalty": self.hard_collision_penalty,
                "depth_step": self.depth_step,
            },
        )
        bounds = self.config.get_seven_segment_parameter_bounds()
        self.lower = bounds[:, 0].astype(float)
        self.upper = bounds[:, 1].astype(float)
        self.dimension = len(self.lower)

        if optigan_dir is None:
            optigan_dir = os.path.join(os.path.dirname(__file__), "GA-optiGAN")
        self.optigan_dir = os.path.abspath(optigan_dir)

    def _objective_function(self, x: np.ndarray) -> float:
        x = np.asarray(x, dtype=float)
        return float(self.objective.calculate_objective(x))

    def _load_optigan_modules(self):
        if not os.path.isdir(self.optigan_dir):
            raise FileNotFoundError(f"未找到 GA-optiGAN 目录: {self.optigan_dir}")

        if self.optigan_dir not in sys.path:
            sys.path.insert(0, self.optigan_dir)

        from GA_optiGAN import GA_optiGAN_min  # type: ignore
        from Variable import Dict, Problem, setup_seed, hyperparameter_defaults  # type: ignore

        return GA_optiGAN_min, Dict, Problem, setup_seed, dict(hyperparameter_defaults)

    def optimize(self) -> Dict[str, Any]:
        start_time = time.time()

        GA_optiGAN_min, Dict, Problem, setup_seed, hp = self._load_optigan_modules()

        hp["MAXFes"] = self.max_evaluations
        hp["pop_size"] = self.population_size
        hp["opt_size"] = self.opt_size
        hp["gamma"] = self.gamma
        hp["lambda2"] = self.lambda2
        hp["pretrain"] = self.pretrain
        hp["epochs"] = self.epochs
        hp["D_iter"] = self.d_iter
        hp["gen_n"] = self.gen_n
        hp["elite_ratio"] = self.elite_ratio

        hp["train_every"] = self.train_every
        hp["random_injection_ratio"] = self.random_injection_ratio
        hp["stagnation_patience"] = self.stagnation_patience
        hp["reheat_factor"] = self.reheat_factor
        hp["refine_mode"] = self.refine_mode
        hp["residual_strength"] = self.residual_strength

        config_init = Dict(hp)
        problem = Problem(self._objective_function)
        config_wandb = Dict(
            {
                "upper": self.upper,
                "lower": self.lower,
                "lambda2": config_init.lambda2,
                "opt_size": config_init.opt_size,
                "pop_size": config_init.pop_size,
                "gamma": config_init.gamma,
                "MAXFes": config_init.MAXFes,
                "dimension": self.dimension,
                "ZSCORESTEP": 1.0,
            }
        )

        seed = int(self.random_seed if self.random_seed is not None else 0)
        result_raw = GA_optiGAN_min(
            problem=problem,
            config_init=config_init,
            config_wandb=config_wandb,
            problem_id="WellTrajectoryDesignParameterOptimization_i0_d8",
            seed=setup_seed(seed),
        )

        best_solution = None
        best_fitness = float("inf")
        total_evaluations = int(getattr(problem, "maxFes", 0))
        if isinstance(result_raw, (list, tuple)) and len(result_raw) >= 5:
            best_fitness = float(result_raw[1])
            total_evaluations = int(result_raw[3])
            best_solution = np.asarray(result_raw[4], dtype=float)

        elapsed = time.time() - start_time

        # 七段式统一返回格式：best_solution_dict 供 quick_visualize_seven_segment 使用
        best_solution_dict = None
        final_deviation = None
        trajectory_info = None
        if best_solution is not None:
            names = self.config.SEVEN_SEG_PARAM_NAMES
            best_solution_dict = {k: float(v) for k, v in zip(names, np.asarray(best_solution).ravel())}
            info = self.objective.get_trajectory_info(best_solution)
            if info.get("success", False):
                trajectory_info = info
                final_deviation = info.get("target_deviation")

        result = {
            "best_solution": best_solution,
            "best_solution_dict": best_solution_dict,
            "best_fitness": best_fitness,
            "total_iterations": None,
            "total_evaluations": total_evaluations,
            "optimization_time": elapsed,
            "time_to_target_seconds": None,
            "hit_threshold": self.hit_threshold,
            "hit_iteration": None,
            "fitness_history": [best_fitness] if np.isfinite(best_fitness) else [],
            "final_deviation": final_deviation,
            "config": self.config,
        }
        if trajectory_info is not None:
            result["trajectory_info"] = trajectory_info
        return result


def optimize_well_trajectory_ga_optigan(
    target_e,
    target_n,
    target_d,
    wellhead_position=(0, 0, 0),
    excel_files=None,
    wellhead_positions=None,
    # 七段式目标与防碰（与 PSO/B2OPT 一致）
    safety_radius=10.0,
    segment_length=150.0,
    depth_step=10.0,
    hit_threshold=30.0,
    w_target=1e5,
    w_length=1.0,
    w_collision_hard=1e8,
    hard_collision_penalty=1e24,
    # GA-optiGAN 算法参数
    max_evaluations=300000,
    population_size=100,
    opt_size=300,
    gamma=1.2,
    lambda2=0.3,
    pretrain=1,
    epochs=150,
    d_iter=4,
    gen_n=10,
    elite_ratio=0.5,
    random_seed=42,
    train_every=3,
    random_injection_ratio=0.10,
    stagnation_patience=30,
    reheat_factor=1.5,
    refine_mode=True,
    residual_strength=0.08,
    optigan_dir=None,
):
    """七段式井眼轨迹 GA-optiGAN 优化，与 run_optimization_workflow 统一接口。"""
    optimizer = GAOptiGANWellTrajectoryOptimizer(
        target_e=target_e,
        target_n=target_n,
        target_d=target_d,
        wellhead_position=wellhead_position,
        excel_files=excel_files,
        wellhead_positions=wellhead_positions,
        safety_radius=safety_radius,
        segment_length=segment_length,
        depth_step=depth_step,
        hit_threshold=hit_threshold,
        w_target=w_target,
        w_length=w_length,
        w_collision_hard=w_collision_hard,
        hard_collision_penalty=hard_collision_penalty,
        max_evaluations=max_evaluations,
        population_size=population_size,
        opt_size=opt_size,
        gamma=gamma,
        lambda2=lambda2,
        pretrain=pretrain,
        epochs=epochs,
        d_iter=d_iter,
        gen_n=gen_n,
        elite_ratio=elite_ratio,
        random_seed=random_seed,
        train_every=train_every,
        random_injection_ratio=random_injection_ratio,
        stagnation_patience=stagnation_patience,
        reheat_factor=reheat_factor,
        refine_mode=refine_mode,
        residual_strength=residual_strength,
        optigan_dir=optigan_dir,
    )
    return optimizer.optimize()
