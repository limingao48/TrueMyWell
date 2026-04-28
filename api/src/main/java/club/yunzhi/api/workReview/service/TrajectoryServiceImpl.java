package club.yunzhi.api.workReview.service;

import club.yunzhi.api.workReview.entity.TrajectoryDesignRequest;
import club.yunzhi.api.workReview.entity.TrajectoryDesignResult;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;
import java.util.Random;

@Service
public class TrajectoryServiceImpl implements TrajectoryService {

    @Override
    public TrajectoryDesignResult design(TrajectoryDesignRequest request) {
        TrajectoryDesignResult result = new TrajectoryDesignResult();

        Map<String, Double> bestSolution = new HashMap<>();
        Random random = new Random();

        bestSolution.put("L0", 800.0 + random.nextInt(200));
        bestSolution.put("DLS1", 3.0 + random.nextDouble() * 1.0);
        bestSolution.put("alpha3", 40.0 + random.nextInt(20));
        bestSolution.put("L3", 1000.0 + random.nextInt(400));
        bestSolution.put("DLS_turn", 2.0 + random.nextDouble() * 1.0);
        bestSolution.put("L4", 250.0 + random.nextInt(150));
        bestSolution.put("phi_target", 0.1 + random.nextDouble() * 0.3);
        bestSolution.put("L5", 500.0 + random.nextInt(200));
        bestSolution.put("DLS6", 2.5 + random.nextDouble() * 1.0);
        bestSolution.put("alpha_e", 87.0 + random.nextDouble() * 3.0);
        bestSolution.put("L7", 700.0 + random.nextInt(300));
        bestSolution.put("phi_init", 40.0 + random.nextInt(20));

        result.setBest_solution_dict(bestSolution);
        result.setFinal_deviation(0.1 + random.nextDouble() * 0.3);
        result.setOptimization_time(5.0 + random.nextDouble() * 5.0);

        return result;
    }
}
