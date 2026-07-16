# gaoptgan

独立 GA-optiGAN 井轨迹优化项目，包含：

- `GA-optiGAN/` — 核心算法（GAN + GA + 约束支配 + 探索 warm-up）
- `well_trajectory_objective/` — 七段式目标函数、防碰检测、邻井 Excel 读取
- `optimize_well_trajectory_ga_optigan.py` — Python 优化器封装
- `run_ga_optigan_design_cli.py` — Java 后端 CLI 入口
- `test_ga_optigan_local.py` — 本地冒烟测试
- `check_ga_optigan_env.py` — 环境检查

## 安装

```bash
cd gaoptgan
pip install -r requirements.txt
python check_ga_optigan_env.py
```

## 本地试跑

```bash
python test_ga_optigan_local.py              # 快速
python test_ga_optigan_local.py --full       # 较大预算
```

## Java 后端配置

`api/src/main/resources/application.yml`：

```yaml
trajectory:
  optimization:
    python-executable: python
    script-dir: ../gaoptgan
```

CLI 命令：`python run_ga_optigan_design_cli.py --input in.json --output out.json --progress prog.json`

## Python 调用

```python
from optimize_well_trajectory_ga_optigan import optimize_well_trajectory_ga_optigan

result = optimize_well_trajectory_ga_optigan(
    target_e=1500.64, target_n=1200.71, target_d=2936.06,
    wellhead_position=(0, 0, 0),
    max_evaluations=30000,
)
print(result["best_solution_dict"])
```

## 目录结构

```
gaoptgan/
├── GA-optiGAN/              # 算法核心
├── well_trajectory_objective/
├── optimize_well_trajectory_ga_optigan.py
├── run_ga_optigan_design_cli.py
├── test_ga_optigan_local.py
├── check_ga_optigan_env.py
└── requirements.txt
```
