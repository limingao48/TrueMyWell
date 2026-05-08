package club.yunzhi.api.workReview.trajectory;

import java.util.*;

/**
 * 邻井轨迹障碍物：在重叠垂深范围内按步长扫描，计算与设计轨迹之间的最小井眼中心距（CTC 扫描）。
 * 设计轨迹可为 {@code [3][n]}（E/N/D 分行）或 {@code [n][3]}（逐点）格式。
 */
public class WellObstacleDetector {
    private double[][] wellTrajectory;
    private double safetyRadius;
    private List<Map<String, double[]>> wellSegments;
    private List<Map<String, double[]>> segmentBounds;

    public WellObstacleDetector(double[][] wellTrajectory, double safetyRadius) {
        this.wellTrajectory = normalizeRowPoints(wellTrajectory);
        this.safetyRadius = safetyRadius;
        if (this.wellTrajectory != null) {
            createWellSegments(10.0);
            calculateSegmentBounds();
        }
    }

    /** 将 [3][n] 或 [n][3] 统一为按垂深递增的 [n][3]，便于插值 */
    public static double[][] normalizeRowPoints(double[][] traj) {
        if (traj == null || traj.length == 0) {
            return traj;
        }
        // 设计轨迹多为 [3][n]（E/N/D）；邻井多为 [n][3]。长度均为 3 时按列格式处理（与本项目计算器输出一致）。
        if (traj.length == 3 && traj[0] != null && traj[1] != null && traj[2] != null
                && traj[0].length == traj[1].length && traj[1].length == traj[2].length && traj[0].length > 0) {
            int n = traj[0].length;
            double[][] rows = new double[n][3];
            for (int i = 0; i < n; i++) {
                rows[i][0] = traj[0][i];
                rows[i][1] = traj[1][i];
                rows[i][2] = traj[2][i];
            }
            return sortByDepthAscending(rows);
        }
        return sortByDepthAscending(copyRows(traj));
    }

    private static double[][] copyRows(double[][] rows) {
        double[][] out = new double[rows.length][3];
        for (int i = 0; i < rows.length; i++) {
            out[i][0] = rows[i][0];
            out[i][1] = rows[i][1];
            out[i][2] = rows[i][2];
        }
        return out;
    }

    private static double[][] sortByDepthAscending(double[][] pts) {
        if (pts.length <= 1) {
            return pts;
        }
        Integer[] ord = new Integer[pts.length];
        for (int i = 0; i < ord.length; i++) {
            ord[i] = i;
        }
        Arrays.sort(ord, (a, b) -> Double.compare(pts[a][2], pts[b][2]));
        double[][] sorted = new double[pts.length][3];
        for (int i = 0; i < ord.length; i++) {
            sorted[i][0] = pts[ord[i]][0];
            sorted[i][1] = pts[ord[i]][1];
            sorted[i][2] = pts[ord[i]][2];
        }
        return sorted;
    }

    public static double[] interpolateAtDepth(double[][] sortedPts, double depth) {
        if (sortedPts.length == 0) {
            return new double[]{0, 0, depth};
        }
        if (sortedPts.length == 1) {
            return new double[]{sortedPts[0][0], sortedPts[0][1], depth};
        }
        if (depth <= sortedPts[0][2]) {
            return linearInterpHorizontalAtDepth(sortedPts[0], sortedPts[1], depth);
        }
        if (depth >= sortedPts[sortedPts.length - 1][2]) {
            int n = sortedPts.length;
            return linearInterpHorizontalAtDepth(sortedPts[n - 2], sortedPts[n - 1], depth);
        }
        for (int i = 0; i < sortedPts.length - 1; i++) {
            double z0 = sortedPts[i][2];
            double z1 = sortedPts[i + 1][2];
            if (depth >= z0 && depth <= z1) {
                return linearInterpHorizontalAtDepth(sortedPts[i], sortedPts[i + 1], depth);
            }
        }
        return new double[]{sortedPts[sortedPts.length - 1][0], sortedPts[sortedPts.length - 1][1], depth};
    }

    private static double[] linearInterpHorizontalAtDepth(double[] p0, double[] p1, double depth) {
        double z0 = p0[2];
        double z1 = p1[2];
        if (Math.abs(z1 - z0) < 1e-12) {
            return new double[]{p0[0], p0[1], depth};
        }
        double t = (depth - z0) / (z1 - z0);
        t = Math.max(0.0, Math.min(1.0, t));
        double e = p0[0] + t * (p1[0] - p0[0]);
        double n = p0[1] + t * (p1[1] - p0[1]);
        return new double[]{e, n, depth};
    }

