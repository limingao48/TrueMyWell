import numpy as np
from Variable import *
from GA_optiGAN import GA_optiGAN_min
from WellPathCalculator import WellPathCalculator
import math
import matplotlib.pyplot as plt
def plot_trajectory_obstacles(x,y,z,obstacles,config):

    x1, x2, x3, x4, x5 = x[:100], x[100:200], x[200:300], x[300:400], x[400:500]
    y1, y2, y3, y4, y5 = y[:100], y[100:200], y[200:300], y[300:400], y[400:500]
    z1, z2, z3, z4, z5 = z[:100], z[100:200], z[200:300], z[300:400], z[400:500]

    junction_points = [
        (x1[-1], y1[-1], z1[-1]),
        (x2[-1], y2[-1], z2[-1]),
        (x3[-1], y3[-1], z3[-1]),
        (x4[-1], y4[-1], z4[-1]),
        # (x5[-1], y5[-1], z5[-1])
    ]

    segment_start_points = [
        (x1[0], y1[0], z1[0]),
        (x2[0], y2[0], z2[0]),
        (x3[0], y3[0], z3[0]),
        (x4[0], y4[0], z4[0]),
        (x5[0], y5[0], z5[0])
    ]
    segment_end_points = [
        (x1[-1], y1[-1], z1[-1]),
        (x2[-1], y2[-1], z2[-1]),
        (x3[-1], y3[-1], z3[-1]),
        (x4[-1], y4[-1], z4[-1]),
        (x5[-1], y5[-1], z5[-1])
    ]

    
    viewpoints = [
        (30, 120),
        (45, 60),
        (60, 270),
        (20, 180)
    ]
    segment_colors = ['red', 'green', 'blue', 'orange', 'purple']
    segment_labels = ['Vertical', 'Build', 'Tangent 1', 'Turn', 'Tangent 2']
    for i, (elev, azim) in enumerate(viewpoints):
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')
        ax.plot(x1, y1, -z1, color=segment_colors[0], label=segment_labels[0])
        ax.plot(x2, y2, -z2, color=segment_colors[1], label=segment_labels[1])
        ax.plot(x3, y3, -z3, color=segment_colors[2], label=segment_labels[2])
        ax.plot(x4, y4, -z4, color=segment_colors[3], label=segment_labels[3])
        ax.plot(x5, y5, -z5, color=segment_colors[4], label=segment_labels[4])

        ax.scatter(config.E_wellhead, config.N_wellhead, config.D_wellhead, c='red', s=50, label='Wellhead')
        ax.scatter(config.E_target, config.N_target, -config.D_target, c='green', s=50, label='Target')\

        for obstacle in obstacles:
            center_x, center_y, center_z = obstacle["center"]
            radius = obstacle["radius"]
            
            u = np.linspace(0, 2 * np.pi, 100)
            v = np.linspace(0, np.pi, 100)
            X = center_x + radius * np.outer(np.cos(u), np.sin(v))
            Y = center_y + radius * np.outer(np.sin(u), np.sin(v))
            Z = center_z + radius * np.outer(np.ones(np.size(u)), np.cos(v))
            
            ax.plot_surface(X, Y, -Z, color='red', alpha=0.3, linewidth=0)
            
            ax.plot_wireframe(X, Y, -Z, color='red', alpha=0.1, linewidth=0.5)


        ax.set_xlabel('East (m)')
        ax.set_ylabel('North (m)')
        ax.set_zlabel('Depth (m)')

        ax.view_init(elev=elev, azim=azim)
        ax.dist = 10 

        all_x = np.concatenate([x1, x2, x3, x4, x5, [0, config.E_target], [p[0] for p in junction_points]])
        all_y = np.concatenate([y1, y2, y3, y4, y5, [0, config.N_target], [p[1] for p in junction_points]])
        all_z = np.concatenate([-z1, -z2, -z3, -z4, -z5, [0, -config.D_target], [-p[2] for p in junction_points]])

        min_val = min(np.min(all_x), np.min(all_y), np.min(all_z))
        max_val = max(np.max(all_x), np.max(all_y), np.max(all_z))

        ax.legend()
        plt.title(f'3D Well Trajectory (Elev: {elev}, Azim: {azim})')

       
        plt.savefig(f'/obstacle_well_trajectory_view_full_v1{i}.png')

        ax.set_xlim([min_val, max_val])
        ax.set_ylim([min_val, max_val])
        ax.set_zlim([min_val, max_val])

        ax.legend()
        plt.title(f'3D Well Trajectory (Elev: {elev}, Azim: {azim})')

        plt.savefig(f'well_trajectory_view_full_v2{i}.png')
        plt.close()
    return x, y, z, junction_points, segment_start_points, segment_end_points
