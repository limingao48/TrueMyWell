package club.yunzhi.api.workReview.trajectory.optimizer;

import club.yunzhi.api.workReview.trajectory.WellTrajectoryConfig;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/**
 * L-SHADE (Success-History Adaptive Differential Evolution with
 * linear population size reduction) 的简化实现。
 */
public class LSHADEOptimizer implements ProgressAwareOptimizer {
    private final Random random = new Random();
    private static final double MIN_CR = 0.0;
    private static final double MAX_CR = 1.0;
    private static final double MIN_F = 0.1;
    private static final double MAX_F = 1.0;
    private static final int DEFAULT_MEMORY_SIZE = 5;
    private static final int MIN_POPULATION_SIZE = 4;

    @Override
    public double[] optimize(ObjectiveFunction objectiveFunc, WellTrajectoryConfig config,
                             double[][] bounds, int population, int iterations) {
        return optimize(objectiveFunc, config, bounds, population, iterations, null);
    }

    @Override
    public double[] optimize(ObjectiveFunction objectiveFunc, WellTrajectoryConfig config,
                             double[][] bounds, int population, int iterations,
                             ProgressCallback callback) {
        final int dim = bounds.length;
        final int initialPopulation = Math.max(MIN_POPULATION_SIZE + 1, population);

        List<double[]> pop = new ArrayList<>();
        List<Double> fitness = new ArrayList<>();
        for (int i = 0; i < initialPopulation; i++) {
            double[] individual = randomVector(bounds, dim);
            pop.add(individual);
            fitness.add(objectiveFunc.evaluate(individual));
        }

        double[] best = cloneVector(pop.get(0));
        double bestFitness = fitness.get(0);
        for (int i = 1; i < pop.size(); i++) {
            if (fitness.get(i) < bestFitness) {
                bestFitness = fitness.get(i);
                best = cloneVector(pop.get(i));
            }
        }

        double[] memoryCr = new double[DEFAULT_MEMORY_SIZE];
        double[] memoryF = new double[DEFAULT_MEMORY_SIZE];
        for (int i = 0; i < DEFAULT_MEMORY_SIZE; i++) {
            memoryCr[i] = 0.5;
            memoryF[i] = 0.5;
        }
        int memoryIndex = 0;
        List<double[]> archive = new ArrayList<>();

        int progressInterval = Math.max(1, iterations / 100);
        for (int iter = 0; iter < iterations; iter++) {
            int currentSize = pop.size();
            int pBestCount = Math.max(2, (int) Math.ceil(0.11 * currentSize));
            int[] sortedIndices = sortIndicesByFitness(fitness);

            List<double[]> newPop = new ArrayList<>(currentSize);
            List<Double> newFitness = new ArrayList<>(currentSize);

            List<Double> successCr = new ArrayList<>();
            List<Double> successF = new ArrayList<>();
            List<Double> successDelta = new ArrayList<>();

            for (int i = 0; i < currentSize; i++) {
                int memorySlot = random.nextInt(DEFAULT_MEMORY_SIZE);
                double cr = clamp(normalSample(memoryCr[memorySlot], 0.1), MIN_CR, MAX_CR);
                double f = clamp(cauchySample(memoryF[memorySlot], 0.1), MIN_F, MAX_F);

                int pBestIdx = sortedIndices[random.nextInt(pBestCount)];
                int r1 = randomDistinctIndex(currentSize, i, pBestIdx, -1);
                int r2 = randomIndexFromPopulationAndArchive(currentSize, archive.size(), i, pBestIdx, r1);

                double[] xi = pop.get(i);
                double[] xpBest = pop.get(pBestIdx);
                double[] xr1 = pop.get(r1);
                double[] xr2 = r2 < currentSize ? pop.get(r2) : archive.get(r2 - currentSize);

                double[] mutant = new double[dim];
                for (int d = 0; d < dim; d++) {
                    mutant[d] = xi[d] + f * (xpBest[d] - xi[d]) + f * (xr1[d] - xr2[d]);
                }
                enforceBounds(mutant, bounds);

                double[] trial = binomialCrossover(xi, mutant, cr);
                enforceBounds(trial, bounds);
                double trialFitness = objectiveFunc.evaluate(trial);

                if (trialFitness <= fitness.get(i)) {
                    newPop.add(trial);
                    newFitness.add(trialFitness);
                    archive.add(cloneVector(xi));
                    successCr.add(cr);
                    successF.add(f);
                    successDelta.add(Math.abs(fitness.get(i) - trialFitness));
                    if (trialFitness < bestFitness) {
                        bestFitness = trialFitness;
                        best = cloneVector(trial);
                    }
                } else {
                    newPop.add(xi);
                    newFitness.add(fitness.get(i));
                }
            }

            pop = newPop;
            fitness = newFitness;

            while (archive.size() > pop.size()) {
                archive.remove(random.nextInt(archive.size()));
            }

            if (!successF.isEmpty()) {
                double totalDelta = successDelta.stream().mapToDouble(Double::doubleValue).sum();
                if (totalDelta > 0) {
                    double crMean = 0.0;
                    double fNum = 0.0;
                    double fDen = 0.0;
                    for (int k = 0; k < successF.size(); k++) {
                        double w = successDelta.get(k) / totalDelta;
                        crMean += w * successCr.get(k);
                        fNum += w * successF.get(k) * successF.get(k);
                        fDen += w * successF.get(k);
                    }
                    memoryCr[memoryIndex] = crMean;
                    memoryF[memoryIndex] = fDen == 0 ? memoryF[memoryIndex] : (fNum / fDen);
                    memoryIndex = (memoryIndex + 1) % DEFAULT_MEMORY_SIZE;
                }
            }

            int targetSize = (int) Math.round(initialPopulation - (double) iter * (initialPopulation - MIN_POPULATION_SIZE) / Math.max(1, iterations - 1));
            targetSize = Math.max(MIN_POPULATION_SIZE, targetSize);
            if (pop.size() > targetSize) {
                int[] sorted = sortIndicesByFitness(fitness);
                List<double[]> reducedPop = new ArrayList<>(targetSize);
                List<Double> reducedFitness = new ArrayList<>(targetSize);
                for (int k = 0; k < targetSize; k++) {
                    reducedPop.add(pop.get(sorted[k]));
                    reducedFitness.add(fitness.get(sorted[k]));
                }
                pop = reducedPop;
                fitness = reducedFitness;
                while (archive.size() > pop.size()) {
                    archive.remove(random.nextInt(archive.size()));
                }
            }

            if (callback != null && (iter % progressInterval == 0 || iter == iterations - 1)) {
                String message = String.format("L-SHADE优化中... 迭代 %d/%d, 当前最优: %.2f, 种群: %d",
                        iter + 1, iterations, bestFitness, pop.size());
                callback.onProgress(iter + 1, iterations, bestFitness, message);
            }
        }

        return best;
    }

