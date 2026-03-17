# L-SHADE 井轨迹优化器

## 简介

L-SHADE (Success-History based Adaptive Differential Evolution with Linear population size reduction) 是一种改进的差分进化算法，通过历史记忆自适应调整参数和线性减少种群大小来增强搜索能力。

## 文件结构

```
L_SHADE/
├── l_shade_core.py                    # L-SHADE核心算法实现
├── l_shade_well_trajectory.py         # L-SHADE主优化器
├── minimal_l_shade.py                 # 简化接口
├── test_l_shade.py                    # 测试脚本
├── 使用说明_L_SHADE.md                # 详细使用说明
└── README.md                           # 本文件
```

## 快速开始

### 1. 基础使用

```python
from minimal_l_shade import optimize_well_trajectory

result = optimize_well_trajectory(
    target_e=100.64,
    target_n=2200.71,
    target_d=2936.06,
    wellhead_position=(214, 2030, 0),
    excel_files=["米41-37YH3-simple.xlsx"],
    wellhead_positions=[(208, 2015, 0.0)],
    max_iterations=1000,
    random_seed=42
)

print(f"最佳适应度: {result['best_fitness']:.6f}")
```

### 2. 运行测试

```bash
cd L_SHADE
python test_l_shade.py
```

### 3. 运行示例

```bash
cd L_SHADE
python minimal_l_shade.py
```

## 核心特性

1. **参数自适应**: 通过历史记忆自动调整F和CR参数
2. **线性种群缩减**: 随着迭代逐步减少种群大小，提高收敛速度
3. **外部存档机制**: 存储历史解，增强搜索多样性
4. **多样性分析**: 提供完整的多样性分析功能（复用IPOP_CMA_ES的工具）
5. **可视化输出**: 自动生成收敛图和多样性分析图

## 主要参数

- `initial_population_size`: 初始种群大小（默认100）
- `min_population_size`: 最小种群大小（默认4）
- `max_iterations`: 最大迭代次数（默认1000）
- `memory_size`: 历史记忆大小（默认5）

## 详细文档

请参阅 [使用说明_L_SHADE.md](使用说明_L_SHADE.md) 获取完整的使用说明和参数调优建议。

## 依赖

- numpy
- pandas
- matplotlib
- well_trajectory_objective (父目录中的模块)
- IPOP_CMA_ES/diversity_utils (用于多样性分析)

## 与PSO和IPOP-CMA-ES的对比

L-SHADE作为基线算法，与其他算法相比：

- **搜索策略**: 差分进化 vs 群体搜索/自适应分布
- **参数自适应**: 强（历史记忆）vs 弱/强
- **种群缩减**: 线性缩减 vs 无/递增
- **外部存档**: 有 vs 无
- **全局搜索能力**: 强
- **实现复杂度**: 中等

## 算法特点

L-SHADE的主要创新点：
1. **历史记忆自适应**: 使用成功历史的加权均值更新F和CR参数
2. **线性种群缩减**: 种群大小从初始值线性减少到最小值
3. **外部存档**: 存储失败的个体，用于增强搜索多样性
4. **current-to-pbest/1变异**: 使用当前个体到pbest个体的差分进行变异

## 许可证

与主项目保持一致。

