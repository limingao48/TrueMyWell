package club.yunzhi.api.workReview.repository;

import club.yunzhi.api.workReview.entity.TrajectoryFile;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.repository.PagingAndSortingRepository;

/**
 * 井仓库
 */
public interface TrajectoryFileRepository extends PagingAndSortingRepository<TrajectoryFile, Long>,
        JpaSpecificationExecutor<TrajectoryFile> {
}
