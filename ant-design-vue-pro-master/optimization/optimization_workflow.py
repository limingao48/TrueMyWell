#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
算法无关的工作流 / 可视化 / 后处理工具
"""

import os
from typing import Callable, Dict, Any, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import ScalarFormatter

from well_trajectory_objective import create_multiple_well_obstacles, WellTrajectoryConfig
from well_trajectory_objective.well_calculator import WellPathCalculator
from well_trajectory_objective.objective_function import SEVEN_SEG_PARAM_NAMES

# 8 参数（旧模型）
PARAM_NAMES = ["D_kop", "alpha1", "alpha2", "phi1", "phi2", "R1", "R2", "D_turn_kop"]


def run_optimization_workflow(target_e,
                              target_n,
                              target_d,
                              wellhead_position=(0, 0, 0),
                              excel_files=None,
                              wellhead_positions=None,
                              optimizer_fn: Optional[Callable[..., Dict[str, Any]]] = None,
                              optimizer_kwargs: Optional[Dict[str, Any]] = None,
                              auto_plot=True,
                              plot_save_path="ga_population_boxplot_from_csv.png"):
    """通用工作流：执行优化并可选做后处理绘图。"""
    if optimizer_fn is None:
        raise ValueError("optimizer_fn 不能为空，请传入具体优化算法函数")
    if optimizer_kwargs is None:
        optimizer_kwargs = {}

    result = optimizer_fn(
        target_e=target_e,
        target_n=target_n,
        target_d=target_d,
        wellhead_position=wellhead_position,
        excel_files=excel_files,
        wellhead_positions=wellhead_positions,
        **optimizer_kwargs,
    )

    if auto_plot:
        population_csv_path = optimizer_kwargs.get("population_csv_path")
        if population_csv_path:
            try:
                plot_population_boxplot_from_csv(csv_path=population_csv_path, save_path=plot_save_path)
            except Exception as e:
                print(f"Auto plot (boxplot) failed: {e}")

    return result


def plot_population_boxplot_from_csv(csv_path="ga_population_all_individuals.csv",
                                     save_path="ga_population_boxplot_from_csv.png",
                                     param_names: Optional[list] = None):
    """从 CSV 绘制参数箱线图。不传 param_names 时自动检测：12 列为七段式，8 列为旧模型。"""
    if not os.path.exists(csv_path):
        print(f"CSV not found: {csv_path}")
        return
    df = pd.read_csv(csv_path)
    names = param_names
    if names is None:
        if set(SEVEN_SEG_PARAM_NAMES).issubset(df.columns):
            names = SEVEN_SEG_PARAM_NAMES
        elif set(PARAM_NAMES).issubset(df.columns):
            names = PARAM_NAMES
        else:
            print("Parameter columns missing in CSV (need 12 seven-segment or 8 legacy), cannot plot boxplots")
            return
    if not set(names).issubset(df.columns):
        print("Parameter columns missing in CSV, cannot plot boxplots")
        return

    n = len(names)
    ncols = 4
    nrows = (n + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(4 * ncols, 4 * nrows))
    axes = np.atleast_2d(axes)
    axes_flat = axes.flatten()
    for idx, name in enumerate(names):
        ax = axes_flat[idx]
        df[[name]].boxplot(
            ax=ax,
            grid=True,
            showfliers=False,
            patch_artist=True,
            boxprops={"facecolor": "#4C78A8", "edgecolor": "#4C78A8", "linewidth": 1.0},
        )
        ax.set_title(name)
        ax.set_ylabel('Value')
        ax.ticklabel_format(style='plain', axis='y')
        yfmt = ScalarFormatter(useOffset=False)
        yfmt.set_scientific(False)
        ax.yaxis.set_major_formatter(yfmt)
    for j in range(len(names), len(axes_flat)):
        axes_flat[j].set_visible(False)

    plt.suptitle('GA population parameters (box-only)', y=0.98)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Saved box-only figure: {save_path}")
    plt.close()


def calculate_vector_angle(v1, v2):
    """
    计算两个三维向量的夹角（度）
    参数：
        v1 (np.ndarray): 第一个向量 [ΔN1, ΔE1, ΔV1]
        v2 (np.ndarray): 第二个向量 [ΔN2, ΔE2, ΔV2]
    返回：
        angle_deg (float): 向量夹角（度，0~180°）
        angle_rad (float): 向量夹角（弧度）
    """
    # 计算向量点积
    dot_product = np.dot(v1, v2)
    # 计算向量的模（避免除以0）
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)

    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0, 0.0  # 向量为零，夹角为0

    # 计算余弦值（限制在[-1,1]，避免浮点误差导致nan）
    cos_theta = np.clip(dot_product / (norm_v1 * norm_v2), -1.0, 1.0)
    # 计算弧度，再转换为度
    angle_rad = np.arccos(cos_theta)
    angle_deg = np.degrees(angle_rad)

    return angle_deg, angle_rad


def calculate_vector_angle(v1, v2):
    """计算两个三维向量的夹角（度），带调试信息"""
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)

    debug_info = {
        "v1": np.round(v1, 4),
        "v2": np.round(v2, 4),
        "dot_product": round(dot_product, 4),
        "norm_v1": round(norm_v1, 4),
        "norm_v2": round(norm_v2, 4),
        "cos_theta": 0.0,
        "error": None
    }

    if norm_v1 == 0 or norm_v2 == 0:
        debug_info["error"] = "存在零向量（模为0）"
        return 0.0, 0.0, debug_info

    cos_theta = dot_product / (norm_v1 * norm_v2)
    cos_theta_clipped = np.clip(cos_theta, -1.0, 1.0)
    debug_info["cos_theta"] = round(cos_theta_clipped, 4)

    angle_rad = np.arccos(cos_theta_clipped)
    angle_deg = np.degrees(angle_rad)

    return angle_deg, angle_rad, debug_info


def detect_direction_jump(N, E, V, threshold_deg=10.0):
    """检测方向突变，新增零向量（重复点）过滤"""
    N = np.array(N, dtype=np.float64)
    E = np.array(E, dtype=np.float64)
    V = np.array(V, dtype=np.float64)

    # 输入校验
    if not (len(N) == len(E) == len(V)):
        raise ValueError("N、E、V数组长度必须相同！")
    n_points = len(N)
    if n_points < 3:
        raise ValueError("至少需要3个点（两段向量）！")

    # 第一步：计算方向向量，过滤零向量
    valid_vectors = []  # 存储非零向量
    valid_vector_labels = []  # 非零向量对应的点对
    duplicate_points = []  # 存储重复点信息
    # print("===== 第一步：计算方向向量 & 过滤重复点 =====")

    for i in range(n_points - 1):
        ΔN = N[i + 1] - N[i]
        ΔE = E[i + 1] - E[i]
        ΔV = V[i + 1] - V[i]
        vec = np.array([ΔN, ΔE, ΔV])
        vec_norm = np.linalg.norm(vec)
        label = f"P{i + 1}→P{i + 2}"

        # 判断是否为零向量（重复点）
        if vec_norm < 1e-8:  # 浮点精度容错，避免微小值误判
            duplicate_points.append(label)
            # print(f"⚠️ {label}：向量={np.round(vec, 4)}（模={vec_norm:.8f}）→ 重复点，跳过")
        else:
            valid_vectors.append(vec)
            valid_vector_labels.append(label)
            # print(f"✅ {label}：向量={np.round(vec, 4)}, 模={vec_norm:.4f} → 有效向量")
    # print("\n")

    # 检查过滤后是否有足够的有效向量
    if len(valid_vectors) < 2:
        # print(f"❌ 过滤重复点后仅剩余 {len(valid_vectors)} 个有效向量，无法计算夹角！")
        return [], duplicate_points

    # 第二步：计算有效向量的夹角，检测突变
    jump_results = []
    # print("===== 第二步：计算有效向量夹角 & 突变检测 =====")
    for i in range(len(valid_vectors) - 1):
        v1 = valid_vectors[i]
        v2 = valid_vectors[i + 1]
        v1_label = valid_vector_labels[i]
        v2_label = valid_vector_labels[i + 1]

        # 计算夹角
        angle_deg, angle_rad, debug = calculate_vector_angle(v1, v2)
        is_jump = angle_deg > threshold_deg
        jump_level = "严重突变" if angle_deg > 20 else "轻微突变" if is_jump else "无突变"

        # 存储结果
        jump_results.append({
            "vector_pair": f"{v1_label} ↔ {v2_label}",
            "angle_deg": angle_deg,
            "angle_rad": angle_rad,
            "is_jump": is_jump,
            "jump_level": jump_level,
            "debug": debug
        })

        # 打印结果
        # status = "❌ 突变" if is_jump else "✅ 平稳"
        # print(f"【{v1_label} ↔ {v2_label}】 {status}")
        # print(f"  夹角：{angle_deg:.4f}°（阈值：{threshold_deg}°）")
        # print(f"  突变等级：{jump_level}")
        # print("-" * 80)

    return jump_results, duplicate_points
def visualize_optimized_vs_existing_wells(best_params,
                                          target_e,
                                          target_n,
                                          target_d,
                                          wellhead_position=(0, 0, 0),
                                          excel_files=None,
                                          wellhead_positions=None,
                                          safety_radius=10.0,
                                          depth_step=10.0,
                                          save_filename="optimized_vs_existing_3d.png",
                                          viewpoints=None,
                                          view_elev=None,
                                          view_azim=None):
    """与 objective 同口径（R1/R2 为半径 m）绘制优化井与已有井。"""
    if best_params is None or len(best_params) != 8:
        print("best_params 无效，无法可视化")
        return

    relative_target = (
        target_e - wellhead_position[0],
        target_n - wellhead_position[1],
        target_d - wellhead_position[2],
    )
    cfg = WellTrajectoryConfig(
        E_target=float(relative_target[0]),
        N_target=float(relative_target[1]),
        D_target=float(relative_target[2]),
    )
    calc = WellPathCalculator(cfg)
    points, total_length, flag, loss = calc.calculate_coordinates(list(best_params))
    # print(points)
    if points is None or not flag:
        print(f"无法根据最优参数重建轨迹: flag={flag}, loss={loss}")
        return

    x_rel, y_rel, z_rel = points
    x_abs = np.asarray(x_rel, dtype=float) + float(wellhead_position[0])
    y_abs = np.asarray(y_rel, dtype=float) + float(wellhead_position[1])
    z_abs = np.asarray(z_rel, dtype=float) + float(wellhead_position[2])
    # print(x_abs, y_abs, z_abs)
    # 统计突变数量
    jump_results, duplicate_points = detect_direction_jump(x_rel, y_rel, z_rel, threshold_deg=10.0)
    print("\n===== 最终汇总 =====")
    print(f"🔍 检测到重复点：{duplicate_points if duplicate_points else '无'}")
    print(f"📊 有效突变检测结果：{len(jump_results)} 组")
    if jump_results:
        jump_count = sum([1 for res in jump_results if res['is_jump']])
        print(f"🚨 方向突变数量：{jump_count} 处")
    well_obstacles = []
    if excel_files and wellhead_positions:
        try:
            well_obstacles = create_multiple_well_obstacles(
                excel_files,
                wellhead_positions=wellhead_positions,
                safety_radius=safety_radius,
                segment_length=150.0,
            )
        except Exception as e:
            print(f"加载已有井失败: {e}")

    min_horizontal_distance = float('inf')
    has_collision = False
    for i, wo in enumerate(well_obstacles):
        if wo is not None and wo.well_trajectory is not None and len(wo.well_trajectory) > 1:
            d_min = wo._min_horizontal_distance_scan(
                trajectory=(x_abs, y_abs, z_abs),
                horizontal_threshold=safety_radius,
                depth_step=depth_step,
            )
            min_horizontal_distance = min(min_horizontal_distance, d_min)
            if d_min < safety_radius:
                has_collision = True

    final_deviation = float(np.sqrt(
        (x_rel[-1] - cfg.E_target) ** 2 +
        (y_rel[-1] - cfg.N_target) ** 2 +
        (z_rel[-1] - cfg.D_target) ** 2
    ))
    reaches_target = (final_deviation <= 30.0)

    if viewpoints is None:
        if view_elev is not None and view_azim is not None:
            viewpoints = [(float(view_elev), float(view_azim))]
        else:
            viewpoints = [
                (25, 45),
                (25, 135),
                (40, 225),
                (60, 315),
            ]

    os.makedirs('../images', exist_ok=True)
    base_name, ext = os.path.splitext(save_filename)
    if not ext:
        ext = '.png'

    saved_paths = []
    for idx, (elev, azim) in enumerate(viewpoints, start=1):
        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_subplot(111, projection='3d')

        ax.plot(x_abs, y_abs, -z_abs, 'b-', linewidth=2.5, label='Optimized Well')
        ax.scatter([x_abs[0]], [y_abs[0]], [-z_abs[0]], c='green', s=100, marker='o', label='Wellhead')
        ax.scatter([target_e], [target_n], [-target_d], c='red', s=120, marker='*', label='Target')
        ax.scatter([x_abs[-1]], [y_abs[-1]], [-z_abs[-1]], c='orange', s=60, marker='x', label='Trajectory End')

        for i, wo in enumerate(well_obstacles):
            if wo is not None and wo.well_trajectory is not None and len(wo.well_trajectory) > 1:
                wt = wo.well_trajectory
                ax.plot(wt[:, 0], wt[:, 1], -wt[:, 2], linewidth=2, alpha=0.85, label=f'Existing Well {i+1}')

        ax.set_xlabel('Easting E (m)')
        ax.set_ylabel('Northing N (m)')
        ax.set_zlabel('Depth D (m, downward)')
        ax.set_title(f'Optimized Well Trajectory vs Existing Wells (elev={elev}, azim={azim})')
        ax.view_init(elev=elev, azim=azim)
        ax.legend()
        plt.tight_layout()

        view_filename = f"{base_name}_view{idx}{ext}"
        save_path = os.path.join('../images', view_filename)
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        saved_paths.append(os.path.abspath(save_path))

    print("\n" + "=" * 60)
    print("优化结果可视化检查")
    print("=" * 60)
    print("保存图像:")
    for p in saved_paths:
        print(f"  - {p}")
    print(f"轨迹总长度: {float(total_length):.3f} m")
    print(f"是否入靶(<=30m): {'是' if reaches_target else '否'}")
    print(f"最终入靶偏差(与objective同口径): {final_deviation:.3f} m")
    if np.isfinite(min_horizontal_distance):
        print(f"与已有井最小水平距离: {min_horizontal_distance:.3f} m")
    else:
        print("与已有井最小水平距离: 无法计算（可能没有已有井）")
    print(f"是否与已有井碰撞(阈值 {safety_radius}m): {'是' if has_collision else '否'}")
    print("=" * 60 + "\n")


# =====================
# 可落地：参数直配 + 一键可视化
# =====================
PARAM_BOUNDS = {
    "D_kop": (300.0, 3500.0),
    "alpha1": (1.0, 89.0),
    "alpha2": (1.0, 89.0),
    "phi1": (0.0, 360.0),
    "phi2": (0.0, 360.0),
    "R1": (50.0, 3000.0),
    "R2": (50.0, 3000.0),
    "D_turn_kop": (300.0, 5000.0),
}

DEFAULT_PARAMS = {
    "D_kop": 1200.0,
    "alpha1": 45.0,
    "alpha2": 35.0,
    "phi1": 60.0,
    "phi2": 120.0,
    "R1": 900.0,
    "R2": 800.0,
    "D_turn_kop": 2200.0,
}


def _clip_param(name: str, value: float) -> float:
    """把参数限制在推荐边界内，避免无效输入导致几何失败。"""
    lo, hi = PARAM_BOUNDS[name]
    return float(np.clip(float(value), lo, hi))


def build_param_vector(custom_params: Optional[Dict[str, float]] = None,
                       strict: bool = False) -> list:
    """
    构造8参数向量（按 PARAM_NAMES 顺序）。

    Args:
        custom_params: 你想覆盖的参数字典，例如 {"alpha1": 50, "phi2": 200}
        strict: True时参数越界直接报错；False时自动裁剪到边界
    """
    params = dict(DEFAULT_PARAMS)
    if custom_params:
        params.update(custom_params)

    vec = []
    for name in PARAM_NAMES:
        if name not in params:
            raise ValueError(f"缺少参数: {name}")
        value = float(params[name])
        lo, hi = PARAM_BOUNDS[name]
        if strict and not (lo <= value <= hi):
            raise ValueError(f"参数 {name}={value} 超出范围 [{lo}, {hi}]")
        vec.append(_clip_param(name, value) if not strict else value)
    return vec


def quick_visualize_with_params(custom_params: Optional[Dict[str, float]] = None,
                                target=(1500.64, 1200.71, 2936.06),
                                wellhead_position=(0, 0, 0),
                                excel_files=None,
                                wellhead_positions=None,
                                safety_radius=10.0,
                                depth_step=10.0,
                                save_filename="manual_params_trajectory.png",
                                viewpoints=None,
                                strict=False):
    """
    直接手动配8参数并可视化轨迹。

    Returns:
        dict: 包含参数向量、是否成功、轨迹长度、终点偏差等信息。
    """
    target_e, target_n, target_d = [float(v) for v in target]
    vec = build_param_vector(custom_params=custom_params, strict=strict)

    cfg = WellTrajectoryConfig(
        E_target=target_e - float(wellhead_position[0]),
        N_target=target_n - float(wellhead_position[1]),
        D_target=target_d - float(wellhead_position[2]),
    )
    calc = WellPathCalculator(cfg)
    points, total_length, flag, loss = calc.calculate_coordinates(vec)

    result = {
        "params": dict(zip(PARAM_NAMES, vec)),
        "param_vector": vec,
        "success": bool(flag and points is not None),
        "length": float(total_length),
        "loss": float(loss),
        "final_deviation": None,
    }

    if points is not None:
        x_rel, y_rel, z_rel = points
        final_deviation = float(np.sqrt(
            (x_rel[-1] - cfg.E_target) ** 2 +
            (y_rel[-1] - cfg.N_target) ** 2 +
            (z_rel[-1] - cfg.D_target) ** 2
        ))
        result["final_deviation"] = final_deviation

    if result["success"]:
        visualize_optimized_vs_existing_wells(
            best_params=vec,
            target_e=target_e,
            target_n=target_n,
            target_d=target_d,
            wellhead_position=wellhead_position,
            excel_files=excel_files,
            wellhead_positions=wellhead_positions,
            safety_radius=safety_radius,
            depth_step=depth_step,
            save_filename=save_filename,
            viewpoints=viewpoints,
        )
    else:
        print(f"参数组合不可行: success={result['success']}, loss={result['loss']:.3f}")

    return result


SEVEN_SEG_DEFAULT = {
    # ===== 简化空间七段式参数（统一用狗腿度 DLS, 单位 °/30m） =====
    # 1) L0: 直井段长度（m）
    "L0": 900.0,
    # 2) DLS1: 第一增斜段狗腿度（°/30m）
    "DLS1": 2.4,
    # 3) alpha3: 第一稳斜段井斜（°）
    "alpha3": 42.0,
    # 4) L3: 第一稳斜段长度（m）
    "L3": 750.0,
    # 5) DLS_turn: 扭方位段狗腿度（°/30m）
    "DLS_turn": 2.0,
    # 6) L4: 扭方位圆弧段长度（m）
    "L4": 600.0,
    # 7) L5: 扭方位后稳斜段长度（m）
    "L5": 600.0,
    # 8) DLS6: 末次井斜调整段狗腿度（°/30m）
    "DLS6": 1.5,
    # 9) alpha_e: 末端目标井斜（°）
    "alpha_e": 35.0,
    # 10) L7: 末端稳斜段长度（m）
    "L7": 900.0,
    # 11) phi_init: 初始方位（°），仅在进入斜井后生效
    "phi_init": 65.0,
    # 12) phi_target: 显式末端目标方位（°）
    "phi_target": 95.0,
}


def generate_seven_segment_trajectory(custom_params: Optional[Dict[str, float]] = None,
                                      ds: float = 10.0):
    """生成简化空间七段式轨迹（第4段为专用扭方位圆弧段）。"""
    p = dict(SEVEN_SEG_DEFAULT)
    if custom_params:
        p.update(custom_params)

    L0 = float(max(0.0, p["L0"]))
    DLS1 = float(max(1e-6, p["DLS1"]))
    alpha3 = float(np.clip(p["alpha3"], 0.0, 89.0))
    L3 = float(max(0.0, p["L3"]))
    DLS_turn = float(max(1e-6, p["DLS_turn"]))
    L4 = float(max(0.0, p["L4"]))
    L5 = float(max(0.0, p["L5"]))
    DLS6 = float(max(1e-6, p["DLS6"]))
    alpha_e = float(np.clip(p["alpha_e"], 0.0, 89.0))
    L7 = float(max(0.0, p["L7"]))
    phi_init = float(p["phi_init"] % 360.0)
    phi_target = float(p["phi_target"] % 360.0)

    # DLS(°/30m) -> 角度变化率(°/m)
    k1 = DLS1 / 30.0
    k_turn = DLS_turn / 30.0
    k6 = DLS6 / 30.0

    # 第2段增斜长度
    L1 = abs(alpha3 - 0.0) / k1
    # 第4段扭方位：与 objective_function 一致——目标角自由，段长由目标推导（与井斜 L6 对称）
    dphi_target = (phi_target - phi_init + 180.0) % 360.0 - 180.0
    sin_alpha = max(np.sin(np.radians(max(alpha3, 1e-3))), 1e-3)
    L4_needed = abs(dphi_target) * sin_alpha / abs(k_turn) if abs(k_turn) > 1e-9 else 0.0
    L4_used = min(L4_needed, 1e6) if L4_needed < 1e9 else 0.0
    dphi_turn = float(dphi_target)
    # 第6段井斜调整长度（增/降皆可）
    L6 = abs(alpha_e - alpha3) / k6

    seg_lengths = {
        "seg1_vertical": L0,
        "seg2_build": L1,
        "seg3_hold_before_turn": L3,
        "seg4_azimuth_turn_arc": L4_used,
        "seg5_hold_after_turn": L5,
        "seg6_inc_adjust": L6,
        "seg7_final_hold": L7,
    }

    E = [0.0]
    N = [0.0]
    D = [0.0]
    INC = [0.0]
    AZI = [phi_init]
    MD = [0.0]
    md = 0.0

    def append_step(step_len: float, inc_deg: float, azi_deg: float):
        nonlocal md
        inc = np.radians(inc_deg)
        azi = np.radians(azi_deg)
        dN = step_len * np.sin(inc) * np.cos(azi)
        dE = step_len * np.sin(inc) * np.sin(azi)
        dD = step_len * np.cos(inc)
        N.append(N[-1] + dN)
        E.append(E[-1] + dE)
        D.append(D[-1] + dD)
        INC.append(inc_deg)
        AZI.append(azi_deg % 360.0)
        md += step_len
        MD.append(md)

    # 1) 直井段（方位几何上不生效，但保留记录）
    n = max(1, int(np.ceil(L0 / ds))) if L0 > 0 else 0
    for _ in range(n):
        append_step(L0 / n, 0.0, phi_init)

    # 2) 增斜段（方位固定）
    n = max(1, int(np.ceil(L1 / ds))) if L1 > 0 else 0
    for k in range(1, n + 1):
        frac = k / n
        inc = 0.0 + (alpha3 - 0.0) * frac
        append_step(L1 / n, inc, phi_init)

    # 3) 稳斜段（扭方位前）
    n = max(1, int(np.ceil(L3 / ds))) if L3 > 0 else 0
    for _ in range(n):
        append_step(L3 / n, alpha3, phi_init)

    # 4) 专用扭方位圆弧段（井斜保持 alpha3），长度 L4_used（由 phi_target 推导，与 objective 一致）
    n = max(1, int(np.ceil(L4_used / ds))) if L4_used > 0 else 0
    for k in range(1, n + 1):
        frac = k / n
        azi = phi_init + dphi_turn * frac
        append_step(L4_used / n, alpha3, azi)

    phi_after_turn = (phi_init + dphi_turn) % 360.0

    # 5) 稳斜段（扭方位后）
    n = max(1, int(np.ceil(L5 / ds))) if L5 > 0 else 0
    for _ in range(n):
        append_step(L5 / n, alpha3, phi_after_turn)

    # 6) 井斜调整段（方位固定）
    n = max(1, int(np.ceil(L6 / ds))) if L6 > 0 else 0
    for k in range(1, n + 1):
        frac = k / n
        inc = alpha3 + (alpha_e - alpha3) * frac
        append_step(L6 / n, inc, phi_after_turn)

    # 7) 末端稳斜段
    n = max(1, int(np.ceil(L7 / ds))) if L7 > 0 else 0
    for _ in range(n):
        append_step(L7 / n, alpha_e, phi_after_turn)

    return {
        "params": {
            "L0": L0, "DLS1": DLS1, "alpha3": alpha3, "L3": L3,
            "DLS_turn": DLS_turn, "L4": L4, "L4_used": L4_used, "dphi_turn": dphi_turn, "L5": L5,
            "DLS6": DLS6, "alpha_e": alpha_e, "L7": L7,
            "phi_init": phi_init, "phi_target": phi_target,
        },
        "segment_lengths": seg_lengths,
        "total_length": float(sum(seg_lengths.values())),
        "E": np.asarray(E, dtype=float),
        "N": np.asarray(N, dtype=float),
        "D": np.asarray(D, dtype=float),
        "INC": np.asarray(INC, dtype=float),
        "AZI": np.asarray(AZI, dtype=float),
        "MD": np.asarray(MD, dtype=float),
    }


def quick_visualize_seven_segment(custom_params: Optional[Dict[str, float]] = None,
                                  target: Optional[tuple] = None,
                                  wellhead_position=(0, 0, 0),
                                  excel_files=None,
                                  wellhead_positions=None,
                                  safety_radius: float = 10.0,
                                  save_filename="seven_segment_manual.png",
                                  viewpoints=None,
                                  ds: float = 10.0):
    """手动配七段式参数并可视化（可叠加显示邻井）。"""
    traj = generate_seven_segment_trajectory(custom_params=custom_params, ds=ds)
    # print(traj)
    x_abs = traj["E"] + float(wellhead_position[0])
    y_abs = traj["N"] + float(wellhead_position[1])
    z_abs = traj["D"] + float(wellhead_position[2])

    well_obstacles = []
    if excel_files and wellhead_positions:
        try:
            well_obstacles = create_multiple_well_obstacles(
                excel_files=excel_files,
                wellhead_positions=wellhead_positions,
                safety_radius=safety_radius,
                segment_length=150.0,
            )
        except Exception as e:
            print(f"加载邻井失败: {e}")

    if viewpoints is None:
        viewpoints = [(25, 45), (35, 135), (50, 225), (60, 315)]

    os.makedirs('../images', exist_ok=True)
    base_name, ext = os.path.splitext(save_filename)
    if not ext:
        ext = '.png'

    saved_paths = []
    for idx, (elev, azim) in enumerate(viewpoints, start=1):
        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_subplot(111, projection='3d')

        ax.plot(x_abs, y_abs, -z_abs, 'b-', linewidth=2.5, label='Seven-Segment Well')
        ax.scatter([x_abs[0]], [y_abs[0]], [-z_abs[0]], c='green', s=100, marker='o', label='Wellhead')
        ax.scatter([x_abs[-1]], [y_abs[-1]], [-z_abs[-1]], c='orange', s=70, marker='x', label='Trajectory End')

        if target is not None:
            te, tn, td = [float(v) for v in target]
            ax.scatter([te], [tn], [-td], c='red', s=120, marker='*', label='Target')

        for i, wo in enumerate(well_obstacles):
            if wo is not None and wo.well_trajectory is not None and len(wo.well_trajectory) > 1:
                wt = wo.well_trajectory
                ax.plot(wt[:, 0], wt[:, 1], -wt[:, 2], linewidth=2, alpha=0.85, label=f'Existing Well {i+1}')

        ax.set_xlabel('Easting E (m)')
        ax.set_ylabel('Northing N (m)')
        ax.set_zlabel('Depth D (m, downward)')
        ax.set_title(f'Seven-Segment Well Trajectory (elev={elev}, azim={azim})')
        ax.view_init(elev=elev, azim=azim)
        ax.legend()
        plt.tight_layout()

        view_filename = f"{base_name}_view{idx}{ext}"
        save_path = os.path.join('../images', view_filename)
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        saved_paths.append(os.path.abspath(save_path))

    result = {
        "params": traj["params"],
        "segment_lengths": traj["segment_lengths"],
        "total_length": traj["total_length"],
        "end_point": {
            "E": float(x_abs[-1]),
            "N": float(y_abs[-1]),
            "D": float(z_abs[-1]),
        },
        "saved_images": saved_paths,
    }

    if target is not None:
        te, tn, td = [float(v) for v in target]
        result["final_deviation"] = float(np.sqrt(
            (x_abs[-1] - te) ** 2 +
            (y_abs[-1] - tn) ** 2 +
            (z_abs[-1] - td) ** 2
        ))

    print("\n===== 七段式轨迹结果 =====")
    print(f"总井深(MD): {result['total_length']:.3f} m")
    print(f"终点(E,N,D): ({result['end_point']['E']:.3f}, {result['end_point']['N']:.3f}, {result['end_point']['D']:.3f})")
    if "final_deviation" in result:
        print(f"与目标点偏差: {result['final_deviation']:.3f} m")
    print("分段长度:")
    for k, v in result["segment_lengths"].items():
        print(f"  - {k}: {v:.3f} m")
    print("图像输出:")
    for p in saved_paths:
        print(f"  - {p}")
    print("========================\n")

    return result


if __name__ == "__main__":
    # 空间七段式示例：你可以只改一个参数，比如 dphi_turn（扭方位角）
    custom = {
       'L0': 1803.2186279296875, 'DLS1': 3.8669002056121826, 'alpha3': 59.645233154296875, 'L3': 626.4422607421875, 'DLS_turn': 1.0, 'L4': 47.9384651184082, 'L5': 77.52780151367188, 'DLS6': 4.392568588256836, 'alpha_e': 85.7606201171875, 'L7': 200.0, 'phi_init': 167.94325256347656, 'phi_target': 0.05666998028755188
    }
    target_e, target_n, target_d =502.64, 790.71, 2636.06
    wellhead_position = (222, 2030, 0)
    quick_visualize_seven_segment(
        custom_params=custom,
        target=(target_e, target_n, target_d),
        wellhead_position=wellhead_position,
        # excel_files=excel_files,
        # wellhead_positions=wellhead_positions,
        safety_radius=10,
        save_filename="seven_segment_minimal_result.png",
        ds=10.0,
    )

    print("空间七段式手动参数可视化结果:")
    # print(info)
