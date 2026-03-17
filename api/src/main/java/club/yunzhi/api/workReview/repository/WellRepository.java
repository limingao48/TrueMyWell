package club.yunzhi.api.workReview.repository;

import club.yunzhi.api.workReview.entity.Well;
import club.yunzhi.api.workReview.repository.sepcs.WellSpecs;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.repository.PagingAndSortingRepository;

import java.util.List;

public interface WellRepository extends PagingAndSortingRepository<Well, Long>,
        JpaSpecificationExecutor<Well> {
    List<Well> findAll();

    default Page<Well> pageOfWellIdEqual(String wellId, Pageable pageable) {
        Specification<Well> specification = WellSpecs.equalWellId(wellId);
        return this.findAll(specification, pageable);
    }

    long count();

    Well findByUniqueKey(String uniqueKey);
}
