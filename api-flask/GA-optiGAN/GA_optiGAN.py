import csv
import os
import time
from typing import Dict as TypingDict, List, Tuple

import matplotlib
import numpy as np
import torch

from GA_optiGAN_model import *  # noqa: F403
from Variable import *  # noqa: F403

matplotlib.use("Agg")


# =========================
# Utility helpers
# =========================


def _as_bounds(para_dict):
    bounds = np.array([para_dict.lower, para_dict.upper]).T
    return bounds[:, 0], bounds[:, 1], np.maximum(bounds[:, 1] - bounds[:, 0], 1e-8)


def _clip_to_bounds(x: np.ndarray, para_dict) -> np.ndarray:
    lower, upper, _ = _as_bounds(para_dict)
    return np.clip(x, lower, upper)


def _evaluate_population_with_cache(problem, population: np.ndarray, cache: dict) -> np.ndarray:
    """Evaluate population with memoization to avoid repeated expensive calls."""
    fitness = np.zeros((population.shape[0], 1), dtype=np.float32)
    for i, ind in enumerate(population):
        key = tuple(np.round(ind.astype(np.float64), 6))
        if key in cache:
            value = cache[key]
        else:
            value = float(problem(ind))
            cache[key] = value
        fitness[i, 0] = value
    return fitness


# =========================
# Logging
# =========================


def InitLOGGING(save_csv, id):
    result_csv = open(save_csv + "/" + id + ".csv", "w", newline="")
    result_csv_writer = csv.writer(result_csv)
    result_csv_writer.writerow(
        (
            "iter",
            "fes",
            "curr_bestf",
            "bestf",
            "time",
            "distance_history",
            "distance_gen",
            "distance_train",
            "d1_loss",
            "d1_real",
            "d1_fake",
            "d1_Wdistance",
            "d2_loss",
            "d2_real",
            "d2_fake",
            "d2_Wdistance",
            "g_loss",
            "g_d1_loss",
            "g_d2_loss",
            "spread_history",
            "spread_gen",
            "spread_train",
            "best_x",
        )
    )
    result_csv.close()


def LOGGING(save_csv, id, values):
    result_csv = open(save_csv + "/" + id + ".csv", "a+", newline="")
    result_csv_writer = csv.writer(result_csv)
    result_csv_writer.writerow(values)
    result_csv.close()


def genSavePath(id, config_wandb):
    return (
        "./data_save/"
        + id
        + "lambda"
        + str(config_wandb.lambda2)
        + "_optset"
        + str(config_wandb.opt_size)
        + "_pop"
        + str(config_wandb.pop_size)
        + "_gamma"
        + str(config_wandb.gamma)
    )


# =========================
# Hybrid candidate generation
# =========================


def genetic_operations(population, para_dict, crossover_rate, mutation_rate):
    lower, upper, span = _as_bounds(para_dict)
    dim = population.shape[1]
    offspring: List[np.ndarray] = []

    for i in range(0, len(population), 2):
        if i + 1 >= len(population) or np.random.random() >= crossover_rate:
            continue

        parent1, parent2 = population[i], population[i + 1]
        alpha = np.random.rand(dim)
        child1 = alpha * parent1 + (1 - alpha) * parent2
        child2 = (1 - alpha) * parent1 + alpha * parent2
        offspring.extend([child1, child2])

    if not offspring:
        return np.empty((0, dim), dtype=np.float32)

    offspring = np.asarray(offspring, dtype=np.float32)

    # Sparse mutation with scale-aware noise
    mutate_ind = np.random.rand(offspring.shape[0]) < mutation_rate
    if np.any(mutate_ind):
        mask = (np.random.rand(*offspring.shape) < 0.2).astype(np.float32)
        noise = np.random.normal(0.0, 0.05, size=offspring.shape).astype(np.float32) * span
        offspring[mutate_ind] = offspring[mutate_ind] + mask[mutate_ind] * noise[mutate_ind]

    offspring = np.clip(offspring, lower, upper)
    return offspring


