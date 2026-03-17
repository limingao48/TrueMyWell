package club.yunzhi.api.workReview.schedule;

import club.yunzhi.api.workReview.entity.Message;
import club.yunzhi.api.workReview.entity.Predict;
import club.yunzhi.api.workReview.repository.PredictRepository;
import club.yunzhi.api.workReview.webSocketServer.WebSocketServer;
import com.alibaba.fastjson2.JSONObject;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

@Service
public class PredictPolling implements ApplicationRunner {

    private final PredictRepository predictRepository;
    private Long PredictNumber = 0L;
    private Predict latestPredict;

    public PredictPolling(PredictRepository predictRepository) {
        this.predictRepository = predictRepository;
    }

    //设置定时每秒一次
    @Scheduled(cron = "0/3 * * * * ?")
    public void Polling() throws Exception {
        System.out.println("执行轮询任务");
        if (this.PredictNumber != this.predictRepository.count()) {
            // 有新预测数据存储
            System.out.println("有新预测数据，通知前台");
            List<Predict> predicts = predictRepository.findAll();
            List<Predict> newPredictList = new ArrayList<>();
            boolean find = false;
            Set<Long> set = new HashSet<>();
            // 寻找上次读取最近的预测数据，其后为新增数据，将新增数据存至NewPredictList
            for (Predict predict : predicts) {
                if (this.latestPredict == null) {
                    find = true;
                    continue;
                }
                if (!find && predict.equals(this.latestPredict)) {
                    find = true;
                } else if (find) {
                    newPredictList.add(predict);
                    set.add(predict.getTask().getId());
                }
            }

            // 更新预测数据总数和最近预测数据
            this.PredictNumber = this.predictRepository.count();
            if(predicts.isEmpty()){
                this.latestPredict = null;
            }else{
                this.latestPredict = predicts.get(predicts.size() - 1);
            }
            List<Message.TaskIdAndModelId> taskIdAndModelIds = new ArrayList<>();
            newPredictList.forEach(predict -> {
                boolean isFind = false;
                for (Message.TaskIdAndModelId idAndModelId : taskIdAndModelIds) {
                    if (Objects.equals(idAndModelId.taskId, predict.getTask().getId())) {
                        isFind = true;
                        idAndModelId.ModelIds.add(predict.getModel().getType());
                        break;
                    }
                }
                if(!isFind){
                    Message.TaskIdAndModelId taskIdAndModelId = new Message.TaskIdAndModelId();
                    taskIdAndModelId.ModelIds = new ArrayList<>();
                    taskIdAndModelId.taskId = predict.getTask().getId();
                    taskIdAndModelId.ModelIds.add(predict.getModel().getType());
                    taskIdAndModelIds.add(taskIdAndModelId);
                }
            });
//            Map<String, Object> map = new HashMap<>();
            // 获取当前日期和时间
            LocalDateTime nowDateTime = LocalDateTime.now();
            DateTimeFormatter dateTimeFormatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
            System.out.println(dateTimeFormatter.format(nowDateTime));
            // 获取新预测数据
//            map.put("server_time", dateTimeFormatter.format(nowDateTime));
//            map.put("server_code", "200");
//            map.put("server_message", newPredictList);
            Message message = new Message();

            List<Long> longs = new ArrayList<>(set);
            message.setTaskIds(longs);
            message.setTaskIdAndModelId(taskIdAndModelIds);
            WebSocketServer.sendAllMessage(message);
        }

    }

    @Override
    public void run(ApplicationArguments args) throws Exception {
        System.out.println("项目启动，初始化PredictNumber");
        this.PredictNumber = predictRepository.count();
        List<Predict> predicts = predictRepository.findAll();
        if(predicts.isEmpty()){
            this.latestPredict = null;
        }else{
            this.latestPredict = predicts.get(predicts.size() - 1);
        }
    }
}
