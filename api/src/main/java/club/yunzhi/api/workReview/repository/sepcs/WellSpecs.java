package club.yunzhi.api.workReview.repository.sepcs;

import club.yunzhi.api.workReview.entity.Well;
import org.springframework.data.jpa.domain.Specification;

public class WellSpecs {
    /**
     * 按井Id查询.
     *
     * @param wellId wellId
     * @return 谓语
     */
    public static Specification<Well> equalWellId(String wellId) {
        if (wellId != null) {
            return (root, criteriaQuery, criteriaBuilder) ->
                    criteriaBuilder.like(root.get("id").as(String.class), wellId);
        } else {
            return Specification.where(null);
        }
    }
}