    public void createWellSegments(double depthStep) {
        if (wellTrajectory == null) {
            return;
        }

        double[] zObs = new double[wellTrajectory.length];
        double[] xObs = new double[wellTrajectory.length];
        double[] yObs = new double[wellTrajectory.length];

        for (int i = 0; i < wellTrajectory.length; i++) {
            xObs[i] = wellTrajectory[i][0];
            yObs[i] = wellTrajectory[i][1];
            zObs[i] = wellTrajectory[i][2];
        }

        double[] zSorted = zObs.clone();
        double[] xSorted = xObs.clone();
        double[] ySorted = yObs.clone();

        for (int i = 0; i < zSorted.length; i++) {
            for (int j = i + 1; j < zSorted.length; j++) {
                if (zSorted[i] > zSorted[j]) {
                    double temp = zSorted[i];
                    zSorted[i] = zSorted[j];
                    zSorted[j] = temp;
                    temp = xSorted[i];
                    xSorted[i] = xSorted[j];
                    xSorted[j] = temp;
                    temp = ySorted[i];
                    ySorted[i] = ySorted[j];
                    ySorted[j] = temp;
                }
            }
        }

        double zMin = Double.MAX_VALUE;
        double zMax = -Double.MAX_VALUE;
        for (double z : zSorted) {
            if (z < zMin) zMin = z;
            if (z > zMax) zMax = z;
        }

        List<Double> depthList = new ArrayList<>();
        for (double d = zMin; d <= zMax + 1e-9; d += depthStep) {
            depthList.add(d);
        }
        if (depthList.get(depthList.size() - 1) < zMax) {
            depthList.add(zMax);
        }

        double[] depths = new double[depthList.size()];
        for (int i = 0; i < depthList.size(); i++) {
            depths[i] = depthList.get(i);
        }

        double[] xInterp = interpolate(depths, zSorted, xSorted);
        double[] yInterp = interpolate(depths, zSorted, ySorted);

        wellSegments = new ArrayList<>();
        for (int i = 0; i < depths.length - 1; i++) {
            Map<String, double[]> segment = new HashMap<>();
            segment.put("start", new double[]{xInterp[i], yInterp[i], depths[i]});
            segment.put("end", new double[]{xInterp[i + 1], yInterp[i + 1], depths[i + 1]});

            double dx = xInterp[i + 1] - xInterp[i];
            double dy = yInterp[i + 1] - yInterp[i];
            double horizontalLength = Math.sqrt(dx * dx + dy * dy);
            segment.put("horizontalLength", new double[]{horizontalLength});

            wellSegments.add(segment);
        }
    }

    private double[] interpolate(double[] x, double[] xp, double[] fp) {
        double[] result = new double[x.length];
        for (int i = 0; i < x.length; i++) {
            result[i] = linearInterpolate(x[i], xp, fp);
        }
        return result;
    }

    private double linearInterpolate(double x, double[] xp, double[] fp) {
        if (xp.length != fp.length) {
            throw new IllegalArgumentException("xp and fp must have same length");
        }
        if (xp.length < 2) {
            return fp.length > 0 ? fp[0] : 0.0;
        }

        if (x <= xp[0]) {
            return fp[0];
        }
        if (x >= xp[xp.length - 1]) {
            return fp[xp.length - 1];
        }

        for (int i = 0; i < xp.length - 1; i++) {
            if (x >= xp[i] && x <= xp[i + 1]) {
                if (xp[i + 1] == xp[i]) {
                    return fp[i];
                }
                double t = (x - xp[i]) / (xp[i + 1] - xp[i]);
                return fp[i] + t * (fp[i + 1] - fp[i]);
            }
        }
        return fp[xp.length - 1];
    }

    public void calculateSegmentBounds() {
        if (wellSegments == null) {
            return;
        }

        segmentBounds = new ArrayList<>();
        for (Map<String, double[]> segment : wellSegments) {
            double[] start = segment.get("start");
            double[] end = segment.get("end");

            double[] min = new double[3];
            double[] max = new double[3];
            for (int i = 0; i < 3; i++) {
                min[i] = Math.min(start[i], end[i]) - safetyRadius;
                max[i] = Math.max(start[i], end[i]) + safetyRadius;
            }

            Map<String, double[]> bounds = new HashMap<>();
            bounds.put("min", min);
            bounds.put("max", max);
            bounds.put("horizontalLength", segment.get("horizontalLength"));
            segmentBounds.add(bounds);
        }
    }

