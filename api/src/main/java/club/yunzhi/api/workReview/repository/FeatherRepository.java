package club.yunzhi.api.workReview.repository;

import club.yunzhi.api.workReview.entity.Feather;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.repository.PagingAndSortingRepository;

import java.util.List;

public interface FeatherRepository  extends PagingAndSortingRepository<Feather, Long>,
        JpaSpecificationExecutor<Feather> {
    List<Feather> findByWellIdOrderByCreateTimeDesc(long wellId, Pageable pageable);

    Long countAllByWellId(long wellId);
}
