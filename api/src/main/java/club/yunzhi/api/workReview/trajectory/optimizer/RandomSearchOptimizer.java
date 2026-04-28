package club.yunzhi.api.workReview.trajectory.optimizer;

import club.yunzhi.api.workReview.trajectory.WellTrajectoryConfig;

import java.util.Random;

public class RandomSearchOptimizer implements TrajectoryOptimizer {

    private static final int DEFAULT_MAX_ITERATIONS = 1000;

    private final Random random;

    public RandomSearchOptimizer() {
        this.random = new Random();
    }

    @Override
    public double[] optimize(ObjectiveFunction objectiveFunc, WellTrajectoryConfig config,
                             double[][] bounds, int population, int iterations) {
        int dim = bounds.length;
        int maxIter = iterations > 0 ? iterations : DEFAULT_MAX_ITERATIONS;

        double[] bestPosition = null;
        double bestFitness = Double.MAX_VALUE;

        for (int iter = 0; iter < maxIter; iter++) {
            double[] position = new double[dim];
            for (int i = 0; i < dim; i++) {
                position[i] = bounds[i][0] + random.nextDouble() * (bounds[i][1] - bounds[i][0]);
            }

            double fitness = objectiveFunc.evaluate(position);

            if (fitness < bestFitness) {
                bestFitness = fitness;
                bestPosition = position.clone();
            }

            if (bestFitness < 100.0) {
                break;
            }
        }

        if (bestPosition == null) {
            bestPosition = new double[dim];
            for (int i = 0; i < dim; i++) {
                bestPosition[i] = (bounds[i][0] + bounds[i][1]) / 2;
            }
        }

        return bestPosition;
    }
}
