package club.yunzhi.api.workReview.trajectory;

/**
 * 轨迹外推：由监测点序列估计 A→B 段测斜，假设全角变化率（DLS）维持恒定，沿测深外延后续点。
 */
public final class TrajectoryExtrapolator {

    private TrajectoryExtrapolator() {
    }

    /** 三维点 [E, N, D] */
    public static class Point3D {
        public final double e;
        public final double n;
        public final double d;

        public Point3D(double e, double n, double d) {
            this.e = e;
            this.n = n;
            this.d = d;
        }
    }

    /** 测斜状态：井斜(rad)、方位(rad)、段长(m) */
    public static class SurveyState {
        public final double inc;
        public final double azi;
        public final double md;

        public SurveyState(double inc, double azi, double md) {
            this.inc = inc;
            this.azi = azi;
            this.md = md;
        }
    }

    /** A→B 段测斜：A 点入段方向、B 点出段方向及狗腿 */
    public static class SegmentSurveys {
        public final double incA;
        public final double aziA;
        public final double incB;
        public final double aziB;
        public final double mdSeg;
        public final double doglegRad;
        public final double dlsDegPer30m;

        public SegmentSurveys(double incA, double aziA, double incB, double aziB,
                              double mdSeg, double doglegRad, double dlsDegPer30m) {
            this.incA = incA;
            this.aziA = aziA;
            this.incB = incB;
            this.aziB = aziB;
            this.mdSeg = mdSeg;
            this.doglegRad = doglegRad;
            this.dlsDegPer30m = dlsDegPer30m;
        }
    }

    /**
     * 由三点 C→A→B 估计 A→B 段测斜。
     *
     * @param beforeA A 点之前一点（通常为 C）；若无则传井口，用于确定 A 点入段方向
     * @param a       上一监测点 A
     * @param b       当前监测点 B
     */
    public static SegmentSurveys surveysFromPoints(Point3D beforeA, Point3D a, Point3D b) {
        SurveyState outB = directionFromDelta(b.e - a.e, b.n - a.n, b.d - a.d);
        double incB = outB.inc;
        double aziB = outB.azi;
        double mdSeg = outB.md;
        if (mdSeg < 1e-9) {
            mdSeg = 1e-9;
        }

        double incA;
        double aziA;
        if (beforeA != null) {
            SurveyState inA = directionFromDelta(a.e - beforeA.e, a.n - beforeA.n, a.d - beforeA.d);
            incA = inA.inc;
            aziA = inA.azi;
        } else {
            incA = incB;
            aziA = aziB;
        }

        double dogleg = computeDogleg(incA, aziA, incB, aziB);
        double dls = Math.toDegrees(dogleg) / mdSeg * 30.0;
        return new SegmentSurveys(incA, aziA, incB, aziB, mdSeg, dogleg, dls);
    }

    public static SurveyState directionFromDelta(double dE, double dN, double dD) {
        double md = Math.sqrt(dE * dE + dN * dN + dD * dD);
        if (md < 1e-9) {
            return new SurveyState(0, 0, 0);
        }
        double inc = Math.acos(Math.max(-1, Math.min(1, dD / md)));
        double azi = Math.atan2(dE, dN);
        if (azi < 0) {
            azi += 2 * Math.PI;
        }
        return new SurveyState(inc, azi, md);
    }

    /**
     * 按 A→B 段恒定 DLS 外推：以 B 点测斜为起点，沿用 (incB-incA)/mdSeg 与方位变化率。
     */
    public static Point3D[] extrapolateConstantDls(SegmentSurveys seg, Point3D b,
                                                    double stepMd, int steps) {
        double mdSeg = seg.mdSeg < 1e-9 ? stepMd : seg.mdSeg;
        double rateInc = (seg.incB - seg.incA) / mdSeg;
        double rateAzi = normalizeAngleDiff(seg.aziB - seg.aziA) / mdSeg;

        Point3D[] out = new Point3D[steps];
        double curE = b.e;
        double curN = b.n;
        double curD = b.d;
        double curInc = seg.incB;
        double curAzi = seg.aziB;

        for (int i = 0; i < steps; i++) {
            double nextInc = curInc + rateInc * stepMd;
            double nextAzi = curAzi + rateAzi * stepMd;
            double[] delta = minimumCurvatureDelta(curInc, curAzi, nextInc, nextAzi, stepMd);
            curE += delta[0];
            curN += delta[1];
            curD += delta[2];
            curInc = nextInc;
            curAzi = nextAzi;
            out[i] = new Point3D(curE, curN, curD);
        }
        return out;
    }

    /** 最小曲率法计算一段测深的 E/N/D 增量 */
    public static double[] minimumCurvatureDelta(double inc1, double azi1, double inc2, double azi2, double dMd) {
        double dogleg = computeDogleg(inc1, azi1, inc2, azi2);
        double rf = dogleg < 1e-12 ? 1.0 : (2.0 / dogleg) * Math.tan(dogleg / 2.0);
        double dN = 0.5 * dMd * (Math.sin(inc1) * Math.cos(azi1) + Math.sin(inc2) * Math.cos(azi2)) * rf;
        double dE = 0.5 * dMd * (Math.sin(inc1) * Math.sin(azi1) + Math.sin(inc2) * Math.sin(azi2)) * rf;
        double dD = 0.5 * dMd * (Math.cos(inc1) + Math.cos(inc2)) * rf;
        return new double[]{dE, dN, dD};
    }

    public static double computeDogleg(double inc1, double azi1, double inc2, double azi2) {
        double cosDl = Math.cos(inc1) * Math.cos(inc2)
                + Math.sin(inc1) * Math.sin(inc2) * Math.cos(azi2 - azi1);
        cosDl = Math.max(-1.0, Math.min(1.0, cosDl));
        return Math.acos(cosDl);
    }

    private static double normalizeAngleDiff(double diff) {
        while (diff > Math.PI) {
            diff -= 2 * Math.PI;
        }
        while (diff < -Math.PI) {
            diff += 2 * Math.PI;
        }
        return diff;
    }
}
