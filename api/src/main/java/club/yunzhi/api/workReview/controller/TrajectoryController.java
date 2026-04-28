package club.yunzhi.api.workReview.controller;

import club.yunzhi.api.workReview.entity.TrajectoryDesignRequest;
import club.yunzhi.api.workReview.entity.TrajectoryDesignResult;
import club.yunzhi.api.workReview.service.TrajectoryService;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("trajectory")
public class TrajectoryController {

    private final TrajectoryService trajectoryService;

    public TrajectoryController(TrajectoryService trajectoryService) {
        this.trajectoryService = trajectoryService;
    }

    @PostMapping("design")
    public TrajectoryDesignResult design(@RequestBody TrajectoryDesignRequest request) {
        return trajectoryService.design(request);
    }
}
