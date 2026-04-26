#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
极简的L-SHADE井轨迹优化器
直接使用 l_shade_well_trajectory 模块，不重复实现任何功能
"""

import sys
import os
import numpy as np

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(current_dir)
sys.path.append(parent_dir)

from l_shade_well_trajectory import optimize_well_trajectory_l_shade, get_trajectory_info

def optimize_well_trajectory(target_e, target_n, target_d, 
                           wellhead_position=(0, 0, 0),
                           excel_files=None, wellhead_positions=None,
                           # L-SHADE 核心参数
                           initial_population_size=100, min_population_size=4,
                           max_iterations=1000, memory_size=5,
                           random_seed=1):
    """
    极简的L-SHADE井轨迹优化函数
    
    Args:
        target_e, target_n, target_d: 目标点坐标
        wellhead_position: 井口坐标 (E, N, D)
        excel_files: Excel文件列表
        wellhead_positions: 井轨迹障碍物井口位置
        
        # L-SHADE 核心参数
        initial_population_size: 初始种群大小 (默认100)
        min_population_size: 最小种群大小 (默认4)
        max_iterations: 最大迭代次数 (默认1000)
        memory_size: 历史记忆大小 (默认5)
        random_seed: 随机种子 (默认42)
    
    Returns:
        优化结果字典
    """
    return optimize_well_trajectory_l_shade(
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


def run_multiple_optimizations_with_stats(num_runs=10,
                                         target_e=502.64,
                                         target_n=790.71,
                                         target_d=2636.06,
                                         wellhead_position=(254, 2030, 0),
                                         excel_files=None,
                                         wellhead_positions=None,
                                         initial_population_size=100,
                                         min_population_size=4,
                                         max_iterations=1000,
                                         memory_size=5,
                                         base_seed=100):
    """
    多次运行L-SHADE优化，计算最终优化结果的目标值（适应度）的平均值和标准差。
    
    Args:
        num_runs: 运行次数（默认10次）
        target_e, target_n, target_d: 目标点坐标
        wellhead_position: 井口坐标 (E, N, D)
        excel_files: Excel文件列表
        wellhead_positions: 井轨迹障碍物井口位置
        initial_population_size: 初始种群大小
        min_population_size: 最小种群大小
        max_iterations: 最大迭代次数
        memory_size: 历史记忆大小
        base_seed: 基础随机种子（每次运行会递增）
    
    Returns:
        包含统计信息的字典：
        - fitness_values: 所有运行的最佳适应度值列表
        - mean: 平均值
        - std: 标准差
        - min: 最小值
        - max: 最大值
        - all_results: 所有运行的完整结果列表
    """
    print(f"开始运行 {num_runs} 次L-SHADE优化...")
    fitness_values = []
    all_results = []
    
    for i in range(num_runs):
        seed = None if base_seed is None else int(base_seed) + i
        print(f"\n第 {i+1}/{num_runs} 次运行 (seed={seed})...")
        
        result = optimize_well_trajectory(
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
            random_seed=seed
        )
        
        fitness = float(result.get('best_fitness', np.nan))
        fitness_values.append(fitness)
        all_results.append(result)
        
        print(f"  本次运行最佳适应度: {fitness:.6f}")
    
    # 计算统计量
    fitness_array = np.array(fitness_values)
    mean_fitness = np.mean(fitness_array)
    std_fitness = np.std(fitness_array, ddof=1)  # 样本标准差
    min_fitness = np.min(fitness_array)
    max_fitness = np.max(fitness_array)
    
    # 输出统计结果
    print("\n" + "=" * 50)
    print("多次运行统计结果:")
    print("=" * 50)
    print(f"运行次数: {num_runs}")
    print(f"目标值（适应度）平均值: {mean_fitness:.6f}")
    print(f"目标值（适应度）标准差: {std_fitness:.6f}")
    print(f"目标值（适应度）最小值: {min_fitness:.6f}")
    print(f"目标值（适应度）最大值: {max_fitness:.6f}")
    print("=" * 50)
    
    return {
        'fitness_values': fitness_values,
        'mean': mean_fitness,
        'std': std_fitness,
        'min': min_fitness,
        'max': max_fitness,
        'num_runs': num_runs,
        'all_results': all_results
    }

# 使用示例
if __name__ == "__main__":
    print("极简L-SHADE井轨迹优化示例")
    print("=" * 50)
    
    # # 高精度优化（大参数）
    # print("\n高精度优化（大参数）:")
    # result4 = optimize_well_trajectory(
    #     target_e=502.64,
    #     target_n=790.71,
    #     target_d=2736.06,
    #     wellhead_position=(254, 2030, 0),
    #     excel_files=["米431-37YH3-simple.xlsx", "米421-37YH5-simple.xlsx"],
    #     wellhead_positions=[(208, 2015, 0.0), (210, 2007, 0.0)],
    #     initial_population_size=100,   # 初始种群
    #     min_population_size=10,         # 最小种群
    #     max_iterations=200,            # 迭代次数
    #     memory_size=2                   # 历史记忆大小
    # )
    # print(f"最佳适应度: {result4['best_fitness']:.6f}")
    # print(f"最佳参数: {result4['best_solution']}")
    # 
    # # Display diversity analysis results
    # if 'diversity_analysis' in result4 and result4['diversity_analysis'] is not None:
    #     diversity_data = result4['diversity_analysis']
    #     print(f"\n=== Diversity Analysis Results ===")
    #     print(f"Maximum diversity: {diversity_data['diversity_max']:.6f}")
    #     print(f"Final diversity: {diversity_data['diversity'][-1]:.6f}")
    #     print(f"Final exploration ability: {diversity_data['xpl_percent'][-1]:.2f}%")
    #     print(f"Final exploitation ability: {diversity_data['xpt_percent'][-1]:.2f}%")
    #     
    #     # Export diversity analysis to Excel for later inspection
    #     try:
    #         import sys
    #         import os
    #         parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    #         sys.path.append(os.path.join(parent_dir, 'IPOP_CMA_ES'))
    #         from diversity_utils import export_diversity_analysis_to_excel
    #         export_diversity_analysis_to_excel(diversity_data, excel_path="l_shade_diversity_analysis_export.xlsx")
    #     except:
    #         print("无法导出多样性分析到Excel")
    #     
    #     # Generate additional diversity summary statistics plot
    #     try:
    #         from diversity_utils import plot_diversity_summary_statistics
    #         plot_diversity_summary_statistics(diversity_data, save_path="l_shade_diversity_summary.png")
    #     except:
    #         print("无法生成多样性统计摘要图")
    # else:
    #     print("\n=== Diversity Analysis Not Available ===")
    #     print("Underlying L-SHADE algorithm did not return population history data, cannot perform diversity analysis")
    
    # 多次运行并计算统计值
    print("\n多次运行L-SHADE优化并计算统计值:")
    stats_result = run_multiple_optimizations_with_stats(
        num_runs=10,  # 指定运行次数
        target_e=502.64,
        target_n=790.71,
        target_d=2736.06,
        wellhead_position=(254, 2030, 0),
        excel_files=["米431-37YH3-simple.xlsx", "米421-37YH5-simple.xlsx"],
        wellhead_positions=[(208, 2015, 0.0), (210, 2007, 0.0)],
        initial_population_size=100,
        min_population_size=10,
        max_iterations=200,
        memory_size=2,
        base_seed=100
    )
    # 可以访问统计结果
    print(f"\n统计结果已返回，平均值: {stats_result['mean']:.6f}, 标准差: {stats_result['std']:.6f}")

