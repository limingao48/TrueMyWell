package club.yunzhi.api.workReview.trajectory;

import java.util.*;

public class WellPathCalculator {
    private final WellTrajectoryConfig config;

    public WellPathCalculator(WellTrajectoryConfig config) {
        this.config = config;
    }

    public static class LengthResult {
        public final Map<String, Double> lengths;
        public final double loss;

        public LengthResult(Map<String, Double> lengths, double loss) {
            this.lengths = lengths;
            this.loss = loss;
        }
    }

    public static class CoordinateResult {
        public final double[][] points;
        public final double totalLength;
        public final boolean flag;
        public final double loss;

        public CoordinateResult(double[][] points, double totalLength, boolean flag, double loss) {
            this.points = points;
            this.totalLength = totalLength;
            this.flag = flag;
            this.loss = loss;
        }
    }

    public LengthResult calculateLengths(double D_kop, double alpha_1, double alpha_2,
                                         double phi_1, double phi_2, double R_1,
                                         double R_2, double D_turn_kop) {
        double cosGamma = Math.cos(alpha_1) * Math.cos(alpha_2) +
                          Math.sin(alpha_1) * Math.sin(alpha_2) * Math.cos(phi_2 - phi_1);
        cosGamma = Math.max(-1.0, Math.min(1.0, cosGamma));
        double gamma = Math.acos(cosGamma);
        double gammaHalf = gamma / 2.0;

        Map<String, Double> lengths = new HashMap<>();
        lengths.put("vertical", D_kop);
        lengths.put("build", R_1 * alpha_1);
        lengths.put("tangent1", 0.0);
        lengths.put("turn", R_2 * gamma);

        double deltaDBuild = R_1 * (1.0 - Math.cos(alpha_1));
        double remainingD = D_turn_kop - D_kop - deltaDBuild;
        if (remainingD < 0) {
            return new LengthResult(null, remainingD * (-1000));
        }

        double RF = gamma != 0 ? 2.0 * Math.tan(gammaHalf) / gamma : 1.0;
        double deltaDTurn = R_2 * (Math.cos(alpha_1) + Math.cos(alpha_2)) * RF / 2.0;

        lengths.put("tangent1", remainingD / Math.cos(alpha_1));

        for (int i = 0; i < 20; i++) {
            double finalD = D_kop + deltaDBuild + lengths.get("tangent1") * Math.cos(alpha_1);
            double depthError = finalD - D_turn_kop;
            if (Math.abs(depthError) < config.TOLERANCE) {
                break;
            }
            lengths.put("tangent1", lengths.get("tangent1") - depthError / Math.cos(alpha_1));
            if (lengths.get("tangent1") < 0) {
                lengths.put("tangent1", 0.0);
            }
        }

        double remainingToTarget = config.D_target - D_turn_kop - deltaDTurn;
        if (remainingToTarget < 0) {
            return new LengthResult(null, remainingToTarget * (-1000));
        }

        lengths.put("tangent2", remainingToTarget / Math.cos(alpha_2));
        return new LengthResult(lengths, 0.0);
    }

    public LengthResult calculateSevenSegmentLengths(double[] sevenSegParams) {
        double L0 = sevenSegParams[0];
        double DLS1 = sevenSegParams[1];
        double alpha3 = sevenSegParams[2];
        double L3 = sevenSegParams[3];
        double DLSTurn = sevenSegParams[4];
        double L4 = sevenSegParams[5];
        double L5 = sevenSegParams[6];
        double DLS6 = sevenSegParams[7];
        double alpha_e = sevenSegParams[8];
        double L7 = sevenSegParams[9];

        double alpha3Rad = Math.toRadians(alpha3);
        double alpha_eRad = Math.toRadians(alpha_e);

        double K1 = DLS1 / 30.0;
        double L2 = alpha3Rad / K1;

        double K6 = DLS6 / 30.0;
        double deltaAlpha = Math.abs(alpha_eRad - alpha3Rad);
        double L6 = deltaAlpha / K6;

        Map<String, Double> lengths = new HashMap<>();
        lengths.put("L0", L0);
        lengths.put("L1", L2);
        lengths.put("L2", L3);
        lengths.put("L3", L4);
        lengths.put("L4", L5);
        lengths.put("L5", L6);
        lengths.put("L6", L7);

        double totalLength = L0 + L2 + L3 + L4 + L5 + L6 + L7;

        double totalDepth = L0 + L2 * Math.cos(alpha3Rad) + L3 * Math.cos(alpha3Rad) +
                           L4 * Math.cos(alpha3Rad) + L5 * Math.cos(alpha3Rad) +
                           L6 * Math.cos((alpha3Rad + alpha_eRad) / 2) + L7 * Math.cos(alpha_eRad);

        if (totalDepth > config.D_target + 100) {
            return new LengthResult(null, (totalDepth - config.D_target) * 100);
        }

        return new LengthResult(lengths, 0.0);
    }

