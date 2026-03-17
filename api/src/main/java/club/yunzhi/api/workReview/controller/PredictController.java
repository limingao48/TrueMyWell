package club.yunzhi.api.workReview.controller;

import club.yunzhi.api.workReview.entity.*;
import club.yunzhi.api.workReview.service.PredictService;
import com.fasterxml.jackson.annotation.JsonView;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.web.SortDefault;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;


import java.sql.Timestamp;
import java.text.SimpleDateFormat;
import java.util.*;


@RestController
@RequestMapping("predict")
public class PredictController {
    private PredictService predictService;


    public PredictController(PredictService predictService) {
        this.predictService = predictService;
    }

    @GetMapping("getAllPredict")
    @JsonView(getAllJsonView.class)
    public List<Predict> getAllTasksByWellId(@RequestParam(required = false) ArrayList<Long> modelsId,
                                             @RequestParam(required = false) String wellId,
                                             @RequestParam(required = false) String taskId) {
        return this.predictService.getPredicts(modelsId, wellId, taskId);
    }

    @GetMapping("getPredictByWell")
    @JsonView(getPredictsJsonView.class)
    public List<Predict> getAllRealTimePredictByWellId(@RequestParam(required = false) String wellId) {
        return this.predictService.getPredictsByWell(wellId);
    }

    @GetMapping("getModelsByTask")
    @JsonView(getAllJsonView.class)
    public List<Model> getModelsByTask(@RequestParam(required = false) String taskId) {
        List<Predict> predicts = predictService.getPredictsByTask(taskId);
        List<Model> models = new ArrayList<>();
        predicts.forEach(predict -> {
            if(!models.contains(predict.getModel())){
                models.add(predict.getModel());
            }
        });
        return models;
    }
    @GetMapping("getTimeByTask")
    @JsonView(getAllJsonView.class)
    public List<Map<String, String>> getTimetByTask(@RequestParam(required = false) String taskId) {
        List<Predict> predicts = predictService.getPredictsByTask(taskId);
        // 初始化最小和最大时间为第一个createTime
        Timestamp minTimestamp = predicts.get(0).getCreateTime();
        Timestamp maxTimestamp = predicts.get(0).getCreateTime();
        // 找到最小和最大时间
        for (Predict predict : predicts) {
            Timestamp createTime = predict.getCreateTime();
            if (createTime.before(minTimestamp)) {
                minTimestamp = createTime;
            }
            if (createTime.after(maxTimestamp)) {
                maxTimestamp = createTime;
            }
        }
        // 格式化时间为 YYYY-MM-DD HH:mm
        SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd HH:mm");
        String minTimeFormatted = dateFormat.format(minTimestamp);
        String maxTimeFormatted = dateFormat.format(maxTimestamp);

        // 创建包含这两个格式化时间的Map并添加到列表中
        List<Map<String, String>> result = new ArrayList<>();
        Map<String, String> timeMap = new HashMap<>();
        timeMap.put("minTime", minTimeFormatted);
        timeMap.put("maxTime", maxTimeFormatted);
        result.add(timeMap);
        return result;
    }


    @GetMapping("getHistory")
    @JsonView(getAllJsonView.class)
    public List<Predict> getHistory(@RequestParam(required = false) ArrayList<Long> modelsId,
                                             @RequestParam(required = false) String wellId,
                                             @RequestParam(required = false) String taskId,
                                             @RequestParam(required = false) String startTime,
                                             @RequestParam(required = false) String endTime) {
        return this.predictService.getPredictsByTime(modelsId, wellId, taskId,startTime,endTime);
    }

    @GetMapping("getAll")
    @JsonView(getAllJsonView.class)
    public List<Map<String, Object>> getAll(@RequestParam(required = false) String wellId,
                                            @RequestParam(required = false) String taskId) {
        return this.predictService.getPredictsByWellAndTask(wellId, taskId);
    }

    @GetMapping("getPredictNumber")
    public ArrayList<BarData> getPredictNumber() {
        return this.predictService.getPredictNumber();
    }


    @GetMapping("getOffset")
    @JsonView(getAllJsonView.class)
    public List<Map<String, List<Map<String, Object>>>> getOffset(@RequestParam(required = false) String wellId,
                                                                  @RequestParam(required = false) String taskId) {
        return this.predictService.getOffsetsByWellAndTask(wellId, taskId);
    }

    @GetMapping("page")
    @JsonView(getAllJsonView.class)
    public Page<Predict> page(@RequestParam(required = false) String wellId,
                           @RequestParam(required = false) String taskId,
                           @SortDefault(sort = "id", direction = Sort.Direction.DESC) Pageable pageable) {
        return this.predictService.page(wellId,taskId ,pageable);
    }


    public interface getAllJsonView extends Predict.FeatherJsonView, Predict.ModelJsonView {
    }

    public interface getPredictsJsonView extends Predict.FeatherJsonView, Predict.TaskJsonView, Predict.ModelJsonView{}

}
