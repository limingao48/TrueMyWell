package club.yunzhi.api.workReview.service;
import club.yunzhi.api.workReview.entity.BarData;
import club.yunzhi.api.workReview.entity.Predict;
import club.yunzhi.api.workReview.repository.PredictRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;


import java.util.*;

@Service
public class PredictServiceImpl implements PredictService{

    private final PredictRepository predictRepository;

    public PredictServiceImpl(PredictRepository predictRepository) {
        this.predictRepository = predictRepository;
    }

    @Override
    public List<Predict> getPredicts(ArrayList<Long> modelsId, String wellId, String taskId) {
        //当查询条件为空时返回空
        List<Predict> empty = new ArrayList<>();
        if (modelsId == null || wellId == null || taskId == null) {
            return empty;
        } else if (modelsId.isEmpty()) {
            return empty;
        }
        List<Predict> sortedPredicts = predictRepository.getPredictByModelAndFeatherAndTask(modelsId, wellId, taskId);

        // 逆转数组，返回最新数据
        Collections.reverse(sortedPredicts);
        Set<Long> modelIds = new HashSet<>();
        Set<Long> fullModelIds = new HashSet<>();
        HashMap<Long, List<Predict>> modelToPredicts = new HashMap<>();
        List<Predict> returnSortedPredicts = new ArrayList<>();

        // 返回该井下两个任务的数据即可,每个模型至多返回50条数据
        for (int i = 0; i < sortedPredicts.size(); i++) {
            if(modelIds.contains(sortedPredicts.get(i).getModel().getId())){
                // 每有一个模型队列满50则记录词模型
                if(Objects.requireNonNull(modelToPredicts.get(sortedPredicts.get(i).getModel().getId())).size() < 50){
                    Objects.requireNonNull(modelToPredicts.get(sortedPredicts.get(i).getModel().getId())).add(sortedPredicts.get(i));
                    returnSortedPredicts.add(sortedPredicts.get(i));
                }else {
                    fullModelIds.add(sortedPredicts.get(i).getModel().getId());
                }
            }else {
                // 将所有要求的模型ID加入，构建模型-》预测数据队列映射
                if(modelIds.size() < modelsId.size()){
                    modelIds.add(sortedPredicts.get(i).getModel().getId());
                    List<Predict> predicts = new ArrayList<>();
                    predicts.add(sortedPredicts.get(i));
                    modelToPredicts.put(sortedPredicts.get(i).getModel().getId(),predicts);
                    returnSortedPredicts.add(sortedPredicts.get(i));
                }
            }
            // 如果数据填充完成则推出循环
            if(fullModelIds.size() == modelsId.size()){
                break;
            }
        }
        // 按照深度排序，用于前端页面图像展示
        Collections.sort(returnSortedPredicts);
        return returnSortedPredicts;
    }

    @Override
    public List<Predict> getPredictsByWell(String wellId) {
        // 当查询条件为空时返回空
        List<Predict> empty = new ArrayList<>();
        if (wellId == null) {
            return empty;
        }
        List<Predict> sortedPredicts = predictRepository.getPredictByWell(wellId);
        // 逆转数组，返回最新数据
        Collections.reverse(sortedPredicts);
        Set<Long> taskIds = new HashSet<>();
        HashMap<Long, List<Predict>> taskToPredicts = new HashMap<>();
        List<Predict> returnSortedPredicts = new ArrayList<>();
        // 返回该井下两个任务的数据即可，并且每个任务最多10条数据
        sortedPredicts.forEach( predict -> {
            if(taskIds.contains(predict.getTask().getId())){
                if(Objects.requireNonNull(taskToPredicts.get(predict.getTask().getId())).size() < 10){
                    Objects.requireNonNull(taskToPredicts.get(predict.getTask().getId())).add(predict);
                    returnSortedPredicts.add(predict);
                }
            }else {
                if(taskIds.size() < 2){
                    taskIds.add(predict.getTask().getId());
                    List<Predict> predicts = new ArrayList<>();
                    predicts.add(predict);
                    taskToPredicts.put(predict.getTask().getId(),predicts);
                    returnSortedPredicts.add(predict);
                }
            }
        });
        Collections.sort(returnSortedPredicts);
        return returnSortedPredicts;
    }

