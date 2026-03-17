"""
Well Trajectory Optimization Result Visualization Script
Visualize optimization results based on configuration bounds, existing wells, and optimal parameters
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from typing import Tuple, List, Dict, Any, Optional
import argparse
import sys
import os

# Add paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GA_DIR = os.path.join(ROOT_DIR, "GA")
if GA_DIR not in sys.path:
    sys.path.append(GA_DIR)

from well_trajectory_objective import (
    WellTrajectoryConfig,
    WellTrajectoryObjective,
    create_multiple_well_obstacles,
)
from well_trajectory_objective.well_calculator import WellPathCalculator


PARAM_NAMES = ["D_kop", "alpha1", "alpha2", "phi1", "phi2", "R1", "R2", "D_turn_kop"]


def parse_triplet(triplet_str: str) -> Tuple[float, float, float]:
    """Parse coordinate string 'e,n,d'"""
    parts = [float(x) for x in triplet_str.split(",")]
    if len(parts) != 3:
        raise ValueError("Coordinate format should be 'e,n,d'")
    return parts[0], parts[1], parts[2]


def visualize_optimization_result(
    optimal_params: List[float],
    config: WellTrajectoryConfig,
    well_obstacles: Optional[List] = None,
    wellhead_position: Tuple[float, float, float] = (254.0, 2030.0, 0.0),
    save_path: Optional[str] = None,
    show: bool = True,
    show_parameter_info: bool = False,
):
    """
    Visualize optimization results - trajectory only with multiple views
    
    Args:
        optimal_params: Optimal parameters [D_kop, alpha1, alpha2, phi1, phi2, R1, R2, D_turn_kop]
        config: Well trajectory configuration
        well_obstacles: List of existing well obstacles
        wellhead_position: Wellhead position
        save_path: Save path (if None, will save as multiple files with view names)
        show: Whether to display
        show_parameter_info: Whether to show parameter information (deprecated, kept for compatibility)
    """
    # Create calculator
    calculator = WellPathCalculator(config)
    
    # Calculate optimal trajectory
    result = calculator.calculate_coordinates(optimal_params)
    if result[0] is None:
        print("❌ Error: Unable to calculate trajectory, parameters may be invalid")
        return
    
    points, total_length, flag, loss = result
    x, y, z = points  # x=E (East), y=N (North), z=D (Depth, positive downward)
    # Convert depth to negative for visualization (depth increases downward)
    z_vis = -z  # Negative z for visualization: positive depth goes down
    
    # Define multiple viewpoints
    viewpoints = [
        (30, 120, "Front View"),
        (45, 60, "Side View"),
        (60, 270, "Top View"),
        (20, 180, "Back View"),
        (0, 0, "Frontal View"),
        (90, 0, "Vertical View")
    ]
    
    # Calculate segment boundaries
    total_points = len(x)
    n_points_per_segment = total_points // 5
    segments = []
    for i in range(5):
        start = i * n_points_per_segment
        if i == 4:
            end = total_points
        else:
            end = min((i + 1) * n_points_per_segment, total_points)
        if start < total_points:
            segments.append((start, end))
    
    segment_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    segment_labels = ['Vertical', 'Build', 'Tangent 1', 'Turn', 'Tangent 2']
    
    # Create visualization for each viewpoint
    for view_idx, (elev, azim, view_name) in enumerate(viewpoints):
        fig = plt.figure(figsize=(14, 10))
        ax_3d = fig.add_subplot(111, projection='3d')
        
        # Plot trajectory segments
        # Use negative z for visualization: positive depth goes downward
        for i, (start, end) in enumerate(segments):
            if i < len(segment_labels) and start < len(x):
                end = min(end, len(x))
                ax_3d.plot(
                    x[start:end], y[start:end], z_vis[start:end],
                    color=segment_colors[i],
                    label=segment_labels[i],
                    linewidth=2.5,
                    alpha=0.9
                )
        
        # Plot wellhead point
        # Wellhead coordinates: x=E, y=N, z=D (Depth, positive downward)
        # Convert depth to negative for visualization
        ax_3d.scatter(
            config.E_wellhead, config.N_wellhead, -config.D_wellhead,
            c='red', s=200, label='Wellhead', marker='o', 
            edgecolors='black', linewidths=2, zorder=10
        )
        
        # Plot target point
        # Note: config.E_target, N_target, D_target are RELATIVE to wellhead
        # Convert to absolute coordinates: absolute = wellhead + relative
        # Convert depth to negative for visualization
        E_target_abs = config.E_wellhead + config.E_target
        N_target_abs = config.N_wellhead + config.N_target
        D_target_abs = config.D_wellhead + config.D_target
        ax_3d.scatter(
            E_target_abs, N_target_abs, -D_target_abs,
            c='green', s=200, label='Target', marker='s',
            edgecolors='black', linewidths=2, zorder=10
        )
        
        # Plot existing well trajectories
        if well_obstacles:
            for idx, well_obstacle in enumerate(well_obstacles):
                if well_obstacle is not None and well_obstacle.well_trajectory is not None:
                    well_traj = well_obstacle.well_trajectory
                    # well_traj[:, 0]=E, well_traj[:, 1]=N, well_traj[:, 2]=D
                    # Convert depth to negative for visualization
                    ax_3d.plot(
                        well_traj[:, 0], well_traj[:, 1], -well_traj[:, 2],
                        color='orange', linewidth=2.5, alpha=0.7,
                        label=f'Existing Well {idx+1}' if idx == 0 else ''
                    )
        
        # Set 3D plot properties
        ax_3d.set_xlabel('East E (m)', fontsize=12, fontweight='bold')
        ax_3d.set_ylabel('North N (m)', fontsize=12, fontweight='bold')
        ax_3d.set_zlabel('Depth D (m)', fontsize=12, fontweight='bold')
        ax_3d.set_title(f'Well Trajectory - {view_name}', fontsize=14, fontweight='bold', pad=20)
        
        # Set view angle
        ax_3d.view_init(elev=elev, azim=azim)
        
        # Set equal aspect ratio for better visualization
        # Calculate ranges (using original z for range calculation, but display negative z)
        x_range = max(x) - min(x) if len(x) > 0 else 1
        y_range = max(y) - min(y) if len(y) > 0 else 1
        z_range = max(z) - min(z) if len(z) > 0 else 1
        max_range = max(x_range, y_range, z_range)
        
        ax_3d.set_xlim([min(x) - 0.1*max_range, max(x) + 0.1*max_range])
        ax_3d.set_ylim([min(y) - 0.1*max_range, max(y) + 0.1*max_range])
        # z-axis: negative values (depth increases downward visually)
        ax_3d.set_zlim([-max(z) - 0.1*max_range, -min(z) + 0.1*max_range])
        
        ax_3d.legend(loc='upper left', fontsize=9)
        ax_3d.grid(True, alpha=0.3)
        
        # Save figure
        if save_path:
            if len(viewpoints) > 1:
                # Multiple views: add view name to filename
                base_path = save_path.rsplit('.', 1)
                if len(base_path) == 2:
                    filename = f"{base_path[0]}_{view_name.lower().replace(' ', '_')}.{base_path[1]}"
                else:
                    filename = f"{save_path}_{view_name.lower().replace(' ', '_')}.png"
            else:
                filename = save_path
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"✅ Saved: {filename}")
        
        # Show or close
        if show:
            plt.show()
        else:
            plt.close()
        
        # If only one view requested, break after first
        if save_path and len(viewpoints) == 1:
            break


def main():
    parser = argparse.ArgumentParser(description="Well Trajectory Optimization Result Visualization")
    
    # Target point and wellhead
    parser.add_argument("--target-e", type=float, default=502.64, help="Target point East coordinate")
    parser.add_argument("--target-n", type=float, default=790.71, help="Target point North coordinate")
    parser.add_argument("--target-d", type=float, default=2636.06, help="Target point Depth")
    parser.add_argument("--wellhead", type=str, default="254.0,2030.0,0.0",
                       help="Wellhead coordinates e,n,d")
    
    # Existing wells
    parser.add_argument("--excel-files", nargs="*", default=None,
                       help="List of existing well Excel files")
    parser.add_argument("--wellhead-positions", nargs="*", default=None,
                       help="List of existing well wellhead positions, format: e1,n1,d1 e2,n2,d2")
    
    # Optimal parameters
    parser.add_argument("--optimal-params", type=str, required=True,
                       help="Optimal parameters, format: D_kop,alpha1,alpha2,phi1,phi2,R1,R2,D_turn_kop")
    
    # Output options
    parser.add_argument("--save-path", type=str, default=None,
                       help="Save path (optional)")
    parser.add_argument("--no-show", action="store_true",
                       help="Do not display plot (save only)")
    parser.add_argument("--no-param-info", action="store_true",
                       help="Do not show parameter information plot")
    
    args = parser.parse_args()
    
    # Parse wellhead position
    wellhead = parse_triplet(args.wellhead)
    
    # Calculate relative target point
    relative_target = (
        args.target_e - wellhead[0],
        args.target_n - wellhead[1],
        args.target_d - wellhead[2],
    )
    
    # Create configuration
    config = WellTrajectoryConfig(
        E_target=relative_target[0],
        N_target=relative_target[1],
        D_target=relative_target[2],
        E_wellhead=wellhead[0],
        N_wellhead=wellhead[1],
        D_wellhead=wellhead[2],
    )
    
    # Create existing well obstacles
    well_obstacles = []
    if args.excel_files and args.wellhead_positions:
        obstacle_wellheads = [parse_triplet(pos) for pos in args.wellhead_positions]
        well_obstacles = create_multiple_well_obstacles(
            args.excel_files,
            wellhead_positions=obstacle_wellheads,
            safety_radius=10.0,
            segment_length=150.0,
        )
        print(f"✅ Loaded {len(well_obstacles)} existing wells")
    
    # Parse optimal parameters
    optimal_params = [float(x) for x in args.optimal_params.split(",")]
    if len(optimal_params) != 8:
        raise ValueError(f"Parameter count error: expected 8 parameters, got {len(optimal_params)}")
    
    print(f"\nOptimal Parameters:")
    for name, value in zip(PARAM_NAMES, optimal_params):
        print(f"  {name}: {value:.6f}")
    
    # Visualize
    visualize_optimization_result(
        optimal_params=optimal_params,
        config=config,
        well_obstacles=well_obstacles,
        wellhead_position=wellhead,
        save_path=args.save_path,
        show=not args.no_show,
        show_parameter_info=not args.no_param_info,
    )


if __name__ == "__main__":
    main()

