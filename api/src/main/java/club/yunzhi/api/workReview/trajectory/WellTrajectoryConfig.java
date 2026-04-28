package club.yunzhi.api.workReview.trajectory;

import java.util.HashMap;
import java.util.Map;

public class WellTrajectoryConfig {
    public double E_target = 1500.64;
    public double N_target = 1200.71;
    public double D_target = 2936.06;

    public double E_wellhead = 30.0;
    public double N_wellhead = 15.0;
    public double D_wellhead = 0.0;

    public double TOLERANCE = 10.0;

    public int obstacleCount = 0;
    public double obstacleMinRadius = 50.0;
    public double obstacleMaxRadius = 50.0;
    public double[] obstacleXRange = {0, 1500};
    public double[] obstacleYRange = {0, 1500};
    public double[] obstacleZRange = {1600, 3000};

    public double safetyRadius = 10.0;
    public double targetDeviationThreshold = 30.0;
    public double targetDeviationPenalty = 100000.0;

    public double[] sevenL0Range = {500.0, 2500.0};
    public double[] sevenDLS1Range = {1.0, 6.0};
    public double[] sevenAlpha3Range = {5.0, 85.0};
    public double[] sevenL3Range = {0.0, 2500.0};
    public double[] sevenDLSTurnRange = {1.0, 6.0};
    public double[] sevenL4Range = {0.0, 2000.0};
    public double[] sevenL5Range = {0.0, 2500.0};
    public double[] sevenDLS6Range = {1.0, 6.0};
    public double[] sevenAlphaERange = {85.0, 90.0};
    public double[] sevenL7Range = {0.0, 2500.0};
    public double[] sevenPhiInitRange = {0.0, 360.0};
    public double[] sevenPhiTargetRange = {355.0, 360.0};

    public static final String[] SEVEN_SEG_PARAM_NAMES = {
        "L0", "DLS1", "alpha3", "L3", "DLS_turn", "L4",
        "L5", "DLS6", "alpha_e", "L7", "phi_init", "phi_target"
    };

    public Map<String, double[]> SEVEN_SEG_BOUNDS_DICT;
    public double[][] SEVEN_SEG_BOUNDS;

    public double D_kop_min = 500;
    public double D_kop_max = 1500;
    public double alpha_1_min = 10;
    public double alpha_1_max = 60;
    public double alpha_2_min = 88;
    public double alpha_2_max = 92;
    public double phi_1_min = 0;
    public double phi_1_max = 360;
    public double phi_2_min = 355;
    public double phi_2_max = 360;
    public double R_1_min = 286;
    public double R_1_max = 1145;
    public double R_2_min = 286;
    public double R_2_max = 1145;
    public double D_turn_kop_min = 1500;
    public double D_turn_kop_max = 2400;

    public double[][] BOUNDS;

    public WellTrajectoryConfig() {
        SEVEN_SEG_BOUNDS_DICT = new HashMap<>();
        SEVEN_SEG_BOUNDS_DICT.put("L0", sevenL0Range);
        SEVEN_SEG_BOUNDS_DICT.put("DLS1", sevenDLS1Range);
        SEVEN_SEG_BOUNDS_DICT.put("alpha3", sevenAlpha3Range);
        SEVEN_SEG_BOUNDS_DICT.put("L3", sevenL3Range);
        SEVEN_SEG_BOUNDS_DICT.put("DLS_turn", sevenDLSTurnRange);
        SEVEN_SEG_BOUNDS_DICT.put("L4", sevenL4Range);
        SEVEN_SEG_BOUNDS_DICT.put("L5", sevenL5Range);
        SEVEN_SEG_BOUNDS_DICT.put("DLS6", sevenDLS6Range);
        SEVEN_SEG_BOUNDS_DICT.put("alpha_e", sevenAlphaERange);
        SEVEN_SEG_BOUNDS_DICT.put("L7", sevenL7Range);
        SEVEN_SEG_BOUNDS_DICT.put("phi_init", sevenPhiInitRange);
        SEVEN_SEG_BOUNDS_DICT.put("phi_target", sevenPhiTargetRange);

        SEVEN_SEG_BOUNDS = new double[SEVEN_SEG_PARAM_NAMES.length][2];
        for (int i = 0; i < SEVEN_SEG_PARAM_NAMES.length; i++) {
            SEVEN_SEG_BOUNDS[i] = SEVEN_SEG_BOUNDS_DICT.get(SEVEN_SEG_PARAM_NAMES[i]);
        }

        BOUNDS = new double[][] {
            {D_kop_min, D_kop_max},
            {alpha_1_min, alpha_1_max},
            {alpha_2_min, alpha_2_max},
            {phi_1_min, phi_1_max},
            {phi_2_min, phi_2_max},
            {R_1_min, R_1_max},
            {R_2_min, R_2_max},
            {D_turn_kop_min, D_turn_kop_max}
        };
    }

    public boolean validateParameters(double[] positionTuple) {
        if (positionTuple == null || positionTuple.length != 8) {
            return false;
        }

        for (int i = 0; i < positionTuple.length; i++) {
            if (!(BOUNDS[i][0] <= positionTuple[i] && positionTuple[i] <= BOUNDS[i][1])) {
                return false;
            }
        }

        if (positionTuple[0] > positionTuple[7]) {
            return false;
        }

        return true;
    }

    public boolean validateSevenSegmentParameters(double[] params) {
        if (params == null || params.length != SEVEN_SEG_PARAM_NAMES.length) {
            return false;
        }

        for (int i = 0; i < params.length; i++) {
            if (!(SEVEN_SEG_BOUNDS[i][0] <= params[i] && params[i] <= SEVEN_SEG_BOUNDS[i][1])) {
                return false;
            }
        }

        double alpha3 = params[2];
        double alpha_e = params[8];
        if (!(0.0 <= alpha3 && alpha3 <= 89.0 && 0.0 <= alpha_e && alpha_e <= 89.0)) {
            return false;
        }

        return true;
    }

    public double[] getTargetPoint() {
        return new double[]{E_target, N_target, D_target};
    }

    public double[] getWellheadPoint() {
        return new double[]{E_wellhead, N_wellhead, D_wellhead};
    }

    public double[][] getSevenSegmentBounds() {
        return SEVEN_SEG_BOUNDS.clone();
    }
}