    public double[][] calculateBuildCoords(double alphaStart, double alphaEnd,
                                           double phi, double R, double length,
                                           int nPoints) {
        double[] x = new double[nPoints];
        double[] y = new double[nPoints];
        double[] z = new double[nPoints];

        double[] alpha = new double[nPoints];
        for (int i = 0; i < nPoints; i++) {
            alpha[i] = alphaStart + (alphaEnd - alphaStart) * i / (nPoints - 1);
        }

        for (int i = 0; i < nPoints - 1; i++) {
            double cosAlphaPrev = Math.cos(alpha[i]);
            double cosAlphaCurr = Math.cos(alpha[i + 1]);
            double sinAlphaPrev = Math.sin(alpha[i]);
            double sinAlphaCurr = Math.sin(alpha[i + 1]);

            double deltaN = R * (cosAlphaPrev - cosAlphaCurr) * Math.cos(phi);
            double deltaE = R * (cosAlphaPrev - cosAlphaCurr) * Math.sin(phi);
            double deltaV = R * (sinAlphaCurr - sinAlphaPrev);

            x[i + 1] = x[i] + deltaE;
            y[i + 1] = y[i] + deltaN;
            z[i + 1] = z[i] + deltaV;
        }

        return new double[][]{x, y, z};
    }

    public double[][] calculateTangentCoords(double alpha, double phi, double length, int nPoints) {
        double dl = length / (nPoints - 1);
        double deltaN = dl * Math.sin(alpha) * Math.cos(phi);
        double deltaE = dl * Math.sin(alpha) * Math.sin(phi);
        double deltaV = dl * Math.cos(alpha);

        double[] x = new double[nPoints];
        double[] y = new double[nPoints];
        double[] z = new double[nPoints];

        for (int i = 0; i < nPoints; i++) {
            x[i] = i * deltaE;
            y[i] = i * deltaN;
            z[i] = i * deltaV;
        }

        return new double[][]{x, y, z};
    }

    public double[][] calculateTurnCoords(double alphaStart, double alphaEnd,
                                          double phiStart, double phiEnd, double R,
                                          double length, int nPoints) {
        double[] alpha = new double[nPoints];
        double[] phiArr = new double[nPoints];
        for (int i = 0; i < nPoints; i++) {
            alpha[i] = alphaStart + (alphaEnd - alphaStart) * i / (nPoints - 1);
            phiArr[i] = phiStart + (phiEnd - phiStart) * i / (nPoints - 1);
        }

        double dl = length / (nPoints - 1);
        double[] x = new double[nPoints];
        double[] y = new double[nPoints];
        double[] z = new double[nPoints];

        for (int i = 0; i < nPoints - 1; i++) {
            double alphaAvg = 0.5 * (alpha[i] + alpha[i + 1]);
            double phiAvg = 0.5 * (phiArr[i] + phiArr[i + 1]);

            double deltaN = dl * Math.sin(alphaAvg) * Math.cos(phiAvg);
            double deltaE = dl * Math.sin(alphaAvg) * Math.sin(phiAvg);
            double deltaV = dl * Math.cos(alphaAvg);

            x[i + 1] = x[i] + deltaE;
            y[i + 1] = y[i] + deltaN;
            z[i + 1] = z[i] + deltaV;
        }

        return new double[][]{x, y, z};
    }

    public static double[] calculateVectorAngle(double[] v1, double[] v2) {
        double dotProduct = v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2];
        double normV1 = Math.sqrt(v1[0] * v1[0] + v1[1] * v1[1] + v1[2] * v2[2]);
        double normV2 = Math.sqrt(v2[0] * v2[0] + v2[1] * v2[1] + v2[2] * v2[2]);

        if (normV1 == 0 || normV2 == 0) {
            return new double[]{0.0, 0.0};
        }

        double cosTheta = Math.max(-1.0, Math.min(1.0, dotProduct / (normV1 * normV2)));
        double angleRad = Math.acos(cosTheta);
        double angleDeg = Math.toDegrees(angleRad);

