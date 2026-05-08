package club.yunzhi.api.workReview.trajectory.iscwsa;

import club.yunzhi.api.workReview.trajectory.WellTrajectoryConfig;

/**
 * ISCWSA 类 MWD 测斜不确定度（1σ，与 {@link IscwsaMwdSeparationFactor} 中管状椭球模型配套）。
 * 全为标量 MWD 典型量级，非完整 178 项误差模型。
 */
public final class IscwsaMwdParameters {

    /** 测深 1σ 不确定度 (m) */
    public final double sigmaMdMeters;
    /** 井斜 1σ 不确定度 (rad) */
    public final double sigmaIncRad;
    /** 方位 1σ 不确定度 (rad) */
    public final double sigmaAziRad;

    public IscwsaMwdParameters(double sigmaMdMeters, double sigmaIncRad, double sigmaAziRad) {
        this.sigmaMdMeters = Math.max(1e-6, sigmaMdMeters);
        this.sigmaIncRad = Math.max(1e-9, sigmaIncRad);
        this.sigmaAziRad = Math.max(1e-9, sigmaAziRad);
    }

    public static IscwsaMwdParameters fromConfig(WellTrajectoryConfig config) {
        return new IscwsaMwdParameters(
                config.iscwsaSigmaMdMeters,
                Math.toRadians(config.iscwsaSigmaIncDegrees),
                Math.toRadians(config.iscwsaSigmaAziDegrees));
    }
}
