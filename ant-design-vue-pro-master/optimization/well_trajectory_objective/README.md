# 井轨迹目标函数计算库
## Well Trajectory Objective Function Library

一个专门用于井眼轨迹优化目标函数计算的独立库，支持CPU和GPU加速计算。

## 🎯 功能特性

- **井轨迹计算**: 支持5段式井眼轨迹计算（垂直段、造斜段、切线段、转向段）
- **障碍物检测**: 支持球形障碍物和井轨迹障碍物检测
- **GPU加速**: 提供GPU加速版本，大幅提升计算性能
- **灵活配置**: 支持自定义目标点、障碍物参数等
- **易于集成**: 简洁的API设计，易于集成到优化算法中

## 📦 安装

```bash
# 克隆项目
git clone <repository-url>
cd well_trajectory_objective

# 安装依赖
pip install numpy pandas matplotlib scipy openpyxl

# 如需GPU支持，安装PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## 🚀 快速开始

### 基本使用

```python
from well_trajectory_objective import WellTrajectoryConfig, WellTrajectoryObjective

# 创建配置
config = WellTrajectoryConfig(
    E_target=1500.64,
    N_target=1200.71,
    D_target=2936.06
)

# 创建目标函数
objective = WellTrajectoryObjective(config)

# 计算目标函数值
position = [1200, 45, 87, 90, 180, 800, 900, 2000]  # [D_kop, alpha1, alpha2, phi1, phi2, R1, R2, D_turn_kop]
fitness = objective.calculate_objective(position)
print(f"目标函数值: {fitness}")
```

### GPU加速版本

```python
from well_trajectory_objective import WellTrajectoryConfig, WellTrajectoryObjectiveGPU

# 创建配置
config = WellTrajectoryConfig(
    E_target=1500.64,
    N_target=1200.71,
    D_target=2936.06
)

# 创建GPU目标函数
objective = WellTrajectoryObjectiveGPU(config)

# 计算目标函数值
position = [1200, 45, 87, 90, 180, 800, 900, 2000]
fitness = objective.calculate_objective(position)
print(f"GPU目标函数值: {fitness}")
```

### 带井轨迹障碍物

```python
from well_trajectory_objective import (
    WellTrajectoryConfig, 
    WellTrajectoryObjective,
    create_well_obstacle_from_excel
)

# 创建配置
config = WellTrajectoryConfig(
    E_target=1500.64,
    N_target=1200.71,
    D_target=2936.06
)

# 从Excel文件创建井轨迹障碍物
well_obstacle = create_well_obstacle_from_excel(
    "米41-37YH3井斜数据表.xls",
    safety_radius=15.0
)

# 创建带井轨迹障碍物的目标函数
objective = WellTrajectoryObjective(config, well_obstacle)

# 计算目标函数值
position = [1200, 45, 87, 90, 180, 800, 900, 2000]
fitness = objective.calculate_objective(position)
print(f"带井轨迹障碍物的目标函数值: {fitness}")
```

## 📊 参数说明

### 位置参数 (position_tuple)
- `D_kop`: 造斜点深度 (m)
- `alpha1`: 第一造斜角 (度)
- `alpha2`: 第二造斜角 (度)
- `phi1`: 第一方位角 (度)
- `phi2`: 第二方位角 (度)
- `R1`: 第一造斜半径 (m)
- `R2`: 第二造斜半径 (m)
- `D_turn_kop`: 转向点深度 (m)

### 配置参数
- `E_target`, `N_target`, `D_target`: 目标点坐标 (m)
- `obstacle_count`: 球形障碍物数量
- `safety_radius`: 井轨迹安全半径 (m)
- `target_deviation_threshold`: 目标偏差阈值 (m)

## 🔧 API 参考

### WellTrajectoryConfig
井轨迹配置类，用于设置计算参数和约束条件。

### WellTrajectoryObjective
CPU版本的目标函数计算器。

### WellTrajectoryObjectiveGPU
GPU版本的目标函数计算器。

### ObstacleDetector
球形障碍物检测器。

### WellObstacleDetector
井轨迹障碍物检测器。

### WellDataReader
井斜数据读取器，支持从Excel文件读取井轨迹数据。

## 📈 性能对比

| 版本 | 计算时间 | 内存使用 | 适用场景 |
|------|----------|----------|----------|
| CPU | 基准 | 低 | 小规模计算 |
| GPU | 2-4x加速 | 高 | 大规模计算 |

## 🎨 可视化

```python
# 获取轨迹详细信息
info = objective.get_trajectory_info(position)
if info['success']:
    x, y, z = info['trajectory']
    print(f"轨迹长度: {info['total_length']:.2f}m")
    print(f"目标偏差: {info['target_deviation']:.2f}m")
    print(f"是否碰撞: {info['sphere_collision'] or info['well_collision']}")
```

## 🛠️ 自定义扩展

### 自定义障碍物
```python
from well_trajectory_objective import ObstacleDetector

# 创建自定义障碍物
obstacles = [
    {"center": (100, 100, 1000), "radius": 50},
    {"center": (200, 200, 1500), "radius": 30}
]

detector = ObstacleDetector(config)
detector.obstacles = obstacles
```

### 自定义配置
```python
config = WellTrajectoryConfig(
    E_target=2000.0,
    N_target=1500.0,
    D_target=3000.0,
    obstacle_count=50,
    safety_radius=20.0,
    target_deviation_threshold=50.0
)
```

## 📝 注意事项

1. **参数范围**: 确保输入参数在有效范围内
2. **GPU内存**: GPU版本需要足够的显存
3. **数据格式**: Excel文件需要包含正确的列名
4. **精度设置**: 可根据需要调整计算容差

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个库。

## 📄 许可证

MIT License

## 📞 联系方式

如有问题，请通过Issue联系我们。
