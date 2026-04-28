package club.yunzhi.api.workReview.trajectory.optimizer;

import club.yunzhi.api.workReview.trajectory.WellTrajectoryConfig;

import java.util.Random;

public class PSOOptimizer implements ProgressAwareOptimizer {

    private static final double DEFAULT_WEIGHT = 0.7298;
    private static final double DEFAULT_C1 = 1.49618;
    private static final double DEFAULT_C2 = 1.49618;

    private final double inertiaWeight;
    private final double cognitiveCoeff;
    private final double socialCoeff;
    private final Random random;

    public PSOOptimizer() {
        this(DEFAULT_WEIGHT, DEFAULT_C1, DEFAULT_C2);
    }

    public PSOOptimizer(double inertiaWeight, double cognitiveCoeff, double socialCoeff) {
        this.inertiaWeight = inertiaWeight;
        this.cognitiveCoeff = cognitiveCoeff;
        this.socialCoeff = socialCoeff;
        this.random = new Random();
    }

    @Override
    public double[] optimize(ObjectiveFunction objectiveFunc, WellTrajectoryConfig config,
                             double[][] bounds, int population, int iterations) {
        return optimize(objectiveFunc, config, bounds, population, iterations, null);
    }

    public double[] optimize(ObjectiveFunction objectiveFunc, WellTrajectoryConfig config,
                             double[][] bounds, int population, int iterations,
                             ProgressCallback callback) {
        int dim = bounds.length;

        double[][] positions = new double[population][dim];
        double[][] velocities = new double[population][dim];
        double[][] personalBest = new double[population][dim];
        double[] personalBestFitness = new double[population];
        double[] globalBest = new double[dim];
        double globalBestFitness = Double.MAX_VALUE;

        initializePopulation(positions, velocities, personalBest, bounds, population, dim);

        for (int i = 0; i < population; i++) {
            personalBestFitness[i] = objectiveFunc.evaluate(positions[i]);
            if (personalBestFitness[i] < globalBestFitness) {
                globalBestFitness = personalBestFitness[i];
                System.arraycopy(positions[i], 0, globalBest, 0, dim);
            }
        }

        int progressInterval = Math.max(1, iterations / 100);

        for (int iter = 0; iter < iterations; iter++) {
            for (int i = 0; i < population; i++) {
                updateVelocity(velocities[i], positions[i], personalBest[i], globalBest, dim);
                updatePosition(positions[i], velocities[i], bounds, dim);

                double currentFitness = objectiveFunc.evaluate(positions[i]);

                if (currentFitness < personalBestFitness[i]) {
                    personalBestFitness[i] = currentFitness;
                    System.arraycopy(positions[i], 0, personalBest[i], 0, dim);

                    if (currentFitness < globalBestFitness) {
                        globalBestFitness = currentFitness;
                        System.arraycopy(positions[i], 0, globalBest, 0, dim);
                    }
                }
            }

            if (callback != null && (iter % progressInterval == 0 || iter == iterations - 1)) {
                int progress = (int) ((iter + 1) * 100.0 / iterations);
                String message = String.format("PSO优化中... 迭代 %d/%d, 当前最优: %.2f",
                        iter + 1, iterations, globalBestFitness);
                callback.onProgress(iter + 1, iterations, globalBestFitness, message);
            }
        }

        return globalBest;
    }

    private void initializePopulation(double[][] positions, double[][] velocities,
                                     double[][] personalBest, double[][] bounds,
                                     int population, int dim) {
        for (int i = 0; i < population; i++) {
            for (int j = 0; j < dim; j++) {
                double min = bounds[j][0];
                double max = bounds[j][1];
                positions[i][j] = min + random.nextDouble() * (max - min);
                velocities[i][j] = (random.nextDouble() - 0.5) * (max - min) * 0.1;
                personalBest[i][j] = positions[i][j];
            }
        }
    }

    private void updateVelocity(double[] velocity, double[] position,
                                double[] personalBest, double[] globalBest, int dim) {
        for (int j = 0; j < dim; j++) {
            double r1 = random.nextDouble();
            double r2 = random.nextDouble();

            double cognitiveTerm = cognitiveCoeff * r1 * (personalBest[j] - position[j]);
            double socialTerm = socialCoeff * r2 * (globalBest[j] - position[j]);

            velocity[j] = inertiaWeight * velocity[j] + cognitiveTerm + socialTerm;
        }
    }

    private void updatePosition(double[] position, double[] velocity, double[][] bounds, int dim) {
        for (int j = 0; j < dim; j++) {
            position[j] += velocity[j];

            if (position[j] < bounds[j][0]) {
                position[j] = bounds[j][0];
                velocity[j] *= -0.5;
            } else if (position[j] > bounds[j][1]) {
                position[j] = bounds[j][1];
                velocity[j] *= -0.5;
            }
        }
    }
}
