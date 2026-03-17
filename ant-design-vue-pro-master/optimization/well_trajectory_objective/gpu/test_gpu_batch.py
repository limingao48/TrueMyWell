"""
简单的GPU批量计算测试脚本
"""

import torch
import numpy as np
from ..config import WellTrajectoryConfig
from .objective_function_gpu import create_gpu_objective_function

def main():
    """主测试函数"""
    
    print("=" * 60)
    print("GPU批量计算井眼轨迹目标函数测试")
    print("=" * 60)
    
    # 检查GPU
    if torch.cuda.is_available():
        print(f"\n✅ GPU可用: {torch.cuda.get_device_name(0)}")
    else:
        print("\n⚠️  GPU不可用，将使用CPU")
    
    # 创建配置
    config = WellTrajectoryConfig(
        E_target=1500.64,
        N_target=1200.71,
        D_target=2936.06,
        E_wellhead=30.0,
        N_wellhead=15.0
    )
    
    # 创建GPU目标函数
    print("\n创建GPU目标函数...")
    gpu_objective = create_gpu_objective_function(config, n_points=50)
    
    # 生成测试参数
    batch_size = 100
    print(f"\n生成 {batch_size} 个测试参数...")
    
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
    
    # 转换为张量
    params_tensor = torch.tensor(params_list, device=gpu_objective.device, dtype=torch.float32)
    
    # 批量计算
    print("开始批量计算...")
    import time
    start_time = time.time()
    fitness = gpu_objective.calculate_objective_batch(params_tensor)
    elapsed_time = time.time() - start_time
    
    print(f"\n✅ 计算完成！")
    print(f"   计算时间: {elapsed_time:.4f} 秒")
    print(f"   平均每个: {elapsed_time/batch_size*1000:.4f} 毫秒")
    
    # 显示结果
    fitness_np = fitness.detach().cpu().numpy()
    valid_mask = fitness_np < 1e19
    valid_count = np.sum(valid_mask)
    
    print(f"\n结果统计:")
    print(f"   总数量: {batch_size}")
    print(f"   有效解: {valid_count}")
    print(f"   无效解: {batch_size - valid_count}")
    
    if valid_count > 0:
        valid_fitness = fitness_np[valid_mask]
        print(f"\n有效解统计:")
        print(f"   最小值: {np.min(valid_fitness):.2f}")
        print(f"   最大值: {np.max(valid_fitness):.2f}")
        print(f"   平均值: {np.mean(valid_fitness):.2f}")
        
        # 显示前5个结果
        print(f"\n前5个结果:")
        for i in range(min(5, batch_size)):
            print(f"   轨迹 {i+1}: {fitness_np[i]:.2f}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()

