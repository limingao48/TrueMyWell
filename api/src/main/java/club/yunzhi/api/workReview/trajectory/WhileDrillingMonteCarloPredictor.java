package club.yunzhi.api.workReview.trajectory;

import club.yunzhi.api.workReview.trajectory.iscwsa.IscwsaMwdParameters;
import club.yunzhi.api.workReview.trajectory.iscwsa.PolylineHoleGeometry;

import java.util.Random;

/**
 * ISCWSA MWD 误差蒙特卡洛：抽样后外推 2 步，统计综合概率。
 * 判定一次「偏差」：下一步水平偏移 &gt; 阈值，且下下步偏移更大。
 */
public final class WhileDrillingMonteCarloPredictor {

    /** 蒙特卡洛仅外推 2 步（下一步 + 下下步） */
    public static final int MC_EXTRAPOLATION_STEPS = 2;

    private WhileDrillingMonteCarloPredictor() {
    }

    public static class MonteCarloResult {
        public int sampleCount;
        /** 满足「下一步&gt;阈值且下下步更大」的样本数 */
        public int comprehensiveDeviationCount;
        /** 综合概率 (0~100%) */
        public double comprehensiveProbability;
        /** 下下步水平偏移样本均值 (m) */
        public double meanSecondStepHorizontalDistance;
        public boolean stopRecommended;
        public double sigmaMdMeters;
        public double sigmaIncDeg;
        public double sigmaAziDeg;
        public double deviationThresholdM;
    }

    public static MonteCarloResult analyze(
            double[][] designTrajectory,
            TrajectoryExtrapolator.SegmentSurveys nominalSeg,
            TrajectoryExtrapolator.Point3D currentPoint,
            double mdAlongB,
            double comprehensiveDeviationThresholdM,
            double extrapolationStepMd,
            IscwsaMwdParameters mwdParams,
            int sampleCount,
            double stopProbabilityThresholdPct,
            Random random) {

        MonteCarloResult mc = new MonteCarloResult();
        mc.sampleCount = sampleCount;
        mc.deviationThresholdM = comprehensiveDeviationThresholdM;
        mc.sigmaMdMeters = mwdParams.sigmaMdMeters;
        mc.sigmaIncDeg = Math.toDegrees(mwdParams.sigmaIncRad);
        mc.sigmaAziDeg = Math.toDegrees(mwdParams.sigmaAziRad);

        if (sampleCount <= 0 || nominalSeg == null || currentPoint == null) {
            mc.comprehensiveProbability = 0;
            return mc;
        }

        int comprehensiveCount = 0;
        double[] secondStepDists = new double[sampleCount];

        for (int s = 0; s < sampleCount; s++) {
            double dIncA = gaussian(random) * mwdParams.sigmaIncRad;
            double dAziA = gaussian(random) * mwdParams.sigmaAziRad;
            double dIncB = gaussian(random) * mwdParams.sigmaIncRad;
            double dAziB = gaussian(random) * mwdParams.sigmaAziRad;
            double dMd = gaussian(random) * mwdParams.sigmaMdMeters;

            double incA = nominalSeg.incA + dIncA;
            double aziA = nominalSeg.aziA + dAziA;
            double incB = nominalSeg.incB + dIncB;
            double aziB = nominalSeg.aziB + dAziB;

            TrajectoryExtrapolator.SegmentSurveys perturbedSeg = buildPerturbedSegment(
                    incA, aziA, incB, aziB, nominalSeg.mdSeg);

            double[] posDelta = positionErrorDelta(mdAlongB, incB, aziB, dIncB, dAziB, dMd);
            TrajectoryExtrapolator.Point3D perturbedB = new TrajectoryExtrapolator.Point3D(
                    currentPoint.e + posDelta[0],
                    currentPoint.n + posDelta[1],
                    currentPoint.d + posDelta[2]);

            TrajectoryExtrapolator.Point3D[] extrap = TrajectoryExtrapolator.extrapolateConstantDls(
                    perturbedSeg, perturbedB, extrapolationStepMd, MC_EXTRAPOLATION_STEPS);

            double[] futureDists = new double[extrap.length];
            for (int i = 0; i < extrap.length; i++) {
                TrajectoryExtrapolator.Point3D p = extrap[i];
                futureDists[i] = WhileDrillingEvaluator.horizontalDistanceAtDepth(
                        designTrajectory, p.e, p.n, p.d);
            }

            secondStepDists[s] = futureDists.length >= 2
                    ? futureDists[1]
                    : (futureDists.length == 1 ? futureDists[0] : 0);

            if (isComprehensiveDeviation(futureDists, comprehensiveDeviationThresholdM)) {
                comprehensiveCount++;
            }
        }

        mc.comprehensiveDeviationCount = comprehensiveCount;
        mc.comprehensiveProbability = round2(100.0 * comprehensiveCount / sampleCount);
        mc.meanSecondStepHorizontalDistance = round2(mean(secondStepDists));
        mc.stopRecommended = mc.comprehensiveProbability >= stopProbabilityThresholdPct;
        return mc;
    }

