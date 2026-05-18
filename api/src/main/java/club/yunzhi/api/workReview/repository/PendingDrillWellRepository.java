package club.yunzhi.api.workReview.repository;

import club.yunzhi.api.workReview.entity.PendingDrillWell;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.repository.PagingAndSortingRepository;

import java.util.List;

public interface PendingDrillWellRepository extends PagingAndSortingRepository<PendingDrillWell, Long>,
        JpaSpecificationExecutor<PendingDrillWell> {

    List<PendingDrillWell> findAllByOrderByIdDesc();

    List<PendingDrillWell> findBySiteIdOrderByIdDesc(Long siteId);
}
