package club.yunzhi.api.workReview.controller;

import club.yunzhi.api.workReview.entity.*;
import club.yunzhi.api.workReview.repository.FeatherRepository;
import club.yunzhi.api.workReview.repository.TaskRepository;
import club.yunzhi.api.workReview.repository.WellRepository;
import club.yunzhi.api.workReview.schedule.TaskRunHandler;
import com.fasterxml.jackson.annotation.JsonView;
import com.fasterxml.jackson.core.JsonProcessingException;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.List;

@RestController
@RequestMapping("feather")
public class FeatherController {
    private final FeatherRepository featherRepository;
    private final WellRepository wellRepository;
    private final TaskRepository taskRepository;
    private FeatherController(FeatherRepository featherRepository,
                              WellRepository wellRepository,
                              TaskRepository taskRepository) {
        this.featherRepository = featherRepository;
        this.wellRepository = wellRepository;
        this.taskRepository = taskRepository;
    }

    @PostMapping("add/{uniqueKey}")
    @JsonView(AddJsonView.class)
    public String add(@PathVariable String uniqueKey, @RequestBody ReceiveFeather receiveFeather) throws JsonProcessingException {
        // TODO 接收井数据先判断是否有启动的任务，有的话再选出最好的模型预测并将返回值传给对方
        Well well = this.wellRepository.findByUniqueKey(uniqueKey);
        List<Task> tasks = this.taskRepository.findByStatusAndWellId(Task.STATUS_RUNNING, well.getId());

        // 判断当前是否有该井对应的任务，必须先订阅才能新增特征对象
        if (tasks.size() == 0) {
            return new String("请先订阅该井");
        } else {
            List<Long> models = new ArrayList<>();
            for (Task task :
                 tasks) {
                for (Model model:
                        task.getModels()) {
                    if (!models.contains(model.getId())) {
                        models.add(model.getId());
                    }
                }
            }

            // 获取任务中优先级最高的模型，并将该模型的预测值返回给对方
            Long modelId = getHighPriority(models);
            Feather feather = setFeather(receiveFeather);
            feather.setWell(well);
            this.featherRepository.save(feather);
            well.setPredictNumber(this.featherRepository.countAllByWellId(well.getId()).intValue());
            this.wellRepository.save(well);
            double distance = TaskRunHandler.getDistanceByModel(feather, modelId);
            return String.valueOf(distance);
        }
    }

    /**
     * @param modelsId 这个方法主要是为了获取当前订阅任务中优先级最高的模型
     * @return
     */
    public static Long getHighPriority(List<Long> modelsId) {
        if (modelsId.contains(3L))
            return 3L;
        if (modelsId.contains(6L))
            return 6L;
        if (modelsId.contains(9L))
            return 9L;
        if (modelsId.contains(2L))
            return 2L;
        if (modelsId.contains(5L))
            return 5L;
        if (modelsId.contains(8L))
            return 8L;
        if (modelsId.contains(1L))
            return 1L;
        if (modelsId.contains(4L))
            return 4L;
        if (modelsId.contains(7L))
            return 7L;
        return 3L;
    }

    /**
     * @param receiveFeather 将接收到的数据赋值给特征对象
     * @return
     */
    public static Feather setFeather(ReceiveFeather receiveFeather) {
        List<ReceiveOneFeather> receiveOneFeather = receiveFeather.getOneFeathers();
        Feather feather = new Feather();

        // TODO 目前我们获得的是一次数据的第一条，后边要把这里改为平均数
        // 对一次数据进行赋值
        // 将数据打乱，然后获取50条数据进行平均值赋值
        Collections.shuffle(receiveOneFeather);
        int randomSeriesLength = Math.min(receiveOneFeather.size(), 50);
        List<ReceiveOneFeather> receiveOneFeathers = receiveOneFeather.subList(0, randomSeriesLength);
        feather.setX0((float) receiveOneFeathers.stream().mapToDouble(ReceiveOneFeather::getX0).average().getAsDouble());
        feather.setX1((float) receiveOneFeathers.stream().mapToDouble(ReceiveOneFeather::getX1).average().getAsDouble());
        feather.setX2((float) receiveOneFeathers.stream().mapToDouble(ReceiveOneFeather::getX2).average().getAsDouble());
        feather.setY0((float) receiveOneFeathers.stream().mapToDouble(ReceiveOneFeather::getY0).average().getAsDouble());
        feather.setY1((float) receiveOneFeathers.stream().mapToDouble(ReceiveOneFeather::getY1).average().getAsDouble());
        feather.setY2((float) receiveOneFeathers.stream().mapToDouble(ReceiveOneFeather::getY2).average().getAsDouble());
        feather.setZ0((float) receiveOneFeathers.stream().mapToDouble(ReceiveOneFeather::getZ0).average().getAsDouble());
        feather.setZ1((float) receiveOneFeathers.stream().mapToDouble(ReceiveOneFeather::getZ1).average().getAsDouble());
        feather.setZ2((float) receiveOneFeathers.stream().mapToDouble(ReceiveOneFeather::getZ2).average().getAsDouble());
        feather.setG_x((float) receiveOneFeathers.stream().mapToDouble(ReceiveOneFeather::getG_x).average().getAsDouble());
        feather.setG_y((float) receiveOneFeathers.stream().mapToDouble(ReceiveOneFeather::getG_y).average().getAsDouble());
        feather.setG_z((float) receiveOneFeathers.stream().mapToDouble(ReceiveOneFeather::getG_z).average().getAsDouble());
        feather.setD_angle((float) receiveOneFeathers.stream().mapToDouble(ReceiveOneFeather::getD_angle).average().getAsDouble());
        feather.setL_angle((float) receiveOneFeathers.stream().mapToDouble(ReceiveOneFeather::getL_angle).average().getAsDouble());
        feather.setR_angle((float) receiveOneFeathers.stream().mapToDouble(ReceiveOneFeather::getR_angle).average().getAsDouble());
        feather.setTemperature((float) receiveOneFeathers.stream().mapToDouble(ReceiveOneFeather::getTemperature).average().getAsDouble());

        // 对二次数据进行赋值
        feather.setOffset(receiveFeather.getOffset());
        feather.setRelative_north_orientation(receiveFeather.getRelative_north_orientation());
        feather.setRelative_distance(receiveFeather.getRelative_distance());
        feather.setInclinometer_relative_distance(receiveFeather.getInclinometer_relative_distance());
        feather.setMagnetic_amount(receiveFeather.getMagnetic_amount());
        feather.setMagnetic_angle(receiveFeather.getMagnetic_angle());
        feather.setMagnetic_amplitude(receiveFeather.getMagnetic_amplitude());
        feather.setNorth_orientation(receiveFeather.getNorth_orientation());
        feather.setHigh_orientation(receiveFeather.getHigh_orientation());
        feather.setDepth(receiveFeather.getDepth());
        return feather;
    }

    private interface AddJsonView {}
}
