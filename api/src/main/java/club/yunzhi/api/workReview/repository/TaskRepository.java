package club.yunzhi.api.workReview.repository;

import club.yunzhi.api.workReview.entity.Task;
import club.yunzhi.api.workReview.repository.sepcs.TaskSpecs;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.repository.PagingAndSortingRepository;

import java.sql.Timestamp;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Optional;

public interface TaskRepository extends PagingAndSortingRepository<Task, Long>,
        JpaSpecificationExecutor<Task> {
    default Page<Task> pageOfNameLike(String name, String wellId, ArrayList<Long> modelIds, Integer status, String startDate, String endDate, Pageable pageable) {
        Specification<Task> specification = TaskSpecs.containingName(name)
                .and(TaskSpecs.idWellId(wellId))
                .and(TaskSpecs.isModels(modelIds))
                .and(TaskSpecs.isStatus(status))
                .and(TaskSpecs.timeBetween(startDate, endDate));
        return this.findAll(specification, pageable);
    }

    default List<Task> getTaskByWell(String wellId) {
        Specification<Task> specification = TaskSpecs.idWellId(wellId);
        return this.findAll(specification);
    }

    Optional<Task> findById(Long id);

    long count();

    long countAllByUpdateTimeBetween(Date beginTime, Date endTime);

    long countAllByWellIdAndUpdateTimeBetweenAndStatus(Long wellId, Date beginTime, Date endTime, Integer status);

    default List<Task> getRunningTask() {
        Specification<Task> specification = TaskSpecs.idRun();
        return this.findAll(specification);
    }

    default long byWellIdGetRunningTask(String wellId) {
        Specification<Task> specification = TaskSpecs.idRun().and(TaskSpecs.idWellId(wellId));
        return this.count(specification);
    }

    int countAllByWellId(Long wellId);

    List<Task> findByStatusAndWellId(Integer status, Long wellId);
}
