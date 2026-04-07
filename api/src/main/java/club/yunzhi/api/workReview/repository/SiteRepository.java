package club.yunzhi.api.workReview.repository;

import club.yunzhi.api.workReview.entity.Site;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.repository.PagingAndSortingRepository;

/**
 * 井场仓库
 */
public interface SiteRepository extends PagingAndSortingRepository<Site, Long>,
        JpaSpecificationExecutor<Site> {
}
