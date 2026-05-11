package club.yunzhi.api.workReview.trajectory;

import club.yunzhi.api.workReview.entity.TrajectoryDesignRequest;

/**
 * 将前端 {@link TrajectoryDesignRequest.Algorithm} 中的防碰选项写入 {@link WellTrajectoryConfig}，
 * 供「开始设计」与同步 {@code POST /trajectory/design} 共用。
 */
public final class TrajectoryAnticollisionConfig {

    private TrajectoryAnticollisionConfig() {
    }

    /**
     * 规范化方法名：仅区分 SF 与其它（其它一律按 CTC 井眼中心距阈值处理）。
     */
    public static String normalizeAnticollisionMethod(String raw) {
        if (raw == null || raw.trim().isEmpty()) {
            return "CTC";
        }
        return "SF".equalsIgnoreCase(raw.trim()) ? "SF" : "CTC";
    }

    public static void applyFromAlgorithm(TrajectoryDesignRequest.Algorithm algorithm, WellTrajectoryConfig config) {
        if (algorithm == null || config == null) {
            return;
        }
        if (algorithm.getSafeRadius() != null && algorithm.getSafeRadius() > 0) {
            config.safetyRadius = algorithm.getSafeRadius();
        }
        if (algorithm.getMinSafetyFactor() != null && algorithm.getMinSafetyFactor() > 0) {
            config.minSafetyFactor = algorithm.getMinSafetyFactor();
        }
        if (algorithm.getAnticollisionMethod() != null && !algorithm.getAnticollisionMethod().trim().isEmpty()) {
            config.anticollisionMethod = normalizeAnticollisionMethod(algorithm.getAnticollisionMethod());
        }
        if (algorithm.getIscwsaSigmaMd() != null && algorithm.getIscwsaSigmaMd() > 0) {
            config.iscwsaSigmaMdMeters = algorithm.getIscwsaSigmaMd();
        }
        if (algorithm.getIscwsaSigmaIncDeg() != null && algorithm.getIscwsaSigmaIncDeg() > 0) {
            config.iscwsaSigmaIncDegrees = algorithm.getIscwsaSigmaIncDeg();
        }
        if (algorithm.getIscwsaSigmaAziDeg() != null && algorithm.getIscwsaSigmaAziDeg() > 0) {
            config.iscwsaSigmaAziDegrees = algorithm.getIscwsaSigmaAziDeg();
        }
    }
}
