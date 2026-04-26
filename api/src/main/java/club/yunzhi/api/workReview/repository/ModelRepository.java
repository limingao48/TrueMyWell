package club.yunzhi.api.workReview.repository;

import club.yunzhi.api.workReview.entity.Model;
import club.yunzhi.api.workReview.entity.Well;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.repository.PagingAndSortingRepository;

import java.util.List;

public interface ModelRepository extends PagingAndSortingRepository<Model, Long>,
        JpaSpecificationExecutor<Model> {
}
