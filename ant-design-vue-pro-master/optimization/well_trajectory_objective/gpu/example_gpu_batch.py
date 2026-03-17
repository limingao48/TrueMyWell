"""
GPU批量计算井眼轨迹目标函数示例

演示如何使用GPU版本并行计算多个井眼轨迹的目标函数值
"""

import torch
import numpy as np
import time
from ..config import WellTrajectoryConfig
from .objective_function_gpu import WellTrajectoryObjectiveGPU, create_gpu_objective_function
from ..objective_function import WellTrajectoryObjective


def example_batch_calculation():
    """示例：批量计算多个井眼轨迹的目标函数值"""
    
    # 创建配置
    config = WellTrajectoryConfig(
        E_target=1500.64,
        N_target=1200.71,
        D_target=2936.06,
        E_wellhead=30.0,
        N_wellhead=15.0
    )
    
    # 创建GPU目标函数
    print("=" * 60)
    print("创建GPU目标函数")
    print("=" * 60)
    gpu_objective = create_gpu_objective_function(config, n_points=50)
    
    # 生成多个随机参数（批量）
    batch_size = 1000  # 一次计算1000个井眼轨迹
    print(f"\n生成 {batch_size} 个随机参数...")
    
    # 参数范围
    bounds = config.get_parameter_bounds()
    lower_bounds = bounds[:, 0]
    upper_bounds = bounds[:, 1]
    
    # 生成随机参数
    np.random.seed(42)
    params_list = []
    for _ in range(batch_size):
        params = np.random.uniform(lower_bounds, upper_bounds)
        # 确保 D_kop <= D_turn_kop
        if params[0] > params[7]:
            params[0], params[7] = params[7], params[0]
        params_list.append(params)
    
    # 转换为PyTorch张量并移到GPU
    params_tensor = torch.tensor(params_list, device=gpu_objective.device, dtype=torch.float32)
    print(f"参数张量形状: {params_tensor.shape}")
    print(f"参数张量设备: {params_tensor.device}")
    
    # GPU批量计算
    print("\n" + "=" * 60)
    print("开始GPU批量计算...")
    print("=" * 60)
    
    start_time = time.time()
    fitness_batch = gpu_objective.calculate_objective_batch(params_tensor)
    gpu_time = time.time() - start_time
    
    print(f"\n✅ GPU批量计算完成！")
    print(f"   计算时间: {gpu_time:.4f} 秒")
    print(f"   平均每个轨迹: {gpu_time/batch_size*1000:.4f} 毫秒")
    print(f"   吞吐量: {batch_size/gpu_time:.2f} 轨迹/秒")
    
    # 显示结果统计
    fitness_np = fitness_batch.detach().cpu().numpy()
    valid_mask = fitness_np < 1e19  # 有效解
    valid_count = np.sum(valid_mask)
    
    print(f"\n结果统计:")
    print(f"   总数量: {batch_size}")
    print(f"   有效解: {valid_count} ({valid_count/batch_size*100:.1f}%)")
    print(f"   无效解: {batch_size - valid_count} ({(batch_size-valid_count)/batch_size*100:.1f}%)")
    
    if valid_count > 0:
        valid_fitness = fitness_np[valid_mask]
        print(f"\n有效解的目标函数值:")
        print(f"   最小值: {np.min(valid_fitness):.2f}")
        print(f"   最大值: {np.max(valid_fitness):.2f}")
        print(f"   平均值: {np.mean(valid_fitness):.2f}")
        print(f"   中位数: {np.median(valid_fitness):.2f}")
    
    # 获取详细信息（前10个）
    print("\n" + "=" * 60)
    print("获取前10个轨迹的详细信息...")
    print("=" * 60)
    
    info_list = gpu_objective.get_trajectory_info_batch(params_tensor[:10])
    for i, info in enumerate(info_list):
        if info['success']:
            print(f"\n轨迹 {i+1}:")
            print(f"  总长度: {info['total_length']:.2f} m")
            print(f"  目标偏差: {info['target_deviation']:.2f} m")
            print(f"  终点: E={info['final_point'][0]:.2f}, "
                  f"N={info['final_point'][1]:.2f}, D={info['final_point'][2]:.2f}")
        else:
            print(f"\n轨迹 {i+1}: 计算失败 - {info.get('error', 'Unknown error')}")
    
    return fitness_batch, params_tensor


