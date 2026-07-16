#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轨迹随钻评估 — 坐标推送测试脚本

支持两种数据来源：
  1. Excel 测斜表（测深 / 井斜角 / 网格方位）+ 井口坐标 → 最小曲率法转 E/N/TVD 后推送
  2. 内置线性漂移模拟（无 Excel 时使用）

示例：
  # 从 Excel 推送（井口坐标单独配置）
  python scripts/while_drilling_push_test.py --session-id xxx --excel survey.xlsx \\
    --wellhead-e 100 --wellhead-n 200 --wellhead-d 0 --interval 2

  # REST / TCP、自动建会话、模拟漂移等见 --help

Excel 列名与系统一致，支持：测深(m)、井斜角(°)、网格方位(°) 及 md/inclination/azimuth 等别名。
依赖：Python 3 标准库（.xlsx 用 zip+xml 解析）；可选 pip install openpyxl 加速读取。
"""

from __future__ import annotations

import argparse
import json
import math
import re
import socket
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

XLSX_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

MD_ALIASES = {"测深(m)", "测深（m）", "测深", "md"}
INC_ALIASES = {"井斜角(°)", "井斜角（°）", "井斜角", "井斜", "inclination"}
AZI_ALIASES = {"网格方位(°)", "网格方位（°）", "网格方位", "方位", "azimuth"}


def normalize_header(value: str) -> str:
    return (
        str(value)
        .lower()
        .replace("（", "(")
        .replace("）", ")")
        .replace(" ", "")
        .strip()
    )


def is_alias(normalized: str, aliases: set[str]) -> bool:
    return normalized in {normalize_header(a) for a in aliases}


def http_post_json(url: str, payload: dict, timeout: float = 10.0) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body) if body else {}


def start_session(api_base: str, site_id: int, pending_well_id: int) -> str:
    url = f"{api_base.rstrip('/')}/whileDrilling/session/start"
    info = http_post_json(url, {"siteId": site_id, "pendingWellId": pending_well_id})
    session_id = info.get("sessionId")
    if not session_id:
        raise RuntimeError(f"创建会话失败，响应: {info}")
    print(f"[OK] 会话已创建 sessionId={session_id}")
    print(f"     TCP 端口: {info.get('tcpPort', 9010)}")
    print(f"     告警阈值: {info.get('alertDistanceM', 30)} m")
    return session_id


def push_rest(api_base: str, session_id: str, x: float, y: float, z: float) -> dict:
    url = f"{api_base.rstrip('/')}/whileDrilling/position"
    return http_post_json(url, {"sessionId": session_id, "x": x, "y": y, "z": z})


def push_tcp(host: str, port: int, session_id: str, x: float, y: float, z: float) -> None:
    line = json.dumps({"sessionId": session_id, "x": x, "y": y, "z": z}, ensure_ascii=False)
    with socket.create_connection((host, port), timeout=5) as sock:
        sock.sendall((line + "\n").encode("utf-8"))


def format_result(result: dict | None) -> str:
    if not result:
        return "（无响应体）"
    parts = [
        f"偏移={result.get('horizontalDistance')}m",
        f"状态={result.get('status')}",
    ]
    if result.get("shouldStopDrilling"):
        parts.append(">>> 建议停止钻进 <<<")
    msg = result.get("message")
    if msg:
        parts.append(str(msg))
    return " | ".join(parts)


def minimum_curvature_to_end(
    survey_rows: list[tuple[float, float, float]],
    wellhead_e: float,
    wellhead_n: float,
    wellhead_d: float,
) -> list[dict]:
    """测斜 MD/Inc/Azi(°) → E/N/TVD，算法与后端 ExcelParser 一致。"""
    if not survey_rows:
        return []

    rows = sorted(survey_rows, key=lambda r: r[0])
    points = [
        {"md": rows[0][0], "inc": rows[0][1], "azi": rows[0][2],
         "e": wellhead_e, "n": wellhead_n, "tvd": wellhead_d}
    ]

    for i in range(1, len(rows)):
        md1, inc1_deg, azi1_deg = rows[i - 1]
        md2, inc2_deg, azi2_deg = rows[i]
        dmd = md2 - md1
        if dmd <= 0:
            continue

        inc1, inc2 = math.radians(inc1_deg), math.radians(inc2_deg)
        az1, az2 = math.radians(azi1_deg), math.radians(azi2_deg)

        cos_dogleg = math.cos(inc1) * math.cos(inc2) + math.sin(inc1) * math.sin(inc2) * math.cos(az2 - az1)
        cos_dogleg = max(-1.0, min(1.0, cos_dogleg))
        dogleg = math.acos(cos_dogleg)
        rf = 1.0 if dogleg < 1e-12 else (2.0 / dogleg) * math.tan(dogleg / 2.0)

        d_n = 0.5 * dmd * (math.sin(inc1) * math.cos(az1) + math.sin(inc2) * math.cos(az2)) * rf
        d_e = 0.5 * dmd * (math.sin(inc1) * math.sin(az1) + math.sin(inc2) * math.sin(az2)) * rf
        d_d = 0.5 * dmd * (math.cos(inc1) + math.cos(inc2)) * rf

        prev = points[-1]
        points.append({
            "md": md2,
            "inc": inc2_deg,
            "azi": azi2_deg,
            "e": prev["e"] + d_e,
            "n": prev["n"] + d_n,
            "tvd": prev["tvd"] + d_d,
        })

    return points


def _read_xlsx_with_openpyxl(path: Path, sheet: str | int) -> list[list]:
    import openpyxl  # type: ignore

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    if isinstance(sheet, int):
        ws = wb.worksheets[sheet]
    else:
        ws = wb[sheet]
    rows = []
    for row in ws.iter_rows(values_only=True):
        rows.append(["" if c is None else c for c in row])
    wb.close()
    return rows


def _cell_col_index(cell_ref: str) -> int:
    col = 0
    for ch in cell_ref:
        if ch.isalpha():
            col = col * 26 + (ord(ch.upper()) - ord("A") + 1)
        else:
            break
    return col - 1


def _cell_row_index(cell_ref: str) -> int:
    m = re.search(r"(\d+)", cell_ref)
    return int(m.group(1)) if m else 0


def _read_xlsx_stdlib(path: Path, sheet_index: int = 0) -> list[list]:
    with zipfile.ZipFile(path) as zf:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in root.findall(f"{XLSX_NS}si"):
                parts = [t.text or "" for t in si.iter(f"{XLSX_NS}t")]
                shared.append("".join(parts))

        sheet_files = sorted(
            n for n in zf.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml$", n)
        )
        if not sheet_files:
            raise ValueError("Excel 中未找到工作表")
        if sheet_index >= len(sheet_files):
            raise ValueError(f"工作表索引 {sheet_index} 超出范围（共 {len(sheet_files)} 个）")

        root = ET.fromstring(zf.read(sheet_files[sheet_index]))
        sparse: dict[int, dict[int, object]] = {}
        max_row = 0
        max_col = 0

        for cell in root.iter(f"{XLSX_NS}c"):
            ref = cell.attrib.get("r")
            if not ref:
                continue
            r_idx = _cell_row_index(ref) - 1
            c_idx = _cell_col_index(ref)
            max_row = max(max_row, r_idx)
            max_col = max(max_col, c_idx)

            val_el = cell.find(f"{XLSX_NS}v")
            if val_el is None or val_el.text is None:
                continue
            raw = val_el.text
            if cell.attrib.get("t") == "s":
                value = shared[int(raw)] if int(raw) < len(shared) else raw
            else:
                try:
                    num = float(raw)
                    value = int(num) if num.is_integer() else num
                except ValueError:
                    value = raw
            sparse.setdefault(r_idx, {})[c_idx] = value

        rows: list[list] = []
        for r in range(max_row + 1):
            row_map = sparse.get(r, {})
            rows.append([row_map.get(c, "") for c in range(max_col + 1)])
        return rows


def read_excel_rows(path: Path, sheet: str | int = 0) -> list[list]:
    suffix = path.suffix.lower()
    if suffix not in (".xlsx", ".xlsm"):
        raise ValueError(f"暂不支持 {suffix}，请使用 .xlsx 测斜表")

    try:
        import openpyxl  # noqa: F401

        return _read_xlsx_with_openpyxl(path, sheet)
    except ImportError:
        if isinstance(sheet, str):
            raise ValueError("按名称指定工作表需安装 openpyxl：pip install openpyxl") from None
        return _read_xlsx_stdlib(path, int(sheet))


def parse_survey_excel(
    path: Path,
    sheet: str | int = 0,
) -> list[tuple[float, float, float]]:
    """解析测深、井斜角、网格方位列，返回 [(md, inc_deg, azi_deg), ...]。"""
    grid = read_excel_rows(path, sheet)
    if not grid:
        raise ValueError("Excel 为空")

    md_col = inc_col = azi_col = -1
    data_start = 0

    for i, row in enumerate(grid[:4]):
        for j, cell in enumerate(row):
            norm = normalize_header(str(cell))
            if is_alias(norm, MD_ALIASES):
                md_col = j
            elif is_alias(norm, INC_ALIASES):
                inc_col = j
            elif is_alias(norm, AZI_ALIASES):
                azi_col = j
        if md_col >= 0 and inc_col >= 0 and azi_col >= 0:
            data_start = i + 1
            break

    if md_col < 0 or inc_col < 0 or azi_col < 0:
        md_col, inc_col, azi_col = 0, 1, 2
        data_start = 0

    surveys: list[tuple[float, float, float]] = []
    for row in grid[data_start:]:
        if max(md_col, inc_col, azi_col) >= len(row):
            continue
        try:
            md = float(row[md_col])
            inc = float(row[inc_col])
            azi = float(row[azi_col])
        except (TypeError, ValueError):
            continue
        surveys.append((md, inc, azi))

    if len(surveys) < 2:
        raise ValueError("有效测斜行不足 2 行，请检查 Excel 格式与列名")
    return surveys


def load_trajectory_from_excel(
    excel_path: Path,
    wellhead_e: float,
    wellhead_n: float,
    wellhead_d: float,
    sheet: str | int = 0,
) -> list[dict]:
    surveys = parse_survey_excel(excel_path, sheet)
    return minimum_curvature_to_end(surveys, wellhead_e, wellhead_n, wellhead_d)


def build_synthetic_trajectory(
    start_e: float,
    start_n: float,
    start_tvd: float,
    step_tvd: float,
    drift_e: float,
    drift_n: float,
    count: int,
):
    e, n, tvd = start_e, start_n, start_tvd
    for i in range(count):
        yield i + 1, e, n, tvd, None, None, None
        e += drift_e
        n += drift_n
        tvd += step_tvd


def iter_excel_points(args: argparse.Namespace) -> list[dict]:
    path = Path(args.excel)
    if not path.is_file():
        raise FileNotFoundError(f"Excel 不存在: {path}")
    sheet: str | int = args.sheet
    if isinstance(sheet, str) and sheet.isdigit():
        sheet = int(sheet)
    trajectory = load_trajectory_from_excel(
        path, args.wellhead_e, args.wellhead_n, args.wellhead_d, sheet
    )
    start = max(0, args.from_index - 1)
    if args.count == 0:
        end = len(trajectory)
    else:
        end = min(len(trajectory), start + args.count)
    if start >= len(trajectory):
        raise ValueError(f"--from-index {args.from_index} 超出轨迹点数 {len(trajectory)}")
    return trajectory[start:end]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="向轨迹随钻评估接口定时推送坐标")
    p.add_argument("--session-id", help="随钻评估会话 ID（前端开始评估后复制）")
    p.add_argument("--site-id", type=int, help="井场 ID（与 --pending-well-id 一起用时自动创建会话）")
    p.add_argument("--pending-well-id", type=int, help="待钻井 ID")
    p.add_argument("--mode", choices=("rest", "tcp"), default="rest", help="推送方式")
    p.add_argument("--api-base", default="http://127.0.0.1:8003", help="后端地址（REST）")
    p.add_argument("--tcp-host", default="127.0.0.1", help="TCP 主机")
    p.add_argument("--tcp-port", type=int, default=9010, help="TCP 端口")
    p.add_argument("--interval", type=float, default=2.0, help="推送间隔（秒）")
    p.add_argument("--count", type=int, default=30, help="推送点数；Excel 模式设 0 表示推完整个表；模拟模式设 0 表示无限循环")

    src = p.add_argument_group("Excel 测斜表（与 --wellhead-* 配合）")
    src.add_argument("--excel", help="测斜 Excel 路径（.xlsx），含测深/井斜角/网格方位")
    src.add_argument("--sheet", default="0", help="工作表序号(0起)或名称，默认 0")
    src.add_argument("--wellhead-e", type=float, help="井口东坐标 E (m)")
    src.add_argument("--wellhead-n", type=float, help="井口北坐标 N (m)")
    src.add_argument("--wellhead-d", type=float, default=0.0, help="井口垂深 D/TVD (m)，默认 0")
    src.add_argument("--from-index", type=int, default=1, help="从第几个轨迹点开始推（1 起，含井口后第一点）")

    sim = p.add_argument_group("模拟漂移（未指定 --excel 时使用）")
    sim.add_argument("--start-e", type=float, default=0.0)
    sim.add_argument("--start-n", type=float, default=0.0)
    sim.add_argument("--start-tvd", type=float, default=500.0)
    sim.add_argument("--step-tvd", type=float, default=10.0)
    sim.add_argument("--drift-e", type=float, default=0.0)
    sim.add_argument("--drift-n", type=float, default=0.5)

    args = p.parse_args()
    if args.excel:
        missing = [n for n, v in [("wellhead-e", args.wellhead_e), ("wellhead-n", args.wellhead_n)] if v is None]
        if missing:
            p.error(f"使用 --excel 时必须指定：{', '.join('--' + m for m in missing)}")
    return args


def main() -> int:
    args = parse_args()

    session_id = args.session_id
    if not session_id:
        if args.site_id is None or args.pending_well_id is None:
            print("错误：请指定 --session-id，或同时指定 --site-id 与 --pending-well-id", file=sys.stderr)
            return 1
        try:
            session_id = start_session(args.api_base, args.site_id, args.pending_well_id)
        except (urllib.error.URLError, RuntimeError) as e:
            print(f"创建会话失败: {e}", file=sys.stderr)
            return 1

    try:
        excel_points = iter_excel_points(args) if args.excel else None
    except (OSError, ValueError, FileNotFoundError) as e:
        print(f"加载轨迹失败: {e}", file=sys.stderr)
        return 1

    if args.excel and not excel_points:
        print("没有可推送的轨迹点", file=sys.stderr)
        return 1

    infinite = not args.excel and args.count == 0
    if args.excel:
        total = str(len(excel_points))
    elif infinite:
        total = "∞"
    else:
        total = str(args.count)

    print("=" * 60)
    print(f"sessionId : {session_id}")
    print(f"模式      : {args.mode.upper()}")
    print(f"间隔      : {args.interval}s")
    print(f"点数      : {total}")
    if args.excel:
        print(f"数据源    : Excel {args.excel}")
        print(f"井口      : E={args.wellhead_e}, N={args.wellhead_n}, D={args.wellhead_d}")
        print(f"起始序号  : {args.from_index}")
    else:
        print(f"数据源    : 模拟漂移")
        print(f"起点      : E={args.start_e}, N={args.start_n}, TVD={args.start_tvd}")
    print("=" * 60)
    print("Ctrl+C 停止。\n")

    sent = 0
    excel_idx = 0
    synthetic_gen = None if args.excel else build_synthetic_trajectory(
        args.start_e, args.start_n, args.start_tvd,
        args.step_tvd, args.drift_e, args.drift_n,
        args.count if not infinite else 10**9,
    )

    try:
        while True:
            if args.excel:
                if excel_idx >= len(excel_points):
                    break
                pt = excel_points[excel_idx]
                excel_idx += 1
            else:
                if not infinite and sent >= args.count:
                    break
                try:
                    _, e, n, tvd, md, inc, azi = next(synthetic_gen)
                except StopIteration:
                    break
                pt = {"e": e, "n": n, "tvd": tvd, "md": md, "inc": inc, "azi": azi}

            e = round(pt["e"], 3)
            n = round(pt["n"], 3)
            tvd = round(pt["tvd"], 3)
            md_info = ""
            if pt.get("md") is not None:
                md_info = f" MD={pt['md']:.2f} Inc={pt['inc']:.2f}° Azi={pt['azi']:.2f}° |"

            try:
                if args.mode == "rest":
                    result = push_rest(args.api_base, session_id, e, n, tvd)
                    print(f"[{sent + 1}]{md_info} REST -> E={e}, N={n}, TVD={tvd}")
                    print(f"      {format_result(result)}")
                else:
                    push_tcp(args.tcp_host, args.tcp_port, session_id, e, n, tvd)
                    print(f"[{sent + 1}]{md_info} TCP  -> E={e}, N={n}, TVD={tvd}")
            except (urllib.error.URLError, OSError, TimeoutError) as err:
                print(f"[{sent + 1}] 推送失败: {err}", file=sys.stderr)

            sent += 1
            if sent > 0 and (not infinite and not args.excel and sent >= args.count):
                break
            if args.excel and excel_idx >= len(excel_points):
                break
            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\n已停止推送。")

    print(f"\n共推送 {sent} 个点。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
