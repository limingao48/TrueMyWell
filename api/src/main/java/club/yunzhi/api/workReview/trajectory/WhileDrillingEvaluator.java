package club.yunzhi.api.workReview.trajectory;

import club.yunzhi.api.workReview.trajectory.iscwsa.IscwsaMwdParameters;

import java.util.Random;

/**
 * 随钻轨迹评估：对设计井进行同垂深水平距离计算，超阈值时基于偏移概率辅助停钻决策。
 */
public final class WhileDrillingEvaluator {

    public static final double DEFAULT_ALERT_DISTANCE_M = 30.0;
    public static final double EXTRAPOLATION_STEP_MD = 10.0;

    private WhileDrillingEvaluator() {
    }

    /** 同垂深水平距离(m)：在当前 TVD 处插值设计轨迹，计算 EN 平面距离 */
    public static double horizontalDistanceAtDepth(double[][] designTrajectory, double e, double n, double tvd) {
        if (designTrajectory == null || designTrajectory.length == 0) {
            return Double.NaN;
        }
        double[] designPt = WellObstacleDetector.interpolateAtDepth(designTrajectory, tvd);
        double dE = e - designPt[0];
        double dN = n - designPt[1];
        return Math.sqrt(dE * dE + dN * dN);
    }

    public static double[] designPointAtDepth(double[][] designTrajectory, double tvd) {
        return WellObstacleDetector.interpolateAtDepth(designTrajectory, tvd);
    }

    /**
     * 评估当前钻进位置相对设计轨迹的偏移，超阈值时计算偏移概率。
     *
     * @param beforePrevPoint A 点之前一点 C；若无则用井口确定 A 点入段方向
     * @param wellhead        井口坐标，当仅有 A→B 第一段且 beforePrevPoint 为空时使用
     */
    public static EvaluationResult evaluate(double[][] designTrajectory,
                                            TrajectoryExtrapolator.Point3D beforePrevPoint,
                                            TrajectoryExtrapolator.Point3D wellhead,
                                            TrajectoryExtrapolator.Point3D prevPoint,
                                            TrajectoryExtrapolator.Point3D currentPoint,
                                            double prevHorizontalDistance,
                                            double alertDistanceM,
                                            IscwsaMwdParameters mwdParams,
                                            int monteCarloSamples,
                                            double monteCarloStopThresholdPct,
                                            double monteCarloComprehensiveThresholdM) {
        double e = currentPoint.e;
        double n = currentPoint.n;
        double tvd = currentPoint.d;

        double horizontalDist = horizontalDistanceAtDepth(designTrajectory, e, n, tvd);
        double[] designPt = designPointAtDepth(designTrajectory, tvd);

        EvaluationResult result = new EvaluationResult();
        result.currentE = e;
        result.currentN = n;
        result.currentTvd = tvd;
        result.designE = designPt[0];
        result.designN = designPt[1];
        result.horizontalDistance = round2(horizontalDist);
        result.alertDistanceThreshold = alertDistanceM;

        boolean expanding = prevHorizontalDistance > 0
                && horizontalDist > prevHorizontalDistance + 0.01;
        result.distanceExpanding = expanding;

        TrajectoryExtrapolator.SegmentSurveys seg = null;
        if (prevPoint != null) {
            TrajectoryExtrapolator.Point3D beforeA = beforePrevPoint != null ? beforePrevPoint : wellhead;
            seg = TrajectoryExtrapolator.surveysFromPoints(beforeA, prevPoint, currentPoint);
            result.doglegDeg = round2(Math.toDegrees(seg.doglegRad));
            result.dlsDegPer30m = round2(seg.dlsDegPer30m);
        }

        if (horizontalDist <= alertDistanceM) {
            result.status = "正常";
            result.predictionTriggered = false;
            result.shouldStopDrilling = false;
            result.message = String.format("水平偏移 %.2f m，在设计允许范围内", horizontalDist);
            return result;
        }

        if (prevPoint == null) {
            result.predictionTriggered = false;
            result.status = "关注";
            result.shouldStopDrilling = false;
            result.message = String.format(
                    "水平偏移 %.2f m 超过阈值 %.0f m，需至少两个监测点方可计算偏移概率",
                    horizontalDist, alertDistanceM);
            return result;
        }

        result.predictionTriggered = true;

        if (mwdParams != null && monteCarloSamples > 0 && seg != null) {
            TrajectoryExtrapolator.Point3D[] mdChain = buildMdChain(wellhead, beforePrevPoint, prevPoint, currentPoint);
            double mdAlongB = WhileDrillingMonteCarloPredictor.estimateMdAlong(mdChain, currentPoint.d);
            WhileDrillingMonteCarloPredictor.MonteCarloResult mc = WhileDrillingMonteCarloPredictor.analyze(
                    designTrajectory, seg, currentPoint, mdAlongB,
                    monteCarloComprehensiveThresholdM,
                    EXTRAPOLATION_STEP_MD,
                    mwdParams, monteCarloSamples, monteCarloStopThresholdPct, new Random());
            result.monteCarloSampleCount = mc.sampleCount;
            result.monteCarloComprehensiveCount = mc.comprehensiveDeviationCount;
            result.monteCarloComprehensiveProbability = mc.comprehensiveProbability;
            result.monteCarloMeanSecondStepDistance = mc.meanSecondStepHorizontalDistance;
            result.monteCarloComprehensiveThresholdM = mc.deviationThresholdM;
            result.monteCarloStopRecommended = mc.stopRecommended;
            result.iscwsaSigmaMd = mc.sigmaMdMeters;
            result.iscwsaSigmaIncDeg = mc.sigmaIncDeg;
            result.iscwsaSigmaAziDeg = mc.sigmaAziDeg;
        }

        result.shouldStopDrilling = result.monteCarloStopRecommended;

        if (result.shouldStopDrilling) {
            result.status = "危险";
            result.message = String.format(
                    "水平偏移 %.2f m 超过阈值 %.0f m，偏移概率 %.1f%%（≥%.0f%%），建议停止钻进",
                    horizontalDist, alertDistanceM, result.monteCarloComprehensiveProbability,
                    monteCarloStopThresholdPct);
        } else if (result.monteCarloSampleCount > 0) {
            result.status = "预警";
            result.message = String.format(
                    "水平偏移 %.2f m 超过阈值 %.0f m，偏移概率 %.1f%%（停钻阈值 %.0f%%），请密切关注",
                    horizontalDist, alertDistanceM, result.monteCarloComprehensiveProbability,
                    monteCarloStopThresholdPct);
        } else {
            result.status = "关注";
            result.message = String.format(
                    "水平偏移 %.2f m 超过阈值 %.0f m，偏移概率分析未启用",
                    horizontalDist, alertDistanceM);
        }

        return result;
    }