    /**
     * 综合偏差判定：外推第 1 步偏移 &gt; 阈值，且第 2 步偏移 &gt; 第 1 步。
     */
    static boolean isComprehensiveDeviation(double[] futureDists, double thresholdM) {
        if (futureDists == null || futureDists.length < 2) {
            return false;
        }
        return futureDists[0] > thresholdM && futureDists[1] > futureDists[0] + 0.01;
    }

    public static double estimateMdAlong(TrajectoryExtrapolator.Point3D[] chain, double tvd) {
        if (chain == null || chain.length < 2) {
            return Math.max(tvd, 1.0);
        }
        double[][] rows = new double[chain.length][3];
        for (int i = 0; i < chain.length; i++) {
            rows[i][0] = chain[i].e;
            rows[i][1] = chain[i].n;
            rows[i][2] = chain[i].d;
        }
        rows = WellObstacleDetector.normalizeRowPoints(rows);
        PolylineHoleGeometry.Sample sample = PolylineHoleGeometry.sampleAtDepth(rows, tvd);
        return sample != null ? Math.max(sample.mdAlong, 1.0) : Math.max(tvd, 1.0);
    }

    static double[] positionErrorDelta(double mdAlong, double incRad, double aziRad,
                                       double deltaInc, double deltaAzi, double deltaMd) {
        double sinI = Math.sin(incRad);
        double cosI = Math.cos(incRad);
        double sinA = Math.sin(aziRad);
        double cosA = Math.cos(aziRad);

        double dE = deltaMd * sinI * sinA
                + mdAlong * (cosI * deltaInc * sinA + sinI * cosA * deltaAzi);
        double dN = deltaMd * sinI * cosA
                + mdAlong * (cosI * deltaInc * cosA - sinI * sinA * deltaAzi);
        double dD = deltaMd * cosI - mdAlong * sinI * deltaInc;
        return new double[]{dE, dN, dD};
    }

    private static TrajectoryExtrapolator.SegmentSurveys buildPerturbedSegment(
            double incA, double aziA, double incB, double aziB, double mdSeg) {
        double dogleg = TrajectoryExtrapolator.computeDogleg(incA, aziA, incB, aziB);
        double md = mdSeg < 1e-9 ? 1e-9 : mdSeg;
        double dls = Math.toDegrees(dogleg) / md * 30.0;
        return new TrajectoryExtrapolator.SegmentSurveys(incA, aziA, incB, aziB, mdSeg, dogleg, dls);
    }

    private static double gaussian(Random random) {
        double u1 = Math.max(random.nextDouble(), 1e-12);
        double u2 = random.nextDouble();
        return Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2);
    }

    private static double mean(double[] values) {
        if (values.length == 0) {
            return 0;
        }
        double sum = 0;
        for (double v : values) {
            sum += v;
        }
        return sum / values.length;
    }

    private static double round2(double v) {
        return Math.round(v * 100.0) / 100.0;
    }
}
