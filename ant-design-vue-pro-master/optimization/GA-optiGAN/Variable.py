import torch, random
import os
import numpy as np
import argparse
from scipy.spatial.distance import pdist

def setup_seed(seed):
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    random.seed(seed)
    torch.backends.cudnn.deterministic = True

parser = argparse.ArgumentParser(description="manual to this script")

parser.add_argument("--gamma", type=float, default=1.5)
parser.add_argument("--lambda2", type=float, default=0.3)
parser.add_argument("--pop", type=int, default=30)
parser.add_argument("--optset", type=int, default=150)
parser.add_argument("--func_dim", type=int, default="8")
parser.add_argument("--func_ins", type=int, default="0")
parser.add_argument("--func_id", type=str, default="WellTrajectoryDesignParameterOptimization")
parser.add_argument("--func_alg", type=str, default="GA-optiGAN")
parser.add_argument("--maxfes", type=int, default=300000)

args = parser.parse_args()

# device = torch.device("cuda")
device = torch.device("cpu")
hyperparameter_defaults = dict(
    MAXFes=args.maxfes,
    gen_lr=0.0003,
    reg_lr=0.005,
    D_nodes=[256,],
    G_nodes=[256,],
    latent_dim=5,
    encoder_num=0,
    lambda1=[1],
    lambda2=args.lambda2,
    batch_size=30,
    D_iter=4,
    epochs=150,
    pretrain=1,
    pop_size=args.pop,
    opt_size=args.optset,
    gamma=args.gamma,
    gen_n = 10,
    elite_ratio = 0.5
)

# para:show
En_SCALE = False
ENABLE_LOGGING = True

class Dict(dict):
    __setattr__ = dict.__setitem__
    __getattr__ = dict.__getitem__

class Convert(object):
    def __init__(self, samples):
        self.samples = samples

    def to_var(self):
        self.samples = torch.Tensor(self.samples)
        if torch.cuda.is_available():
            self.samples = self.samples.to(device)
        return self.samples

    def to_np(self):
        if self.samples.device == "cpu":
            return self.samples.numpy()
        else:
            return self.samples.data.cpu().numpy()

    def zscore(self):
        x_mean = np.mean(self.samples, 0)
        x_std = np.std(self.samples, 0)
        x_new = (self.samples - x_mean) / x_std
        return x_new, x_mean, x_std

    def reduction(self, para_dict):
        return self.samples * (para_dict.upper - para_dict.lower) + para_dict.lower
# todo old
# def init_history(problem, para_dict):
#     fitness_history = np.zeros((para_dict.init_size, 1))
#     data_history = np.random.rand(para_dict.init_size, para_dict.DIMENSION)
#     data_history = Convert(data_history).reduction(para_dict)
#     print(data_history)
#     print(data_history.shape)
#     print(sadasdas)
#     # print(data_history.shape)
#     for i in range(para_dict.init_size):
#         fitness_history[i, :] = problem(data_history[i, :])
#     return data_history.astype(np.float32), fitness_history.astype(np.float32)
def init_history(problem, para_dict):
    """Initialize the optimal solution set, combine boundary sampling and random sampling strategies"""
    fitness_history = np.zeros((para_dict.init_size, 1))
    data_history = []
    
    # Get search space boundaries
    bounds = np.array([para_dict.lower, para_dict.upper]).T
    dim = para_dict.DIMENSION
    init_size = para_dict.init_size
    boundary_count = init_size // 5
    for _ in range(boundary_count):
        lower_bound = bounds[:, 0]
        lower_noise = np.random.rand(dim) * 0.1 * (bounds[:, 1] - bounds[:, 0])
        lower_indiv = lower_bound + lower_noise
        data_history.append(lower_indiv)
        
        upper_bound = bounds[:, 1]
        upper_noise = np.random.rand(dim) * 0.1 * (bounds[:, 1] - bounds[:, 0])
        upper_indiv = upper_bound - upper_noise
        data_history.append(upper_indiv)

    #  Generate random solutions and verify validity
    while len(data_history) < init_size:
        indiv = np.array([np.random.uniform(low, high) for low, high in bounds])
        data_history.append(indiv)
    
    data_history = np.array(data_history)
    
    for i in range(init_size):
        fitness_history[i, :] = problem(data_history[i, :])
    return data_history.astype(np.float32), fitness_history.astype(np.float32)
def fitnessf(problem, x):
    size = x.shape[0]
    fitness = np.zeros((size, 1))
    for i in range(size):
        fitness[i, :] = problem(x[i, :])
    return fitness

def min_distance(data, size):
    x = data
    x1 = pdist(x)
    x2 = np.sort(x1)[0:size]
    x3 = np.mean(x2)

    return x3

class Problem:
    def __init__(self, func):
        self.maxFes = 0
        self.solutions = []
        self.fitness = []
        self.func = func

    def __call__(self, x):
        self.maxFes += 1
        self.solutions.append(x)
        fit = self.func(x)
        self.fitness.append(fit)
        return fit

class WellPathParams:
    def __init__(self):
        self.E_wellhead = 0 #East coordinate (m)
        self.N_wellhead = 0 #North coordinate (m)
        self.D_wellhead = 0 #Depth (m)
        self.E_target = 1500.64 #East coordinate of target (m)
        self.N_target = 1200.71 #North coordinate of target (m)
        self.D_target = 2936.06 #Target Depth (m)
        self.D_kop_min = 1200 #minimum vertical depth of inclined point
        self.D_kop_max = 1500 #maximum vertical depth of inclined point
        self.alpha_1_min = 0 #Minimum value of inclination angle at the end of inclination increasing section
        self.alpha_1_max = 90 #Maximum inclination angle at the end of the increasing inclination section
        self.alpha_2_min = 85 #minimum inclination angle at the end of the second ramp
        self.alpha_2_max = 92 #Maximum well angle at the end of the second ramp
        self.phi_1_min = 0 #minimum azimuth at the end of the ramp
        self.phi_1_max = 210 #maximum azimuth at the end of the ramp
        self.phi_2_min = 0 #Minimum azimuth at the end of the second ramp
        self.phi_2_max = 210 #Maximum azimuth at the end of the second ramp
        self.R_1_min = 343 #The minimum value of the ramp section corresponds to the maximum slope of 5 °/30m
        self.R_1_max = 1718 #The minimum value of the ramp section corresponds to the maximum slope of 1 °/30m
        self.R_2_min = 343 #Minimum radius of curvature of the second ramp segment
        self.R_2_max = 1718 #Maximum radius of curvature of the second ramp segment
        self.D_turn_kop_min = 1500 #minimum vertical depth of the second inclined segment
        self.D_turn_kop_max = 2600 #Maximum vertical depth of the second inclined segment
        self.BOUNDS = np.array([
            [self.D_kop_min, self.D_kop_max],
            [self.alpha_1_min, self.alpha_1_max],
            [self.alpha_2_min, self.alpha_2_max],
            [self.phi_1_min, self.phi_1_max],
            [self.phi_2_min, self.phi_2_max],
            [self.R_1_min, self.R_1_max],
            [self.R_2_min, self.R_2_max],
            [self.D_turn_kop_min, self.D_turn_kop_max]
        ])

well_path_params = WellPathParams()