        return new double[]{angleDeg, angleRad};
    }

    public int detectDirectionJump(double[] N, double[] E, double[] V, double thresholdDeg) {
        if (N.length != E.length || E.length != V.length) {
            throw new IllegalArgumentException("N、E、V数组长度必须相同！");
        }
        if (N.length < 3) {
            return 0;
        }

        List<double[]> validVectors = new ArrayList<>();
        for (int i = 0; i < N.length - 1; i++) {
            double dN = N[i + 1] - N[i];
            double dE = E[i + 1] - E[i];
            double dV = V[i + 1] - V[i];
            double norm = Math.sqrt(dN * dN + dE * dE + dV * dV);

            if (norm >= 1e-8) {
                validVectors.add(new double[]{dN, dE, dV});
            }
        }

        if (validVectors.size() < 2) {
            return 0;
        }

        int jumpCount = 0;
        for (int i = 0; i < validVectors.size() - 1; i++) {
            double[] angleResult = calculateVectorAngle(validVectors.get(i), validVectors.get(i + 1));
            if (angleResult[0] > thresholdDeg) {
                jumpCount++;
            }
        }
        return jumpCount;
    }

    public CoordinateResult calculateCoordinates(double[] positionTuple) {
        if (positionTuple == null || positionTuple.length < 8) {
            return new CoordinateResult(null, 10000, false, Double.MAX_VALUE);
        }

        double D_kop = positionTuple[0];
        double alpha1 = positionTuple[1];
        double alpha2 = positionTuple[2];
        double phi1 = positionTuple[3];
        double phi2 = positionTuple[4];
        double R1 = positionTuple[5];
        double R2 = positionTuple[6];
        double D_turn_kop = positionTuple[7];

        double alpha1Rad = Math.toRadians(alpha1);
        double alpha2Rad = Math.toRadians(alpha2);
        double phi1Rad = Math.toRadians(phi1);
        double phi2Rad = Math.toRadians(phi2);

        LengthResult lengthResult = calculateLengths(D_kop, alpha1Rad, alpha2Rad,
                                                     phi1Rad, phi2Rad, R1, R2, D_turn_kop);
        if (lengthResult.lengths == null) {
            return new CoordinateResult(null, 10000, false, lengthResult.loss * 1000);
        }

        Map<String, Double> lengths = lengthResult.lengths;
        int nPoints = 50;

        List<Double> xAll = new ArrayList<>();
        List<Double> yAll = new ArrayList<>();
        List<Double> zAll = new ArrayList<>();

        double x0 = config.E_wellhead;
        double y0 = config.N_wellhead;

        for (int i = 0; i < nPoints; i++) {
            xAll.add(x0);
            yAll.add(y0);
            zAll.add(D_kop * i / (nPoints - 1));
        }

        double L2 = lengths.getOrDefault("build", R1 * alpha1Rad);
        double[][] buildCoords = calculateBuildCoords(0.0, alpha1Rad, phi1Rad, R1, L2, nPoints);
        double xBuildLast = xAll.get(xAll.size() - 1);
        double yBuildLast = yAll.get(yAll.size() - 1);
        double zBuildLast = zAll.get(zAll.size() - 1);

        for (int i = 0; i < nPoints; i++) {
            if (i > 0) {
                xAll.add(xBuildLast + buildCoords[0][i]);
                yAll.add(yBuildLast + buildCoords[1][i]);
                zAll.add(zBuildLast + buildCoords[2][i]);
            }
        }

        double L3 = lengths.getOrDefault("tangent1", 0.0);
        double[][] tangent1Coords = calculateTangentCoords(alpha1Rad, phi1Rad, L3, nPoints);
        double xT1Last = xAll.get(xAll.size() - 1);
        double yT1Last = yAll.get(yAll.size() - 1);
        double zT1Last = zAll.get(zAll.size() - 1);

        for (int i = 0; i < nPoints; i++) {
            if (i > 0) {
                xAll.add(xT1Last + tangent1Coords[0][i]);
                yAll.add(yT1Last + tangent1Coords[1][i]);
                zAll.add(zT1Last + tangent1Coords[2][i]);
            }
        }

        double L4 = lengths.getOrDefault("turn", 0.0);
        double[][] turnCoords = calculateTurnCoords(alpha1Rad, alpha2Rad, phi1Rad, phi2Rad, R2, L4, nPoints);
        double xTurnLast = xAll.get(xAll.size() - 1);
        double yTurnLast = yAll.get(yAll.size() - 1);
        double zTurnLast = zAll.get(zAll.size() - 1);

        for (int i = 0; i < nPoints; i++) {
            if (i > 0) {
                xAll.add(xTurnLast + turnCoords[0][i]);
                yAll.add(yTurnLast + turnCoords[1][i]);
                zAll.add(zTurnLast + turnCoords[2][i]);
            }
        }

        double L5 = lengths.getOrDefault("tangent2", 0.0);
        double[][] tangent2Coords = calculateTangentCoords(alpha2Rad, phi2Rad, L5, nPoints);
        double xT2Last = xAll.get(xAll.size() - 1);
        double yT2Last = yAll.get(yAll.size() - 1);
        double zT2Last = zAll.get(zAll.size() - 1);

        for (int i = 0; i < nPoints; i++) {
            if (i > 0) {
                xAll.add(xT2Last + tangent2Coords[0][i]);
                yAll.add(yT2Last + tangent2Coords[1][i]);
                zAll.add(zT2Last + tangent2Coords[2][i]);
            }
        }

        double[] x = new double[xAll.size()];
        double[] y = new double[yAll.size()];
        double[] z = new double[zAll.size()];
        for (int i = 0; i < xAll.size(); i++) {
            x[i] = xAll.get(i);
            y[i] = yAll.get(i);
            z[i] = zAll.get(i);
        }

        double totalLength = 0.0;
        for (Double len : lengths.values()) {
            totalLength += len;
        }

        int jumpCount = detectDirectionJump(y, x, z, 10.0);
        double lossJump = jumpCount > 0 ? jumpCount * 100000.0 : 0.0;

        return new CoordinateResult(new double[][]{x, y, z}, totalLength, true, lossJump);
    }

    public CoordinateResult calculateSevenSegmentCoordinates(double[] sevenSegParams) {
        if (sevenSegParams == null || sevenSegParams.length != 12) {
            return new CoordinateResult(null, 10000, false, Double.MAX_VALUE);
        }

        double L0 = sevenSegParams[0];
        double DLS1 = sevenSegParams[1];
        double alpha3 = sevenSegParams[2];
        double L3 = sevenSegParams[3];
        double DLSTurn = sevenSegParams[4];
        double L5 = sevenSegParams[6];
        double DLS6 = sevenSegParams[7];
        double alpha_e = sevenSegParams[8];
        double L7 = sevenSegParams[9];
        double phi_init = sevenSegParams[10];
        double phi_target = sevenSegParams[11];

        double alpha3Clamped = Math.max(0.0, Math.min(89.0, alpha3));
        double alphaEClamped = Math.max(0.0, Math.min(89.0, alpha_e));
        double phiInitNorm = ((phi_init % 360.0) + 360.0) % 360.0;
        double phiTargetNorm = ((phi_target % 360.0) + 360.0) % 360.0;

        double k1 = Math.max(1e-6, DLS1 / 30.0);
        double kTurn = Math.max(1e-6, DLSTurn / 30.0);
        double k6 = Math.max(1e-6, DLS6 / 30.0);

        double L1 = Math.abs(alpha3Clamped) / k1;
        double deltaPhiTarget = ((phiTargetNorm - phiInitNorm + 180.0) % 360.0) - 180.0;
        double sinAlpha = Math.max(Math.sin(Math.toRadians(Math.max(alpha3Clamped, 1e-3))), 1e-3);
        double L4Used = Math.abs(deltaPhiTarget) * sinAlpha / Math.abs(kTurn);
        double phiAfterTurn = phiInitNorm + deltaPhiTarget;
        double L6 = Math.abs(alphaEClamped - alpha3Clamped) / k6;

        List<Double> xAll = new ArrayList<>();
        List<Double> yAll = new ArrayList<>();
        List<Double> zAll = new ArrayList<>();

        double currentE = config.E_wellhead;
        double currentN = config.N_wellhead;
        double currentD = config.D_wellhead;
        xAll.add(currentE);
        yAll.add(currentN);
        zAll.add(currentD);

        final double ds = 10.0;

        // 1) 直井段
        int n0 = Math.max(1, (int) Math.ceil(Math.max(0.0, L0) / ds));
        for (int i = 0; i < n0; i++) {
            double step = Math.max(0.0, L0) / n0;
            currentD += step;
            xAll.add(currentE);
            yAll.add(currentN);
            zAll.add(currentD);
        }

        // 2) 增斜段
        int n1 = Math.max(1, (int) Math.ceil(Math.max(0.0, L1) / ds));
        for (int i = 1; i <= n1; i++) {
            double frac = (double) i / n1;
            double incDeg = alpha3Clamped * frac;
            double step = Math.max(0.0, L1) / n1;
            double incRad = Math.toRadians(incDeg);
            double aziRad = Math.toRadians(phiInitNorm);
            currentN += step * Math.sin(incRad) * Math.cos(aziRad);
            currentE += step * Math.sin(incRad) * Math.sin(aziRad);
            currentD += step * Math.cos(incRad);
            xAll.add(currentE);
            yAll.add(currentN);
            zAll.add(currentD);
        }

        // 3) 稳斜段
        int n3 = Math.max(1, (int) Math.ceil(Math.max(0.0, L3) / ds));
        for (int i = 0; i < n3; i++) {
            double step = Math.max(0.0, L3) / n3;
            double incRad = Math.toRadians(alpha3Clamped);
            double aziRad = Math.toRadians(phiInitNorm);
            currentN += step * Math.sin(incRad) * Math.cos(aziRad);
            currentE += step * Math.sin(incRad) * Math.sin(aziRad);
            currentD += step * Math.cos(incRad);
            xAll.add(currentE);
            yAll.add(currentN);
            zAll.add(currentD);
        }

        // 4) 扭方位段（长度由 phi_target 推导）
        int n4 = Math.max(1, (int) Math.ceil(Math.max(0.0, L4Used) / ds));
        for (int i = 1; i <= n4; i++) {
            double frac = (double) i / n4;
            double aziDeg = phiInitNorm + deltaPhiTarget * frac;
            double step = Math.max(0.0, L4Used) / n4;
            double incRad = Math.toRadians(alpha3Clamped);
            double aziRad = Math.toRadians(aziDeg);
            currentN += step * Math.sin(incRad) * Math.cos(aziRad);
            currentE += step * Math.sin(incRad) * Math.sin(aziRad);
            currentD += step * Math.cos(incRad);
            xAll.add(currentE);
            yAll.add(currentN);
            zAll.add(currentD);
        }

        // 5) 稳斜段
        int n5 = Math.max(1, (int) Math.ceil(Math.max(0.0, L5) / ds));
        for (int i = 0; i < n5; i++) {
            double step = Math.max(0.0, L5) / n5;
            double incRad = Math.toRadians(alpha3Clamped);
            double aziRad = Math.toRadians(phiAfterTurn);
            currentN += step * Math.sin(incRad) * Math.cos(aziRad);
            currentE += step * Math.sin(incRad) * Math.sin(aziRad);
            currentD += step * Math.cos(incRad);
            xAll.add(currentE);
            yAll.add(currentN);
            zAll.add(currentD);
        }

        // 6) 井斜调整段
        int n6 = Math.max(1, (int) Math.ceil(Math.max(0.0, L6) / ds));
        for (int i = 1; i <= n6; i++) {
            double frac = (double) i / n6;
            double incDeg = alpha3Clamped + (alphaEClamped - alpha3Clamped) * frac;
            double step = Math.max(0.0, L6) / n6;
            double incRad = Math.toRadians(incDeg);
            double aziRad = Math.toRadians(phiAfterTurn);
            currentN += step * Math.sin(incRad) * Math.cos(aziRad);
            currentE += step * Math.sin(incRad) * Math.sin(aziRad);
            currentD += step * Math.cos(incRad);
            xAll.add(currentE);
            yAll.add(currentN);
            zAll.add(currentD);
        }

        // 7) 末端稳斜段
        int n7 = Math.max(1, (int) Math.ceil(Math.max(0.0, L7) / ds));
        for (int i = 0; i < n7; i++) {
            double step = Math.max(0.0, L7) / n7;
            double incRad = Math.toRadians(alphaEClamped);
            double aziRad = Math.toRadians(phiAfterTurn);
            currentN += step * Math.sin(incRad) * Math.cos(aziRad);
            currentE += step * Math.sin(incRad) * Math.sin(aziRad);
            currentD += step * Math.cos(incRad);
            xAll.add(currentE);
            yAll.add(currentN);
            zAll.add(currentD);
        }

        double[] x = xAll.stream().mapToDouble(Double::doubleValue).toArray();
        double[] y = yAll.stream().mapToDouble(Double::doubleValue).toArray();
        double[] z = zAll.stream().mapToDouble(Double::doubleValue).toArray();

        double totalLength = Math.max(0.0, L0) + Math.max(0.0, L1) + Math.max(0.0, L3)
                + Math.max(0.0, L4Used) + Math.max(0.0, L5) + Math.max(0.0, L6) + Math.max(0.0, L7);

        int jumpCount = detectDirectionJump(y, x, z, 10.0);
        double lossJump = jumpCount > 0 ? jumpCount * 100000.0 : 0.0;

        return new CoordinateResult(new double[][]{x, y, z}, totalLength, true, lossJump);
    }
}
