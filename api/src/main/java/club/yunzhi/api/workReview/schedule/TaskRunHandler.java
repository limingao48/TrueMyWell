package club.yunzhi.api.workReview.schedule;

import club.yunzhi.api.workReview.entity.Feather;
import club.yunzhi.api.workReview.entity.Model;
import club.yunzhi.api.workReview.entity.Predict;
import club.yunzhi.api.workReview.entity.Task;
import club.yunzhi.api.workReview.repository.FeatherRepository;
import club.yunzhi.api.workReview.repository.PredictRepository;
import club.yunzhi.api.workReview.repository.TaskRepository;
import club.yunzhi.api.workReview.repository.WellRepository;
import club.yunzhi.api.workReview.service.TaskService;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.sql.Timestamp;
import java.util.*;

@Component
public class  TaskRunHandler {
    private final Logger logger = LoggerFactory.getLogger(this.getClass());
    private TaskRepository taskRepository;
    private FeatherRepository featherRepository;
    private final WellRepository wellRepository;
    private final PredictRepository predictRepository;

    public TaskRunHandler(TaskRepository taskRepository,
                          FeatherRepository featherRepository,
                          WellRepository wellRepository,
                          PredictRepository predictRepository) {
        this.taskRepository = taskRepository;
        this.featherRepository = featherRepository;
        this.wellRepository = wellRepository;
        this.predictRepository = predictRepository;
    }

    @Scheduled(cron = "0/3 * * * * *")
    public void demo() throws JsonProcessingException {
        // 每隔3秒执行一次任务查看
        List<Task> taskList = this.taskRepository.getRunningTask();
        for (Task task: taskList) {
            // 判断运行中的任务的预测特征量和井的预测特征量是否相等，不相等说明井更新了
            if (!Objects.equals(task.getPredictNumber(), task.getWell().getPredictNumber())) {
                List<Model> models = task.getModels();
                System.out.println(models);
                for (Model model: models) {
                    this.taskRun(task, task.getWell().getId(),
                            model.getId(), task.getPredictNumber(),
                            task.getWell().getPredictNumber());
                }
                // 执行完成后更新当前任务的预测条数和更新时间
                task.setPredictNumber(task.getWell().getPredictNumber());
                task.setUpdateTime(new Timestamp(System.currentTimeMillis()));
                this.taskRepository.save(task);
            } else {
                // 这种情况说的是当前的任务是启动状态，但是没有新数据，那么就要判断是否该任务要终止了，当前我使用的时间是15分钟
                if (System.currentTimeMillis() - task.getUpdateTime().getTime() > 900000) {
                    task.setStatus(Task.STATUS_FREEZE);
                    this.taskRepository.save(task);
                }
                long count = this.taskRepository.byWellIdGetRunningTask(String.valueOf(task.getWell().getId()));
                if (count == 0) {
                    // TODO 向对方发起取消订阅的请求，通过uniqueKey
//                    TaskService.requestSubOrUnSub(task.getWell().getUniqueKey(), "0");
                }
            }
        }
    }

    public void taskRun(Task task, Long wellId, Long modelId, int taskPredictNumber, int wellPredictNumber) throws JsonProcessingException {
        int limit = wellPredictNumber - taskPredictNumber;
        Pageable pageable =  PageRequest.of(0, limit, Sort.by("id").descending());
        List<Feather> feathers = this.featherRepository.findByWellIdOrderByCreateTimeDesc(wellId, pageable);
        List<Feather> res = feathers;
        for (Feather feather : feathers) {
            // 将特征feather传给py模型进行预测，其中使用modelId来判断传给哪个模型
            Predict predict = new Predict();
            Model model = new Model();
            model.setId(modelId);
            predict.setModel(model);
            predict.setTask(task);
            predict.setFeather(feather);
            double distance = getDistanceByModel(feather, modelId);
            predict.setDistance((float) distance);
            this.predictRepository.save(predict);
        }
    }

    public static double getDistanceByModel(Feather feather, Long modelId) throws JsonProcessingException {
        RestTemplate restTemplate = new RestTemplate();
        ObjectMapper objectMapper = new ObjectMapper();
        // Flask 接口的 URL
        String flaskApiUrl = String.format("http://flask:8083/%d",modelId);
        // 创建一个 Map 对象，只包含需要转换的属性
        Map<String, Object> jsonMap = new HashMap<>();
        jsonMap.put("0.X", feather.getX0());
        jsonMap.put("0.Y", feather.getY0());
        jsonMap.put("0.Z", feather.getZ0());
        jsonMap.put("1.X", feather.getX1());
        jsonMap.put("1.Y", feather.getY1());
        jsonMap.put("1.Z", feather.getZ1());
        jsonMap.put("2.X", feather.getX2());
        jsonMap.put("2.Y", feather.getY2());
        jsonMap.put("2.Z", feather.getZ2());
        jsonMap.put("重力X", feather.getG_x());
        jsonMap.put("重力Y", feather.getG_y());
        jsonMap.put("重力Z", feather.getG_z());
        jsonMap.put("翻滚角", feather.getR_angle());
        jsonMap.put("倾斜角", feather.getL_angle());
        jsonMap.put("方位角", feather.getD_angle());
        jsonMap.put("温度", feather.getTemperature());
        jsonMap.put("相对方位", feather.getOffset());
        jsonMap.put("磁倾角", feather.getMagnetic_angle());
        jsonMap.put("磁总量", feather.getMagnetic_amount());
        jsonMap.put("磁场幅值", feather.getMagnetic_amplitude());
        jsonMap.put("北向方位", feather.getNorth_orientation());
        jsonMap.put("高边方位", feather.getHigh_orientation());
        // 将 Map 对象转换为 JSON 字符串
        String json = objectMapper.writeValueAsString(jsonMap);

        // 设置请求头，指定 Content-Type 为 application/json
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        // 构建请求实体，包含 JSON 数据和请求头
        HttpEntity<String> requestEntity = new HttpEntity<>(json, headers);

        // 发送 POST 请求到 Flask 接口
        String response = restTemplate.postForObject(flaskApiUrl, requestEntity, String.class);
        // 使用 Jackson 解析 JSON 字符串
        JsonNode jsonNode = objectMapper.readTree(response);

        // 获取 distance 字段的值并打印
        double distance = jsonNode.get("distance").asDouble();
//        double distance = new Random().nextFloat();
        return distance;
    }
}
