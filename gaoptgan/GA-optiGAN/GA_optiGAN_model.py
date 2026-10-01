import numpy as np
import torch
import torch.autograd as autograd
import torch.nn as nn

from Variable import *

my_device = "cpu"
class Discriminator(nn.Module):
    def __init__(self, in_nodes, hidden_nodes, out_nodes):
        super(Discriminator, self).__init__()
        modules = []
        in_dim = in_nodes
        for h_dim in hidden_nodes:
            modules.append(nn.Sequential(nn.Linear(in_dim, h_dim), nn.LeakyReLU()))
            in_dim = h_dim
        modules.append(nn.Sequential(nn.Linear(in_dim, out_nodes)))
        self.net = nn.Sequential(*modules)
        self.device = torch.device(my_device)
        self.to(self.device)

    def forward(self, x):
        x = x.to(self.device)
        for name, module in self.named_modules():
            if isinstance(module, nn.Linear):
                if module.weight.device != self.device:
                    print(f"linear layer {name} weight is in {module.weight.device} 上")
                if module.bias is not None and module.bias.device != self.device:
                    print(f"linear layer {name} weight is in {module.bias.device} 上")
        return self.net(x)

    def gradient_penalty(self, x_real, x_fake, LAMBDA=10):
        alpha = torch.rand(x_real.size(), device=x_real.device)
        x_fake = x_fake.to(x_real.device)
        
        interpolates = alpha * x_real + ((1 - alpha) * x_fake)
        interpolates = interpolates.to(device)
        interpolates = autograd.Variable(interpolates, requires_grad=True)
        disc_interpolates = self(interpolates)
        gradients = autograd.grad(
            outputs=disc_interpolates,
            inputs=interpolates,
            grad_outputs=torch.ones(disc_interpolates.size()).to(device),
            create_graph=True,
            retain_graph=True,
            only_inputs=True,
        )[0]
        gradient_penalty = ((gradients.norm(2, dim=1) - 1) ** 2).mean() * LAMBDA
        return gradient_penalty


class Generator(nn.Module):
    def __init__(self, in_nodes, hidden_nodes, out_nodes,upper,lower):
        super(Generator, self).__init__()
        modules = []
        in_dim = in_nodes
        for h_dim in hidden_nodes:
            modules.append(nn.Sequential(nn.Linear(in_dim, h_dim), nn.LeakyReLU()))
        in_dim = h_dim
        modules.append(nn.Sequential(nn.Linear(in_dim, out_nodes)))
        self.net = nn.Sequential(*modules)
    
        self.device = torch.device(my_device)
        self.lower = torch.tensor(lower, device=self.device, dtype=torch.float32)
        self.upper = torch.tensor(upper, device=self.device, dtype=torch.float32)
        self.to(self.device)

    def forward(self, x):
        x = x.to(self.device)
        output = self.net(x)
        #Use the tanh function to map the output to the range [-1, 1]
        output = torch.tanh(output)
        # Map output to [lower, upper] range by linear transformation
        output = output.detach()
        output = 0.5 * (output + 1) * (self.upper - self.lower) + self.lower
        output_float = output.float() 
        return output_float


