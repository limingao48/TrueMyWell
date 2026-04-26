#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B2OPT 井轨迹优化推理模块（用于 minimal.py 热插拔对接）。"""

import importlib
import inspect
import os
import random
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch

from well_trajectory_objective import (
    WellTrajectoryConfig,
    create_multiple_well_obstacles,
    create_objective_function,
)


class WellTrajectoryEvaluator:
    """七段式目标函数评估器（与 minimal.py 的七段式口径对齐）。"""

    def __init__(
        self,
        target_e: float,
        target_n: float,
        target_d: float,
        wellhead_position: Tuple[float, float, float],
        excel_files: Optional[List[str]],
        wellhead_positions: Optional[List[Tuple[float, float, float]]],
        hit_threshold: float = 30.0,
        safety_radius: float = 10.0,
        segment_length: float = 150.0,
        depth_step: float = 10.0,
        w_target: float = 1e5,
        w_length: float = 1.0,
        w_collision_hard: float = 1e8,
        hard_collision_penalty: float = 1e24,
    ) -> None:
        relative_target = (
            float(target_e) - float(wellhead_position[0]),
            float(target_n) - float(wellhead_position[1]),
            float(target_d) - float(wellhead_position[2]),
        )

        self.config = WellTrajectoryConfig(
            E_target=relative_target[0],
            N_target=relative_target[1],
            D_target=relative_target[2],
        )

        self.obstacles = []
        if excel_files and wellhead_positions:
            self.obstacles = create_multiple_well_obstacles(
                excel_files,
                wellhead_positions=wellhead_positions,
                safety_radius=float(safety_radius),
                segment_length=float(segment_length),
            )

        self.objective = create_objective_function(
            config=self.config,
            well_obstacles=self.obstacles,
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
        self.lower_bounds = bounds[:, 0].astype(np.float32)
        self.upper_bounds = bounds[:, 1].astype(np.float32)
        self.dim = len(self.lower_bounds)

    def evaluate(self, params: torch.Tensor) -> torch.Tensor:
        original_shape = params.shape
        flat = params.reshape(-1, original_shape[-1]) if params.dim() == 3 else params.view(-1, self.dim)
        values = [float(self.objective.calculate_objective(row)) for row in flat.detach().cpu().numpy()]
        return torch.tensor(values, device=params.device, dtype=torch.float32).view(*original_shape[:-1])

    def get_bounds(self) -> Tuple[np.ndarray, np.ndarray]:
        return self.lower_bounds, self.upper_bounds

    def describe_solution(self, solution: np.ndarray) -> Optional[Dict[str, Any]]:
        info = self.objective.get_trajectory_info(solution)
        return info if info.get("success", False) else None


def set_global_seed(seed: Optional[int]) -> None:
    if seed is None:
        return
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def _load_b2opt_components(b2opt_project_dir: Optional[str] = None):
    if b2opt_project_dir is None:
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        b2opt_project_dir = root

    if b2opt_project_dir not in sys.path:
        sys.path.insert(0, b2opt_project_dir)

    main_mod = importlib.import_module("main")
    b2opt_cls = getattr(main_mod, "B2opt")
    return main_mod.CustomProblem, b2opt_cls, main_mod.DEVICE


def _build_problem(evaluator: WellTrajectoryEvaluator, custom_problem_cls, device, use_normalization: bool):
    lb, ub = evaluator.get_bounds()
    return custom_problem_cls(
        objective_func=evaluator.evaluate,
        xlb=torch.tensor(lb, device=device, dtype=torch.float32),
        xub=torch.tensor(ub, device=device, dtype=torch.float32),
        dim=evaluator.dim,
        repaire=True,
        funname="well_trajectory",
        use_normalization=use_normalization,
    )


def optimize_well_trajectory_b2opt(
    target_e,
    target_n,
    target_d,
    wellhead_position=(0, 0, 0),
    excel_files=None,
    wellhead_positions=None,
    checkpoint=None,
    b2opt_project_dir=None,
    hidden_dim=200,
    population_size=100,
    ems=30,
    max_evaluations=20000,
    print_interval=10,
    random_seed=None,
    use_normalization=True,
    random_direction_ratio=0.2,
    cma_elite_ratio=0.2,
    cma_sample_ratio=0.5,
    cma_cov_scale=1.0,
    nn_scale=0.1,
    cma_survival_ratio=0.3,
    neural_sample_ratio=0.3,
    crossover_rate=0.7,
    mutation_rate=0.3,
    elite_fraction=0.05,
    tournament_k=10,
    ga_sample_ratio=0.8,
    min_population_ratio=0.6,
    shrink_curve_power=3.0,
    memory_size=12,
    restart_patience=20,
    restart_fraction=0.3,
    pure_lshade=True,
    mode="ga",
    top_k=5,
    local_method="Powell",
    local_maxiter=120,
    # ===== 七段式目标函数关键配置（与 minimal.py 对齐） =====
    hit_threshold=30.0,
    safety_radius=10.0,
    segment_length=150.0,
    depth_step=10.0,
    w_target=1e5,
    w_length=1.0,
    w_collision_hard=1e8,
    hard_collision_penalty=1e24,
):
    set_global_seed(random_seed)
    custom_problem_cls, b2opt_cls, device = _load_b2opt_components(b2opt_project_dir)
    evaluator = WellTrajectoryEvaluator(
        target_e=target_e,
        target_n=target_n,
        target_d=target_d,
        wellhead_position=wellhead_position,
        excel_files=excel_files,
        wellhead_positions=wellhead_positions,
        hit_threshold=hit_threshold,
        safety_radius=safety_radius,
        segment_length=segment_length,
        depth_step=depth_step,
        w_target=w_target,
        w_length=w_length,
        w_collision_hard=w_collision_hard,
        hard_collision_penalty=hard_collision_penalty,
    )
    # 统一策略：全程在归一化空间 [0,1] 优化，评估前再反归一化
    if not bool(use_normalization):
        print("[B2OPT] 检测到 use_normalization=False，已强制切换为 True 以保证跨量纲稳定性。")
    use_normalization = True
    problem = _build_problem(evaluator, custom_problem_cls, device, use_normalization)

    xlb = getattr(problem, "xlb", None)
    xub = getattr(problem, "xub", None)

    # 兼容不同版本 B2opt 构造函数：仅传入对方支持的参数
    candidate_kwargs = {
        "dim": problem.dim,
        "hidden_dim": hidden_dim,
        "popSize": population_size,
        "ems": ems,
        "ws": True,
        "xlb": xlb,
        "xub": xub,
        "random_direction_ratio": random_direction_ratio,
        "cma_elite_ratio": cma_elite_ratio,
        "cma_sample_ratio": cma_sample_ratio,
        "cma_cov_scale": cma_cov_scale,
        "nn_scale": nn_scale,
        "cma_survival_ratio": cma_survival_ratio,
        "neural_sample_ratio": neural_sample_ratio,
        "crossover_rate": crossover_rate,
        "mutation_rate": mutation_rate,
        "elite_fraction": elite_fraction,
        "tournament_k": tournament_k,
        "ga_sample_ratio": ga_sample_ratio,
        "min_population_ratio": min_population_ratio,
        "shrink_curve_power": shrink_curve_power,
        "memory_size": memory_size,
        "restart_patience": restart_patience,
        "restart_fraction": restart_fraction,
        "pure_lshade": pure_lshade,
    }
    sig = inspect.signature(b2opt_cls.__init__)
    supported = set(sig.parameters.keys())
    filtered_kwargs = {k: v for k, v in candidate_kwargs.items() if k in supported}

    b2opt = b2opt_cls(**filtered_kwargs).to(device)

    if checkpoint:
        ckpt = torch.load(checkpoint, map_location=device, weights_only=False)
        b2opt.load_state_dict(ckpt, strict=False)
    else:
        print("[B2OPT] 未提供 checkpoint，使用随机初始化模型进行优化。")
    b2opt.eval()

    pop = problem.genRandomPop((1, population_size, problem.dim))
    total_evals = 0
    best_solution = None
    best_fitness = float("inf")
    history: List[Dict[str, Any]] = []
    start = time.time()

    first_hit_time = None
    first_hit_iter = None
    
    with torch.no_grad():
        it = 0
        while total_evals < max_evaluations:
            print("mode",mode)
            it += 1
            if mode == "hybrid" and hasattr(b2opt, "forward_hybrid"):
                off, trail, evalnums = b2opt.forward_hybrid(
                    pop,
                    problem,
                    top_k=int(top_k),
                    local_method=str(local_method),
                    local_maxiter=int(local_maxiter),
                )
            else:
                off, trail, evalnums = b2opt(pop, problem)
            total_evals += int(evalnums[-1]) if evalnums else population_size

            cand = off[0]
            if problem.useRepaire:
                cand = problem.repaire(cand.unsqueeze(0))[0]
            fit = problem.calfitness(cand.unsqueeze(0))[0]
            total_evals += int(fit.numel())

            idx = int(torch.argmin(fit).item())
            fval = float(fit[idx].item())
            sol = cand[idx]
            if getattr(problem, "use_normalization", False):
                sol = problem.denormalize(sol.unsqueeze(0))[0]
            sol = sol.detach().cpu().numpy()

            if fval < best_fitness:
                best_fitness = fval
                best_solution = sol.copy()
            print("记录首次入靶时间（按固定阈值判定）")
            # 记录首次入靶时间（按固定阈值判定）
            if first_hit_time is None:
                info = evaluator.describe_solution(sol)
                print(info.get("target_deviation", 1e20))
                if info is not None and float(info.get("target_deviation", 1e20)) <=( float(hit_threshold)+0.5):
                    first_hit_time = time.time() - start
                    print(first_hit_time)
                    first_hit_iter = it

            history.append({"iteration": it, "evaluations": total_evals, "best_fitness": best_fitness})
            if it % print_interval == 0 or total_evals >= max_evaluations:
                print(f"B2OPT Iter {it:4d} | Eval {total_evals:7d}/{max_evaluations} | Best {best_fitness:.6e}")

            if total_evals >= max_evaluations:
                break
            pop = problem.repaire(off) if problem.useRepaire else off

    traj = evaluator.describe_solution(best_solution) if best_solution is not None else None
    best_solution_dict = None
    if best_solution is not None:
        names = list(evaluator.config.SEVEN_SEG_PARAM_NAMES)
        best_solution_dict = {k: float(v) for k, v in zip(names, best_solution)}

    final_deviation = None
    if traj is not None and traj.get("target_deviation") is not None:
        final_deviation = float(traj["target_deviation"])

    return {
        "best_solution": best_solution,
        "best_solution_dict": best_solution_dict,
        "best_fitness": best_fitness,
        "total_iterations": len(history),
        "total_evaluations": total_evals,
        "optimization_time": time.time() - start,
        "fitness_history": [x["best_fitness"] for x in history],
        "history": history,
        "trajectory_info": traj,
        "final_deviation": final_deviation,
        "time_to_target_seconds": first_hit_time,
        "hit_iteration": first_hit_iter,
        "hit_threshold": float(hit_threshold),
    }
