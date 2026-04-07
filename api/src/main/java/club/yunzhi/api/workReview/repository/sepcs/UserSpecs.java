package club.yunzhi.api.workReview.repository.sepcs;

import club.yunzhi.api.workReview.entity.User;
import org.springframework.data.jpa.domain.Specification;

public class UserSpecs {
    /**
     * 按用户Id查询.
     *
     * @param userId userId
     * @return 谓语
     */
    public static Specification<User> equalUserId(String userId) {
        if (userId != null) {
            return (root, criteriaQuery, criteriaBuilder) ->
                    criteriaBuilder.like(root.get("id").as(String.class), userId);
        } else {
            return Specification.where(null);
        }
    }
}