    private static TrajectoryExtrapolator.Point3D[] buildMdChain(
            TrajectoryExtrapolator.Point3D wellhead,
            TrajectoryExtrapolator.Point3D beforePrev,
            TrajectoryExtrapolator.Point3D prev,
            TrajectoryExtrapolator.Point3D current) {
        int n = (wellhead != null ? 1 : 0) + (beforePrev != null ? 1 : 0) + (prev != null ? 1 : 0) + 1;
        TrajectoryExtrapolator.Point3D[] chain = new TrajectoryExtrapolator.Point3D[n];
        int i = 0;
        if (wellhead != null) {
            chain[i++] = wellhead;
        }
        if (beforePrev != null) {
            chain[i++] = beforePrev;
        }
        if (prev != null) {
            chain[i++] = prev;
        }
        chain[i] = current;
        return chain;
    }

    private static double round2(double v) {
        return Math.round(v * 100.0) / 100.0;
    }

    public static class EvaluationResult {
        public double currentE;
        public double currentN;
        public double currentTvd;
        public double designE;
        public double designN;
        public double horizontalDistance;
        public double alertDistanceThreshold;
        public boolean distanceExpanding;
        public boolean predictionTriggered;
        public boolean shouldStopDrilling;
        public String status;
        public String message;
        public Double doglegDeg;
        public Double dlsDegPer30m;
        public int monteCarloSampleCount;
        public int monteCarloComprehensiveCount;
        public double monteCarloComprehensiveProbability;
        public double monteCarloMeanSecondStepDistance;
        public double monteCarloComprehensiveThresholdM;
        public boolean monteCarloStopRecommended;
        public double iscwsaSigmaMd;
        public double iscwsaSigmaIncDeg;
        public double iscwsaSigmaAziDeg;
    }
}