def example_comparison_cpu_vs_gpu():
    """示例：比较CPU和GPU版本的性能"""
    
    # 创建配置
    config = WellTrajectoryConfig(
        E_target=1500.64,
        N_target=1200.71,
        D_target=2936.06,
        E_wellhead=30.0,
        N_wellhead=15.0
    )
    
    # 创建CPU和GPU版本
    cpu_objective = WellTrajectoryObjective(config)
    gpu_objective = create_gpu_objective_function(config, n_points=50)
    
    # 生成测试参数
    test_size = 100
    bounds = config.get_parameter_bounds()
    lower_bounds = bounds[:, 0]
    upper_bounds = bounds[:, 1]
    
    np.random.seed(42)
    params_list = []
    for _ in range(test_size):
        params = np.random.uniform(lower_bounds, upper_bounds)
        if params[0] > params[7]:
            params[0], params[7] = params[7], params[0]
        params_list.append(params)
    
    # CPU版本计算
    print("=" * 60)
    print("CPU版本计算...")
    print("=" * 60)
    start_time = time.time()
    cpu_results = []
    for params in params_list:
        result = cpu_objective.calculate_objective(params)
        cpu_results.append(result)
    cpu_time = time.time() - start_time
    
    print(f"CPU计算时间: {cpu_time:.4f} 秒")
    print(f"平均每个: {cpu_time/test_size*1000:.4f} 毫秒")
    
    # GPU版本计算
    print("\n" + "=" * 60)
    print("GPU版本计算...")
    print("=" * 60)
    params_tensor = torch.tensor(params_list, device=gpu_objective.device, dtype=torch.float32)
    start_time = time.time()
    gpu_results = gpu_objective.calculate_objective_batch(params_tensor)
    gpu_time = time.time() - start_time
    
    print(f"GPU计算时间: {gpu_time:.4f} 秒")
    print(f"平均每个: {gpu_time/test_size*1000:.4f} 毫秒")
    
    # 比较结果
    print("\n" + "=" * 60)
    print("性能比较")
    print("=" * 60)
    speedup = cpu_time / gpu_time
    print(f"加速比: {speedup:.2f}x")
    print(f"GPU比CPU快 {speedup:.2f} 倍")
    
    # 验证结果一致性（允许小的数值误差）
    gpu_results_np = gpu_results.detach().cpu().numpy()
    max_diff = np.max(np.abs(np.array(cpu_results) - gpu_results_np))
    print(f"\n结果差异（最大绝对误差）: {max_diff:.6f}")
    
    if max_diff < 1.0:  # 允许1.0的误差（由于数值精度和简化计算）
        print("✅ 结果基本一致（在允许误差范围内）")
    else:
        print("⚠️  结果存在较大差异（可能是GPU版本使用了简化计算）")


def example_optimization_usage():
    """示例：在优化算法中使用GPU批量计算"""
    
    config = WellTrajectoryConfig(
        E_target=1500.64,
        N_target=1200.71,
        D_target=2936.06,
        E_wellhead=30.0,
        N_wellhead=15.0
    )
    
    # 创建GPU目标函数
    gpu_objective = create_gpu_objective_function(config, n_points=50)
    
    # 模拟优化算法中的种群评估
    population_size = 100
    bounds = config.get_parameter_bounds()
    lower_bounds = bounds[:, 0]
    upper_bounds = bounds[:, 1]
    
    print("=" * 60)
    print("模拟优化算法中的种群评估")
    print("=" * 60)
    
    # 生成初始种群
    np.random.seed(42)
    population = []
    for _ in range(population_size):
        params = np.random.uniform(lower_bounds, upper_bounds)
        if params[0] > params[7]:
            params[0], params[7] = params[7], params[0]
        population.append(params)
    
    # 转换为张量
    population_tensor = torch.tensor(population, device=gpu_objective.device, dtype=torch.float32)
    
    # 批量评估适应度
    print(f"\n评估 {population_size} 个个体的适应度...")
    start_time = time.time()
    fitness = gpu_objective.calculate_objective_batch(population_tensor)
    eval_time = time.time() - start_time
    
    print(f"评估时间: {eval_time:.4f} 秒")
    print(f"平均每个个体: {eval_time/population_size*1000:.4f} 毫秒")
    
    # 找到最佳个体
    fitness_np = fitness.detach().cpu().numpy()
    valid_mask = fitness_np < 1e19
    if np.any(valid_mask):
        best_idx = np.argmin(fitness_np[valid_mask])
        valid_indices = np.where(valid_mask)[0]
        best_individual_idx = valid_indices[best_idx]
        best_fitness = fitness_np[best_individual_idx]
        best_params = population[best_individual_idx]
        
        print(f"\n最佳个体:")
        print(f"  索引: {best_individual_idx}")
        print(f"  适应度: {best_fitness:.2f}")
        print(f"  参数: {best_params}")
        
        # 获取最佳个体的详细信息
        best_info = gpu_objective.get_trajectory_info_batch(
            population_tensor[best_individual_idx:best_individual_idx+1]
        )[0]
        if best_info['success']:
            print(f"  总长度: {best_info['total_length']:.2f} m")
            print(f"  目标偏差: {best_info['target_deviation']:.2f} m")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("GPU批量计算井眼轨迹目标函数示例")
    print("=" * 60)
    
    # 检查GPU是否可用
    if torch.cuda.is_available():
        print(f"\n✅ 检测到GPU: {torch.cuda.get_device_name(0)}")
        print(f"   GPU内存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    else:
        print("\n⚠️  未检测到GPU，将使用CPU（速度较慢）")
    
    # 运行示例
    print("\n" + "=" * 60)
    print("示例1: 批量计算")
    print("=" * 60)
    example_batch_calculation()
    
    print("\n" + "=" * 60)
    print("示例2: CPU vs GPU性能比较")
    print("=" * 60)
    example_comparison_cpu_vs_gpu()
    
    print("\n" + "=" * 60)
    print("示例3: 优化算法中的使用")
    print("=" * 60)
    example_optimization_usage()
    
    print("\n" + "=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)

