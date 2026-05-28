#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查当前 Python 是否满足 GA-optiGAN 运行条件。"""

import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)


def main() -> int:
    print("Python:", sys.executable)
    print("Version:", sys.version.replace("\n", " "))
    missing = []
    for name in ("numpy", "pandas", "torch", "openpyxl"):
        try:
            mod = __import__(name)
            ver = getattr(mod, "__version__", "?")
            print(f"  OK  {name} {ver}")
        except ImportError:
            print(f"  MISSING  {name}")
            missing.append(name)

    cli = os.path.join(_SCRIPT_DIR, "run_ga_optigan_design_cli.py")
    optigan = os.path.join(_SCRIPT_DIR, "GA-optiGAN")
    print("CLI:", cli, "exists=" + str(os.path.isfile(cli)))
    print("GA-optiGAN dir:", optigan, "exists=" + str(os.path.isdir(optigan)))

    if missing:
        print("\n请安装依赖:")
        print("  pip install -r requirements-ga-optigan.txt")
        print("然后在 api/application.yml 配置 trajectory.optimization.python-executable 为本解释器路径。")
        return 1
    print("\n环境检查通过，可用于 GA-optiGAN。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
