package club.yunzhi.api.workReview.trajectory.iscwsa;

import club.yunzhi.api.workReview.trajectory.WellObstacleDetector;

/**
 * ISCWSA-MWD 简化：井眼位置不确定度取沿井眼方向 σ_MD 与横向 σ⊥ 的包络，
 * 误差椭球长半轴 R = max(σ_MD, σ⊥)，其中
 * σ⊥ ≈ MD · √(σ_inc² + sin²(I)·σ_azi²)（小角 MWD 横向传播常用形式）。
 * <p>
 * 分离系数（与图示一致）： f_S = R_S / (R_1 + R_2)，
 * R_S 为同一垂深处两口井井眼中心三维距离，R_1、R_2 为两口井误差椭球长半轴。
 */
public final class IscwsaMwdSeparationFactor {

    private IscwsaMwdSeparationFactor() {
    }

    /**
     * 误差椭球长半轴 (m)，管状协方差主轴近似。
     */
    public static double semiMajorAxisMeters(double mdAlong, double incRad, IscwsaMwdParameters p) {
        double sigmaPerp = mdAlong * Math.sqrt(
                p.sigmaIncRad * p.sigmaIncRad
                        + Math.sin(incRad) * Math.sin(incRad) * p.sigmaAziRad * p.sigmaAziRad);
        return Math.max(p.sigmaMdMeters, sigmaPerp);
    }

    /**
     * 在重叠垂深窗内按步长扫描，返回最小的分离系数 f_S（越小越危险）。
     */
    public static double minimumSeparationFactorScan(double[][] designTrajectory,
                                                     double[][] obstacleSortedRows,
                                                     IscwsaMwdParameters designParams,
                                                     IscwsaMwdParameters obstacleParams,
                                                     double depthStepMeters) {
        double[][] subject = WellObstacleDetector.normalizeRowPoints(designTrajectory);
        double[][] obs = obstacleSortedRows;
        if (subject.length < 2 || obs.length < 2) {
            return Double.POSITIVE_INFINITY;
        }

        double zMin = Math.max(subject[0][2], obs[0][2]);
        double zMax = Math.min(subject[subject.length - 1][2], obs[obs.length - 1][2]);
        if (zMax <= zMin) {
            return Double.POSITIVE_INFINITY;
        }

        double minFs = Double.POSITIVE_INFINITY;
        for (double d = zMin; d <= zMax + 1e-9; d += depthStepMeters) {
            PolylineHoleGeometry.Sample sSub = PolylineHoleGeometry.sampleAtDepth(subject, d);
            PolylineHoleGeometry.Sample sObs = PolylineHoleGeometry.sampleAtDepth(obs, d);
            if (sSub == null || sObs == null) {
                continue;
            }
            double dx = sSub.e - sObs.e;
            double dy = sSub.n - sObs.n;
            double dz = sSub.d - sObs.d;
            double rS = Math.sqrt(dx * dx + dy * dy + dz * dz);

            double r1 = semiMajorAxisMeters(sSub.mdAlong, sSub.incRad, designParams);
            double r2 = semiMajorAxisMeters(sObs.mdAlong, sObs.incRad, obstacleParams);
            double denom = r1 + r2;
            if (denom < 1e-9) {
                continue;
            }
            double f = rS / denom;
            if (f < minFs) {
                minFs = f;
            }
        }
        return minFs;
    }
}
