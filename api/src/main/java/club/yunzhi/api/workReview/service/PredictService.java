package club.yunzhi.api.workReview.service;

import club.yunzhi.api.workReview.entity.BarData;
import club.yunzhi.api.workReview.entity.Predict;
import club.yunzhi.api.workReview.entity.Task;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

public interface PredictService {
    List<Predict> getPredicts(ArrayList<Long> modelsId, String wellId, String taskId);
    List<Predict> getPredictsByWell(String wellId);
    List<Predict> getPredictsByTime(ArrayList<Long> modelsId, String wellId, String taskId,String startTime, String endTime);
    List<Predict> getPredictsByTask(String taskId);
    List<Map<String, Object>> getPredictsByWellAndTask(String wellId, String taskId);
    List<Map<String, List<Map<String, Object>>>> getOffsetsByWellAndTask(String wellId, String taskId);
    List<Predict> getAll();
  
    List<Predict> findByModelName(String modelName);

    ArrayList<BarData> getPredictNumber();

    Page<Predict> page(String wellId,String taskId, Pageable pageable);

}
