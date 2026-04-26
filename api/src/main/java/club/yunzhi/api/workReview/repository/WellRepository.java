package club.yunzhi.api.workReview.repository;

import club.yunzhi.api.workReview.entity.Well;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.repository.PagingAndSortingRepository;

/**
 * 井仓库
 */
public interface WellRepository extends PagingAndSortingRepository<Well, Long>,
        JpaSpecificationExecutor<Well> {
}
