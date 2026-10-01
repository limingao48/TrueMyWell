import numpy as np
import math

class WellPathCalculator:
    
    def __init__(self, config):
        self.config = config
        
    def calculate_lengths(self, D_kop, alpha_1, alpha_2, phi_1, phi_2, R_1, R_2, D_turn_kop):
        gamma = math.acos(
            math.cos(alpha_1) * math.cos(alpha_2) +
            math.sin(alpha_1) * math.sin(alpha_2) * math.cos(phi_2 - phi_1)
        )
        gamma_half = gamma / 2

        lengths = {
            'vertical': D_kop,
            'build': R_1 * alpha_1,
            'tangent1': 0,
            'turn': R_2 * gamma
        }

        delta_D_build = R_1 * (1 - math.cos(alpha_1))
        remaining_D = D_turn_kop - D_kop - delta_D_build

        if remaining_D < 0:
            return None,remaining_D*(-1000)

        RF = 2 * math.tan(gamma_half) / gamma if gamma != 0 else 1 
        delta_D_turn = R_2 * (math.cos(alpha_1) + math.cos(alpha_2)) * RF / 2

        lengths['tangent1'] = remaining_D / math.cos(alpha_1)

        max_iterations = 500
        for _ in range(max_iterations):
            final_D = D_kop + delta_D_build + lengths['tangent1'] * math.cos(alpha_1)
            depth_error = final_D - D_turn_kop

            if abs(depth_error) < self.config.TOLERANCE:
                break

            if depth_error > 0:
                if lengths['tangent1'] > 0:
                    lengths['tangent1'] -= depth_error / math.cos(alpha_1)
            else:
                lengths['tangent1'] += abs(depth_error) / math.cos(alpha_1)

            if lengths['tangent1'] < 0:
                lengths['tangent1'] = 0

        remaining_to_target = self.config.D_target - D_turn_kop - delta_D_turn
        if remaining_to_target < 0:
            return None,remaining_to_target*(-1000)

        lengths['tangent2'] = remaining_to_target / math.cos(alpha_2)

        return lengths,0
    
    def calculate_build_coords(self, alpha_start, alpha_end, phi, R, length, n_points):
        alpha = np.linspace(alpha_start, alpha_end, n_points)
        dl = length / (n_points - 1)
        x = np.zeros(n_points)
        y = np.zeros(n_points)
        z = np.zeros(n_points)
        for i in range(1, n_points):
            delta_alpha = alpha[i] - alpha[i - 1]
            delta_N = R * (np.cos(alpha[i - 1]) - np.cos(alpha[i])) * np.cos(phi)
            delta_E = R * (np.cos(alpha[i - 1]) - np.cos(alpha[i])) * np.sin(phi)
            delta_V = R * (np.sin(alpha[i]) - np.sin(alpha[i - 1]))
            x[i] = x[i - 1] + delta_E
            y[i] = y[i - 1] + delta_N
            z[i] = z[i - 1] + delta_V
        return x, y, z

    def calculate_tangent_coords(self, alpha, phi, length, n_points):
        dl = length / (n_points - 1)
        x = np.zeros(n_points)
        y = np.zeros(n_points)
        z = np.zeros(n_points)
        for i in range(1, n_points):
            delta_N = dl * np.sin(alpha) * np.cos(phi)
            delta_E = dl * np.sin(alpha) * np.sin(phi)
            delta_V = dl * np.cos(alpha)
            x[i] = x[i - 1] + delta_E
            y[i] = y[i - 1] + delta_N
            z[i] = z[i - 1] + delta_V
        return x, y, z

    def calculate_turn_coords(self, alpha_start, alpha_end, phi_start, phi_end, R, length, n_points):
        alpha = np.linspace(alpha_start, alpha_end, n_points)
        phi = np.linspace(phi_start, phi_end, n_points)
        dl = length / (n_points - 1)
        x = np.zeros(n_points)
        y = np.zeros(n_points)
        z = np.zeros(n_points)
        for i in range(1, n_points):
            alpha_avg = 0.5*(alpha[i-1] + alpha[i])
            phi_avg = 0.5*(phi[i-1] + phi[i])
            
            delta_N = dl * np.sin(alpha_avg) * np.cos(phi_avg)
            delta_E = dl * np.sin(alpha_avg) * np.sin(phi_avg)
            delta_V = dl * np.cos(alpha_avg)
            
            x[i] = x[i-1] + delta_E
            y[i] = y[i-1] + delta_N
            z[i] = z[i-1] + delta_V
        return x, y, z
    
    def calculate_coordinates(self, position_tuple):
       
        D_kop, alpha1, alpha2, phi1, phi2, R1, R2, D_turn_kop = position_tuple
        alpha1_rad = np.radians(alpha1)
        alpha2_rad = np.radians(alpha2)
        phi1_rad = np.radians(phi1)
        phi2_rad = np.radians(phi2)

        n_points = 100

        x_vertical = np.zeros(n_points)
        y_vertical = np.zeros(n_points)
        x_vertical += self.config.E_wellhead
        y_vertical += self.config.N_wellhead
        z_vertical = np.linspace(0, D_kop, n_points)

        length_build = R1 * alpha1_rad
        x_build, y_build, z_build = self.calculate_build_coords(0, alpha1_rad, phi1_rad, R1, length_build, n_points)
        x_build += x_vertical[-1]
        y_build += y_vertical[-1]
        z_build += D_kop
        
        delta_D_build = R1 * (1 - np.cos(alpha1_rad))
        remaining_D = D_turn_kop - D_kop - delta_D_build
        if remaining_D < 0:
            return None, 10000,False, remaining_D * (-1000)

        L3 = remaining_D / np.cos(alpha1_rad)
        x_tangent, y_tangent, z_tangent = self.calculate_tangent_coords(alpha1_rad, phi1_rad, L3, n_points)
        x_tangent += x_build[-1]
        y_tangent += y_build[-1]
        z_tangent += z_build[-1]
        if abs(z_tangent[-1] - D_turn_kop) > self.config.TOLERANCE:
            length_error = D_turn_kop - z_tangent[-1]
            L3 += length_error / np.cos(alpha1_rad) 
            x_tangent, y_tangent, z_tangent = self.calculate_tangent_coords(alpha1_rad, phi1_rad, L3, n_points)
            x_tangent += x_build[-1]
            y_tangent += y_build[-1]
            z_tangent += z_build[-1]

        z_turn_start = z_tangent[-1]
        x_turn_start = x_tangent[-1]
        y_turn_start = y_tangent[-1]

        gamma = np.arccos(np.cos(alpha1_rad) * np.cos(alpha2_rad) +
                          np.sin(alpha1_rad) * np.sin(alpha2_rad) * np.cos(phi2_rad - phi1_rad))
        L4 = R2 * gamma

        x_turn, y_turn, z_turn = self.calculate_turn_coords(alpha1_rad, alpha2_rad, phi1_rad, phi2_rad, R2, L4, n_points)
        z_turn += z_turn_start  
        x_turn += x_turn_start
        y_turn += y_turn_start
        
        lengths,loss = self.calculate_lengths(D_kop, alpha1_rad, alpha2_rad, phi1_rad, phi2_rad, R1, R2, D_turn_kop)
        if lengths is None:
            return None,10000 ,False, loss * (1000)
        L5 = lengths.get('tangent2', 0)
        x_tangent2, y_tangent2, z_tangent2 = self.calculate_tangent_coords(alpha2_rad, phi2_rad, L5, n_points)
        x_tangent2 += x_turn[-1]
        y_tangent2 += y_turn[-1]
        z_tangent2 += z_turn[-1]

        x = np.concatenate([x_vertical, x_build, x_tangent, x_turn, x_tangent2])
        y = np.concatenate([y_vertical, y_build, y_tangent, y_turn, y_tangent2])
        z = np.concatenate([z_vertical, z_build, z_tangent, z_turn, z_tangent2])
        
        segment_start_points = [
            (x_vertical[0], y_vertical[0], z_vertical[0]),
            (x_build[0], y_build[0], z_build[0]),
            (x_tangent[0], y_tangent[0], z_tangent[0]),
            (x_turn[0], y_turn[0], z_turn[0]),
            (x_tangent2[0], y_tangent2[0], z_tangent2[0])
        ]
        
        segment_end_points = [
            (x_vertical[-1], y_vertical[-1], z_vertical[-1]),
            (x_build[-1], y_build[-1], z_build[-1]),
            (x_tangent[-1], y_tangent[-1], z_tangent[-1]),
            (x_turn[-1], y_turn[-1], z_turn[-1]),
            (x_tangent2[-1], y_tangent2[-1], z_tangent2[-1])
        ]
        lengths = {
            'vertical': D_kop,
            'build': R1 * alpha1_rad,
            'tangent1': L3,
            'turn': L4,
            'tangent2': L5
        }
        total_length = sum(lengths.values())
        
        total_N = y[-1]
        total_E = x[-1]
        total_D = z[-1]
        
        junction_points = segment_start_points[1:]
        
        return (x, y, z),total_length,True,0