def local_hybrid_generation(
    fake_data,
    data_history,
    fitness_history,
    para_dict,
    config_init,
    epoch,
    maxfun,
    refine_mode=True,
    residual_strength=0.08,
):
    """
    Hybrid generation with optional neural refinement mode.

    - refine_mode=True: treat GAN output as residual hint around elite anchors
    - refine_mode=False: legacy projection behavior
    """
    if fake_data is None or len(fake_data) == 0:
        return fake_data

    lower, upper, span = _as_bounds(para_dict)

    elite_ratio = float(_cfg_get(config_init, "elite_ratio", 0.5))
    elite_size = max(2, int(len(data_history) * elite_ratio))
    elite_idx = np.argsort(fitness_history.reshape(-1))[:elite_size]
    elites = data_history[elite_idx]

    progress = np.clip(epoch / max(maxfun - 1, 1), 0.0, 1.0)
    trust_scale = 0.10 * (1.0 - progress) + 0.02 * progress

    anchor_idx = np.random.randint(0, elite_size, size=fake_data.shape[0])
    anchors = elites[anchor_idx]

    if refine_mode:
        # Interpret GAN output as directional hint; convert to bounded residual step.
        raw_delta = fake_data - anchors
        per_dim_cap = span * max(0.005, min(0.20, residual_strength)) * (1.2 - 0.8 * progress)
        bounded_delta = np.clip(raw_delta, -per_dim_cap, per_dim_cap)
        hybrid = anchors + bounded_delta
    else:
        # Legacy projection toward anchor.
        hybrid = anchors + trust_scale * (fake_data - anchors)

    # Sparse local mutation
    mutate_prob = 0.25 * (1.0 - progress) + 0.08 * progress
    mutate_mask = (np.random.rand(*hybrid.shape) < mutate_prob).astype(np.float32)
    noise = np.random.normal(0.0, 0.05, size=hybrid.shape).astype(np.float32) * (span * trust_scale)
    hybrid = hybrid + mutate_mask * noise

    # Small chance linear blend with anchor
    cross_mask = np.random.rand(hybrid.shape[0], 1) < 0.2
    alpha = np.random.rand(hybrid.shape[0], 1)
    mixed = alpha * hybrid + (1.0 - alpha) * anchors
    hybrid = np.where(cross_mask, mixed, hybrid)

    return np.clip(hybrid, lower, upper)


# =========================
# Main algorithm
# =========================


def _init_para_dict(config_init, config_wandb):
    return Dict(
        {
            "init_size": config_init.opt_size,
            "upper": config_wandb.upper,
            "lower": config_wandb.lower,
            "ADD_SIZE": config_init.pop_size,
            "Gnodes_in": int(config_wandb.dimension * 2),
            "DIMENSION": config_wandb.dimension,
            "D_iter": config_init.D_iter,
            "epoch": config_init.epochs,
            "pretrain": config_init.pretrain,
            "LatentDim": config_init.latent_dim,
            "Lambda1": config_init.lambda1,
            "Lambda2": config_init.lambda2,
        }
    )


def _build_module(config_init, para_dict):
    return GA_optiGANMD(  # noqa: F405
        config_init.batch_size,
        para_dict.DIMENSION,
        para_dict.Gnodes_in,
        config_init.gen_lr,
        config_init.reg_lr,
        para_dict.upper,
        para_dict.lower,
        config_init.D_nodes,
        config_init.G_nodes,
    )


def _default_nn_stats() -> TypingDict[str, float]:
    return {
        "D1_loss": 0.0,
        "D1_real": 0.0,
        "D1_fake": 0.0,
        "D1_Wasserstein": 0.0,
        "D2_loss": 0.0,
        "D2_real": 0.0,
        "D2_fake": 0.0,
        "D2_Wasserstein": 0.0,
        "G_loss": 0.0,
        "G_D1_loss": 0.0,
        "G_D2_loss": 0.0,
    }


def _cfg_get(cfg, key, default):
    """Safe getter for both dict-like config and objects."""
    if isinstance(cfg, dict):
        return cfg.get(key, default)
    try:
        return getattr(cfg, key)
    except Exception:
        return default


def _extract_nn_stats(nn_dict) -> TypingDict[str, float]:
    if nn_dict is None:
        return _default_nn_stats()
    out = _default_nn_stats()
    for k in out.keys():
        out[k] = float(getattr(nn_dict, k, out[k]))
    return out


