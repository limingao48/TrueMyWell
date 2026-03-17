package club.yunzhi.api.workReview.service;

import club.yunzhi.api.workReview.entity.BarData;
import club.yunzhi.api.workReview.entity.Task;
import club.yunzhi.api.workReview.repository.TaskRepository;
import com.mengyunzhi.core.annotation.query.In;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;

import java.sql.Timestamp;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
import java.util.List;

@Service
public class TaskServiceImpl implements TaskService {
    private final TaskRepository taskRepository;

    public TaskServiceImpl(TaskRepository taskRepository) {
        this.taskRepository = taskRepository;
    }

    @Override
    public Page<Task> page(String name, String wellId, ArrayList<Long> models, Integer status, String startDate, String endDate, Pageable pageable) {
        return this.taskRepository.pageOfNameLike(name, wellId, models, status, startDate, endDate, pageable);
    }

    @Override
    public List<Task> getTasksByWell(String wellId) {
        return this.taskRepository.getTaskByWell(wellId);
    }

    @Override
    public Task add(Task task) {
        String wellId = String.valueOf(task.getWell().getId());
        // 首先需要查一下当前井对应的任务是否有在启动的，有的话就不需要订阅了
        long runTasks = this.taskRepository.byWellIdGetRunningTask(wellId);
        if (runTasks == 0) {
            // 如果当前没有正在启动的任务说明需要向对方发起订阅请求
            // TODO 向对方发起订阅请求通过uniqueKey
//            TaskService.requestSubOrUnSub(task.getWell().getUniqueKey(), "1");
        }
        Task task1 = new Task();
        task1.setName(task.getName());
        task1.setWell(task.getWell());
        task1.setModels(task.getModels());
        task1.setPredictNumber(0);
        task1.setUpdateTime(new Timestamp(System.currentTimeMillis()));
        return this.taskRepository.save(task1);
    }

    @Override
    public Task run(Long taskId) {
        Task task = this.taskRepository.findById(taskId).get();
        task.setStatus(Task.STATUS_RUNNING);
        // 将时间也要更新为启动的时间
        task.setUpdateTime(new Timestamp(System.currentTimeMillis()));
        this.taskRepository.save(task);
        return task;
    }

    @Override
    public Task freeze(Long taskId) {
        Task task = this.taskRepository.findById(taskId).get();
        task.setStatus(Task.STATUS_FREEZE);
        this.taskRepository.save(task);
        return task;
    }

    @Override
    public Task edit(Long id, Task task) {
        Task task1 = this.taskRepository.findById(id).get();
        task1.setName(task.getName());
        this.taskRepository.save(task1);
        return task1;
    }

    @Override
    public Long getAllNumber() {
        return this.taskRepository.count();
    }

    @Override
    public Long monthTaskNumber() {
        Date currentTime = new Date(System.currentTimeMillis());
        Date beginTime = new Date(System.currentTimeMillis() - 2592000000L);
        return this.taskRepository.countAllByUpdateTimeBetween(beginTime, currentTime);
    }

    @Override
    public long todayTaskNumber() {
        Date currentTime = new Date(System.currentTimeMillis());
        Calendar calendar = Calendar.getInstance();
        calendar.set(Calendar.SECOND, 0);
        calendar.set(Calendar.MINUTE, 0);
        calendar.set(Calendar.HOUR_OF_DAY, 0);
        calendar.set(Calendar.MILLISECOND, 0);
        long todayZero = calendar.getTimeInMillis();
        Date beginTime = new Date(todayZero);
        return this.taskRepository.countAllByUpdateTimeBetween(beginTime, currentTime);
    }

    @Override
    public ArrayList<BarData> getMonthTaskNumber() {
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
            long number = this.taskRepository.countAllByUpdateTimeBetween(beginTime, endTime);
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
    public void delete(Long id) {
        this.taskRepository.deleteById(id);
    }

    @Override
    public Integer getTaskNumberByWellIdAndStatus(Long wellId, Integer status) {
        Date endTime = new Date(System.currentTimeMillis());
        Calendar calendar = Calendar.getInstance();
        calendar.set(Calendar.SECOND, 0);
        calendar.set(Calendar.MINUTE, 0);
        calendar.set(Calendar.HOUR_OF_DAY, 0);
        calendar.set(Calendar.MILLISECOND, 0);
        long todayZero = calendar.getTimeInMillis();
        Date beginTime = new Date(todayZero);
        return Math.toIntExact(this.taskRepository.countAllByWellIdAndUpdateTimeBetweenAndStatus(wellId, beginTime, endTime, status));
    }
}
