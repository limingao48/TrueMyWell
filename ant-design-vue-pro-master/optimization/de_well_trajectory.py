#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
差分进化井轨迹优化器
Differential Evolution Well Trajectory Optimizer

直接使用 well_trajectory_objective 模块，不重复实现任何功能
"""

import sys
import os
import numpy as np
import random
import time
import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Tuple, Optional, Dict, Any

# 添加父目录到路径以导入井轨迹模块
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

try:
    from well_trajectory_objective import (
        WellTrajectoryConfig,
        create_multiple_well_obstacles,
        create_objective_function,
    )
    from well_trajectory_objective.visualization import plot_well_comparison_3d
    WELL_TRAJECTORY_AVAILABLE = True
except ImportError as e:
    print(f"错误：无法导入井轨迹模块: {e}")
    print("请确保 well_trajectory_objective 模块在父目录中")
    WELL_TRAJECTORY_AVAILABLE = False


class DEWellTrajectoryOptimizer:
    """差分进化井轨迹优化器"""
    
    def __init__(self, 
                 target_e: float = 1500.64,
                 target_n: float = 1200.71, 
                 target_d: float = 2936.06,
                 wellhead_position: Optional[Tuple[float, float, float]] = None,
                 excel_files: Optional[List[str]] = None,
                 wellhead_positions: Optional[List[Tuple[float, float, float]]] = None,
                 # DE 核心参数
                 population_size: int = 30,
                 max_iterations: int = 1000,
                 F: float = 0.5,  # 缩放因子
                 CR: float = 0.9,  # 交叉概率
                 strategy: str = "rand/1/bin",  # 变异策略
                 random_seed: Optional[int] = None):
        """
        初始化差分进化优化器
        
        Args:
            target_e: 目标东坐标
            target_n: 目标北坐标  
            target_d: 目标深度
            wellhead_position: 被优化井的井口坐标 (E, N, D)
            excel_files: Excel文件列表
            wellhead_positions: 井轨迹障碍物的井口位置列表
            population_size: 种群大小
            max_iterations: 最大迭代次数
            F: 缩放因子
            CR: 交叉概率
            strategy: 变异策略
            random_seed: 随机种子
        """
        if not WELL_TRAJECTORY_AVAILABLE:
            raise ImportError("well_trajectory_objective 模块不可用")
        
        # 目标点
        self.target_e = target_e
        self.target_n = target_n
        self.target_d = target_d
        
        # 被优化井的井口坐标
        if wellhead_position is None:
            wellhead_position = (0, 0, 0)
        self.wellhead_position = wellhead_position
        
        # 计算相对目标点
        self.relative_target_e = target_e - wellhead_position[0]
        self.relative_target_n = target_n - wellhead_position[1]
        self.relative_target_d = target_d - wellhead_position[2]
        
        # DE 参数
        self.population_size = population_size
        self.max_iterations = max_iterations
        self.F = F
        self.CR = CR
        self.strategy = strategy
        self.random_seed = random_seed
        
        # 设置随机种子
        if random_seed is not None:
            random.seed(random_seed)
            np.random.seed(random_seed)
            print(f"随机种子设置为: {random_seed}")
        
        # 创建井轨迹配置（使用相对目标点）
        # 统一坐标系：
        # - 配置中的 E/N/D_target 使用“绝对坐标”（目标点本身）
        # - E/N/D_wellhead 使用被优化井的井口坐标
        # - 内部几何与可视化全部在同一全局坐标系下工作
        self.config = WellTrajectoryConfig(
            E_target=self.target_e,
            N_target=self.target_n,
            D_target=self.target_d,
            E_wellhead=wellhead_position[0],
            N_wellhead=wellhead_position[1],
            D_wellhead=wellhead_position[2],
        )
        
        # 创建井轨迹障碍物
        self.well_obstacles = []
        if excel_files and wellhead_positions:
            self.well_obstacles = create_multiple_well_obstacles(
                excel_files,
                wellhead_positions=wellhead_positions,
                safety_radius=10.0,
                segment_length=150.0
            )
        
        # 创建目标函数
        self.objective = WellTrajectoryObjective(self.config, well_obstacles=self.well_obstacles)
        
        # 获取参数边界
        bounds = self.config.get_parameter_bounds()
        self.param_bounds = [(bounds[i, 0], bounds[i, 1]) for i in range(len(bounds))]
        self.dimension = len(self.param_bounds)
        
        # 初始化种群
        self.population = []
        self.fitness = []
        self.best_individual = None
        self.best_fitness = float('inf')
        
        # 数据记录
        self.iteration_data = []
        self.fitness_history = []
        self.diversity_history = []
        # 记录每一代的全部个体参数与适应度（用于统计分布）
        self.population_history = []  # List[List[Dict[str, float]]]
        
    def initialize_population(self):
        """初始化种群"""
        self.population = []
        self.fitness = []
        
        for i in range(self.population_size):
            # 随机初始化个体
            individual = []
            for min_val, max_val in self.param_bounds:
                individual.append(random.uniform(min_val, max_val))
            self.population.append(np.array(individual))
            
            # 评估适应度
            # position = [945.21346381, 85.09860853, 88.00130255, 194.27114862,  91.99755115, 1529.72007077, 408.66985563, 2591.81569619]
            # fitness = self.objective.calculate_objective(position)

            fitness = self.objective.calculate_objective(individual)
            self.fitness.append(fitness)
            
            # 更新最优解
            if fitness < self.best_fitness:
                self.best_fitness = fitness
                self.best_individual = individual.copy()
    # //////////////////////////   9.48！！！！！！！！！！！！！！！！！
    def mutation(self, target_idx: int) -> np.ndarray:
        """变异操作"""
        if self.strategy == "rand/1/bin":
            # 随机选择3个不同的个体
            candidates = list(range(self.population_size))
            candidates.remove(target_idx)
            a, b, c = random.sample(candidates, 3)
            
            # 变异向量
            mutant = self.population[a] + self.F * (self.population[b] - self.population[c])
            
        elif self.strategy == "best/1/bin":
            # 使用最优个体
            candidates = list(range(self.population_size))
            candidates.remove(target_idx)
            a, b = random.sample(candidates, 2)
            
            mutant = self.best_individual + self.F * (self.population[a] - self.population[b])
            
        elif self.strategy == "rand/2/bin":
            # 随机选择5个不同的个体
            candidates = list(range(self.population_size))
            candidates.remove(target_idx)
            a, b, c, d, e = random.sample(candidates, 5)
            
            mutant = (self.population[a] + 
                     self.F * (self.population[b] - self.population[c]) +
                     self.F * (self.population[d] - self.population[e]))
            
        elif self.strategy == "best/2/bin":
            # 使用最优个体和4个随机个体
            candidates = list(range(self.population_size))
            a, b, c, d = random.sample(candidates, 4)
            
            mutant = (self.best_individual + 
                     self.F * (self.population[a] - self.population[b]) +
                     self.F * (self.population[c] - self.population[d]))
        
        else:
            raise ValueError(f"未知的变异策略: {self.strategy}")
        
        return mutant
    
    def crossover(self, target: np.ndarray, mutant: np.ndarray) -> np.ndarray:
        """交叉操作"""
        trial = target.copy()
        
        # 确保至少有一个维度来自变异向量
        j_rand = random.randint(0, self.dimension - 1)
        
        for j in range(self.dimension):
            if random.random() < self.CR or j == j_rand:
                trial[j] = mutant[j]
        
        return trial
    
    def boundary_handling(self, individual: np.ndarray) -> np.ndarray:
        """边界处理"""
        for j in range(self.dimension):
            min_val, max_val = self.param_bounds[j]
            if individual[j] < min_val:
                individual[j] = min_val
            elif individual[j] > max_val:
                individual[j] = max_val
        
        return individual
    
    def calculate_diversity(self):
        """计算种群多样性"""
        if len(self.population) <= 1:
            return 0.0
        
        # 计算所有个体到质心的距离
        centroid = np.mean(self.population, axis=0)
        distances = [np.linalg.norm(individual - centroid) for individual in self.population]
        return np.mean(distances)
    
    def optimize(self) -> Dict[str, Any]:
        """执行优化"""
        print("=" * 60)
        print("差分进化井轨迹优化器")
        print("=" * 60)
        print(f"绝对目标点: E={self.target_e}, N={self.target_n}, D={self.target_d}")
        print(f"被优化井井口: E={self.wellhead_position[0]}, N={self.wellhead_position[1]}, D={self.wellhead_position[2]}")
        print(f"相对目标点: E={self.relative_target_e:.2f}, N={self.relative_target_n:.2f}, D={self.relative_target_d:.2f}")
        print(f"种群大小: {self.population_size}")
        print(f"最大迭代次数: {self.max_iterations}")
        print(f"缩放因子: {self.F}")
        print(f"交叉概率: {self.CR}")
        print(f"变异策略: {self.strategy}")
        print(f"随机种子: {self.random_seed if self.random_seed is not None else '未设置'}")
        print(f"井轨迹障碍物数量: {len(self.well_obstacles)}")
        print()
        
        start_time = time.time()
        
        # 初始化种群
        self.initialize_population()
        
        print(f"初始最优适应度: {self.best_fitness:.6f}")
        
        # 主循环
        for iteration in range(self.max_iterations):
            new_population = []
            new_fitness = []
            
            for i in range(self.population_size):
                # 变异
                mutant = self.mutation(i)
                
                # 交叉
                trial = self.crossover(self.population[i], mutant)
                
                # 边界处理
                trial = self.boundary_handling(trial)
                
                # 评估试验向量
                trial_fitness = self.objective.calculate_objective(trial)
                
                # 选择
                if trial_fitness < self.fitness[i]:
                    new_population.append(trial)
                    new_fitness.append(trial_fitness)
                else:
                    new_population.append(self.population[i])
                    new_fitness.append(self.fitness[i])
            
            # 更新种群
            self.population = new_population
            self.fitness = new_fitness
            
            # 更新最优解
            best_idx = np.argmin(self.fitness)
            if self.fitness[best_idx] < self.best_fitness:
                self.best_fitness = self.fitness[best_idx]
                self.best_individual = self.population[best_idx].copy()
            
            # 计算多样性
            diversity = self.calculate_diversity()
            
            # 记录数据
            self.fitness_history.append(self.best_fitness)
            self.diversity_history.append(diversity)
            
            # 记录详细数据
            iteration_info = {
                'iteration': iteration + 1,
                'best_fitness': self.best_fitness,
                'mean_fitness': np.mean(self.fitness),
                'std_fitness': np.std(self.fitness),
                'diversity': diversity
            }
            
            # 添加最优解的参数
            param_names = ["D_kop", "alpha1", "alpha2", "phi1", "phi2", "R1", "R2", "D_turn_kop"]
            for i, name in enumerate(param_names):
                iteration_info[f'best_{name}'] = self.best_individual[i]
            
            self.iteration_data.append(iteration_info)
            
            # 输出进度
            if (iteration + 1) % 2 == 0:
                print(f"Iteration {iteration + 1}: Best Fitness = {self.best_fitness:.6f}, Diversity = {diversity:.6f}")
        
        end_time = time.time()
        
        # 最终结果
        result = {
            'best_solution': self.best_individual,
            'best_fitness': self.best_fitness,
            'total_iterations': len(self.fitness_history),
            'optimization_time': end_time - start_time,
            'iteration_data': self.iteration_data,
            'config': self.config
        }
        
        # 获取轨迹信息
        if self.best_individual is not None:
            info = self.objective.get_trajectory_info(self.best_individual)
            if info['success']:
                result['trajectory_info'] = info
        
        # 保存数据到CSV
        self.save_data_to_csv("de_optimization_data.csv")
        
        # 生成收敛图
        self.plot_convergence("de_convergence_plot.png", show=False)

        # 可视化：最佳待钻井 + 已有井三维对比
        if self.best_individual is not None:
            try:
                plot_well_comparison_3d(
                    position_tuple=self.best_individual.tolist(),
                    config=self.config,
                    well_obstacles=self.well_obstacles,
                    title="差分进化优化结果 - 待钻井与已有井对比",
                    save_path="de_best_well_comparison",
                    show=False,
                )
                print("已生成最佳井轨迹与已有井的对比图（前缀 de_best_well_comparison_*.png）")
            except Exception as e:
                print(f"生成井轨迹对比图失败: {e}")
        
        print(f"\n优化完成!")
        print(f"最佳适应度: {self.best_fitness:.6f}")
        print(f"优化时间: {result['optimization_time']:.2f} 秒")
        print(f"总迭代次数: {len(self.fitness_history)}")
        
        if self.best_individual is not None:
            param_names = ["D_kop", "alpha1", "alpha2", "phi1", "phi2", "R1", "R2", "D_turn_kop"]
            print(f"\n最佳参数:")
            for name, value in zip(param_names, self.best_individual):
                print(f"  {name}: {value:.4f}")
            
            if 'trajectory_info' in result:
                traj_info = result['trajectory_info']
                print(f"\n轨迹信息:")
                print(f"  总长度: {traj_info['total_length']:.2f} m")
                print(f"  目标偏差: {traj_info['target_deviation']:.2f} m")
                print(f"  井轨迹碰撞: {'是' if traj_info['well_collision'] else '否'}")
        
        return result
    
    def save_data_to_csv(self, filename: str = "de_optimization_data.csv"):
        """保存数据到CSV文件"""
        if not self.iteration_data:
            print("No data to save")
            return
        df = pd.DataFrame(self.iteration_data)
        df.to_csv(filename, index=False)
        print(f"Optimization data saved to: {filename}")
    
    def plot_convergence(self, save_path: str = "de_convergence_plot.png", show: bool = True):
        """绘制收敛图"""
        if not self.fitness_history:
            print("No convergence data available")
            return
        
        # 设置matplotlib为英文
        plt.rcParams['font.family'] = 'DejaVu Sans'
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # 绘制适应度曲线
        ax1.plot(self.fitness_history, 'r-', linewidth=2, label='Best Fitness')
        ax1.set_xlabel('Iteration')
        ax1.set_ylabel('Fitness Value')
        ax1.set_title('Differential Evolution Convergence')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_yscale('log')
        
        # 绘制多样性曲线
        ax2.plot(self.diversity_history, 'g-', linewidth=1)
        ax2.set_xlabel('Iteration')
        ax2.set_ylabel('Diversity')
        ax2.set_title('Population Diversity')
        ax2.grid(True, alpha=0.3)
        
        # 绘制适应度分布（最后100次迭代）
        if len(self.fitness_history) >= 100:
            recent_fitness = self.fitness_history[-100:]
            ax3.hist(recent_fitness, bins=20, alpha=0.7, color='orange')
            ax3.axvline(self.best_fitness, color='red', linestyle='--', linewidth=2, label=f'Best: {self.best_fitness:.6f}')
            ax3.set_xlabel('Fitness Value')
            ax3.set_ylabel('Frequency')
            ax3.set_title('Recent Fitness Distribution (Last 100 iterations)')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            ax3.set_yscale('log')
        
        # 绘制收敛速度
        if len(self.fitness_history) > 1:
            improvement = np.diff(self.fitness_history)
            ax4.plot(improvement, 'purple', linewidth=1)
            ax4.set_xlabel('Iteration')
            ax4.set_ylabel('Fitness Improvement')
            ax4.set_title('Convergence Speed')
            ax4.grid(True, alpha=0.3)
            ax4.set_yscale('log')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Convergence plot saved to: {save_path}")
        
        if show:
            plt.show()
        else:
            plt.close()


class GAWellTrajectoryOptimizer:
    """遗传算法井轨迹优化器"""
    def __init__(self,
                 target_e: float = 1500.64,
                 target_n: float = 1200.71,
                 target_d: float = 2936.06,
                 wellhead_position: Optional[Tuple[float, float, float]] = None,
                 excel_files: Optional[List[str]] = None,
                 wellhead_positions: Optional[List[Tuple[float, float, float]]] = None,
                 # GA 核心参数
                 population_size: int = 30,
                 max_generations: int = 1000,
                 crossover_rate: float = 0.9,
                 mutation_rate: float = 0.1,
                 elite_fraction: float = 0.05,
                 tournament_k: int = 3,
                 random_seed: Optional[int] = None,
                 population_csv_path: Optional[str] = None,
                 ga_csv_path: str = "ga_optimization_data.csv",
                 convergence_plot_path: str = "ga_convergence_plot.png",
                 # 收敛指标相关
                 enable_convergence_metrics: bool = True,
                 global_optimum: Optional[List[float]] = None,
                 wasserstein_uniform_samples: int = 512):
        if not WELL_TRAJECTORY_AVAILABLE:
            raise ImportError("well_trajectory_objective 模块不可用")

        # 目标点
        self.target_e = target_e
        self.target_n = target_n
        self.target_d = target_d

        # 被优化井的井口坐标
        if wellhead_position is None:
            wellhead_position = (0, 0, 0)
        self.wellhead_position = wellhead_position

        # 相对目标点
        self.relative_target_e = target_e - wellhead_position[0]
        self.relative_target_n = target_n - wellhead_position[1]
        self.relative_target_d = target_d - wellhead_position[2]

        # GA 参数
        self.population_size = population_size
        self.max_generations = max_generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.elite_fraction = elite_fraction
        self.tournament_k = tournament_k
        self.random_seed = random_seed

        if random_seed is not None:
            random.seed(random_seed)
            np.random.seed(random_seed)
            print(f"随机种子设置为: {random_seed}")

        # 配置与目标函数：统一使用绝对坐标系（与DE版本一致）
        self.config = WellTrajectoryConfig(
            E_target=self.target_e,
            N_target=self.target_n,
            D_target=self.target_d,
            E_wellhead=wellhead_position[0],
            N_wellhead=wellhead_position[1],
            D_wellhead=wellhead_position[2],
        )
        
        self.well_obstacles = []
        if excel_files and wellhead_positions:
            self.well_obstacles = create_multiple_well_obstacles(
                excel_files,
                wellhead_positions=wellhead_positions,
                safety_radius=10.0,
                segment_length=150.0
            )

        self.objective = WellTrajectoryObjective(self.config, well_obstacles=self.well_obstacles)

        bounds = self.config.get_parameter_bounds()
        self.param_bounds = [(bounds[i, 0], bounds[i, 1]) for i in range(len(bounds))]
        self.dimension = len(self.param_bounds)
        
        # 运行态
        self.population = []
        self.fitness = []
        self.best_individual = None
        self.best_fitness = float('inf')
        self.iteration_data = []
        self.fitness_history = []
        self.diversity_history = []
        
        # 运行期将每代全体个体流式写入CSV，避免占用内存
        self.population_csv_path = population_csv_path
        self._csv_initialized = False
        # 输出路径
        self.ga_csv_path = ga_csv_path
        self.convergence_plot_path = convergence_plot_path

        # 收敛指标记录
        self.enable_convergence_metrics = enable_convergence_metrics
        self.global_optimum = np.array(global_optimum, dtype=float) if global_optimum is not None else None
        self.wasserstein_uniform_samples = int(max(8, wasserstein_uniform_samples))
        self.best_history: List[np.ndarray] = []  # 历史最优解集合（用于 DI）
        self.convergence_metrics: List[Dict[str, Any]] = []
        
    def _initialize(self):
        self.population = []
        self.fitness = []
        for _ in range(self.population_size):
            individual = np.array([random.uniform(lo, hi) for lo, hi in self.param_bounds])
            self.population.append(individual)
            f = self.objective.calculate_objective(individual)
            self.fitness.append(f)
            if f < self.best_fitness:
                self.best_fitness = f
                self.best_individual = individual.copy()

    def _boundary(self, individual: np.ndarray) -> np.ndarray:
        for j in range(self.dimension):
            lo, hi = self.param_bounds[j]
            if individual[j] < lo:
                individual[j] = lo
            elif individual[j] > hi:
                individual[j] = hi
        return individual

    def _diversity(self) -> float:
        if len(self.population) <= 1:
            return 0.0
        centroid = np.mean(self.population, axis=0)
        distances = [np.linalg.norm(ind - centroid) for ind in self.population]
        return float(np.mean(distances))

    # ===== 收敛指标辅助函数 =====
    def _wasserstein_1d(self, a: np.ndarray, b: np.ndarray) -> float:
        """简化的一维Wasserstein-1距离估计：两样本等权时可用排序后均值绝对差近似。"""
        a = np.asarray(a, dtype=float)
        b = np.asarray(b, dtype=float)
        if a.size == 0 or b.size == 0:
            return float('nan')
        n = min(len(a), len(b))
        if n == 0:
            return float('nan')
        a_sorted = np.sort(a)[:n]
        b_sorted = np.sort(b)[:n]
        return float(np.mean(np.abs(a_sorted - b_sorted)))

    def _compute_wasserstein_estimate(self, X: np.ndarray, Y: np.ndarray) -> Tuple[float, float]:
        """对每个维度计算1D W1并取均值/标准差，返回(mean, std)。"""
        if X.size == 0 or Y.size == 0:
            return float('nan'), float('nan')
        dim = X.shape[1]
        vals = []
        for j in range(dim):
            vals.append(self._wasserstein_1d(X[:, j], Y[:, j]))
        vals = np.array(vals, dtype=float)
        return float(np.nanmean(vals)), float(np.nanstd(vals))

    def _compute_DI_DR(self) -> Tuple[float, float, float, float]:
        """返回 (DI_mean, DI_std, DR_mean, DR_std)"""
        X = np.array(self.population, dtype=float)
        if X.size == 0:
            return float('nan'), float('nan'), float('nan'), float('nan')
        # DI: 生成分布 vs 历史最优分布
        if self.best_history:
            Y_opt = np.array(self.best_history, dtype=float)
            # 采样匹配规模
            if len(Y_opt) >= len(X):
                idx = np.random.choice(len(Y_opt), size=len(X), replace=False)
                Y_opt_s = Y_opt[idx]
            else:
                idx = np.random.choice(len(Y_opt), size=len(X), replace=True)
                Y_opt_s = Y_opt[idx]
            di_mean, di_std = self._compute_wasserstein_estimate(X, Y_opt_s)
        else:
            di_mean, di_std = float('nan'), float('nan')

        # DR: 生成分布 vs 均匀分布（在参数边界内）
        U = []
        for _ in range(self.wasserstein_uniform_samples):
            u = [np.random.uniform(lo, hi) for lo, hi in self.param_bounds]
            U.append(u)
        U = np.array(U, dtype=float)
        # 匹配规模
        if len(U) >= len(X):
            idx = np.random.choice(len(U), size=len(X), replace=False)
            U_s = U[idx]
        else:
            idx = np.random.choice(len(U), size=len(X), replace=True)
            U_s = U[idx]
        dr_mean, dr_std = self._compute_wasserstein_estimate(X, U_s)
        return di_mean, di_std, dr_mean, dr_std

    def _mean_nearest_neighbor(self) -> Tuple[float, float]:
        """计算当前种群的平均最近邻距离（均值、标准差）。"""
        X = np.array(self.population, dtype=float)
        if len(X) <= 1:
            return float('nan'), float('nan')
        n = len(X)
        dists = []
        for i in range(n):
            # 与其它点的距离
            diff = X - X[i]
            dist = np.linalg.norm(diff, axis=1)
            dist[i] = np.inf
            dists.append(np.min(dist))
        dists = np.array(dists, dtype=float)
        return float(np.mean(dists)), float(np.std(dists))

    def _mean_distance_to_global(self, points: List[np.ndarray]) -> Tuple[float, float]:
        if self.global_optimum is None or len(points) == 0:
            return float('nan'), float('nan')
        arr = np.array(points, dtype=float)
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)
        d = np.linalg.norm(arr - self.global_optimum, axis=1)
        return float(np.mean(d)), float(np.std(d))

    def _tournament_select(self) -> int:
        idxs = random.sample(range(self.population_size), k=min(self.tournament_k, self.population_size))
        best = min(idxs, key=lambda i: self.fitness[i])
        return best

    def _select_parents(self) -> Tuple[np.ndarray, np.ndarray]:
        return self.population[self._tournament_select()], self.population[self._tournament_select()]

    def _crossover(self, p1: np.ndarray, p2: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """SBX（模拟二进制交叉）。
        参考 Deb's SBX；分量级边界裁剪；不改变外部参数签名。
        """
        if random.random() > self.crossover_rate:
            return p1.copy(), p2.copy()
        eta_c = 15.0  # 分布指数，经验常用 10~20
        child1 = p1.copy()
        child2 = p2.copy()
        eps = 1e-14
        for j in range(self.dimension):
            if random.random() <= 0.5:
                x1 = float(p1[j])
                x2 = float(p2[j])
                if abs(x1 - x2) > eps:
                    if x1 > x2:
                        x1, x2 = x2, x1
                    lo, hi = self.param_bounds[j]
                    rand = random.random()
                    # 计算第一个孩子的 beta_q
                    beta = 1.0 + 2.0 * (x1 - lo) / (x2 - x1)
                    alpha = 2.0 - pow(beta, -(eta_c + 1.0))
                    if rand <= 1.0 / alpha:
                        betaq = pow(rand * alpha, 1.0 / (eta_c + 1.0))
                    else:
                        betaq = pow(1.0 / (2.0 - rand * alpha), 1.0 / (eta_c + 1.0))
                    c1 = 0.5 * ((x1 + x2) - betaq * (x2 - x1))

                    # 计算第二个孩子的 beta_q
                    beta = 1.0 + 2.0 * (hi - x2) / (x2 - x1)
                    alpha = 2.0 - pow(beta, -(eta_c + 1.0))
                    if rand <= 1.0 / alpha:
                        betaq = pow(rand * alpha, 1.0 / (eta_c + 1.0))
                    else:
                        betaq = pow(1.0 / (2.0 - rand * alpha), 1.0 / (eta_c + 1.0))
                    c2 = 0.5 * ((x1 + x2) + betaq * (x2 - x1))

                    # 随机交换，保持无偏
                    if random.random() < 0.5:
                        child1[j] = c1
                        child2[j] = c2
                    else:
                        child1[j] = c2
                        child2[j] = c1
                else:
                    child1[j] = x1
                    child2[j] = x2
            else:
                # 不交叉该维度
                child1[j] = p1[j]
                child2[j] = p2[j]
        return self._boundary(child1), self._boundary(child2)

    def _mutate(self, individual: np.ndarray) -> np.ndarray:
        # 对每个维度以 mutation_rate 的概率进行均匀微扰
        for j in range(self.dimension):
            if random.random() < self.mutation_rate:
                lo, hi = self.param_bounds[j]
                # 以区间 10% 的幅度作局部扰动
                span = (hi - lo) * 0.1
                perturb = random.uniform(-span, span)
                individual[j] = individual[j] + perturb
        return self._boundary(individual)

    def optimize(self) -> Dict[str, Any]:
        print("=" * 60)
        print("遗传算法井轨迹优化器")
        print("=" * 60)
        print(f"绝对目标点: E={self.target_e}, N={self.target_n}, D={self.target_d}")
        print(f"被优化井井口: E={self.wellhead_position[0]}, N={self.wellhead_position[1]}, D={self.wellhead_position[2]}")
        print(f"相对目标点: E={self.relative_target_e:.2f}, N={self.relative_target_n:.2f}, D={self.relative_target_d:.2f}")
        print(f"种群大小: {self.population_size}")
        print(f"最大世代数: {self.max_generations}")
        print(f"交叉概率: {self.crossover_rate}")
        print(f"变异概率: {self.mutation_rate}")
        print(f"精英比例: {self.elite_fraction}")
        print(f"锦标赛规模: {self.tournament_k}")
        print(f"随机种子: {self.random_seed if self.random_seed is not None else '未设置'}")
        print(f"井轨迹障碍物数量: {len(self.well_obstacles)}")
        print()

        start_time = time.time()
        self._initialize()

        print(f"初始最优适应度: {self.best_fitness:.6f}")

        elite_count = max(1, int(self.elite_fraction * self.population_size))

        for generation in range(self.max_generations):
            # 排序，获取精英个体
            indices_sorted = sorted(range(self.population_size), key=lambda i: self.fitness[i])
            elites = [self.population[i].copy() for i in indices_sorted[:elite_count]]
            elites_f = [self.fitness[i] for i in indices_sorted[:elite_count]]

            new_population: List[np.ndarray] = []
            new_fitness: List[float] = []

            # 保留精英
            new_population.extend(elites)
            new_fitness.extend(elites_f)

            # 生成后代
            while len(new_population) < self.population_size:
                p1, p2 = self._select_parents()
                c1, c2 = self._crossover(p1, p2)
                c1 = self._mutate(c1)
                c2 = self._mutate(c2)
                f1 = self.objective.calculate_objective(c1)
                f2 = self.objective.calculate_objective(c2)
                new_population.append(c1)
                new_fitness.append(f1)
                if len(new_population) < self.population_size:
                    new_population.append(c2)
                    new_fitness.append(f2)

            # 截断至固定大小
            if len(new_population) > self.population_size:
                new_population = new_population[:self.population_size]
                new_fitness = new_fitness[:self.population_size]

            self.population = new_population
            self.fitness = new_fitness

            # 记录该代所有个体参数与适应度（流式写入CSV以节省内存）
            param_names = ["D_kop", "alpha1", "alpha2", "phi1", "phi2", "R1", "R2", "D_turn_kop"]
            if self.population_csv_path:
                rows = []
                for ind, f in zip(self.population, self.fitness):
                    row = {name: float(ind[i]) for i, name in enumerate(param_names)}
                    row['fitness'] = float(f)
                    row['generation'] = int(generation + 1)
                    rows.append(row)
                df_gen = pd.DataFrame(rows)
                # 初始化或追加写入
                if not self._csv_initialized:
                    df_gen.to_csv(self.population_csv_path, index=False, mode='w', encoding='utf-8-sig')
                    self._csv_initialized = True
                else:
                    df_gen.to_csv(self.population_csv_path, index=False, mode='a', header=False, encoding='utf-8-sig')
            else:
                # 若未指定CSV路径，仍保留内存记录作为回退
                gen_records = []
                for ind, f in zip(self.population, self.fitness):
                    rec = {name: float(ind[i]) for i, name in enumerate(param_names)}
                    rec['fitness'] = float(f)
                    rec['generation'] = int(generation + 1)
                    gen_records.append(rec)
                # 若未设置 population_history 列表，提前创建
                if not hasattr(self, 'population_history'):
                    self.population_history = []
                self.population_history.append(gen_records)

            # 更新全局最优
            gen_best_idx = int(np.argmin(self.fitness))
            if self.fitness[gen_best_idx] < self.best_fitness:
                self.best_fitness = float(self.fitness[gen_best_idx])
                self.best_individual = self.population[gen_best_idx].copy()

            # 记录历史最优集合（用于 DI）
            if self.best_individual is not None:
                self.best_history.append(self.best_individual.copy())

            diversity = self._diversity()
            self.fitness_history.append(self.best_fitness)
            self.diversity_history.append(diversity)

            # 记录信息
            info = {
                'iteration': generation + 1,
                'best_fitness': self.best_fitness,
                'mean_fitness': float(np.mean(self.fitness)),
                'std_fitness': float(np.std(self.fitness)),
                'diversity': diversity
            }
            if self.best_individual is not None:
                for i, name in enumerate(param_names):
                    info[f'best_{name}'] = float(self.best_individual[i])
            self.iteration_data.append(info)

            # ===== 收敛指标计算与记录 =====
            if self.enable_convergence_metrics:
                di_mean, di_std, dr_mean, dr_std = self._compute_DI_DR()
                nn_mean, nn_std = self._mean_nearest_neighbor()
                xg_mean, xg_std = self._mean_distance_to_global(self.population)
                xopt_mean, xopt_std = self._mean_distance_to_global(self.best_history)
                self.convergence_metrics.append({
                    'epochs': generation + 1,
                    'wasserstein_DI_mean': di_mean,
                    'wasserstein_DI_std': di_std,
                    'wasserstein_DR_mean': dr_mean,
                    'wasserstein_DR_std': dr_std,
                    'nearest_neighbor_mean': nn_mean,
                    'nearest_neighbor_std': nn_std,
                    'global_opt_XG_mean': xg_mean,
                    'global_opt_XG_std': xg_std,
                    'global_opt_Xopt_mean': xopt_mean,
                    'global_opt_Xopt_std': xopt_std,
                })

            if (generation + 1) % 2 == 0:
                print(f"Generation {generation + 1}: Best Fitness = {self.best_fitness:.6f}, Diversity = {diversity:.6f}")

        end_time = time.time()

        result = {
            'best_solution': self.best_individual,
            'best_fitness': self.best_fitness,
            'total_iterations': len(self.fitness_history),
            'optimization_time': end_time - start_time,
            'iteration_data': self.iteration_data,
            # 若设置了CSV输出，则不返回内存中的 population_history 以节省内存
            'population_history': getattr(self, 'population_history', None) if not self.population_csv_path else None,
            'convergence_metrics': self.convergence_metrics if self.enable_convergence_metrics else None,
            'config': self.config
        }

        if self.best_individual is not None:
            info = self.objective.get_trajectory_info(self.best_individual)
            if info['success']:
                result['trajectory_info'] = info

        self._save_data_to_csv(self.ga_csv_path)
        # 输出收敛指标CSV
        if self.enable_convergence_metrics and self.convergence_metrics:
            try:
                df_metrics = pd.DataFrame(self.convergence_metrics)
                df_metrics.to_csv('ga_convergence_metrics.csv', index=False)
                print('Convergence metrics saved to: ga_convergence_metrics.csv')
            except Exception as e:
                print(f'Failed to save convergence metrics: {e}')
        self._plot_convergence(self.convergence_plot_path, show=False)

        print(f"\n优化完成!")
        print(f"最佳适应度: {self.best_fitness:.6f}")
        print(f"优化时间: {result['optimization_time']:.2f} 秒")
        print(f"总迭代次数: {len(self.fitness_history)}")

        if self.best_individual is not None:
            param_names = ["D_kop", "alpha1", "alpha2", "phi1", "phi2", "R1", "R2", "D_turn_kop"]
            print(f"\n最佳参数:")
            for name, value in zip(param_names, self.best_individual):
                print(f"  {name}: {value:.4f}")
            if 'trajectory_info' in result:
                traj_info = result['trajectory_info']
                print(f"\n轨迹信息:")
                print(f"  总长度: {traj_info['total_length']:.2f} m")
                print(f"  目标偏差: {traj_info['target_deviation']:.2f} m")
                print(f"  井轨迹碰撞: {'是' if traj_info['well_collision'] else '否'}")

        return result

    def _save_data_to_csv(self, filename: str = "ga_optimization_data.csv"):
        if not self.iteration_data:
            print("No data to save")
            return
        df = pd.DataFrame(self.iteration_data)
        df.to_csv(filename, index=False)
        print(f"Optimization data saved to: {filename}")

    def _plot_convergence(self, save_path: str = "ga_convergence_plot.png", show: bool = True):
        if not self.fitness_history:
            print("No convergence data available")
            return
        plt.rcParams['font.family'] = 'DejaVu Sans'
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        ax1.plot(self.fitness_history, 'r-', linewidth=2, label='Best Fitness')
        ax1.set_xlabel('Generation')
        ax1.set_ylabel('Fitness Value')
        ax1.set_title('Genetic Algorithm Convergence')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_yscale('log')
        ax2.plot(self.diversity_history, 'g-', linewidth=1)
        ax2.set_xlabel('Generation')
        ax2.set_ylabel('Diversity')
        ax2.set_title('Population Diversity')
        ax2.grid(True, alpha=0.3)
        if len(self.fitness_history) >= 100:
            recent_fitness = self.fitness_history[-100:]
            ax3.hist(recent_fitness, bins=20, alpha=0.7, color='orange')
            ax3.axvline(self.best_fitness, color='red', linestyle='--', linewidth=2, label=f'Best: {self.best_fitness:.6f}')
            ax3.set_xlabel('Fitness Value')
            ax3.set_ylabel('Frequency')
            ax3.set_title('Recent Fitness Distribution (Last 100 generations)')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            ax3.set_yscale('log')
        if len(self.fitness_history) > 1:
            improvement = np.diff(self.fitness_history)
            ax4.plot(improvement, 'purple', linewidth=1)
            ax4.set_xlabel('Generation')
            ax4.set_ylabel('Fitness Improvement')
            ax4.set_title('Convergence Speed')
            ax4.grid(True, alpha=0.3)
            ax4.set_yscale('log')
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Convergence plot saved to: {save_path}")
        if show:
            plt.show()
        else:
            plt.close()


def optimize_well_trajectory_de(target_e, target_n, target_d, 
                               wellhead_position=(0, 0, 0),
                               excel_files=None, wellhead_positions=None,
                               population_size=30, max_iterations=1000,
                               F=0.5, CR=0.9, strategy="rand/1/bin",
                               random_seed=42):
    """
    差分进化井轨迹优化函数
    
    Args:
        target_e, target_n, target_d: 目标点坐标
        wellhead_position: 井口坐标 (E, N, D)
        excel_files: Excel文件列表
        wellhead_positions: 井轨迹障碍物井口位置
        population_size: 种群大小
        max_iterations: 最大迭代次数
        F: 缩放因子
        CR: 交叉概率
        strategy: 变异策略
        random_seed: 随机种子
    
    Returns:
        优化结果字典
    """
    optimizer = DEWellTrajectoryOptimizer(
        target_e=target_e,
        target_n=target_n,
        target_d=target_d,
        wellhead_position=wellhead_position,
        excel_files=excel_files,
        wellhead_positions=wellhead_positions,
        population_size=population_size,
        max_iterations=max_iterations,
        F=F,
        CR=CR,
        strategy=strategy,
        random_seed=random_seed
    )
    
    return optimizer.optimize()


def get_trajectory_info(config, individual):
    """获取轨迹信息"""
    objective = WellTrajectoryObjective(config)
    return objective.get_trajectory_info(individual)


def optimize_well_trajectory_ga(target_e, target_n, target_d,
                               wellhead_position=(0, 0, 0),
                               excel_files=None, wellhead_positions=None,
                               population_size=30, max_generations=1000,
                               crossover_rate=0.9, mutation_rate=0.1,
                               elite_fraction=0.05, tournament_k=3,
                               random_seed=42,
                               population_csv_path: Optional[str] = None,
                               ga_csv_path: str = "ga_optimization_data.csv",
                               convergence_plot_path: str = "ga_convergence_plot.png"):
    """
    遗传算法井轨迹优化函数
    """
    optimizer = GAWellTrajectoryOptimizer(
        target_e=target_e,
        target_n=target_n,
        target_d=target_d,
        wellhead_position=wellhead_position,
        excel_files=excel_files,
        wellhead_positions=wellhead_positions,
        population_size=population_size,
        max_generations=max_generations,
        crossover_rate=crossover_rate,
        mutation_rate=mutation_rate,
        elite_fraction=elite_fraction,
        tournament_k=tournament_k,
        random_seed=random_seed,
        population_csv_path=population_csv_path,
        ga_csv_path=ga_csv_path,
        convergence_plot_path=convergence_plot_path
    )
    return optimizer.optimize()


# # 使用示例
# if __name__ == "__main__":
#     print("差分进化井轨迹优化示例")
#     print("=" * 50)
    
#     # 优化参数（参考GA算法的配置）
#     result = optimize_well_trajectory_de(
#         target_e=100.64,        # 绝对目标点
#         target_n=2200.71,
#         target_d=2936.06,
#         wellhead_position=(214, 2030, 0),  # 被优化井的井口坐标
#         excel_files=["米41-37YH3-simple.xlsx", "米41-37YH5-simple.xlsx"],
#         wellhead_positions=[     # 井轨迹障碍物的井口位置
#             (208, 2015, 0.0),
#             (210, 2007, 0.0)
#         ],
#         population_size=30,      # 种群大小
#         max_iterations=1000,     # 最大迭代次数
#         F=0.5,                   # 缩放因子
#         CR=0.9,                  # 交叉概率
#         strategy="rand/1/bin",   # 变异策略
#         random_seed=42
#     )
    
#     print(f"\n最终结果:")
#     print(f"最佳适应度: {result['best_fitness']:.6f}")
#     print(f"最佳参数: {result['best_solution']}")
    
#     # 获取轨迹信息
#     traj_info = get_trajectory_info(result['config'], result['best_solution'])
#     if traj_info['success']:
#         print(f"\n轨迹信息:")
#         print(f"  总长度: {traj_info['total_length']:.2f} m")
#         print(f"  目标偏差: {traj_info['target_deviation']:.2f} m")
#         print(f"  球体碰撞: {'是' if traj_info['sphere_collision'] else '否'}")
#         print(f"  井轨迹碰撞: {'是' if traj_info['well_collision'] else '否'}")
