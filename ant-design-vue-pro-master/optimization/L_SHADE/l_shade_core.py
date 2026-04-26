#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
L-SHADE核心算法实现
L-SHADE: Success-History based Adaptive Differential Evolution with Linear population size reduction
"""

import numpy as np
from typing import Callable, Tuple, Optional, Dict, Any, List

class LSHADE:
    """
    L-SHADE算法核心类
    """
    
    def __init__(self, 
                 dimension: int,
                 bounds: list,
                 objective_func: Callable,
                 initial_population_size: int = 100,
                 min_population_size: int = 4,
                 memory_size: int = 5,
                 random_seed: Optional[int] = None):
        """
        初始化L-SHADE算法
        
        Args:
            dimension: 问题维度
            bounds: 参数边界列表 [(min, max), ...]
            objective_func: 目标函数
            initial_population_size: 初始种群大小
            min_population_size: 最小种群大小
            memory_size: 历史记忆大小
            random_seed: 随机种子
        """
        self.dimension = dimension
        self.bounds = bounds
        self.objective_func = objective_func
        
        # 设置随机种子
        if random_seed is not None:
            np.random.seed(random_seed)
        
        # 计算参数范围
        self.lower_bounds = np.array([b[0] for b in bounds])
        self.upper_bounds = np.array([b[1] for b in bounds])
        self.param_range = self.upper_bounds - self.lower_bounds
        
        # 种群大小参数
        self.initial_population_size = initial_population_size
        self.min_population_size = min_population_size
        self.current_population_size = initial_population_size
        
        # 历史记忆
        self.memory_size = memory_size
        self.M_F = np.ones(memory_size) * 0.5  # F的历史记忆
        self.M_CR = np.ones(memory_size) * 0.5  # CR的历史记忆
        self.memory_index = 0
        
        # 成功历史
        self.S_F = []  # 成功的F值
        self.S_CR = []  # 成功的CR值
        
        # 外部存档
        self.archive = []
        self.archive_size = 0
        
        # 初始化种群
        self.population = None
        self.fitness = None
        self.best_fitness = float('inf')
        self.best_solution = None
        
        # 记录
        self.generation = 0
        
    def initialize_population(self):
        """初始化种群"""
        self.population = np.random.uniform(
            self.lower_bounds,
            self.upper_bounds,
            (self.current_population_size, self.dimension)
        )
        
        # 评估初始种群
        self.fitness = np.array([self.objective_func(ind) for ind in self.population])
        
        # 找到最优解
        best_idx = np.argmin(self.fitness)
        self.best_fitness = self.fitness[best_idx]
        self.best_solution = self.population[best_idx].copy()
        
        # 初始化存档
        self.archive = []
        self.archive_size = 0
    
    def select_F_CR(self) -> Tuple[float, float]:
        """
        从历史记忆中选择F和CR值
        
        Returns:
            (F, CR): 变异因子和交叉概率
        """
        # 选择历史记忆索引
        r = np.random.randint(0, self.memory_size)
        
        # 从历史记忆中获取F和CR
        F = np.random.normal(self.M_F[r], 0.1)
        F = np.clip(F, 0.1, 1.0)  # 限制在[0.1, 1.0]
        
        CR = np.random.normal(self.M_CR[r], 0.1)
        CR = np.clip(CR, 0.0, 1.0)  # 限制在[0.0, 1.0]
        
        return F, CR
    
    def mutation(self, F: float) -> np.ndarray:
        """
        变异操作（current-to-pbest/1）
        
        Args:
            F: 变异因子
        
        Returns:
            变异后的个体
        """
        # 选择pbest个体（前p*N个最优个体）
        p = 0.2  # p值
        pbest_size = max(1, int(self.current_population_size * p))
        pbest_indices = np.argsort(self.fitness)[:pbest_size]
        pbest_idx = np.random.choice(pbest_indices)
        
        # 选择基向量
        x_pbest = self.population[pbest_idx]
        
        # 选择两个不同的个体
        indices = np.arange(self.current_population_size)
        r1 = np.random.choice(indices)
        indices = np.delete(indices, r1)
        r2 = np.random.choice(indices)
        
        # 从当前种群或存档中选择r2
        if len(self.archive) > 0 and np.random.rand() < 0.5:
            r2_archive = np.random.randint(0, len(self.archive))
            x_r2 = self.archive[r2_archive]
        else:
            x_r2 = self.population[r2]
        
        # 变异
        v = self.population[r1] + F * (x_pbest - self.population[r1]) + F * (self.population[r2] - x_r2)
        
        return v
    
    def crossover(self, x: np.ndarray, v: np.ndarray, CR: float) -> np.ndarray:
        """
        交叉操作（二项交叉）
        
        Args:
            x: 当前个体
            v: 变异个体
            CR: 交叉概率
        
        Returns:
            交叉后的个体
        """
        u = x.copy()
        j_rand = np.random.randint(0, self.dimension)  # 确保至少有一个维度来自变异个体
        
        for j in range(self.dimension):
            if np.random.rand() < CR or j == j_rand:
                u[j] = v[j]
        
        return u
    
    def boundary_handling(self, u: np.ndarray) -> np.ndarray:
        """
        边界处理
        
        Args:
            u: 个体
        
        Returns:
            处理后的个体
        """
        # 反射边界
        for j in range(self.dimension):
            if u[j] < self.lower_bounds[j]:
                u[j] = 2 * self.lower_bounds[j] - u[j]
            elif u[j] > self.upper_bounds[j]:
                u[j] = 2 * self.upper_bounds[j] - u[j]
            
            # 再次检查，如果还在边界外，则随机初始化
            if u[j] < self.lower_bounds[j] or u[j] > self.upper_bounds[j]:
                u[j] = np.random.uniform(self.lower_bounds[j], self.upper_bounds[j])
        
        return u
    
    def update_memory(self, successful_F: List[float], successful_CR: List[float]):
        """
        更新历史记忆
        
        Args:
            successful_F: 成功的F值列表
            successful_CR: 成功的CR值列表
        """
        if len(successful_F) > 0:
            # 使用加权Lehmer均值更新F
            weights = np.array(successful_F)
            weights = weights / np.sum(weights)
            M_F_new = np.sum(weights * np.array(successful_F) ** 2) / np.sum(weights * np.array(successful_F))
            
            # 使用加权算术均值更新CR
            M_CR_new = np.mean(successful_CR)
            
            # 更新历史记忆
            self.M_F[self.memory_index] = M_F_new
            self.M_CR[self.memory_index] = M_CR_new
            
            # 更新记忆索引
            self.memory_index = (self.memory_index + 1) % self.memory_size
    
    def update_archive(self, old_population: np.ndarray, old_fitness: np.ndarray):
        """
        更新外部存档
        
        Args:
            old_population: 旧种群
            old_fitness: 旧适应度
        """
        # 将失败的个体添加到存档
        min_len = min(len(old_population), len(self.population))
        for i in range(min_len):
            if old_fitness[i] > self.fitness[i]:  # 如果新个体更好，旧个体失败
                if len(self.archive) < self.current_population_size:
                    self.archive.append(old_population[i].copy())
                else:
                    # 随机替换
                    if len(self.archive) > 0:
                        idx = np.random.randint(0, len(self.archive))
                        self.archive[idx] = old_population[i].copy()
                    else:
                        self.archive.append(old_population[i].copy())
    
    def reduce_population_size(self, max_generations: int, current_generation: int):
        """
        线性减少种群大小
        
        Args:
            max_generations: 最大代数
            current_generation: 当前代数
        """
        # 计算目标种群大小
        target_size = int(
            self.min_population_size + 
            (self.initial_population_size - self.min_population_size) * 
            (1 - current_generation / max_generations)
        )
        
        # 如果目标大小小于当前大小，则减少种群
        if target_size < self.current_population_size:
            # 选择最优的target_size个个体
            sorted_indices = np.argsort(self.fitness)
            keep_indices = sorted_indices[:target_size]
            
            self.population = self.population[keep_indices]
            self.fitness = self.fitness[keep_indices]
            self.current_population_size = target_size
    
    def optimize_step(self, max_generations: int) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
        """
        执行一步优化
        
        Args:
            max_generations: 最大代数
        
        Returns:
            (population, fitness, info): 种群、适应度、信息字典
        """
        if self.population is None:
            self.initialize_population()
        
        old_population = self.population.copy()
        old_fitness = self.fitness.copy()
        
        new_population = []
        new_fitness = []
        successful_F = []
        successful_CR = []
        
        # 对每个个体进行变异、交叉和选择
        for i in range(self.current_population_size):
            # 选择F和CR
            F, CR = self.select_F_CR()
            
            # 变异
            v = self.mutation(F)
            
            # 交叉
            u = self.crossover(self.population[i], v, CR)
            
            # 边界处理
            u = self.boundary_handling(u)
            
            # 评估新个体
            fitness_u = self.objective_func(u)
            
            # 选择（贪婪选择）
            if fitness_u <= self.fitness[i]:
                new_population.append(u)
                new_fitness.append(fitness_u)
                successful_F.append(F)
                successful_CR.append(CR)
            else:
                new_population.append(self.population[i])
                new_fitness.append(self.fitness[i])
        
        # 更新种群
        self.population = np.array(new_population)
        self.fitness = np.array(new_fitness)
        
        # 更新最优解
        best_idx = np.argmin(self.fitness)
        if self.fitness[best_idx] < self.best_fitness:
            self.best_fitness = self.fitness[best_idx]
            self.best_solution = self.population[best_idx].copy()
        
        # 更新存档
        self.update_archive(old_population, old_fitness)
        
        # 更新历史记忆
        if len(successful_F) > 0:
            self.update_memory(successful_F, successful_CR)
        
        # 线性减少种群大小
        self.reduce_population_size(max_generations, self.generation)
        
        self.generation += 1
        
        # 信息
        info = {
            'generation': self.generation,
            'best_fitness': self.best_fitness,
            'mean_fitness': np.mean(self.fitness),
            'std_fitness': np.std(self.fitness),
            'population_size': self.current_population_size,
            'archive_size': len(self.archive)
        }
        
        return self.population, self.fitness, info
    
    def get_best(self) -> Tuple[np.ndarray, float]:
        """
        获取当前最优解
        
        Returns:
            (best_solution, best_fitness)
        """
        return self.best_solution, self.best_fitness

