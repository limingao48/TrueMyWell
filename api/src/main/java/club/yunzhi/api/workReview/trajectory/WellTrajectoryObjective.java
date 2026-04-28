package club.yunzhi.api.workReview.trajectory;

import java.util.*;

public class WellTrajectoryObjective {
    private WellTrajectoryConfig config;
    private WellPathCalculator calculator;
    private List<WellObstacleDetector> wellObstacles;

    public WellTrajectoryObjective(WellTrajectoryConfig config) {
        this.config = config;
        this.calculator = new WellPathCalculator(config);
        this.wellObstacles = new ArrayList<>();
    }

    public WellTrajectoryObjective(WellTrajectoryConfig config, List<WellObstacleDetector> wellObstacles) {
        this.config = config;
        this.calculator = new WellPathCalculator(config);
        this.wellObstacles = wellObstacles != null ? wellObstacles : new ArrayList<>();
    }

    public void addWellObstacle(WellObstacleDetector obstacle) {
        if (obstacle != null) {
            this.wellObstacles.add(obstacle);
        }
    }

    public double calculateObjective(double[] positionTuple) {
        if (positionTuple == null || positionTuple.length < 8) {
            return 1e20;
        }

        if (positionTuple.length == 12) {
            return calculateSevenSegmentObjective(positionTuple);
        }

        if (positionTuple[0] > positionTuple[7]) {
            return 1e20;
        }

        if (checkSpecialCases(positionTuple)) {
            return 1e20;
        }

        WellPathCalculator.CoordinateResult result = calculator.calculateCoordinates(positionTuple);

        if (result.points == null || !result.flag) {
            return 1e20;
        }

        double penalty = 0;

        if (result.loss > 0) {
            penalty += 1e20;
            return penalty;
        }

        for (WellObstacleDetector wellObstacle : wellObstacles) {
            if (wellObstacle != null) {
                double wellCollisionPenalty = wellObstacle.getCollisionPenalty(result.points);
                penalty += wellCollisionPenalty;
                if (wellCollisionPenalty >= 1e20) {
                    return penalty;
                }
            }
        }

        double[] finalPoint = new double[]{
            result.points[0][result.points[0].length - 1],
            result.points[1][result.points[1].length - 1],
            result.points[2][result.points[2].length - 1]
        };

        double targetDeviation = Math.sqrt(
            Math.pow(finalPoint[0] - config.E_target, 2) +
            Math.pow(finalPoint[1] - config.N_target, 2) +
            Math.pow(finalPoint[2] - config.D_target, 2)
        );

        if (targetDeviation > config.targetDeviationThreshold) {
            targetDeviation = targetDeviation * config.targetDeviationPenalty;
        }

        double objectiveValue = targetDeviation + result.totalLength + penalty;

        return objectiveValue;
    }

    public double calculateSevenSegmentObjective(double[] sevenSegParams) {
        if (!config.validateSevenSegmentParameters(sevenSegParams)) {
            return 1e20;
        }

        WellPathCalculator.CoordinateResult result = calculator.calculateSevenSegmentCoordinates(sevenSegParams);

        if (result.points == null || !result.flag) {
            return 1e20;
        }

        double[] finalPoint = new double[]{
            result.points[0][result.points[0].length - 1],
            result.points[1][result.points[1].length - 1],
            result.points[2][result.points[2].length - 1]
        };

        double verticalDeviation = Math.abs(finalPoint[2] - config.D_target);
        double horizontalDeviation = Math.sqrt(
                Math.pow(finalPoint[0] - config.E_target, 2) +
                Math.pow(finalPoint[1] - config.N_target, 2)
        );
        double collisionPenalty = calculateCollisionPenalty(result.points);

        if (!isLandingConstraintsSatisfied(sevenSegParams)) {
            return 1e20 + collisionPenalty;
        }

        boolean hitTarget = horizontalDeviation <= config.horizontalTolerance && verticalDeviation <= config.verticalTolerance;
        if (!hitTarget) {
            double excessH = Math.max(0.0, horizontalDeviation - config.horizontalTolerance);
            double excessV = Math.max(0.0, verticalDeviation - config.verticalTolerance);
            return config.targetDeviationPenalty * (excessH * excessH + excessV * excessV + 0.1) + collisionPenalty;
        }

        return result.totalLength + collisionPenalty;
    }

    private boolean isLandingConstraintsSatisfied(double[] sevenSegParams) {
        double alphaE = sevenSegParams[8];
        double phiTarget = normalizeAzimuth(sevenSegParams[11]);
        if (alphaE < config.landingInclinationMin || alphaE > config.landingInclinationMax) {
            return false;
        }
        return isAzimuthInRange(phiTarget, config.landingAzimuthMin, config.landingAzimuthMax);
    }

    private double normalizeAzimuth(double azimuth) {
        double a = azimuth % 360.0;
        if (a < 0) {
            a += 360.0;
        }
        return a;
    }

