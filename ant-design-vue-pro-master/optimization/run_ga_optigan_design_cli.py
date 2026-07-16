#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""兼容入口：转发至仓库根目录独立项目 gaoptgan。"""

import os
import runpy
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_GAOPTGAN = os.path.normpath(os.path.join(_HERE, "..", "..", "gaoptgan"))
_TARGET = os.path.join(_GAOPTGAN, "run_ga_optigan_design_cli.py")

if not os.path.isfile(_TARGET):
    raise SystemExit(f"未找到 gaoptgan 项目: {_TARGET}")

if _GAOPTGAN not in sys.path:
    sys.path.insert(0, _GAOPTGAN)

runpy.run_path(_TARGET, run_name="__main__")