def _train_gan_if_needed(module, train_data, para_dict, data_mean, data_std, lambda1, lambda2, train_this_epoch):
    if not train_this_epoch:
        return None

    train_score = (train_data - data_mean) / data_std
    train_data_torch = torch.Tensor(train_score).to(device)

    upper = (para_dict.upper - data_mean) / data_std
    lower = (para_dict.lower - data_mean) / data_std

    nn_dict = module.train(
        train_data_torch,
        para_dict.epoch,
        para_dict.D_iter,
        upper,
        lower,
        lambda1,
        lambda2,
    )
    return nn_dict


def _log_epoch(
    save_csv,
    problem_id,
    epoch,
    evaluations,
    curr_best,
    global_best,
    elapsed,
    distance_history,
    distance_gen,
    distance_train,
    spread_history,
    spread_gen,
    spread_train,
    bestpoint_x,
    nn_stats,
):
    LOGGING(
        save_csv,
        problem_id,
        [
            epoch + 1,
            evaluations,
            curr_best,
            global_best,
            elapsed,
            distance_history,
            distance_gen,
            distance_train,
            nn_stats["D1_loss"],
            nn_stats["D1_real"],
            nn_stats["D1_fake"],
            nn_stats["D1_Wasserstein"],
            nn_stats["D2_loss"],
            nn_stats["D2_real"],
            nn_stats["D2_fake"],
            nn_stats["D2_Wasserstein"],
            nn_stats["G_loss"],
            nn_stats["G_D1_loss"],
            nn_stats["G_D2_loss"],
            spread_history,
            spread_gen,
            spread_train,
            bestpoint_x,
        ],
    )