    private double[] randomVector(double[][] bounds, int dim) {
        double[] v = new double[dim];
        for (int d = 0; d < dim; d++) {
            double min = bounds[d][0];
            double max = bounds[d][1];
            v[d] = min + random.nextDouble() * (max - min);
        }
        return v;
    }

    private void enforceBounds(double[] vector, double[][] bounds) {
        for (int d = 0; d < vector.length; d++) {
            vector[d] = clamp(vector[d], bounds[d][0], bounds[d][1]);
        }
    }

    private double[] binomialCrossover(double[] target, double[] donor, double cr) {
        int dim = target.length;
        double[] trial = new double[dim];
        int jRand = random.nextInt(dim);
        for (int j = 0; j < dim; j++) {
            if (random.nextDouble() < cr || j == jRand) {
                trial[j] = donor[j];
            } else {
                trial[j] = target[j];
            }
        }
        return trial;
    }

    private int randomDistinctIndex(int size, int... excludes) {
        while (true) {
            int idx = random.nextInt(size);
            boolean ok = true;
            for (int ex : excludes) {
                if (idx == ex) {
                    ok = false;
                    break;
                }
            }
            if (ok) {
                return idx;
            }
        }
    }

    private int randomIndexFromPopulationAndArchive(int popSize, int archiveSize, int... excludesInPopulation) {
        int total = popSize + archiveSize;
        while (true) {
            int idx = random.nextInt(Math.max(total, 1));
            if (idx < popSize) {
                boolean ok = true;
                for (int ex : excludesInPopulation) {
                    if (idx == ex) {
                        ok = false;
                        break;
                    }
                }
                if (ok) {
                    return idx;
                }
            } else {
                return idx;
            }
        }
    }

    private int[] sortIndicesByFitness(List<Double> fitness) {
        int n = fitness.size();
        Integer[] idx = new Integer[n];
        for (int i = 0; i < n; i++) idx[i] = i;
        java.util.Arrays.sort(idx, java.util.Comparator.comparingDouble(fitness::get));
        int[] out = new int[n];
        for (int i = 0; i < n; i++) out[i] = idx[i];
        return out;
    }

    private double normalSample(double mean, double std) {
        return mean + random.nextGaussian() * std;
    }

    private double cauchySample(double location, double scale) {
        double u = random.nextDouble();
        return location + scale * Math.tan(Math.PI * (u - 0.5));
    }

    private double clamp(double v, double min, double max) {
        return Math.max(min, Math.min(max, v));
    }

    private double[] cloneVector(double[] src) {
        double[] copy = new double[src.length];
        System.arraycopy(src, 0, copy, 0, src.length);
        return copy;
    }
}
