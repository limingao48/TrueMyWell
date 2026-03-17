#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
L-SHADE井轨迹优化器
L-SHADE (Success-History based Adaptive Differential Evolution with Linear population size reduction) Well Trajectory Optimizer

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
        WellTrajectoryObjective,
        create_multiple_well_obstacles
    )
    WELL_TRAJECTORY_AVAILABLE = True
except ImportError as e:
    print(f"错误：无法导入井轨迹模块: {e}")
    print("请确保 well_trajectory_objective 模块在父目录中")
    WELL_TRAJECTORY_AVAILABLE = False

# 导入L-SHADE核心和多样性工具（复用IPOP_CMA_ES的多样性工具）
sys.path.append(os.path.join(parent_dir, 'IPOP_CMA_ES'))
try:
    from diversity_utils import (
        calculate_diversity, track_diversity_evolution,
        export_diversity_analysis_to_excel, plot_diversity_analysis,
        plot_diversity_summary_statistics, PARAM_NAMES
    )
except ImportError:
    # 如果导入失败，尝试从当前目录导入
    try:
        from IPOP_CMA_ES.diversity_utils import (
            calculate_diversity, track_diversity_evolution,
            export_diversity_analysis_to_excel, plot_diversity_analysis,
            plot_diversity_summary_statistics, PARAM_NAMES
        )
    except ImportError:
        print("警告：无法导入多样性工具，多样性分析功能将不可用")
        PARAM_NAMES = ["D_kop", "alpha1", "alpha2", "phi1", "phi2", "R1", "R2", "D_turn_kop"]
        calculate_diversity = None
        track_diversity_evolution = None

from l_shade_core import LSHADE

