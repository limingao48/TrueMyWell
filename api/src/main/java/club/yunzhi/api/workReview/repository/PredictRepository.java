package club.yunzhi.api.workReview.repository;

import club.yunzhi.api.workReview.entity.Predict;
import club.yunzhi.api.workReview.entity.Task;
import club.yunzhi.api.workReview.repository.sepcs.PredictSpecs;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;

import org.springframework.data.jpa.domain.Specification;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.repository.PagingAndSortingRepository;

import java.sql.Timestamp;
import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.util.*;

public interface PredictRepository extends PagingAndSortingRepository<Predict, Long>,
        JpaSpecificationExecutor<Predict> {

    default List<Predict> getPredictByModelAndFeatherAndTask(ArrayList<Long> modelsId, String wellId, String taskId) {
        Specification<Predict> specification = PredictSpecs.idWellId(wellId).and(PredictSpecs.isModels(modelsId).and(PredictSpecs.idTaskId(taskId)));
        return this.findAll(specification);
    }

    default List<Predict> getPredictByWell(String wellId) {
        Specification<Predict> specification = PredictSpecs.idWellId(wellId).and(PredictSpecs.taskIsSelectedStatus(Task.STATUS_RUNNING));
        return this.findAll(specification);
    }

    default Integer getPredictNumberByWell(String wellId) {
        Specification<Predict> specification = PredictSpecs.idWellId(wellId);
        return Math.toIntExact(this.count(specification));
    }

    default Integer getWeekPredictNumberByWell(String wellId) {
        long[] times = PredictRepository.getCurrentWeekTimeFrame();
        Timestamp beginTime = new Timestamp(times[0]);
        Timestamp endTime = new Timestamp(times[1]);
        Specification<Predict> specification = PredictSpecs.idWellId(wellId)
                .and(PredictSpecs.createTimeBetweenUseTimeStamp(beginTime, endTime));
        return Math.toIntExact(this.count(specification));
    }

    default Integer getTodayPredictNumberByWell(String wellId) {
        Date endTime = new Date(System.currentTimeMillis());
        Calendar calendar = Calendar.getInstance();
        calendar.set(Calendar.SECOND, 0);
        calendar.set(Calendar.MINUTE, 0);
        calendar.set(Calendar.HOUR_OF_DAY, 0);
        calendar.set(Calendar.MILLISECOND, 0);
        long todayZero = calendar.getTimeInMillis();
        Date beginTime = new Date(todayZero);
        Timestamp begin = new Timestamp(beginTime.getTime()), end = new Timestamp(endTime.getTime());
        DateFormat sdf = new SimpleDateFormat("yyyy/MM/dd HH:mm:ss");
        String beginString = sdf.format(begin);
        String endString = sdf.format(end);
//        String beigin = String.valueOf(beginTime), end = String.valueOf(endTime);
        Specification<Predict> specification = PredictSpecs.idWellId(wellId)
                .and(PredictSpecs.createTimeBetweenUseTimeStamp(begin, end));
        return Math.toIntExact(this.count(specification));
    }

    default List<Predict> getPredictByWellAndTask(String wellId, String taskId) {
        Specification<Predict> specification = PredictSpecs.idWellId(wellId).and(PredictSpecs.idTaskId(taskId));
        Sort sort = PredictSpecs.sortByCreateTimeDesc();
        return this.findAll(specification, sort);
    }
    default List<Predict> getPredictByTask(String taskId) {
        Specification<Predict> specification = PredictSpecs.idTaskId(taskId);
        return this.findAll(specification);
    }
    // 修改方法以接受limit参数
    default List<Predict> getPredictByModelAndWellAndTaskAndTime(ArrayList<Long> modelsId, String wellId, String taskId, String startTime, String endTime, int limit) {
        // 创建Specification
        Specification<Predict> specification = PredictSpecs.idWellId(wellId)
                .and(PredictSpecs.isModels(modelsId))
                .and(PredictSpecs.idTaskId(taskId))
                .and(PredictSpecs.createTimeBetween(startTime, endTime));

        // 创建Pageable对象，这里我们使用limit作为页面大小，第一页
        Pageable pageable = PageRequest.of(0, limit);

        // 使用Specification和Pageable执行查询
        Page<Predict> page = this.findAll(specification, pageable);
        return page.getContent(); // 返回页面内容
    }


    long countAllByCreateTimeBetween(Date beginTime, Date endTime);
          
    List<Predict> findAll();

    List<Predict> findByModelName(String modelName);

    public static long[] getCurrentWeekTimeFrame() {
        Calendar calendar = Calendar.getInstance();
        calendar.setTimeZone(TimeZone.getTimeZone("GMT+8"));
        //start of the week
        if (calendar.get(Calendar.DAY_OF_WEEK) == Calendar.SUNDAY) {
            calendar.add(Calendar.DAY_OF_YEAR,-1);
        }
        calendar.add(Calendar.DAY_OF_WEEK, -(calendar.get(Calendar.DAY_OF_WEEK) - 2));
        calendar.set(Calendar.HOUR_OF_DAY, 0);
        calendar.set(Calendar.MINUTE, 0);
        calendar.set(Calendar.SECOND, 0);
        calendar.set(Calendar.MILLISECOND, 0);

        long startTime = calendar.getTimeInMillis();
        //end of the week
        calendar.add(Calendar.DAY_OF_WEEK, 6);
        calendar.set(Calendar.HOUR_OF_DAY, 23);
        calendar.set(Calendar.MINUTE, 59);
        calendar.set(Calendar.SECOND, 59);
        calendar.set(Calendar.MILLISECOND, 999);
        long endTime = calendar.getTimeInMillis();
        return new long[]{startTime, endTime};
    }

    default Page<Predict> pageOfNameLike(String wellId, String taskId, Pageable pageable) {
        Specification<Predict> specification = PredictSpecs.idTaskId(taskId)
                .and(PredictSpecs.idWellId(wellId));
        return this.findAll(specification, pageable);
    }
}