    @Override
    public List<Map<String, Object>> getPredictsByWellAndTask(String wellId, String taskId) {
        //当查询条件为空时返回空
        List<Map<String, Object>> empty = new ArrayList<>();
        if (wellId == null || taskId == null) {
            return empty;
        }
        List<Predict> predicts = predictRepository.getPredictByWellAndTask(wellId, taskId);
        List<Map<String, Object>> result = new ArrayList<>();
        for (Predict predict : predicts) {
            if (result.size() < 1000){
                Map<String, Object> predictionMap = new LinkedHashMap<>();
                predictionMap.put("depth", predict.getFeather().getDepth());
                predictionMap.put("x0", predict.getFeather().getX0());
                predictionMap.put("y0", predict.getFeather().getY0());
                predictionMap.put("z0", predict.getFeather().getZ0());
                predictionMap.put("x1", predict.getFeather().getX1());
                predictionMap.put("y1", predict.getFeather().getY1());
                predictionMap.put("z1", predict.getFeather().getZ1());
                predictionMap.put("x2", predict.getFeather().getX2());
                predictionMap.put("y2", predict.getFeather().getY2());
                predictionMap.put("z2", predict.getFeather().getZ2());
                predictionMap.put("g_x", predict.getFeather().getG_x());
                predictionMap.put("g_y", predict.getFeather().getG_y());
                predictionMap.put("g_z", predict.getFeather().getG_z());
                predictionMap.put("r_angle", predict.getFeather().getR_angle());
                predictionMap.put("l_angle", predict.getFeather().getL_angle());
                predictionMap.put("d_angle", predict.getFeather().getD_angle());
                predictionMap.put("temperature", predict.getFeather().getTemperature());
                predictionMap.put("offset", predict.getFeather().getOffset());
                predictionMap.put("magnetic_angle", predict.getFeather().getMagnetic_angle());
                predictionMap.put("magnetic_amount", predict.getFeather().getMagnetic_amount());
                predictionMap.put("magnetic_amplitude", predict.getFeather().getMagnetic_amplitude());
                predictionMap.put("north_orientation", predict.getFeather().getNorth_orientation());
                predictionMap.put("high_orientation", predict.getFeather().getHigh_orientation());
                predictionMap.put("modelName", predict.getModel().getName());
                predictionMap.put("distance", predict.getDistance());
                result.add(predictionMap);
            } else {
                break;
            }
        }
        return result;
    }
    @Override
    public List<Predict> getPredictsByTask(String taskId) {
        return predictRepository.getPredictByTask(taskId);
    }
    @Override
    public List<Map<String, List<Map<String, Object>>>> getOffsetsByWellAndTask(String wellId, String taskId) {
        //当查询条件为空时返回空
        List<Map<String, List<Map<String, Object>>>> empty = new ArrayList<>();
        if (wellId == null || taskId == null) {
            return empty;
        }
        List<Predict> predicts = predictRepository.getPredictByWellAndTask(wellId, taskId);
        List<Map<String, List<Map<String, Object>>>> resultList = new ArrayList<>();
        // 将 predicts 分类到不同的模型名称对应的列表中
        Map<String, List<Map<String, Object>>> modelMap = new HashMap<>();
        for (Predict predict : predicts) {
            String modelName = predict.getModel().getName();
            List<Map<String, Object>> modelPredicts = modelMap.getOrDefault(modelName, new ArrayList<>());
            if (modelPredicts.size() < 10){
                Map<String, Object> predictData = new HashMap<>();
                predictData.put("x", "深" + predict.getFeather().getDepth() + "m");
                predictData.put("y", Math.abs(predict.getDistance() - predict.getFeather().getRef_distance()));
                modelPredicts.add(predictData);
                modelMap.put(modelName, modelPredicts);
            }
        }
        // 将分类好的数据添加到结果列表中
        for (Map.Entry<String, List<Map<String, Object>>> entry : modelMap.entrySet()) {
            Map<String, List<Map<String, Object>>> modelData = new HashMap<>();
            modelData.put(entry.getKey(), entry.getValue());
            resultList.add(modelData);
        }
        return resultList;
    }
    @Override
    public List<Predict> getPredictsByTime(ArrayList<Long> modelsId, String wellId, String taskId,String startTime, String endTime){
        List<Predict> results = new ArrayList<>();
        if (modelsId == null || wellId == null || taskId == null || startTime == null || endTime == null) {
            return results;
        } else if (modelsId.isEmpty()) {
            return results;
        }
        // 遍历每个modelId，单独查询每个model的数据，并限制每个model的数据条数为50
        for (Long modelId : modelsId) {
            ArrayList<Long> modelIdList = new ArrayList<>();
            modelIdList.add(modelId);
            List<Predict> partialResults = predictRepository.getPredictByModelAndWellAndTaskAndTime(
                    modelIdList, wellId, taskId, startTime, endTime, 50
            );
            if (partialResults != null) {
                results.addAll(partialResults);
            }
        }

        return results;
    }

    @Override
    public List<Predict> getAll() {
        List<Predict> predicts = this.predictRepository.findAll();
        return predicts;
    }

    @Override
    public List<Predict> findByModelName(String modelName) {
        return this.predictRepository.findByModelName(modelName);
    }

    @Override
    public ArrayList<BarData> getPredictNumber() {
        Integer days = 30;
        int[] months = new int[]{1, 3, 5, 7, 8, 10, 12};
        ArrayList<BarData> arrayList = new ArrayList<BarData>();
        Date endTime = new Date(System.currentTimeMillis());
        Calendar calendar = Calendar.getInstance();
        calendar.set(Calendar.SECOND, 0);
        calendar.set(Calendar.MINUTE, 0);
        calendar.set(Calendar.HOUR_OF_DAY, 0);
        calendar.set(Calendar.MILLISECOND, 0);
        long todayZero = calendar.getTimeInMillis();
        Date beginTime = new Date(todayZero);
        for (int i = 0; i < months.length; i++) {
            if (months[i] == beginTime.getMonth() || beginTime.getMonth() == 0) {
                days = 31;
                break;
            }
        }
        for (int i = 0; i < days; i++) {
            long number = this.predictRepository.countAllByCreateTimeBetween(beginTime, endTime);
            BarData barData = new BarData();
            barData.setX(String.valueOf(beginTime.getDate()) + '号');
            barData.setY(number);
            arrayList.add(barData);
            calendar.setTime(beginTime);
            calendar.add(Calendar.DATE, -1);
            long aheadZero = calendar.getTimeInMillis();
            endTime = beginTime;
            beginTime = new Date(aheadZero);
        }
        return arrayList;
    }

    @Override
    public Page<Predict> page(String wellId, String taskId, Pageable pageable) {
        return this.predictRepository.pageOfNameLike(wellId,taskId, pageable);
    }
}
