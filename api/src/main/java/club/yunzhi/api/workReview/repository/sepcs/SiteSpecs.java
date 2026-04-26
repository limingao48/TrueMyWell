package club.yunzhi.api.workReview.repository.sepcs;

import club.yunzhi.api.workReview.entity.Site;
import org.springframework.data.jpa.domain.Specification;

public class SiteSpecs {
    /**
     * 按井场Id查询.
     *
     * @param siteId siteId
     * @return 谓语
     */
    public static Specification<Site> equalSiteId(String siteId) {
        if (siteId != null) {
            return (root, criteriaQuery, criteriaBuilder) ->
                    criteriaBuilder.like(root.get("id").as(String.class), siteId);
        } else {
            return Specification.where(null);
        }
    }
}