def generate_obstacles(config):
        obstacles = []
        for _ in range(config.obstacle_count):
            x = random.uniform(*config.obstacle_x_range)
            y = random.uniform(*config.obstacle_y_range)
            z = random.uniform(*config.obstacle_z_range)
            radius = random.uniform(config.obstacle_min_radius, config.obstacle_max_radius)
            obstacles.append({
                "center": (x, y, z),
                "radius": radius
            })
        return obstacles
def distance_to_obstacle(point, obstacle):
    x, y, z = point
    center_x, center_y, center_z = obstacle["center"]
    radius = obstacle["radius"]
    
    dx = x - center_x
    dy = y - center_y
    dz = z - center_z
    distance = math.sqrt(dx**2 + dy**2 + dz**2)
    
    return distance - radius

class myWellboreConfig:
    def __init__(self,E_target,N_target,D_target):
        self.E_wellhead = 0
        self.N_wellhead = 0
        self.D_wellhead = 0
        
        self.E_target = E_target
        self.N_target = N_target
        self.D_target = D_target
        self.obstacle_count = 30  
        self.obstacle_min_radius = 50.0 
        self.obstacle_max_radius = 50.0 
        self.obstacle_x_range = (0, 1500) 
        self.obstacle_y_range = (0, 1500)  
        self.obstacle_z_range = (1600, 3000)  
        self.TOLERANCE = 10.0
def check_collision(trajectory, obstacles):
    x, y, z = trajectory
    points = zip(x, y, z)
    
    for point in points:
        for obstacle in obstacles:
            dist = distance_to_obstacle(point, obstacle)
            if dist <= 0: 
                return True  

myconfig = myWellboreConfig(1500.64,1200.71,2936.06)
original_obstacles = generate_obstacles(myconfig)
calculator = WellPathCalculator(myconfig)

def objective_function(position_tuple):
    E_target = 1500.64
    N_target = 1200.71
    D_target = 2936.06
    if position_tuple[0]>position_tuple[7]:
        return 1e20
    points, total_length, flag,loss =  calculator.calculate_coordinates(position_tuple)
    penal =0
    if loss > 0:
        penal += 1e20
        return penal
    is_collision = check_collision(points,original_obstacles)
    if is_collision:
        penal += 1e20
        return penal
    final_point = (points[0][-1],points[1][-1],points[2][-1])
   
    target_deviation = np.sqrt(
            (final_point[0] - E_target)**2 +
            (final_point[1] - N_target)**2 +
            (final_point[2] - D_target)**2
        )
    if target_deviation > 30:
        target_deviation = target_deviation*100000
    
    penal =  target_deviation + total_length
    return penal

def problem_WellPathOptimization(samples):
    
    
    fitness = objective_function(samples)
    return fitness

def run(func, ins, dimension, algo):
    config_init = Dict(hyperparameter_defaults)
    problem = Problem(problem_WellPathOptimization)
    upper = well_path_params.BOUNDS[:, 1]
    lower = well_path_params.BOUNDS[:, 0]

    config_wandb = Dict(
        {
            "upper": upper,
            "lower": lower,
            "lambda2": config_init.lambda2,
            "opt_size": config_init.opt_size,
            "pop_size": config_init.pop_size,
            "gamma": config_init.gamma,
            "MAXFes": config_init.MAXFes,
            "dimension": dimension,
        }
    )

    fun_id = func + "_i" + str(ins)
    print("--> algorithm %s on function %s ***" % (algo, fun_id + "_" + str(dimension)))
    
    fmin = GA_optiGAN_min(
            problem,
            config_init,
            config_wandb,
            fun_id + "_d" + str(dimension),
            setup_seed(int(ins)),
        )
    (x,y,z), total_length, flag,loss =  calculator.calculate_coordinates(fmin[4])
    plot_trajectory_obstacles(x,y,z,original_obstacles,myconfig)

if __name__ == "__main__":
    func = args.func_id
    ins = args.func_ins
    dim = args.func_dim
    algo = args.func_alg
    run(func, ins, dim, algo)