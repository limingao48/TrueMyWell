package club.yunzhi.api.workReview.repository.sepcs;

import club.yunzhi.api.workReview.entity.TrajectoryFile;
import org.springframework.data.jpa.domain.Specification;

public class TrajectoryFileSpecs {
    /**
     * 按轨迹文件Id查询.
     *
     * @param trajectoryFileId trajectoryFileId
     * @return 谓语
     */
    public static Specification<TrajectoryFile> equalTrajectoryFileIdId(String trajectoryFileId) {
        if (trajectoryFileId != null) {
            return (root, criteriaQuery, criteriaBuilder) ->
                    criteriaBuilder.like(root.get("id").as(String.class), trajectoryFileId);
        } else {
            return Specification.where(null);
        }
    }
}
