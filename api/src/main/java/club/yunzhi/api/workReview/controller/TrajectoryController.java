package club.yunzhi.api.workReview.controller;

import club.yunzhi.api.workReview.entity.OptimizationProgress;
import club.yunzhi.api.workReview.entity.TrajectoryDesignRequest;
import club.yunzhi.api.workReview.entity.TrajectoryDesignResult;
import club.yunzhi.api.workReview.service.OptimizationTaskManager;
import club.yunzhi.api.workReview.service.TrajectoryService;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.util.UUID;

@RestController
@RequestMapping("trajectory")
public class TrajectoryController {

    private final TrajectoryService trajectoryService;
    private final OptimizationTaskManager taskManager;

    public TrajectoryController(TrajectoryService trajectoryService, OptimizationTaskManager taskManager) {
        this.trajectoryService = trajectoryService;
        this.taskManager = taskManager;
    }

    @PostMapping("design")
    public TrajectoryDesignResult design(@RequestBody TrajectoryDesignRequest request) {
        return trajectoryService.design(request);
    }

    @PostMapping("design/start")
    public String startDesign(@RequestBody TrajectoryDesignRequest request) {
        String taskId = UUID.randomUUID().toString();
        taskManager.submitOptimizationTask(taskId, request);
        return taskId;
    }

    @GetMapping(value = "design/progress/{taskId}", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter getProgress(@PathVariable String taskId) {
        return taskManager.createProgressEmitter(taskId);
    }

    @GetMapping("design/status/{taskId}")
    public OptimizationProgress getStatus(@PathVariable String taskId) {
        return taskManager.getProgress(taskId);
    }

    @DeleteMapping("design/task/{taskId}")
    public void cancelTask(@PathVariable String taskId) {
        taskManager.cleanupTask(taskId);
    }
}
