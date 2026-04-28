package club.yunzhi.api.workReview.trajectory;

import java.util.*;

public class WellObstacleDetector {
    private double[][] wellTrajectory;
    private double safetyRadius;
    private List<Map<String, double[]>> wellSegments;
    private List<Map<String, double[]>> segmentBounds;

    public WellObstacleDetector(double[][] wellTrajectory, double safetyRadius) {
        this.wellTrajectory = wellTrajectory;
        this.safetyRadius = safetyRadius;
        if (wellTrajectory != null) {
            createWellSegments(10.0);
            calculateSegmentBounds();
        }
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

    public double minHorizontalDistanceScan(double[][] trajectory) {
        if (wellTrajectory == null || trajectory == null) {
            return Double.MAX_VALUE;
        }

        double[] xNew = trajectory[0];
        double[] yNew = trajectory[1];
        double[] zNew = trajectory[2];

        double[] zObs = new double[wellTrajectory.length];
        double[] xObs = new double[wellTrajectory.length];
        double[] yObs = new double[wellTrajectory.length];

        for (int i = 0; i < wellTrajectory.length; i++) {
            xObs[i] = wellTrajectory[i][0];
            yObs[i] = wellTrajectory[i][1];
            zObs[i] = wellTrajectory[i][2];
        }

        Arrays.sort(zObs);
        Arrays.sort(xObs);
        Arrays.sort(yObs);

        double zMinObs = zObs[0];
        double zMaxObs = zObs[zObs.length - 1];

        double[] zNewSorted = zNew.clone();
        Arrays.sort(zNewSorted);
        double zMinNew = zNewSorted[0];
        double zMaxNew = zNewSorted[zNewSorted.length - 1];

        double zMin = Math.max(zMinObs, zMinNew);
        double zMax = Math.min(zMaxObs, zMaxNew);

        if (zMax <= zMin) {
            return Double.MAX_VALUE;
        }

        double depthStep = 10.0;
        List<Double> depthList = new ArrayList<>();
        for (double d = zMin; d <= zMax + 1e-9; d += depthStep) {
            depthList.add(d);
        }
        double[] depths = new double[depthList.size()];
        for (int i = 0; i < depthList.size(); i++) {
            depths[i] = depthList.get(i);
        }

        double[] xObsInterp = interpolate(depths, zObs, xObs);
        double[] yObsInterp = interpolate(depths, zObs, yObs);
        double[] xNewInterp = interpolate(depths, zNew, xNew);
        double[] yNewInterp = interpolate(depths, zNew, yNew);

        double minDist = Double.MAX_VALUE;
        for (int i = 0; i < depths.length; i++) {
            double dx = xNewInterp[i] - xObsInterp[i];
            double dy = yNewInterp[i] - yObsInterp[i];
            double dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < minDist) {
                minDist = dist;
            }
        }

        return minDist;
    }

    public boolean checkHorizontalCollision(double[][] trajectory, double depthStep) {
        double dMin = minHorizontalDistanceScan(trajectory);
        if (!Double.isFinite(dMin)) {
            return false;
        }
        return dMin < safetyRadius;
    }

    public double getCollisionPenalty(double[][] trajectory) {
        double dMin = minHorizontalDistanceScan(trajectory);
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