class GA_optiGANMD:
    def __init__(
        self, batch_size, x_dim, z_dim, gen_lr, reg_lr,upper,lower, D_nodes=[50], G_nodes=[50],
    ):
        self.generator = Generator(z_dim, G_nodes, x_dim,upper,lower)
        self.discriminator_R = Discriminator(  
            x_dim, D_nodes, 1
        )
        self.discriminator_E = Discriminator(  
            x_dim, D_nodes, 1
        )

        self.g_optim = torch.optim.Adam(self.generator.parameters(), lr=gen_lr)
        self.dr_optim = torch.optim.Adam(self.discriminator_R.parameters(), lr=reg_lr)
        self.de_optim = torch.optim.Adam(
            self.discriminator_E.parameters(), lr=reg_lr
        )

        self.batch_size = batch_size
        self.x_dim = x_dim
        self.z_dim = z_dim

    def train(self, data, data_cv, epochs, d_iter, upper, lower, lambda1=0, lambda2=0,
              enable_exploitation=True, train_feasible_only=True, min_feasible_for_dr=2):
        d_real_loss = torch.tensor(0.0)
        d_fake_loss = torch.tensor(0.0)
        D_LOSS = torch.tensor(0.0)
        g_d_loss = torch.tensor(0.0)

        cv_arr = None
        if data_cv is not None:
            cv_arr = np.asarray(data_cv, dtype=np.float64).reshape(-1)
            feasible_idx = np.where(cv_arr <= CV_FEASIBLE_TOL)[0]
            if train_feasible_only and enable_exploitation and len(feasible_idx) >= min_feasible_for_dr:
                exploit_data = data[feasible_idx, :]
            else:
                exploit_data = data
        else:
            exploit_data = data

        for epoch in range(epochs):
            for iters in range(d_iter):
                z_data = torch.rand(self.batch_size, self.z_dim) * 2 - 1
                fake_data = self.generator(z_data).data

                self.de_optim.zero_grad()
                gd_uniform_data = (
                    torch.rand((self.batch_size, self.x_dim)) * (upper - lower) + lower
                ).float()
                gd_real_loss = self.discriminator_E(gd_uniform_data)
                gd_fake_loss = self.discriminator_E(fake_data)
                gd_gp_loss = self.discriminator_E.gradient_penalty(
                    gd_uniform_data, fake_data
                )
                GD_LOSS = (
                    -torch.mean(gd_real_loss) + torch.mean(gd_fake_loss) + gd_gp_loss
                )
                GD_LOSS.backward()
                self.de_optim.step()

                if enable_exploitation and exploit_data.size()[0] > 0:
                    sam_ind = np.random.choice(
                        a=exploit_data.size()[0],
                        size=self.batch_size,
                        replace=True,
                    )
                    real_data = exploit_data[sam_ind, :]
                    d_real_loss = self.discriminator_R(real_data)
                    d_fake_loss = self.discriminator_R(fake_data)
                    d_gp_loss = self.discriminator_R.gradient_penalty(real_data, fake_data)
                    D_LOSS = -torch.mean(d_real_loss) + torch.mean(d_fake_loss) + d_gp_loss

                    self.dr_optim.zero_grad()
                    D_LOSS.backward()
                    self.dr_optim.step()

            ## train Generator
            self.g_optim.zero_grad()
            z_data = torch.rand(self.batch_size, self.z_dim) * 2 - 1
            fake_data = self.generator(z_data)
            g_gd_loss = self.discriminator_E(fake_data)
            if enable_exploitation:
                g_d_loss = self.discriminator_R(fake_data)
                G_LOSS = -torch.mean(g_d_loss) - lambda2 * torch.mean(g_gd_loss)
            else:
                g_d_loss = torch.tensor(0.0)
                G_LOSS = -torch.mean(g_gd_loss)
            G_LOSS.backward()
            self.g_optim.step()

        NN_dict = Dict(
            {
                "D1_loss": D_LOSS.item() if enable_exploitation else 0.0,
                "D1_real": torch.mean(d_real_loss).item() if enable_exploitation else 0.0,
                "D1_fake": torch.mean(d_fake_loss).item() if enable_exploitation else 0.0,
                "D1_Wasserstein": (
                    (torch.mean(d_real_loss) - torch.mean(d_fake_loss)).item()
                    if enable_exploitation else 0.0
                ),
                "D2_loss": GD_LOSS.item(),
                "D2_real": torch.mean(gd_real_loss).item(),
                "D2_fake": torch.mean(gd_fake_loss).item(),
                "D2_Wasserstein": (
                    torch.mean(gd_real_loss) - torch.mean(gd_fake_loss)
                ).item(),
                "G_loss": G_LOSS.item(),
                "G_D1_loss": torch.mean(g_d_loss).item() if enable_exploitation else 0.0,
                "G_D2_loss": torch.mean(g_gd_loss).item(),
            }
        )
        return NN_dict

    def pretrain(self, epochs, upper, lower):
        for epoch in range(epochs):
            z_data = torch.rand(self.batch_size, self.z_dim) * 2 - 1
            fake_data = self.generator(z_data).data
            ## train Exploration Discriminator
            self.de_optim.zero_grad()
            gd_uniform_data = (
                torch.rand((self.batch_size, self.x_dim)) * (upper - lower) + lower
            ).float()
            gd_real_loss = self.discriminator_E(gd_uniform_data)
            gd_fake_loss = self.discriminator_E(fake_data)
      
            gd_uniform_data = gd_uniform_data.to(device)
            fake_data = fake_data.to(device)
            gd_gp_loss = self.discriminator_E.gradient_penalty(
                gd_uniform_data, fake_data
            )
            GD_LOSS = -torch.mean(gd_real_loss) + torch.mean(gd_fake_loss) + gd_gp_loss
            GD_LOSS.backward()
            self.de_optim.step()

            ## train Generator
            self.g_optim.zero_grad()
            z_data = torch.rand(self.batch_size, self.z_dim) * 2 - 1
            fake_data = self.generator(z_data)
            g_gd_loss = self.discriminator_E(fake_data)
            G_LOSS = -torch.mean(g_gd_loss)
            G_LOSS.backward()
      
            self.g_optim.step()

    def weights_init(self):
        def weights_init(m):
            if isinstance(m, nn.Linear):
                m.weight.data.normal_(0, 0.2)
                m.bias.data.zero_()

        self.discriminator.apply(weights_init)
        self.generator.apply(weights_init)
        self.discriminator_E.apply(weights_init)
        [eld.apply(weights_init) for eld in self.encoder_latent_discriminators]