class LSHADEWellTrajectoryOptimizer:
    """L-SHADE井轨迹优化器"""
    
    def __init__(self, 
                 target_e: float = 1500.64,
                 target_n: float = 1200.71, 
                 target_d: float = 2936.06,
                 wellhead_position: Optional[Tuple[float, float, float]] = None,
                 excel_files: Optional[List[str]] = None,
                 wellhead_positions: Optional[List[Tuple[float, float, float]]] = None,
                 # L-SHADE 核心参数
                 initial_population_size: int = 100,
                 min_population_size: int = 4,
                 max_iterations: int = 1000,
                 memory_size: int = 5,
                 random_seed: Optional[int] = None):
        """
        初始化L-SHADE优化器
        
        Args:
            target_e: 目标东坐标
            target_n: 目标北坐标  
            target_d: 目标深度
            wellhead_position: 被优化井的井口坐标 (E, N, D)
            excel_files: Excel文件列表
            wellhead_positions: 井轨迹障碍物的井口位置列表
            initial_population_size: 初始种群大小
            min_population_size: 最小种群大小
            max_iterations: 最大迭代次数
            memory_size: 历史记忆大小
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
        
        # L-SHADE 参数
        self.initial_population_size = initial_population_size
        self.min_population_size = min_population_size
        self.max_iterations = max_iterations
        self.memory_size = memory_size
        self.random_seed = random_seed
        
        # 设置随机种子
        if random_seed is not None:
            random.seed(random_seed)
            np.random.seed(random_seed)
            print(f"随机种子设置为: {random_seed}")
        
        # 创建井轨迹配置
        self.config = WellTrajectoryConfig(
            E_target=self.relative_target_e,
            N_target=self.relative_target_n,
            D_target=self.relative_target_d,
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
        print(self.config)
        # 创建目标函数
        self.objective = WellTrajectoryObjective(self.config, well_obstacles=self.well_obstacles)
        
        # 获取参数边界
        bounds = self.config.get_parameter_bounds()
        self.param_bounds = [(bounds[i, 0], bounds[i, 1]) for i in range(len(bounds))]
        self.dimension = len(self.param_bounds)
        
        # 全局最优
        self.global_best_fitness = float('inf')
        self.global_best_solution = None
        
        # 数据记录
        self.iteration_data = []
        self.fitness_history = []
        self.diversity_history = []
        self.population_history = []  # 用于多样性分析
        self.population_size_history = []  # 记录种群大小变化
        
    def objective_wrapper(self, x: np.ndarray) -> float:
        """
        目标函数包装器
        
        Args:
            x: 参数向量
        
        Returns:
            适应度值
        """
        return self.objective.calculate_objective(x.tolist())
    
    def optimize(self) -> Dict[str, Any]:
        """执行L-SHADE优化"""
        print("=" * 60)
        print("L-SHADE井轨迹优化器")
        print("=" * 60)
        print(f"绝对目标点: E={self.target_e}, N={self.target_n}, D={self.target_d}")
        print(f"被优化井井口: E={self.wellhead_position[0]}, N={self.wellhead_position[1]}, D={self.wellhead_position[2]}")
        print(f"相对目标点: E={self.relative_target_e:.2f}, N={self.relative_target_n:.2f}, D={self.relative_target_d:.2f}")
        print(f"初始种群大小: {self.initial_population_size}")
        print(f"最小种群大小: {self.min_population_size}")
        print(f"最大迭代次数: {self.max_iterations}")
        print(f"历史记忆大小: {self.memory_size}")
        print(f"随机种子: {self.random_seed if self.random_seed is not None else '未设置'}")
        print(f"井轨迹障碍物数量: {len(self.well_obstacles)}")
        print()
        
        start_time = time.time()
        
        # 创建L-SHADE实例
        l_shade = LSHADE(
            dimension=self.dimension,
            bounds=self.param_bounds,
            objective_func=self.objective_wrapper,
            initial_population_size=self.initial_population_size,
            min_population_size=self.min_population_size,
            memory_size=self.memory_size,
            random_seed=self.random_seed
        )
        
        # 主循环
        for iteration in range(self.max_iterations):
            # 执行一步优化
            population, fitness, info = l_shade.optimize_step(self.max_iterations)
            
            # 更新全局最优
            if l_shade.best_fitness < self.global_best_fitness:
                self.global_best_fitness = l_shade.best_fitness
                self.global_best_solution = l_shade.best_solution.copy()
            
            # 计算多样性
            if calculate_diversity is not None:
                diversity = calculate_diversity(population)
            else:
                diversity = 0.0
            
            # 记录数据
            self.fitness_history.append(self.global_best_fitness)
            self.diversity_history.append(diversity)
            self.population_size_history.append(info['population_size'])
            
            # 记录种群历史（用于多样性分析）
            gen_records = []
            for pos, f in zip(population, fitness):
                rec = {name: float(pos[i]) for i, name in enumerate(PARAM_NAMES)}
                rec['fitness'] = float(f)
                rec['generation'] = int(iteration + 1)
                gen_records.append(rec)
            self.population_history.append(gen_records)
            
            # 记录迭代信息
            iteration_info = {
                'iteration': iteration + 1,
                'best_fitness': self.global_best_fitness,
                'mean_fitness': info['mean_fitness'],
                'std_fitness': info['std_fitness'],
                'diversity': diversity,
                'population_size': info['population_size'],
                'archive_size': info['archive_size']
            }
            
            # 添加最优解的参数
            if self.global_best_solution is not None:
                for i, name in enumerate(PARAM_NAMES):
                    iteration_info[f'best_{name}'] = self.global_best_solution[i]
            
            self.iteration_data.append(iteration_info)
            
            # 输出进度
            if (iteration + 1) % 2 == 0 or iteration == 0:
                print(f"迭代 {iteration + 1}/{self.max_iterations}: "
                      f"最佳适应度 = {self.global_best_fitness:.6f}, "
                      f"多样性 = {diversity:.6f}, "
                      f"种群大小 = {info['population_size']}, "
                      f"存档大小 = {info['archive_size']}")
        
        end_time = time.time()
        
        # 多样性分析
        diversity_data = None
        if self.population_history and track_diversity_evolution is not None:
            print("\n执行多样性分析...")
            diversity_data = track_diversity_evolution(self.population_history)
            
            print(f"最大多样性: {diversity_data['diversity_max']:.6f}")
            print(f"最终多样性: {diversity_data['diversity'][-1]:.6f}")
            print(f"最终探索能力: {diversity_data['xpl_percent'][-1]:.2f}%")
            print(f"最终开发能力: {diversity_data['xpt_percent'][-1]:.2f}%")
            
            # 导出多样性分析
            if export_diversity_analysis_to_excel is not None:
                export_diversity_analysis_to_excel(diversity_data, 
                                                   excel_path="l_shade_diversity_analysis_export.xlsx")
            if plot_diversity_analysis is not None:
                plot_diversity_analysis(diversity_data, save_path="l_shade_diversity_analysis.png")
            if plot_diversity_summary_statistics is not None:
                plot_diversity_summary_statistics(diversity_data, save_path="l_shade_diversity_summary.png")
        
        # 最终结果
        result = {
            'best_solution': self.global_best_solution,
            'best_fitness': self.global_best_fitness,
            'total_iterations': len(self.fitness_history),
            'total_evaluations': sum(self.population_size_history),
            'optimization_time': end_time - start_time,
            'iteration_data': self.iteration_data,
            'population_history': self.population_history,
            'population_size_history': self.population_size_history,
            'diversity_analysis': diversity_data,
            'config': self.config
        }
        
        # 获取轨迹信息
        if self.global_best_solution is not None:
            info = self.objective.get_trajectory_info(self.global_best_solution)
            if info['success']:
                result['trajectory_info'] = info
        
        # 保存数据到CSV
        self.save_data_to_csv("l_shade_optimization_data.csv")
        
        # 生成收敛图
        self.plot_convergence("l_shade_convergence_plot.png", show=False)
        
        print(f"\n优化完成!")
        print(f"最佳适应度: {self.global_best_fitness:.6f}")
        print(f"优化时间: {result['optimization_time']:.2f} 秒")
        print(f"总迭代次数: {len(self.fitness_history)}")
        print(f"总评估次数: {sum(self.population_size_history)}")
        
        if self.global_best_solution is not None:
            print(f"\n最佳参数:")
            for name, value in zip(PARAM_NAMES, self.global_best_solution):
                print(f"  {name}: {value:.4f}")
            
            if 'trajectory_info' in result:
                traj_info = result['trajectory_info']
                print(f"\n轨迹信息:")
                print(f"  总长度: {traj_info['total_length']:.2f} m")
                print(f"  目标偏差: {traj_info['target_deviation']:.2f} m")
                print(f"  球体碰撞: {'是' if traj_info['sphere_collision'] else '否'}")
                print(f"  井轨迹碰撞: {'是' if traj_info['well_collision'] else '否'}")
        
        return result
    
    def save_data_to_csv(self, filename: str = "l_shade_optimization_data.csv"):
        """保存数据到CSV文件"""
        if not self.iteration_data:
            print("No data to save")
            return
        df = pd.DataFrame(self.iteration_data)
        df.to_csv(filename, index=False)
        print(f"Optimization data saved to: {filename}")
    
    def plot_convergence(self, save_path: str = "l_shade_convergence_plot.png", show: bool = True):
        """绘制收敛图"""
        if not self.fitness_history:
            print("No convergence data available")
            return
        
        plt.rcParams['font.family'] = 'DejaVu Sans'
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # 绘制适应度曲线
        ax1.plot(self.fitness_history, 'r-', linewidth=2, label='Best Fitness')
        ax1.set_xlabel('Iteration')
        ax1.set_ylabel('Fitness Value')
        ax1.set_title('L-SHADE Convergence')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_yscale('log')
        
        # 绘制多样性曲线
        if len(self.diversity_history) > 0:
            ax2.plot(self.diversity_history, 'g-', linewidth=1)
            ax2.set_xlabel('Iteration')
            ax2.set_ylabel('Diversity')
            ax2.set_title('Population Diversity')
            ax2.grid(True, alpha=0.3)
        
        # 绘制种群大小变化
        if len(self.population_size_history) > 0:
            ax3.plot(self.population_size_history, 'b-', linewidth=2)
            ax3.set_xlabel('Iteration')
            ax3.set_ylabel('Population Size')
            ax3.set_title('Population Size Reduction')
            ax3.grid(True, alpha=0.3)
        
        # 绘制适应度分布（最后100次迭代）
        if len(self.fitness_history) >= 100:
            recent_fitness = self.fitness_history[-100:]
            ax4.hist(recent_fitness, bins=20, alpha=0.7, color='orange')
            ax4.axvline(self.global_best_fitness, color='red', linestyle='--', 
                       linewidth=2, label=f'Best: {self.global_best_fitness:.6f}')
            ax4.set_xlabel('Fitness Value')
            ax4.set_ylabel('Frequency')
            ax4.set_title('Recent Fitness Distribution (Last 100 iterations)')
            ax4.legend()
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


def optimize_well_trajectory_l_shade(target_e, target_n, target_d, 
                                     wellhead_position=(0, 0, 0),
                                     excel_files=None, wellhead_positions=None,
                                     initial_population_size=100, min_population_size=4,
                                     max_iterations=1000, memory_size=5,
                                     random_seed=42):
    """
    L-SHADE井轨迹优化函数
    
    Args:
        target_e, target_n, target_d: 目标点坐标
        wellhead_position: 井口坐标 (E, N, D)
        excel_files: Excel文件列表
        wellhead_positions: 井轨迹障碍物井口位置
        initial_population_size: 初始种群大小
        min_population_size: 最小种群大小
        max_iterations: 最大迭代次数
        memory_size: 历史记忆大小
        random_seed: 随机种子
    
    Returns:
        优化结果字典
    """
    optimizer = LSHADEWellTrajectoryOptimizer(
        target_e=target_e,
        target_n=target_n,
        target_d=target_d,
        wellhead_position=wellhead_position,
        excel_files=excel_files,
        wellhead_positions=wellhead_positions,
        initial_population_size=initial_population_size,
        min_population_size=min_population_size,
        max_iterations=max_iterations,
        memory_size=memory_size,
        random_seed=random_seed
    )
    
    return optimizer.optimize()


def get_trajectory_info(config, individual):
    """获取轨迹信息"""
    objective = WellTrajectoryObjective(config)
    return objective.get_trajectory_info(individual)


# 使用示例
if __name__ == "__main__":
    print("L-SHADE井轨迹优化示例")
    print("=" * 50)
    
    result = optimize_well_trajectory_l_shade(
        target_e=100.64,
        target_n=2200.71,
        target_d=2936.06,
        wellhead_position=(214, 2030, 0),
        excel_files=["米421-37YH3-simple.xlsx", "米421-37YH5-simple.xlsx"],
        wellhead_positions=[
            (208, 2015, 0.0),
            (210, 2007, 0.0)
        ],
        initial_population_size=100,
        min_population_size=4,
        max_iterations=1000,
        memory_size=5,
        random_seed=42
    )
    
    print(f"\n最终结果:")
    print(f"最佳适应度: {result['best_fitness']:.6f}")
    print(f"最佳参数: {result['best_solution']}")