    private boolean isAzimuthInRange(double value, double min, double max) {
        double v = normalizeAzimuth(value);
        double mn = normalizeAzimuth(min);
        double mx = normalizeAzimuth(max);
        if (mn <= mx) {
            return v >= mn && v <= mx;
        }
        return v >= mn || v <= mx;
    }

    private double calculateCollisionPenalty(double[][] trajectory) {
        double totalPenalty = 0.0;
        for (WellObstacleDetector wellObstacle : wellObstacles) {
            if (wellObstacle == null) {
                continue;
            }
            double dMin = wellObstacle.minHorizontalDistanceScan(trajectory);
            if (!Double.isFinite(dMin)) {
                continue;
            }
            double safe = wellObstacle.getSafetyRadius();
            if (dMin < safe) {
                totalPenalty += 1e24 + 1e8 * Math.pow(safe - dMin + 1.0, 2);
            }
        }
        return totalPenalty;
    }

    public Map<String, Object> getTrajectoryInfo(double[] positionTuple) {
        Map<String, Object> info = new HashMap<>();

        WellPathCalculator.CoordinateResult result;

        if (positionTuple != null && positionTuple.length == 12) {
            result = calculator.calculateSevenSegmentCoordinates(positionTuple);
        } else {
            result = calculator.calculateCoordinates(positionTuple);
        }

        if (result.points == null || !result.flag) {
            info.put("success", false);
            info.put("error", "Invalid parameters or calculation failed");
            info.put("loss", result.loss);
            return info;
        }

        double[] finalPoint = new double[]{
            result.points[0][result.points[0].length - 1],
            result.points[1][result.points[1].length - 1],
            result.points[2][result.points[2].length - 1]
        };

        double targetDeviation = Math.sqrt(
            Math.pow(finalPoint[0] - config.E_target, 2) +
            Math.pow(finalPoint[1] - config.N_target, 2) +
            Math.pow(finalPoint[2] - config.D_target, 2)
        );

        boolean wellCollision = false;
        for (WellObstacleDetector wellObstacle : wellObstacles) {
            if (wellObstacle != null) {
                if (wellObstacle.checkHorizontalCollision(result.points, 10.0)) {
                    wellCollision = true;
                    break;
                }
            }
        }

        info.put("success", true);
        info.put("trajectory", result.points);
        info.put("totalLength", result.totalLength);
        info.put("finalPoint", finalPoint);
        info.put("targetDeviation", targetDeviation);
        info.put("wellCollision", wellCollision);
        info.put("loss", result.loss);

        return info;
    }

    public boolean checkSpecialCases(double[] positionTuple) {
        if (positionTuple.length == 12) {
            return !config.validateSevenSegmentParameters(positionTuple);
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

        double cosGamma = Math.cos(alpha1Rad) * Math.cos(alpha2Rad) +
                         Math.sin(alpha1Rad) * Math.sin(alpha2Rad) * Math.cos(phi2Rad - phi1Rad);

        if (Math.abs(cosGamma) > 1.0) {
            return true;
        }

        cosGamma = Math.max(-1.0, Math.min(1.0, cosGamma));
        double gamma = Math.acos(cosGamma);

        double gammaHalf = gamma / 2;
        double RF = gamma != 0 ? 2 * Math.tan(gammaHalf) / gamma : 1;
        double deltaDTurn = R2 * (Math.cos(alpha1Rad) + Math.cos(alpha2Rad)) * RF / 2;

        double remainingToTarget = config.D_target - D_turn_kop - deltaDTurn;
        if (remainingToTarget < 0) {
            return true;
        }

        double deltaDBuild = R1 * (1 - Math.cos(alpha1Rad));
        double availableSpace = D_turn_kop - D_kop;
        if (availableSpace < deltaDBuild) {
            return true;
        }

        double firstTangentLength = (D_turn_kop - D_kop - deltaDBuild) / Math.cos(alpha1Rad);
        if (firstTangentLength < 0) {
            return true;
        }

        double turnLength = R2 * gamma;
        if (turnLength <= 0) {
            return true;
        }

        double secondTangentLength = remainingToTarget / Math.cos(alpha2Rad);
        if (secondTangentLength < 0) {
            return true;
        }

        double totalLength = D_kop + R1 * alpha1Rad + firstTangentLength + turnLength + secondTangentLength;
        if (totalLength <= 0) {
            return true;
        }

        if (!Double.isFinite(gamma)) {
            return true;
        }

        if (!Double.isFinite(alpha1Rad) || !Double.isFinite(alpha2Rad)) {
            return true;
        }

        if (!Double.isFinite(turnLength) || !Double.isFinite(firstTangentLength) || !Double.isFinite(secondTangentLength)) {
            return true;
        }

        return false;
    }

    public WellPathCalculator getCalculator() {
        return calculator;
    }

    public List<WellObstacleDetector> getWellObstacles() {
        return wellObstacles;
    }
}
