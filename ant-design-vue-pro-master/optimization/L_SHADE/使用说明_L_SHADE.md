# L-SHADE井轨迹优化器使用说明

## 功能
使用L-SHADE（Success-History based Adaptive Differential Evolution with Linear population size reduction）算法寻找最优的井轨迹参数。L-SHADE是差分进化算法的改进版本，通过历史记忆自适应调整参数和线性减少种群大小来增强搜索能力。

## 核心文件
- `l_shade_well_trajectory.py`: 核心算法实现
- `l_shade_core.py`: L-SHADE核心算法
- `minimal_l_shade.py`: 简化接口
- `test_l_shade.py`: 测试脚本
- `使用说明_L_SHADE.md`: 本说明文档

## 使用方法

### 方法1：基础优化（推荐）

```python
from minimal_l_shade import optimize_well_trajectory

# 基础优化（使用默认参数）
result = optimize_well_trajectory(
    target_e=100.64,        # 目标东坐标
    target_n=2200.71,       # 目标北坐标
    target_d=2936.06,       # 目标深度
    wellhead_position=(214, 2030, 0),  # 井口坐标
    excel_files=["米41-37YH3-simple.xlsx"],  # Excel文件
    wellhead_positions=[(208, 2015, 0.0)],    # 障碍物井口位置
    max_iterations=1000,    # 最大迭代次数
    random_seed=42          # 随机种子
)

print(f"最佳适应度: {result['best_fitness']:.6f}")
print(f"最佳参数: {result['best_solution']}")
```

### 方法2：高级优化（自定义参数）

```python
from minimal_l_shade import optimize_well_trajectory

# 高级优化（自定义所有参数）
result = optimize_well_trajectory(
    target_e=100.64, target_n=2200.71, target_d=2936.06,
    wellhead_position=(214, 2030, 0),
    excel_files=["米41-37YH3-simple.xlsx", "米41-37YH5-simple.xlsx"],
    wellhead_positions=[(208, 2015, 0.0), (210, 2007, 0.0)],
    
    # L-SHADE 核心参数
    initial_population_size=100,    # 初始种群大小
    min_population_size=4,          # 最小种群大小
    max_iterations=2000,            # 最大迭代次数
    memory_size=5,                  # 历史记忆大小
    random_seed=42                   # 随机种子
)

print(f"最佳适应度: {result['best_fitness']:.6f}")
print(f"最佳参数: {result['best_solution']}")
```

### 方法3：快速测试

```python
# 快速测试（小参数，快速收敛）
result = optimize_well_trajectory(
    target_e=100.64, target_n=2200.71, target_d=2936.06,
    wellhead_position=(214, 2030, 0),
    initial_population_size=30,     # 小初始种群
    min_population_size=4,           # 最小种群
    max_iterations=200,              # 少迭代次数
    memory_size=3                    # 小历史记忆
)
```

### 方法4：直接使用核心模块

```python
from l_shade_well_trajectory import LSHADEWellTrajectoryOptimizer

# 创建优化器
optimizer = LSHADEWellTrajectoryOptimizer(
    target_e=100.64,
    target_n=2200.71,
    target_d=2936.06,
    wellhead_position=(214, 2030, 0),
    excel_files=["米41-37YH3-simple.xlsx"],
    wellhead_positions=[(208, 2015, 0.0)],
    initial_population_size=100,
    min_population_size=4,
    max_iterations=1000,
    memory_size=5,
    random_seed=42
)

# 执行优化
result = optimizer.optimize()

print(f"最佳适应度: {result['best_fitness']:.6f}")
print(f"最佳参数: {result['best_solution']}")
```

## 参数说明

### 基础参数
- `target_e, target_n, target_d`: 目标点坐标 (m)
- `wellhead_position`: 井口坐标 (E, N, D) (m)
- `excel_files`: Excel文件列表
- `wellhead_positions`: 井轨迹障碍物井口位置列表

### L-SHADE 核心参数
- `initial_population_size`: 初始种群大小 (默认100，建议50-200)
- `min_population_size`: 最小种群大小 (默认4，建议4-10)
- `max_iterations`: 最大迭代次数 (默认1000，建议500-5000)
- `memory_size`: 历史记忆大小 (默认5，建议3-10)
- `random_seed`: 随机种子 (默认42)

### 参数调优说明
- `initial_population_size` (初始种群大小): 较大的初始种群可以增强全局搜索，但增加计算时间
- `min_population_size` (最小种群大小): 控制种群大小的下限，通常设置为4
- `max_iterations` (最大迭代次数): 控制搜索深度，更多迭代通常得到更好的解
- `memory_size` (历史记忆大小): 存储成功参数的历史，用于自适应调整F和CR

### 输出参数
优化器优化以下8个井轨迹参数：
1. `D_kop`: 造斜点深度 (m)
2. `alpha1`: 第一造斜角 (度)
3. `alpha2`: 第二造斜角 (度)
4. `phi1`: 第一方位角 (度)
5. `phi2`: 第二方位角 (度)
6. `R1`: 第一曲率半径 (m)
7. `R2`: 第二曲率半径 (m)
8. `D_turn_kop`: 转向点深度 (m)

## 运行示例

```bash
python minimal_l_shade.py
```

## 参数调优建议

### 快速测试配置
```python
# 适合快速验证和测试
initial_population_size=30, min_population_size=4, max_iterations=200, memory_size=3
```

### 标准配置
```python
# 适合一般优化任务
initial_population_size=100, min_population_size=4, max_iterations=1000, memory_size=5
```