def GA_optiGAN_min(problem, config_init, config_wandb, problem_id, seed, landx=None, landy=None):
    # Core settings
    dim = config_wandb.dimension
    pop_size = config_init.pop_size
    maxfun = int(config_wandb.MAXFes / pop_size + 1)
    init_size = config_init.opt_size
    fin_size = config_init.MAXFes

    # New stable/fast controls (optional, backward-compatible)
    train_every = int(_cfg_get(config_init, "train_every", 5))
    random_injection_ratio = float(_cfg_get(config_init, "random_injection_ratio", 0.05))
    stagnation_patience = int(_cfg_get(config_init, "stagnation_patience", 30))
    reheat_factor = float(_cfg_get(config_init, "reheat_factor", 1.5))
    refine_mode = bool(_cfg_get(config_init, "refine_mode", True))
    residual_strength = float(_cfg_get(config_init, "residual_strength", 0.05))
    ga_dominant_ratio = float(_cfg_get(config_init, "ga_dominant_ratio", 0.8))

    crossover_rate = 0.8
    mutation_rate = 0.1

    para_dict = _init_para_dict(config_init, config_wandb)
    model = _build_module(config_init, para_dict)

    save_csv = genSavePath(problem_id, config_wandb)
    os.makedirs(save_csv, exist_ok=True)

    if ENABLE_LOGGING:
        InitLOGGING(save_csv, problem_id)

    cache = {}
    data_history, fitness_history = init_history(problem, para_dict)
    evaluations = para_dict.init_size

    bestf = np.full(maxfun, np.inf, dtype=np.float64)
    curr_bestf = np.full(maxfun, np.inf, dtype=np.float64)

    distance_train, distance_history, distance_gen = [], [], []
    spread_train, spread_history, spread_gen = [], [], []

    if En_SCALE:
        _, data_mean, data_std = Convert(data_history).zscore()
    else:
        data_mean, data_std = 0, 1

    # Pretrain
    upper = (para_dict.upper - data_mean) / data_std
    lower = (para_dict.lower - data_mean) / data_std
    print(f"Start pretraining, pretrain {para_dict.pretrain} rounds")
    for _ in range(para_dict.pretrain):
        model.pretrain(para_dict.epoch, upper, lower)
    print("Pre-training is over")

    run_time_start = time.time()
    best_so_far = float(np.min(fitness_history))
    stall_counter = 0

    # Initial log
    best_idx = int(np.argmin(fitness_history))
    bestpoint_x = data_history[best_idx, :]
    if ENABLE_LOGGING:
        _log_epoch(
            save_csv=save_csv,
            problem_id=problem_id,
            epoch=-1,
            evaluations=evaluations,
            curr_best=best_so_far,
            global_best=best_so_far,
            elapsed=0.0,
            distance_history=0.0,
            distance_gen=0.0,
            distance_train=0.0,
            spread_history=0.0,
            spread_gen=0.0,
            spread_train=0.0,
            bestpoint_x=bestpoint_x,
            nn_stats=_default_nn_stats(),
        )

    stop = False
    string = ""
    mean_bestf = 1e8

    for epoch in range(maxfun):
        # 1) Shrink optimal set
        top_size = int(
            np.ceil(
                init_size
                * np.exp(config_init.gamma * np.log(1 / init_size) * (evaluations / max(fin_size, 1)))
            )
        )
        top_size = max(2, min(top_size, len(data_history)))

        keep_idx = np.argsort(fitness_history.reshape(-1))[:top_size]
        data_history = data_history[keep_idx, :]
        fitness_history = fitness_history[keep_idx]
        train_data = data_history

        # 2) Optional GA refinement on elite every gen_n epochs
        if epoch > 0 and epoch % max(int(config_init.gen_n), 1) == 0:
            elite_size = max(2, int(len(data_history) * float(config_init.elite_ratio)))
            elite_idx = np.argsort(fitness_history.reshape(-1))[:elite_size]
            elite_solutions = data_history[elite_idx].copy()

            offspring = genetic_operations(
                population=elite_solutions,
                para_dict=para_dict,
                crossover_rate=crossover_rate,
                mutation_rate=mutation_rate,
            )
            if offspring.size > 0:
                off_fit = _evaluate_population_with_cache(problem, offspring, cache)
                evaluations += offspring.shape[0]

                merged_data = np.vstack([data_history, offspring])
                merged_fit = np.vstack([fitness_history, off_fit])
                new_keep = np.argsort(merged_fit.reshape(-1))[: len(data_history)]
                data_history = merged_data[new_keep]
                fitness_history = merged_fit[new_keep]

        # 3) Optional z-score tracking
        if En_SCALE:
            _, dm, ds = Convert(data_history).zscore()
            data_mean = data_mean + config_wandb.ZSCORESTEP * (dm - data_mean)
            data_std = data_std + config_wandb.ZSCORESTEP * (ds - data_std)

        # 4) Train GAN less frequently
        train_this_epoch = (epoch % max(train_every, 1) == 0)
        nn_dict = _train_gan_if_needed(
            module=model,
            train_data=train_data,
            para_dict=para_dict,
            data_mean=data_mean,
            data_std=data_std,
            lambda1=config_init.lambda1,
            lambda2=config_init.lambda2,
            train_this_epoch=train_this_epoch,
        )

        # 5) Generate candidates
        noise = torch.rand(pop_size, para_dict.Gnodes_in, device=device) * 2 - 1
        z_fake = model.generator(noise)
        fake_data = Convert(z_fake.data).to_np()
        fake_data = fake_data * data_std + data_mean

        # Hybrid local projection
        effective_epoch = epoch
        if stall_counter >= stagnation_patience:
            # Reheat: temporarily increase exploration by using earlier-progress scale
            effective_epoch = int(max(0, epoch - reheat_factor * stagnation_patience))

        fake_data = local_hybrid_generation(
            fake_data=fake_data,
            data_history=data_history,
            fitness_history=fitness_history,
            para_dict=para_dict,
            config_init=config_init,
            epoch=effective_epoch,
            maxfun=maxfun,
            refine_mode=refine_mode,
            residual_strength=residual_strength,
        )

        # GA-dominant fusion: mostly GA offspring, less NN samples
        ga_num = int(pop_size * max(0.0, min(ga_dominant_ratio, 1.0)))
        nn_num = max(0, pop_size - ga_num)

        elite_size = max(2, int(len(data_history) * float(config_init.elite_ratio)))
        elite_idx = np.argsort(fitness_history.reshape(-1))[:elite_size]
        elite_pool = data_history[elite_idx].copy()

        ga_candidates = genetic_operations(
            population=elite_pool,
            para_dict=para_dict,
            crossover_rate=crossover_rate,
            mutation_rate=mutation_rate,
        )
        if ga_candidates.shape[0] < ga_num:
            # If GA offspring is insufficient, pad from elite mutation copies
            pad_n = ga_num - ga_candidates.shape[0]
            pad_base = elite_pool[np.random.randint(0, elite_pool.shape[0], size=pad_n)].copy()
            _, _, span = _as_bounds(para_dict)
            pad_noise = np.random.normal(0.0, 0.02, size=pad_base.shape) * span
            pad_base = _clip_to_bounds(pad_base + pad_noise, para_dict)
            ga_candidates = np.vstack([ga_candidates, pad_base]) if ga_candidates.size > 0 else pad_base

        ga_candidates = ga_candidates[:ga_num] if ga_num > 0 else np.empty((0, dim), dtype=np.float32)
        nn_candidates = fake_data[:nn_num] if nn_num > 0 else np.empty((0, dim), dtype=np.float32)

        fake_data = np.vstack([ga_candidates, nn_candidates]) if (ga_num + nn_num) > 0 else fake_data

        # Random injection for anti-collapse (small)
        inj_num = int(pop_size * max(0.0, min(random_injection_ratio, 0.5)))
        if inj_num > 0 and fake_data.shape[0] >= inj_num:
            random_part = np.random.rand(inj_num, dim)
            random_part = Convert(random_part).reduction(para_dict)
            fake_data[:inj_num] = random_part

        fake_data = _clip_to_bounds(fake_data, para_dict)
        fake_fitness = _evaluate_population_with_cache(problem, fake_data, cache)
        evaluations += pop_size

        # 6) Update history via existing pipeline util
        data_history, fitness_history, train_data, index_epoch = update_data_compare(  # noqa: F405
            fake_data,
            fake_fitness,
            data_history,
            fitness_history,
            train_data,
            para_dict.ADD_SIZE,
        )

        # 7) Metrics
        curr = float(np.min(fake_fitness))
        best = float(np.min(fitness_history))
        curr_bestf[epoch] = curr
        bestf[epoch] = best

        if best < best_so_far - 1e-12:
            best_so_far = best
            stall_counter = 0
        else:
            stall_counter += 1

        distance_train.append(min_distance(train_data, para_dict.init_size))
        distance_history.append(min_distance(data_history, para_dict.init_size))
        distance_gen.append(min_distance(fake_data, pop_size))
        spread_gen.append(np.mean(np.std(fake_data, axis=0)))
        spread_history.append(np.mean(np.std(data_history, axis=0)))
        spread_train.append(np.mean(np.std(train_data, axis=0)))

        best_idx = int(np.argmin(fitness_history))
        bestpoint_x = data_history[best_idx, :]

        if evaluations > dim * 3000:
            begin = int((evaluations - dim * 3000) / pop_size)
            mean_bestf = np.abs(np.mean(bestf[max(begin, 0) : epoch + 1]))

        figurepath, stop, string = print_flag(  # noqa: F405
            stop,
            save_csv,
            evaluations,
            bestf[epoch],
            distance_train[epoch],
            mean_bestf,
            dim,
            config_init,
        )

        elapsed = time.time() - run_time_start
        nn_stats = _extract_nn_stats(nn_dict)

        # 8) Logging and print (throttled)
        if ENABLE_LOGGING and (epoch % 10 == 0 or (epoch > 0 and bestf[epoch] < bestf[epoch - 1])):
            _log_epoch(
                save_csv,
                problem_id,
                epoch,
                evaluations,
                curr_bestf[epoch],
                bestf[epoch],
                elapsed,
                distance_history[epoch],
                distance_gen[epoch],
                distance_train[epoch],
                spread_history[epoch],
                spread_gen[epoch],
                spread_train[epoch],
                bestpoint_x,
                nn_stats,
            )

        if epoch % 10 == 0:
            print(
                "epoch=%d, fes=%d, curr_bestf=%.3e, bestf=%.3e, elapsed=%.2fs, stall=%d"
                % (epoch + 1, evaluations, curr_bestf[epoch], bestf[epoch], elapsed, stall_counter)
            )

        if stop:
            return [string, bestf[epoch], distance_history[epoch], evaluations, bestpoint_x]

    # Fallback final return
    last = maxfun - 1
    return ["maxfes", bestf[last], distance_history[last], evaluations, bestpoint_x]
