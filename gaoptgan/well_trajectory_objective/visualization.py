"""
井轨迹可视化模块
Well Trajectory Visualization Module
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from typing import Tuple, List, Dict, Any, Optional
from .config import WellTrajectoryConfig

def plot_trajectory_3d(trajectory: Tuple[np.ndarray, np.ndarray, np.ndarray], 
                      config: WellTrajectoryConfig,
                      obstacles: Optional[List[Dict[str, Any]]] = None,
                      well_obstacle: Optional[Any] = None,
                      title: str = "3D Well Trajectory",
                      save_path: Optional[str] = None,
                      show: bool = True) -> None:
    """
    绘制3D井轨迹图
    
    Args:
        trajectory: 轨迹坐标 (x, y, z)
        config: 井轨迹配置
        obstacles: 球形障碍物列表（可选）
        well_obstacle: 井轨迹障碍物（可选）
        title: 图表标题
        save_path: 保存路径（可选）
        show: 是否显示图表
    """
    x, y, z = trajectory
    
    # 分段显示轨迹
    n_points = 100
    x1, x2, x3, x4, x5 = x[:n_points], x[n_points:2*n_points], x[2*n_points:3*n_points], x[3*n_points:4*n_points], x[4*n_points:5*n_points]
    y1, y2, y3, y4, y5 = y[:n_points], y[n_points:2*n_points], y[2*n_points:3*n_points], y[3*n_points:4*n_points], y[4*n_points:5*n_points]
    z1, z2, z3, z4, z5 = z[:n_points], z[n_points:2*n_points], z[2*n_points:3*n_points], z[3*n_points:4*n_points], z[4*n_points:5*n_points]
    
    # 创建图形
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # 绘制轨迹段
    segment_colors = ['red', 'green', 'blue', 'orange', 'purple']
    segment_labels = ['Vertical', 'Build', 'Tangent 1', 'Turn', 'Tangent 2']
    
    ax.plot(x1, y1, -z1, color=segment_colors[0], label=segment_labels[0], linewidth=2)
    ax.plot(x2, y2, -z2, color=segment_colors[1], label=segment_labels[1], linewidth=2)
    ax.plot(x3, y3, -z3, color=segment_colors[2], label=segment_labels[2], linewidth=2)
    ax.plot(x4, y4, -z4, color=segment_colors[3], label=segment_labels[3], linewidth=2)
    ax.plot(x5, y5, -z5, color=segment_colors[4], label=segment_labels[4], linewidth=2)
    
    # Draw wellhead and target points（深度 D 向下为正，绘图 z 轴用 -D 使“向下”在图中向下）
    ax.scatter(config.E_wellhead, config.N_wellhead, -config.D_wellhead, 
               c='red', s=100, label='Wellhead', marker='o')
    ax.scatter(config.E_target, config.N_target, -config.D_target, 
               c='green', s=100, label='Target', marker='s')
    
    # 绘制球形障碍物
    if obstacles:
        for obstacle in obstacles:
            center_x, center_y, center_z = obstacle["center"]
            radius = obstacle["radius"]
            
            u = np.linspace(0, 2 * np.pi, 20)
            v = np.linspace(0, np.pi, 20)
            X = center_x + radius * np.outer(np.cos(u), np.sin(v))
            Y = center_y + radius * np.outer(np.sin(u), np.sin(v))
            Z = center_z + radius * np.outer(np.ones(np.size(u)), np.cos(v))
            
            ax.plot_surface(X, Y, -Z, color='red', alpha=0.3, linewidth=0)
            ax.plot_wireframe(X, Y, -Z, color='red', alpha=0.1, linewidth=0.5)
    
    # 绘制井轨迹障碍物
    if well_obstacle is not None and well_obstacle.well_trajectory is not None:
        well_traj = well_obstacle.well_trajectory
        # 约定：内部计算使用“向下为正”的深度 D；绘图时统一用 -D 显示“向下”为负轴方向
        ax.plot(well_traj[:, 0], well_traj[:, 1], -well_traj[:, 2], 
               color='orange', linewidth=3, alpha=0.8, label='Existing Well')
        
        # 绘制安全距离
        safety_radius = well_obstacle.safety_radius
        for i in range(0, len(well_traj), 10):  # 每10个点绘制一个安全球
            point = well_traj[i]
            u = np.linspace(0, 2 * np.pi, 20)
            v = np.linspace(0, np.pi, 20)
            X = point[0] + safety_radius * np.outer(np.cos(u), np.sin(v))
            Y = point[1] + safety_radius * np.outer(np.sin(u), np.sin(v))
            Z = point[2] + safety_radius * np.outer(np.ones(np.size(u)), np.cos(v))
            
            ax.plot_surface(X, Y, -Z, color='orange', alpha=0.1, linewidth=0)
    
    # 设置坐标轴
    ax.set_xlabel('East (m)')
    ax.set_ylabel('North (m)')
    ax.set_zlabel('Depth (m)')
    
    # 设置视角
    ax.view_init(elev=30, azim=120)
    ax.dist = 10
    
    # 设置图例
    ax.legend()
    plt.title(title)
    
    # 保存图表
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"图表已保存到: {save_path}")
    
    # 显示图表
    if show:
        plt.show()
    
    plt.close()

def plot_trajectory_multiple_views(trajectory: Tuple[np.ndarray, np.ndarray, np.ndarray], 
                                  config: WellTrajectoryConfig,
                                  obstacles: Optional[List[Dict[str, Any]]] = None,
                                  well_obstacle: Optional[Any] = None,
                                  save_path: Optional[str] = None) -> None:
    """
    绘制多角度井轨迹图
    
    Args:
        trajectory: 轨迹坐标 (x, y, z)
        config: 井轨迹配置
        obstacles: 球形障碍物列表（可选）
        well_obstacle: 井轨迹障碍物（可选）
        save_path: 保存路径前缀（可选）
    """
    viewpoints = [
        (30, 120, "Front View"),
        (45, 60, "Side View"),
        (60, 270, "Top View"),
        (20, 180, "Back View")
    ]
    
    for i, (elev, azim, view_name) in enumerate(viewpoints):
        x, y, z = trajectory
        
        # 分段显示轨迹
        n_points = 100
        x1, x2, x3, x4, x5 = x[:n_points], x[n_points:2*n_points], x[2*n_points:3*n_points], x[3*n_points:4*n_points], x[4*n_points:5*n_points]
        y1, y2, y3, y4, y5 = y[:n_points], y[n_points:2*n_points], y[2*n_points:3*n_points], y[3*n_points:4*n_points], y[4*n_points:5*n_points]
        z1, z2, z3, z4, z5 = z[:n_points], z[n_points:2*n_points], z[2*n_points:3*n_points], z[3*n_points:4*n_points], z[4*n_points:5*n_points]
        
        # 创建图形
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        # 绘制轨迹段
        segment_colors = ['red', 'green', 'blue', 'orange', 'purple']
        segment_labels = ['Vertical', 'Build', 'Tangent 1', 'Turn', 'Tangent 2']
        
        ax.plot(x1, y1, -z1, color=segment_colors[0], label=segment_labels[0], linewidth=2)
        ax.plot(x2, y2, -z2, color=segment_colors[1], label=segment_labels[1], linewidth=2)
        ax.plot(x3, y3, -z3, color=segment_colors[2], label=segment_labels[2], linewidth=2)
        ax.plot(x4, y4, -z4, color=segment_colors[3], label=segment_labels[3], linewidth=2)
        ax.plot(x5, y5, -z5, color=segment_colors[4], label=segment_labels[4], linewidth=2)
        
        # Draw wellhead and target points（深度 D 向下为正，绘图 z 用 -D）
        ax.scatter(config.E_wellhead, config.N_wellhead, -config.D_wellhead, 
                   c='red', s=100, label='Wellhead', marker='o')
        ax.scatter(config.E_target, config.N_target, -config.D_target, 
                   c='green', s=100, label='Target', marker='s')
        
        # 绘制球形障碍物
        if obstacles:
            for obstacle in obstacles:
                center_x, center_y, center_z = obstacle["center"]
                radius = obstacle["radius"]
                
                u = np.linspace(0, 2 * np.pi, 20)
                v = np.linspace(0, np.pi, 20)
                X = center_x + radius * np.outer(np.cos(u), np.sin(v))
                Y = center_y + radius * np.outer(np.sin(u), np.sin(v))
                Z = center_z + radius * np.outer(np.ones(np.size(u)), np.cos(v))
                
                ax.plot_surface(X, Y, -Z, color='red', alpha=0.3, linewidth=0)
                ax.plot_wireframe(X, Y, -Z, color='red', alpha=0.1, linewidth=0.5)
        
        # 绘制井轨迹障碍物
        if well_obstacle is not None and well_obstacle.well_trajectory is not None:
            well_traj = well_obstacle.well_trajectory
            ax.plot(well_traj[:, 0], well_traj[:, 1], -well_traj[:, 2], 
                   color='orange', linewidth=3, alpha=0.8, label='Existing Well')
        
        # 设置坐标轴
        ax.set_xlabel('East (m)')
        ax.set_ylabel('North (m)')
        ax.set_zlabel('Depth (m)')
        
        # 设置视角
        ax.view_init(elev=elev, azim=azim)
        ax.dist = 10
        
        # 设置图例
        ax.legend()
        plt.title(f'3D Well Trajectory - {view_name}')
        
        # 保存图表
        if save_path:
            filename = f"{save_path}_view_{i}_{view_name.lower().replace(' ', '_')}.png"
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"图表已保存到: {filename}")
        
        plt.close()

def plot_fitness_evolution(fitness_history: List[float], 
                          title: str = "Fitness Evolution",
                          save_path: Optional[str] = None,
                          show: bool = True) -> None:
    """
    绘制适应度进化图
    
    Args:
        fitness_history: 适应度历史
        title: 图表标题
        save_path: 保存路径（可选）
        show: 是否显示图表
    """
    plt.figure(figsize=(10, 6))
    plt.plot(fitness_history, linewidth=2, color='blue')
    plt.xlabel('Generation')
    plt.ylabel('Best Fitness')
    plt.title(title)
    plt.grid(True, alpha=0.3)
    
    # 添加统计信息
    min_fitness = min(fitness_history)
    max_fitness = max(fitness_history)
    final_fitness = fitness_history[-1]
    
    plt.text(0.02, 0.98, f'Min: {min_fitness:.2f}\nMax: {max_fitness:.2f}\nFinal: {final_fitness:.2f}', 
             transform=plt.gca().transAxes, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # 保存图表
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"图表已保存到: {save_path}")
    
    # 显示图表
    if show:
        plt.show()
    
    plt.close()

def plot_parameter_analysis(parameter_history: List[List[float]], 
                           parameter_names: List[str],
                           title: str = "Parameter Analysis",
                           save_path: Optional[str] = None,
                           show: bool = True) -> None:
    """
    绘制参数分析图
    
    Args:
        parameter_history: 参数历史
        parameter_names: 参数名称
        title: 图表标题
        save_path: 保存路径（可选）
        show: 是否显示图表
    """
    n_params = len(parameter_names)
    n_generations = len(parameter_history)
    
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    axes = axes.flatten()
    
    for i in range(n_params):
        if i < len(axes):
            param_values = [gen[i] for gen in parameter_history]
            axes[i].plot(param_values, linewidth=2)
            axes[i].set_title(parameter_names[i])
            axes[i].set_xlabel('Generation')
            axes[i].set_ylabel('Value')
            axes[i].grid(True, alpha=0.3)
    
    # 隐藏多余的子图
    for i in range(n_params, len(axes)):
        axes[i].set_visible(False)
    
    plt.suptitle(title)
    plt.tight_layout()
    
    # 保存图表
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"图表已保存到: {save_path}")
    
    # 显示图表
    if show:
        plt.show()
    
    plt.close()

def plot_well_comparison_3d(position_tuple: List[float],
                           config: WellTrajectoryConfig,
                           well_obstacle: Optional[Any] = None,
                           well_obstacles: Optional[List[Any]] = None,
                           obstacles: Optional[List[Dict[str, Any]]] = None,
                           title: str = "井轨迹对比图 - 已添加井 vs 新设计井",
                           save_path: Optional[str] = None,
                           show: bool = True) -> None:
    """
    绘制已添加井和8个参数确定的井的三维对比图
    
    Args:
        position_tuple: 8个参数 [D_kop, alpha1, alpha2, phi1, phi2, R1, R2, D_turn_kop]
        config: 井轨迹配置
        well_obstacle: 单个井轨迹障碍物（已添加的井）
        well_obstacles: 多个井轨迹障碍物列表（可选）
        obstacles: 球形障碍物列表（可选）
        title: 图表标题
        save_path: 保存路径（可选）
        show: 是否显示图表
    """
    from .well_calculator import WellPathCalculator
    
    # 计算新设计井的轨迹
    calculator = WellPathCalculator(config)
    result = calculator.calculate_coordinates(position_tuple)
    
    if result[0] is None:
        print("Error: Unable to calculate well trajectory, please check parameters")
        return
    
    new_trajectory = result[0]
    x_new, y_new, z_new = new_trajectory
    # 创建多角度视图
    viewpoints = [
        (30, 120, "前视图"),
        (45, 60, "侧视图"), 
        (60, 270, "俯视图"),
        (20, 180, "后视图"),
        (0, 0, "正视图"),
        (90, 0, "顶视图")
    ]
    
    for i, (elev, azim, view_name) in enumerate(viewpoints):
        fig = plt.figure(figsize=(14, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        # 绘制新设计井轨迹（分段显示）
        n_points = 100
        x1, x2, x3, x4, x5 = (x_new[:n_points], x_new[n_points:2*n_points], 
                              x_new[2*n_points:3*n_points], x_new[3*n_points:4*n_points], 
                              x_new[4*n_points:5*n_points])
        y1, y2, y3, y4, y5 = (y_new[:n_points], y_new[n_points:2*n_points], 
                              y_new[2*n_points:3*n_points], y_new[3*n_points:4*n_points], 
                              y_new[4*n_points:5*n_points])
        z1, z2, z3, z4, z5 = (z_new[:n_points], z_new[n_points:2*n_points], 
                              z_new[2*n_points:3*n_points], z_new[3*n_points:4*n_points], 
                              z_new[4*n_points:5*n_points])
        # 新设计井轨迹段
        segment_colors = ['red', 'green', 'blue', 'orange', 'purple']
        segment_labels = ['Vertical', 'Build', 'Tangent 1', 'Turn', 'Tangent 2']
        
        ax.plot(x1, y1, -z1, color=segment_colors[0], label=f'New Well-{segment_labels[0]}', linewidth=3, alpha=0.8)
        ax.plot(x2, y2, -z2, color=segment_colors[1], label=f'New Well-{segment_labels[1]}', linewidth=3, alpha=0.8)
        ax.plot(x3, y3, -z3, color=segment_colors[2], label=f'New Well-{segment_labels[2]}', linewidth=3, alpha=0.8)
        ax.plot(x4, y4, -z4, color=segment_colors[3], label=f'New Well-{segment_labels[3]}', linewidth=3, alpha=0.8)
        ax.plot(x5, y5, -z5, color=segment_colors[4], label=f'New Well-{segment_labels[4]}', linewidth=3, alpha=0.8)
        
        # 绘制已添加井轨迹
        well_colors = ['darkblue', 'darkgreen', 'darkred', 'darkorange', 'darkviolet', 'darkcyan', 'darkmagenta', 'darkgoldenrod']
        # print()
        # # 绘制单个井轨迹障碍物
        # if well_obstacle is not None and well_obstacle.well_trajectory is not None:
        #     well_traj = well_obstacle.well_trajectory
        #     ax.plot(well_traj[:, 0], well_traj[:, 1], -well_traj[:, 2], 
        #            color=well_colors[0], linewidth=4, alpha=0.9, label='Existing Well 1')
            
        #     # 绘制已添加井的安全距离
        #     safety_radius = well_obstacle.safety_radius
        #     for j in range(0, len(well_traj), 20):  # 每20个点绘制一个安全球
        #         point = well_traj[j]
        #         u = np.linspace(0, 2 * np.pi, 15)
        #         v = np.linspace(0, np.pi, 15)
        #         X = point[0] + safety_radius * np.outer(np.cos(u), np.sin(v))
        #         Y = point[1] + safety_radius * np.outer(np.sin(u), np.sin(v))
        #         Z = point[2] + safety_radius * np.outer(np.ones(np.size(u)), np.cos(v))
                
        #         ax.plot_surface(X, Y, -Z, color='lightblue', alpha=0.1, linewidth=0)
        
        # 绘制多个井轨迹障碍物
        if well_obstacles is not None:
            for i, well_obstacle in enumerate(well_obstacles):
                if well_obstacle is not None and well_obstacle.well_trajectory is not None:
                    well_traj = well_obstacle.well_trajectory
                    color = well_colors[i % len(well_colors)]
                    ax.plot(well_traj[:, 0], well_traj[:, 1], -well_traj[:, 2], 
                           color=color, linewidth=3, alpha=0.8, label=f'Existing Well {i+1}')
                    
                    # 绘制安全距离
                    safety_radius = well_obstacle.safety_radius
                    for j in range(0, len(well_traj), 30):  # 每30个点绘制一个安全球
                        point = well_traj[j]
                        u = np.linspace(0, 2 * np.pi, 15)
                        v = np.linspace(0, np.pi, 15)
                        X = point[0] + safety_radius * np.outer(np.cos(u), np.sin(v))
                        Y = point[1] + safety_radius * np.outer(np.sin(u), np.sin(v))
                        Z = point[2] + safety_radius * np.outer(np.ones(np.size(u)), np.cos(v))
                        
                        ax.plot_surface(X, Y, -Z, color=color, alpha=0.05, linewidth=0)
        
        # 绘制球形障碍物
        if obstacles:
            for obstacle in obstacles:
                center_x, center_y, center_z = obstacle["center"]
                radius = obstacle["radius"]
                
                u = np.linspace(0, 2 * np.pi, 20)
                v = np.linspace(0, np.pi, 20)
                X = center_x + radius * np.outer(np.cos(u), np.sin(v))
                Y = center_y + radius * np.outer(np.sin(u), np.sin(v))
                Z = center_z + radius * np.outer(np.ones(np.size(u)), np.cos(v))
                
                ax.plot_surface(X, Y, -Z, color='red', alpha=0.3, linewidth=0)
                ax.plot_wireframe(X, Y, -Z, color='red', alpha=0.2, linewidth=0.5)
        
        # Draw wellhead and target points
        ax.scatter(config.E_wellhead, config.N_wellhead, -config.D_wellhead, 
                   c='red', s=150, label='Wellhead', marker='o', edgecolors='black', linewidth=2)
        ax.scatter(config.E_target, config.N_target, -config.D_target, 
                   c='green', s=150, label='Target', marker='s', edgecolors='black', linewidth=2)
        
        # 绘制关键点
        # 新设计井的关键点
        junction_points = [
            (x1[-1], y1[-1], z1[-1]),  # 造斜点
            (x2[-1], y2[-1], z2[-1]),  # 第一切线段起点
            (x3[-1], y3[-1], z3[-1]),  # 转向段起点
            (x4[-1], y4[-1], z4[-1]),  # 第二切线段起点
            (x5[-1], y5[-1], z5[-1])   # 最终点
        ]
        
        junction_labels = ['KOP', 'Tangent 1 Start', 'Turn Start', 'Tangent 2 Start', 'Final Point']
        junction_colors = ['purple', 'cyan', 'magenta', 'yellow', 'lime']
        
        for j, (point, label, color) in enumerate(zip(junction_points, junction_labels, junction_colors)):
            ax.scatter(point[0], point[1], -point[2], 
                      c=color, s=80, label=f'New Well-{label}', marker='^', alpha=0.8)
        
        # 设置坐标轴
        ax.set_xlabel('East (m)', fontsize=12)
        ax.set_ylabel('North (m)', fontsize=12)
        ax.set_zlabel('Depth (m)', fontsize=12)
        
        # 设置视角
        ax.view_init(elev=elev, azim=azim)
        ax.dist = 10
        
        # 设置图例
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
        
        # 设置标题
        plt.title(f'{title} - {view_name}', fontsize=14, fontweight='bold')
        
        # 添加参数信息
        param_text = f'Parameters: D_kop={position_tuple[0]:.0f}, α1={position_tuple[1]:.1f}°, α2={position_tuple[2]:.1f}°\n'
        param_text += f'φ1={position_tuple[3]:.1f}°, φ2={position_tuple[4]:.1f}°, R1={position_tuple[5]:.0f}, R2={position_tuple[6]:.0f}, D_turn={position_tuple[7]:.0f}'
        plt.figtext(0.02, 0.02, param_text, fontsize=9, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        # 保存图表
        if save_path:
            filename = f"{save_path}_comparison_{i}_{view_name}.png"
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"Comparison chart saved to: {filename}")
        
        # 显示图表
        if show:
            plt.show()
        
        plt.close()

def plot_well_comparison_interactive(position_tuple: List[float],
                                   config: WellTrajectoryConfig,
                                   well_obstacle: Optional[Any] = None,
                                   well_obstacles: Optional[List[Any]] = None,
                                   obstacles: Optional[List[Dict[str, Any]]] = None,
                                   title: str = "井轨迹对比图 - 交互式多角度观察",
                                   save_path: Optional[str] = None) -> None:
    """
    绘制交互式井轨迹对比图，支持多角度观察
    
    Args:
        position_tuple: 8个参数 [D_kop, alpha1, alpha2, phi1, phi2, R1, R2, D_turn_kop]
        config: 井轨迹配置
        well_obstacle: 单个井轨迹障碍物（已添加的井）
        well_obstacles: 多个井轨迹障碍物列表（可选）
        obstacles: 球形障碍物列表（可选）
        title: 图表标题
        save_path: 保存路径（可选）
    """
    from .well_calculator import WellPathCalculator
    
    # 计算新设计井的轨迹
    calculator = WellPathCalculator(config)
    result = calculator.calculate_coordinates(position_tuple)
    
    if result[0] is None:
        print("Error: Unable to calculate well trajectory, please check parameters")
        return
    
    new_trajectory = result[0]
    x_new, y_new, z_new = new_trajectory
    
    # 创建交互式图形
    fig = plt.figure(figsize=(16, 12))
    ax = fig.add_subplot(111, projection='3d')
    
    # 绘制新设计井轨迹（分段显示）
    n_points = 100
    x1, x2, x3, x4, x5 = (x_new[:n_points], x_new[n_points:2*n_points], 
                          x_new[2*n_points:3*n_points], x_new[3*n_points:4*n_points], 
                          x_new[4*n_points:5*n_points])
    y1, y2, y3, y4, y5 = (y_new[:n_points], y_new[n_points:2*n_points], 
                          y_new[2*n_points:3*n_points], y_new[3*n_points:4*n_points], 
                          y_new[4*n_points:5*n_points])
    z1, z2, z3, z4, z5 = (z_new[:n_points], z_new[n_points:2*n_points], 
                          z_new[2*n_points:3*n_points], z_new[3*n_points:4*n_points], 
                          z_new[4*n_points:5*n_points])
    
    # 新设计井轨迹段
    segment_colors = ['red', 'green', 'blue', 'orange', 'purple']
    segment_labels = ['Vertical', 'Build', 'Tangent 1', 'Turn', 'Tangent 2']
    
    ax.plot(x1, y1, -z1, color=segment_colors[0], label=f'New Well-{segment_labels[0]}', linewidth=3, alpha=0.8)
    ax.plot(x2, y2, -z2, color=segment_colors[1], label=f'New Well-{segment_labels[1]}', linewidth=3, alpha=0.8)
    ax.plot(x3, y3, -z3, color=segment_colors[2], label=f'New Well-{segment_labels[2]}', linewidth=3, alpha=0.8)
    ax.plot(x4, y4, -z4, color=segment_colors[3], label=f'New Well-{segment_labels[3]}', linewidth=3, alpha=0.8)
    ax.plot(x5, y5, -z5, color=segment_colors[4], label=f'New Well-{segment_labels[4]}', linewidth=3, alpha=0.8)
    
    # 绘制已添加井轨迹
    well_colors = ['darkblue', 'darkgreen', 'darkred', 'darkorange', 'darkviolet', 'darkcyan', 'darkmagenta', 'darkgoldenrod']
    
    # # 绘制单个井轨迹障碍物
    # if well_obstacle is not None and well_obstacle.well_trajectory is not None:
    #     well_traj = well_obstacle.well_trajectory
    #     ax.plot(well_traj[:, 0], well_traj[:, 1], -well_traj[:, 2], 
    #            color=well_colors[0], linewidth=4, alpha=0.9, label='Existing Well 1')
        
    #     # 绘制已添加井的安全距离
    #     safety_radius = well_obstacle.safety_radius
    #     for j in range(0, len(well_traj), 30):  # 每30个点绘制一个安全球
    #         point = well_traj[j]
    #         u = np.linspace(0, 2 * np.pi, 20)
    #         v = np.linspace(0, np.pi, 20)
    #         X = point[0] + safety_radius * np.outer(np.cos(u), np.sin(v))
    #         Y = point[1] + safety_radius * np.outer(np.sin(u), np.sin(v))
    #         Z = point[2] + safety_radius * np.outer(np.ones(np.size(u)), np.cos(v))
            
    #         ax.plot_surface(X, Y, -Z, color='lightblue', alpha=0.1, linewidth=0)
    
    # 绘制多个井轨迹障碍物
    if well_obstacles is not None:
        for i, well_obstacle in enumerate(well_obstacles):
            if well_obstacle is not None and well_obstacle.well_trajectory is not None:
                well_traj = well_obstacle.well_trajectory
                color = well_colors[i % len(well_colors)]
                ax.plot(well_traj[:, 0], well_traj[:, 1], -well_traj[:, 2], 
                       color=color, linewidth=3, alpha=0.8, label=f'Existing Well {i+1}')
                
                # 绘制安全距离
                safety_radius = well_obstacle.safety_radius
                for j in range(0, len(well_traj), 40):  # 每40个点绘制一个安全球
                    point = well_traj[j]
                    u = np.linspace(0, 2 * np.pi, 20)
                    v = np.linspace(0, np.pi, 20)
                    X = point[0] + safety_radius * np.outer(np.cos(u), np.sin(v))
                    Y = point[1] + safety_radius * np.outer(np.sin(u), np.sin(v))
                    Z = point[2] + safety_radius * np.outer(np.ones(np.size(u)), np.cos(v))
                    
                    ax.plot_surface(X, Y, -Z, color=color, alpha=0.05, linewidth=0)
    
    # 绘制球形障碍物
    if obstacles:
        for obstacle in obstacles:
            center_x, center_y, center_z = obstacle["center"]
            radius = obstacle["radius"]
            
            u = np.linspace(0, 2 * np.pi, 20)
            v = np.linspace(0, np.pi, 20)
            X = center_x + radius * np.outer(np.cos(u), np.sin(v))
            Y = center_y + radius * np.outer(np.sin(u), np.sin(v))
            Z = center_z + radius * np.outer(np.ones(np.size(u)), np.cos(v))
            
            ax.plot_surface(X, Y, -Z, color='red', alpha=0.3, linewidth=0)
            ax.plot_wireframe(X, Y, -Z, color='red', alpha=0.2, linewidth=0.5)
    
    # Draw wellhead and target points
    ax.scatter(config.E_wellhead, config.N_wellhead, -config.D_wellhead, 
               c='red', s=200, label='Wellhead', marker='o', edgecolors='black', linewidth=3)
    ax.scatter(config.E_target, config.N_target, -config.D_target, 
               c='green', s=200, label='Target', marker='s', edgecolors='black', linewidth=3)
    
    # 绘制关键点
    junction_points = [
        (x1[-1], y1[-1], z1[-1]),  # 造斜点
        (x2[-1], y2[-1], z2[-1]),  # 第一切线段起点
        (x3[-1], y3[-1], z3[-1]),  # 转向段起点
        (x4[-1], y4[-1], z4[-1]),  # 第二切线段起点
        (x5[-1], y5[-1], z5[-1])   # 最终点
    ]
    
    junction_labels = ['KOP', 'Tangent 1 Start', 'Turn Start', 'Tangent 2 Start', 'Final Point']
    junction_colors = ['purple', 'cyan', 'magenta', 'yellow', 'lime']
    
    for j, (point, label, color) in enumerate(zip(junction_points, junction_labels, junction_colors)):
        ax.scatter(point[0], point[1], -point[2], 
                  c=color, s=100, label=f'New Well-{label}', marker='^', alpha=0.8, edgecolors='black')
    
    # 设置坐标轴
    ax.set_xlabel('East (m)', fontsize=14)
    ax.set_ylabel('North (m)', fontsize=14)
    ax.set_zlabel('Depth (m)', fontsize=14)
    
    # 设置初始视角
    ax.view_init(elev=30, azim=120)
    ax.dist = 10
    
    # 设置图例
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=12)
    
    # 设置标题
    plt.title(title, fontsize=16, fontweight='bold', pad=20)
    
    # 添加参数信息
    param_text = f'New Well Parameters:\n'
    param_text += f'D_kop={position_tuple[0]:.0f}m, α1={position_tuple[1]:.1f}°, α2={position_tuple[2]:.1f}°\n'
    param_text += f'φ1={position_tuple[3]:.1f}°, φ2={position_tuple[4]:.1f}°\n'
    param_text += f'R1={position_tuple[5]:.0f}m, R2={position_tuple[6]:.0f}m, D_turn={position_tuple[7]:.0f}m'
    plt.figtext(0.02, 0.02, param_text, fontsize=11, 
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9))
    
    # 添加操作说明
    instruction_text = 'Instructions:\n• Left mouse drag: Rotate view\n• Mouse wheel: Zoom\n• Right mouse drag: Pan'
    plt.figtext(0.98, 0.02, instruction_text, fontsize=10, ha='right',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    
    # 保存图表
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Interactive comparison chart saved to: {save_path}")
    
    plt.show()

def create_visualization_report(trajectory: Tuple[np.ndarray, np.ndarray, np.ndarray],
                               config: WellTrajectoryConfig,
                               fitness_history: Optional[List[float]] = None,
                               parameter_history: Optional[List[List[float]]] = None,
                               obstacles: Optional[List[Dict[str, Any]]] = None,
                               well_obstacle: Optional[Any] = None,
                               output_dir: str = "visualization_output") -> None:
    """
    创建完整的可视化报告
    
    Args:
        trajectory: 轨迹坐标 (x, y, z)
        config: 井轨迹配置
        fitness_history: 适应度历史（可选）
        parameter_history: 参数历史（可选）
        obstacles: 球形障碍物列表（可选）
        well_obstacle: 井轨迹障碍物（可选）
        output_dir: 输出目录
    """
    import os
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"创建可视化报告到目录: {output_dir}")
    
    # 3D轨迹图
    plot_trajectory_3d(trajectory, config, obstacles, well_obstacle, 
                      save_path=os.path.join(output_dir, "trajectory_3d.png"), 
                      show=False)
    
    # 多角度视图
    plot_trajectory_multiple_views(trajectory, config, obstacles, well_obstacle,
                                  save_path=os.path.join(output_dir, "trajectory"))
    
    # 适应度进化图
    if fitness_history:
        plot_fitness_evolution(fitness_history,
                              save_path=os.path.join(output_dir, "fitness_evolution.png"),
                              show=False)
    
    # 参数分析图
    if parameter_history:
        parameter_names = ['D_kop', 'alpha1', 'alpha2', 'phi1', 'phi2', 'R1', 'R2', 'D_turn_kop']
        plot_parameter_analysis(parameter_history, parameter_names,
                               save_path=os.path.join(output_dir, "parameter_analysis.png"),
                               show=False)
    
    print("可视化报告创建完成！")