def update_data_compare(
    fake_data, fake_fitness, fake_cv, data, fitness, cv, train_data_show, ADD_SIZE
):
    fake_fitness_clear = np.unique(fake_fitness.reshape(-1))
    index = 0
    for i in range(min(ADD_SIZE, len(fake_fitness_clear))):
        cand_fit = float(fake_fitness_clear[i])
        cand_rows = np.argwhere(np.isclose(fake_fitness.reshape(-1), cand_fit)).reshape(-1)
        if cand_rows.size == 0:
            continue
        cand_idx = int(cand_rows[0])
        cand_cv = float(fake_cv[cand_idx, 0])

        worst_idx = None
        worst_fit = None
        worst_cv = None
        for j in range(len(fitness)):
            fj = float(fitness[j, 0])
            cj = float(cv[j, 0])
            if worst_idx is None or _constraint_better(fj, cj, worst_fit, worst_cv):
                worst_idx = j
                worst_fit = fj
                worst_cv = cj

        if worst_idx is not None and _constraint_better(cand_fit, cand_cv, worst_fit, worst_cv):
            index += 1
            data[worst_idx, :] = fake_data[cand_idx, :]
            train_data_show[worst_idx, :] = fake_data[cand_idx, :]
            fitness[worst_idx, 0] = cand_fit
            cv[worst_idx, 0] = cand_cv

    return data, fitness, cv, train_data_show, index


def _constraint_better(f1, c1, f2, c2, tol=CV_FEASIBLE_TOL):
    feas1 = float(c1) <= tol
    feas2 = float(c2) <= tol
    if feas1 and not feas2:
        return True
    if feas2 and not feas1:
        return False
    if feas1 and feas2:
        return float(f1) < float(f2)
    c1, c2 = float(c1), float(c2)
    if abs(c1 - c2) > tol:
        return c1 < c2
    return float(f1) < float(f2)


def update_data_compare_init(fake_data, fake_fitness, data, fitness, epoch):
    ADD_SIZE = fake_data.size()[0]
    data[(epoch * ADD_SIZE) : ((epoch + 1) * ADD_SIZE), :] = fake_data
    fitness[(epoch * ADD_SIZE) : ((epoch + 1) * ADD_SIZE), :] = fake_fitness
    return data, fitness


def print_flag(
    stop, figurepath, evaluations, bestf, distance, mean_bestf, DIMENSION, config
):
    string = ""
    if evaluations >= config.MAXFes:
        stop = True
        print("Equal MAXFes,fitness=%.2e" % (bestf))
        figurepath = figurepath + "/fail_fes" + str(bestf)
        string = "fail_fes"
    return figurepath, stop, string
