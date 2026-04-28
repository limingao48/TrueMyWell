package club.yunzhi.api.workReview.service;

import club.yunzhi.api.workReview.entity.TrajectoryDesignRequest;
import club.yunzhi.api.workReview.entity.TrajectoryDesignResult;

public interface TrajectoryService {
    TrajectoryDesignResult design(TrajectoryDesignRequest request);
}