### 高精度配置
```python
# 适合需要高精度结果的任务
initial_population_size=200, min_population_size=4, max_iterations=2000, memory_size=10
```

### 参数调优策略

1. **初始种群大小**: 较大种群增强全局搜索，但增加计算时间
2. **最小种群大小**: 通常保持为4，确保算法后期仍有足够多样性
3. **历史记忆大小**: 5是常用值，可以根据问题复杂度调整
4. **迭代次数**: 更多迭代通常得到更好的解，但增加计算时间

## 算法特点

### L-SHADE优势
1. **参数自适应**: 通过历史记忆自动调整F和CR参数
2. **线性种群缩减**: 随着迭代逐步减少种群大小，提高收敛速度
3. **外部存档机制**: 存储历史解，增强搜索多样性
4. **全局搜索能力强**: 基于差分进化的强大全局搜索能力
5. **鲁棒性强**: 对参数设置不敏感
6. **适合连续优化**: 特别适合连续优化问题

### 与其他算法的差异
| 特性 | L-SHADE | PSO | IPOP-CMA-ES | 差分进化 |
|------|---------|-----|-------------|----------|
| 搜索策略 | 差分进化 | 群体搜索 | 自适应分布 | 差分进化 |
| 评估次数 | 可变 | 固定 | 可变 | 固定 |
| 参数数量 | 少 | 少 | 中等 | 少 |
| 收敛速度 | 快 | 快 | 快 | 中等 |
| 内存使用 | 中等 | 中等 | 中等 | 中等 |
| 实现复杂度 | 中等 | 简单 | 中等 | 简单 |
| 参数自适应 | 强 | 弱 | 强 | 弱 |
| 种群缩减 | 线性 | 无 | 无 | 无 |
| 外部存档 | 有 | 无 | 无 | 无 |

## 输出结果

### 优化结果字典
```python
{
    'best_solution': List[float],      # 最佳解参数
    'best_fitness': float,             # 最佳适应度
    'total_iterations': int,           # 总迭代次数
    'total_evaluations': int,          # 总评估次数
    'optimization_time': float,        # 优化时间 (秒)
    'iteration_data': List[Dict],      # 迭代数据
    'population_history': List[List],   # 种群历史
    'population_size_history': List[int], # 种群大小历史
    'diversity_analysis': Dict,        # 多样性分析
    'config': object,                  # 配置对象
    'trajectory_info': Dict           # 轨迹信息（可选）
}
```

### 轨迹信息字典
```python
{
    'success': bool,                  # 是否成功
    'total_length': float,            # 总长度 (m)
    'target_deviation': float,        # 目标偏差 (m)
    'sphere_collision': bool,         # 球体碰撞
    'well_collision': bool           # 井轨迹碰撞
}
```

## 可视化输出

优化完成后会自动生成以下文件：
- `l_shade_optimization_data.csv`: 优化过程数据
- `l_shade_convergence_plot.png`: 收敛图（包含适应度、多样性、种群大小变化、分布）
- `l_shade_diversity_analysis.png`: 多样性分析图（如果可用）
- `l_shade_diversity_summary.png`: 多样性统计摘要图（如果可用）
- `l_shade_diversity_analysis_export.xlsx`: 多样性分析Excel文件（如果可用）

## 算法原理

### L-SHADE流程
1. **初始化**: 随机生成初始种群，初始化历史记忆
2. **变异**: 使用current-to-pbest/1策略进行变异
3. **交叉**: 使用二项交叉生成试验个体
4. **选择**: 贪婪选择保留更好的个体
5. **更新历史记忆**: 根据成功的F和CR值更新历史记忆
6. **更新外部存档**: 将失败的个体存入外部存档
7. **线性减少种群大小**: 根据迭代次数线性减少种群大小
8. **迭代**: 重复步骤2-7直到满足终止条件

### L-SHADE核心机制
1. **历史记忆自适应**: 使用成功历史的加权均值更新F和CR参数
2. **线性种群缩减**: 种群大小从初始值线性减少到最小值
3. **外部存档**: 存储失败的个体，用于增强搜索多样性
4. **current-to-pbest/1变异**: 使用当前个体到pbest个体的差分进行变异

### 参数自适应机制
- F（变异因子）从历史记忆M_F中随机选择，使用正态分布
- CR（交叉概率）从历史记忆M_CR中随机选择，使用正态分布
- 成功的F和CR值被记录，用于更新历史记忆
- 使用加权Lehmer均值更新F，使用加权算术均值更新CR

## 注意事项

1. 确保 `well_trajectory_objective` 模块在父目录中
2. Excel文件路径要正确
3. 参数边界由 `well_trajectory_objective` 模块统一管理
4. 算法直接调用 `well_trajectory_objective` 的目标函数，无重复实现
5. L-SHADE通过线性减少种群大小提高收敛速度，但需要合理设置初始和最小种群大小
6. 历史记忆大小影响参数自适应的效果，通常设置为5
7. 建议先用小参数测试，确认无误后再使用大参数进行正式优化
8. L-SHADE是自适应算法，参数会自动调整，但仍需要合理设置初始值
9. **重要**: 算法会运行完整的迭代次数，不会提前停止，确保充分搜索
10. 不同参数组合适用于不同问题，建议根据问题特点选择合适的参数
11. L-SHADE具有强大的全局搜索能力和参数自适应能力，特别适合复杂优化问题
12. 线性种群缩减是L-SHADE的核心特性，可以有效平衡探索和开发