    public double distanceToWellSegment(double[] point, Map<String, double[]> segment) {
        double[] start = segment.get("start");
        double[] end = segment.get("end");

        double[] lineVec = new double[3];
        lineVec[0] = end[0] - start[0];
        lineVec[1] = end[1] - start[1];
        lineVec[2] = end[2] - start[2];

        double[] pointVec = new double[3];
        pointVec[0] = point[0] - start[0];
        pointVec[1] = point[1] - start[1];
        pointVec[2] = point[2] - start[2];

        double lineLen = Math.sqrt(lineVec[0] * lineVec[0] + lineVec[1] * lineVec[1] + lineVec[2] * lineVec[2]);
        if (lineLen == 0) {
            return Math.sqrt(pointVec[0] * pointVec[0] + pointVec[1] * pointVec[1] + pointVec[2] * pointVec[2]);
        }

        double t = (pointVec[0] * lineVec[0] + pointVec[1] * lineVec[1] + pointVec[2] * lineVec[2]) / (lineLen * lineLen);
        t = Math.max(0, Math.min(1, t));

        double[] closestPoint = new double[3];
        closestPoint[0] = start[0] + t * lineVec[0];
        closestPoint[1] = start[1] + t * lineVec[1];
        closestPoint[2] = start[2] + t * lineVec[2];

        double dx = point[0] - closestPoint[0];
        double dy = point[1] - closestPoint[1];
        double dz = point[2] - closestPoint[2];
        return Math.sqrt(dx * dx + dy * dy + dz * dz);
    }

    /**
     * 在重叠垂深区间内按固定步长扫描，对每个垂深在同一 TVD 上插值得到两口井的井眼中心坐标，
     * 取三维欧氏距离的最小值（与同一深度 CTC 扫描一致；同一垂深下主要为水平分量）。
     */
    public double minCenterToCenterScanDistance(double[][] trajectory) {
        if (wellTrajectory == null || trajectory == null) {
            return Double.MAX_VALUE;
        }
        double[][] subjectRows = normalizeRowPoints(trajectory);
        double[][] obsRows = wellTrajectory;
        if (subjectRows.length < 2 || obsRows.length < 2) {
            return Double.MAX_VALUE;
        }

        double zMinObs = obsRows[0][2];
        double zMaxObs = obsRows[obsRows.length - 1][2];
        double zMinSub = subjectRows[0][2];
        double zMaxSub = subjectRows[subjectRows.length - 1][2];

        double zMin = Math.max(zMinObs, zMinSub);
        double zMax = Math.min(zMaxObs, zMaxSub);
        if (zMax <= zMin) {
            return Double.MAX_VALUE;
        }

        double depthStep = 10.0;
        double minDist = Double.MAX_VALUE;
        for (double d = zMin; d <= zMax + 1e-9; d += depthStep) {
            double[] pObs = interpolateAtDepth(obsRows, d);
            double[] pSub = interpolateAtDepth(subjectRows, d);
            double dx = pSub[0] - pObs[0];
            double dy = pSub[1] - pObs[1];
            double dz = pSub[2] - pObs[2];
            double dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
            if (dist < minDist) {
                minDist = dist;
            }
        }
        return minDist;
    }

    /**
     * @deprecated 使用 {@link #minCenterToCenterScanDistance(double[][])}，旧实现对坐标排序有误。
     */
    @Deprecated
    public double minHorizontalDistanceScan(double[][] trajectory) {
        return minCenterToCenterScanDistance(trajectory);
    }

    public boolean checkHorizontalCollision(double[][] trajectory, double depthStep) {
        double dMin = minCenterToCenterScanDistance(trajectory);
        if (!Double.isFinite(dMin)) {
            return false;
        }
        return dMin < safetyRadius;
    }

    public double getCollisionPenalty(double[][] trajectory) {
        double dMin = minCenterToCenterScanDistance(trajectory);
        if (!Double.isFinite(dMin)) {
            return 0.0;
        }

        if (dMin < safetyRadius) {
            return 1e20;
        }

        if (dMin < safetyRadius * 2) {
            return (safetyRadius * 2 - dMin) * 1000.0;
        }

        return 0.0;
    }

    public double getSafetyRadius() {
        return safetyRadius;
    }

    public double[][] getWellTrajectory() {
        return wellTrajectory;
    }
}
