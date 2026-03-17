package club.yunzhi.api.workReview.service;

import club.yunzhi.api.workReview.entity.Message;
import club.yunzhi.api.workReview.entity.Task;
import club.yunzhi.api.workReview.entity.Well;
import club.yunzhi.api.workReview.repository.PredictRepository;
import club.yunzhi.api.workReview.repository.TaskRepository;
import club.yunzhi.api.workReview.repository.WellRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class WellServiceImpl implements WellService {
    private final WellRepository wellRepository;
    private final TaskRepository taskRepository;

    private final PredictRepository predictRepository;

    public WellServiceImpl(WellRepository wellRepository,
                           TaskRepository taskRepository,
                           PredictRepository predictRepository) {
        this.wellRepository = wellRepository;
        this.taskRepository = taskRepository;
        this.predictRepository = predictRepository;
    }

    @Override
    public List<Well> getAll() {
        List<Well> wells = this.wellRepository.findAll();
        return wells;
    }

    @Override
    public Long getAllNumber() {
        return this.wellRepository.count();
    }

    @Override
    public Page<Well> page(String wellId, Pageable pageable) {
        Page<Well> wells = this.wellRepository.pageOfWellIdEqual(wellId, pageable);
        for (Well well: wells) {
            Integer taskNumber = this.taskRepository.countAllByWellId(well.getId());
            Integer totalPredictNumber = this.predictRepository.getPredictNumberByWell(well.getId().toString());
            Integer weekPredictNumber = this.predictRepository.getWeekPredictNumberByWell(well.getId().toString());
            Integer TodayPredictNumber = this.predictRepository.getTodayPredictNumberByWell(well.getId().toString());
            well.setTaskNumber(taskNumber);
            well.setPredictTotalNumber(totalPredictNumber);
            well.setWeekPredictNumber(weekPredictNumber);
            well.setTodayPredictNumber(TodayPredictNumber);
            this.wellRepository.save(well);
        }
        Page<Well> res = this.wellRepository.pageOfWellIdEqual(wellId, pageable);
        return res;
    }

    @Override
    public String add(Well well) {
        Well well1 = new Well();
        well1.setPredictNumber(0);
        well1.setUniqueKey(well.getUniqueKey());
        well1.setWeekPredictNumber(0);
        well1.setTaskNumber(0);
        well1.setName(well.getName());
        well1.setTodayPredictNumber(0);
        well1.setPredictTotalNumber(0);
        try {
            this.wellRepository.save(well1);
        } catch (Exception e) {
            return "传输数据不合格";
        }
        return "传输数据合格";
    }

    @Override
    public Well getById(String wellId) {
        if(wellId == null)
            return null;
        if(this.wellRepository.findById(Long.valueOf(wellId)).isPresent()){
            return this.wellRepository.findById(Long.valueOf(wellId)).get();
        }else {
            return null;
        }
    }
}
