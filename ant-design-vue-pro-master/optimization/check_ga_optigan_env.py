#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""兼容入口：转发至 gaoptgan/check_ga_optigan_env.py。"""

import os
import runpy
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_GAOPTGAN = os.path.normpath(os.path.join(_HERE, "..", "..", "gaoptgan"))
_TARGET = os.path.join(_GAOPTGAN, "check_ga_optigan_env.py")

if not os.path.isfile(_TARGET):
    raise SystemExit(f"未找到 gaoptgan 项目: {_TARGET}")

runpy.run_path(_TARGET, run_name="__main__")
