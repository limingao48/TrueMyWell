#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地 GA-optiGAN 环境自检 + 冒烟运行。

用法（在 optimization 目录下）:
  python test_ga_optigan_local.py              # 检查依赖 + 快速试跑（约几分钟）
  python test_ga_optigan_local.py --check-only # 只检查依赖，不跑优化
  python test_ga_optigan_local.py --full       # 较大预算试跑（更慢，更接近正式任务）

通过后再把本解释器路径写入 api/application.yml:
  trajectory.optimization.python-executable: <上面打印的 Python 路径>
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import traceback

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

# 与 minimal.py 示例一致的默认场景（无邻井，便于先验证算法本身）
DEFAULT_TARGET = (502.64, 2790.71, 2636.06)
DEFAULT_WELLHEAD = (222.0, 2030.0, 0.0)


def check_environment() -> bool:
    """检查依赖与目录，返回是否通过。"""
    print("=" * 60)
    print("1) 环境检查")
    print("=" * 60)
    print("Python:", sys.executable)
    print("Version:", sys.version.replace("\n", " "))

    ok = True
    for name in ("numpy", "pandas", "torch", "openpyxl", "scipy"):
        try:
            mod = __import__(name)
            print(f"  [OK] {name:10s} {getattr(mod, '__version__', '?')}")
        except ImportError as e:
            print(f"  [FAIL] {name:10s} {e}")
            ok = False

    cli = os.path.join(_SCRIPT_DIR, "run_ga_optigan_design_cli.py")
    optigan = os.path.join(_SCRIPT_DIR, "GA-optiGAN")
    print(f"  [{'OK' if os.path.isfile(cli) else 'FAIL'}] CLI 脚本存在")
    print(f"  [{'OK' if os.path.isdir(optigan) else 'FAIL'}] GA-optiGAN 目录存在")

    if not ok:
        print("\n请先安装依赖:")
        print("  pip install -r requirements-ga-optigan.txt")
        return False

    print("\n环境检查通过。\n")
    return True


def run_smoke_test(*, full: bool = False) -> int:
    """运行一次 GA-optiGAN 优化，验证能否算通。"""
    print("=" * 60)
    print("2) GA-optiGAN 冒烟运行" + ("（完整预算）" if full else "（快速预算）"))
    print("=" * 60)

    if full:
        kwargs = dict(
            max_evaluations=8000,
            population_size=50,
            opt_size=200,
            pretrain=1,
            epochs=80,
            random_seed=42,
        )
    else:
        # 快速：少评估、少预训练轮数，仅验证能跑通
        kwargs = dict(
            max_evaluations=600,
            population_size=15,
            opt_size=80,
            pretrain=0,
            epochs=20,
            random_seed=42,
        )

    target_e, target_n, target_d = DEFAULT_TARGET
    wellhead = DEFAULT_WELLHEAD
    print(f"靶点 E,N,D = {target_e}, {target_n}, {target_d}")
    print(f"井口 E,N,D = {wellhead}")
    print("邻井: 无（先不测 Excel 防碰）")
    print("参数:", kwargs)
    print()

    try:
        from optimize_well_trajectory_ga_optigan import optimize_well_trajectory_ga_optigan
    except Exception:
        print("无法导入 optimize_well_trajectory_ga_optigan:")
        traceback.print_exc()
        return 1

    t0 = time.time()
    try:
        result = optimize_well_trajectory_ga_optigan(
            target_e=target_e,
            target_n=target_n,
            target_d=target_d,
            wellhead_position=wellhead,
            excel_files=None,
            wellhead_positions=None,
            safety_radius=10.0,
            hit_threshold=30.0,
            **kwargs,
        )
    except Exception:
        print("\n优化过程异常:")
        traceback.print_exc()
        return 1

    elapsed = time.time() - t0
    print("\n" + "-" * 60)
    print("运行结束，耗时 {:.1f} 秒".format(elapsed))

    best_dict = result.get("best_solution_dict")
    best_fitness = result.get("best_fitness")
    final_dev = result.get("final_deviation")
    total_eval = result.get("total_evaluations")

    if best_dict is None:
        print("[FAIL] 未得到 best_solution_dict，本地环境或算法未正常结束。")
        return 1

    print("[OK] best_fitness =", best_fitness)
    print("[OK] final_deviation (m) =", final_dev)
    print("[OK] total_evaluations =", total_eval)
    print("[OK] 七段式最优参数:")
    for k, v in best_dict.items():
        print(f"      {k:12s} = {v}")

    print("\n" + "=" * 60)
    print("结论: 本地 GA-optiGAN 可以运行。")
    print("请将下列路径写入 application.yml 的 python-executable:")
    print(" ", sys.executable)
    print("=" * 60)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="本地 GA-optiGAN 环境测试")
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="只检查依赖，不执行优化",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="使用较大评估预算（更慢，更接近正式设计）",
    )
    args = parser.parse_args()

    if not check_environment():
        return 1
    if args.check_only:
        return 0
    return run_smoke_test(full=args.full)


if __name__ == "__main__":
    sys.exit(main())
