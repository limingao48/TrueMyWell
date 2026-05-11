package club.yunzhi.api.workReview.trajectory.iscwsa;

import club.yunzhi.api.workReview.trajectory.WellObstacleDetector;

/**
 * 井眼折线（E,N,D，D 为垂深）上按垂深插值：累计狗腿长、井斜与网格方位。
 */
public final class PolylineHoleGeometry {

    private PolylineHoleGeometry() {
    }

    public static final class Sample {
        public final double e;
        public final double n;
        public final double d;
        /** 自轨迹起点沿井眼累计的弧长近似 (m) */
        public final double mdAlong;
        public final double incRad;
        public final double aziRad;

        Sample(double e, double n, double d, double mdAlong, double incRad, double aziRad) {
            this.e = e;
            this.n = n;
            this.d = d;
            this.mdAlong = mdAlong;
            this.incRad = incRad;
            this.aziRad = aziRad;
        }
    }

    /**
     * @param sortedRows 按垂深递增的 [E,N,D]
     */
    public static Sample sampleAtDepth(double[][] sortedRows, double depth) {
        if (sortedRows == null || sortedRows.length < 2) {
            return null;
        }
        double[] p = WellObstacleDetector.interpolateAtDepth(sortedRows, depth);
        int seg = findSegmentIndex(sortedRows, depth);
        if (seg < 0) {
            return null;
        }
        double[] cum = cumulativeChordMd(sortedRows);
        double z0 = sortedRows[seg][2];
        double z1 = sortedRows[seg + 1][2];
        double t = (Math.abs(z1 - z0) < 1e-12) ? 0.0 : (depth - z0) / (z1 - z0);
        t = Math.max(0.0, Math.min(1.0, t));
        double segLen = segmentLength(sortedRows[seg], sortedRows[seg + 1]);
        double mdAlong = cum[seg] + t * segLen;

        double te = sortedRows[seg + 1][0] - sortedRows[seg][0];
        double tn = sortedRows[seg + 1][1] - sortedRows[seg][1];
        double td = sortedRows[seg + 1][2] - sortedRows[seg][2];
        double norm = Math.sqrt(te * te + tn * tn + td * td);
        if (norm < 1e-12) {
            return new Sample(p[0], p[1], p[2], mdAlong, 0.0, 0.0);
        }
        te /= norm;
        tn /= norm;
        td /= norm;
        double horiz = Math.sqrt(te * te + tn * tn);
        double incRad = Math.atan2(horiz, Math.abs(td));
        double aziRad = Math.atan2(te, tn);
        return new Sample(p[0], p[1], p[2], mdAlong, incRad, aziRad);
    }

    private static int findSegmentIndex(double[][] sortedRows, double depth) {
        if (depth <= sortedRows[0][2]) {
            return 0;
        }
        if (depth >= sortedRows[sortedRows.length - 1][2]) {
            return sortedRows.length - 2;
        }
        for (int i = 0; i < sortedRows.length - 1; i++) {
            double z0 = sortedRows[i][2];
            double z1 = sortedRows[i + 1][2];
            if (depth >= z0 && depth <= z1) {
                return i;
            }
        }
        return sortedRows.length - 2;
    }

    private static double[] cumulativeChordMd(double[][] sortedRows) {
        double[] c = new double[sortedRows.length];
        for (int i = 1; i < sortedRows.length; i++) {
            c[i] = c[i - 1] + segmentLength(sortedRows[i - 1], sortedRows[i]);
        }
        return c;
    }

    private static double segmentLength(double[] a, double[] b) {
        double dx = b[0] - a[0];
        double dy = b[1] - a[1];
        double dz = b[2] - a[2];
        return Math.sqrt(dx * dx + dy * dy + dz * dz);
    }
}
