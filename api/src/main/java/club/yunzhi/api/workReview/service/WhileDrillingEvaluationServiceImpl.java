package club.yunzhi.api.workReview.service;

import club.yunzhi.api.workReview.entity.*;
import club.yunzhi.api.workReview.properties.WhileDrillingProperties;
import club.yunzhi.api.workReview.trajectory.TrajectoryExtrapolator;
import club.yunzhi.api.workReview.trajectory.WhileDrillingEvaluator;
import club.yunzhi.api.workReview.trajectory.iscwsa.IscwsaMwdParameters;
import club.yunzhi.api.workReview.util.ExcelParser;
import com.mengyunzhi.core.exception.ValidationException;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class WhileDrillingEvaluationServiceImpl implements WhileDrillingEvaluationService {

    private final PendingDrillWellService pendingDrillWellService;
    private final WhileDrillingProperties properties;
    private final Map<String, SessionState> sessions = new ConcurrentHashMap<>();

    public WhileDrillingEvaluationServiceImpl(PendingDrillWellService pendingDrillWellService,
                                              WhileDrillingProperties properties) {
        this.pendingDrillWellService = pendingDrillWellService;
        this.properties = properties;
    }

    @Override
    public WhileDrillingSessionInfo startSession(WhileDrillingSessionStartRequest request) {
        if (request.getPendingWellId() == null) {
            throw new ValidationException("请选择待钻井");
        }
        PendingDrillWell well = pendingDrillWellService.getById(request.getPendingWellId());
        if (well == null) {
            throw new ValidationException("待钻井不存在");
        }
        if (well.getTrajectoryFileContent() == null || well.getTrajectoryFileContent().length == 0) {
            throw new ValidationException("待钻井未关联设计轨迹 Excel，无法评估");
        }

        double[][] designTrajectory = loadDesignTrajectory(well);
        if (designTrajectory.length < 2) {
            throw new ValidationException("设计轨迹数据不足");
        }

        String sessionId = UUID.randomUUID().toString().replace("-", "");
        SessionState state = new SessionState();
        state.sessionId = sessionId;
        state.siteId = request.getSiteId();
        state.pendingWellId = request.getPendingWellId();
        state.wellName = well.getName() != null ? well.getName() : ("待钻井" + well.getId());
        state.designTrajectory = designTrajectory;
        state.alertDistanceM = properties.getAlertDistanceM();
        state.wellhead = new TrajectoryExtrapolator.Point3D(
                well.getWellheadE() != null ? well.getWellheadE() : 0.0,
                well.getWellheadN() != null ? well.getWellheadN() : 0.0,
                well.getWellheadD() != null ? well.getWellheadD() : 0.0);
        state.active = true;
        sessions.put(sessionId, state);

        WhileDrillingSessionInfo info = new WhileDrillingSessionInfo();
        info.setSessionId(sessionId);
        info.setSiteId(request.getSiteId());
        info.setPendingWellId(request.getPendingWellId());
        info.setWellName(state.wellName);
        info.setTcpPort(properties.getTcpPort());
        info.setWsPath("/whileDrilling/ws/" + sessionId);
        info.setRestPositionUrl("/whileDrilling/position");
        info.setAlertDistanceM(state.alertDistanceM);
        info.setActive(true);
        return info;
    }

    @Override
    public void stopSession(String sessionId) {
        SessionState state = sessions.get(sessionId);
        if (state != null) {
            state.active = false;
            sessions.remove(sessionId);
        }
    }

    @Override
    public WhileDrillingSessionInfo getSessionInfo(String sessionId) {
        SessionState state = sessions.get(sessionId);
        if (state == null) {
            return null;
        }
        WhileDrillingSessionInfo info = new WhileDrillingSessionInfo();
        info.setSessionId(state.sessionId);
        info.setSiteId(state.siteId);
        info.setPendingWellId(state.pendingWellId);
        info.setWellName(state.wellName);
        info.setTcpPort(properties.getTcpPort());
        info.setWsPath("/whileDrilling/ws/" + sessionId);
        info.setRestPositionUrl("/whileDrilling/position");
        info.setAlertDistanceM(state.alertDistanceM);
        info.setActive(state.active);
        return info;
    }

    @Override
    public WhileDrillingEvaluationResult submitPosition(WhileDrillingPositionRequest request) {
        if (request.getSessionId() == null || request.getSessionId().isEmpty()) {
            throw new ValidationException("sessionId 不能为空");
        }
        SessionState state = sessions.get(request.getSessionId());
        if (state == null || !state.active) {
            throw new ValidationException("随钻评估会话不存在或已结束");
        }
        if (request.getX() == null || request.getY() == null || request.getZ() == null) {
            throw new ValidationException("坐标 x、y、z 不能为空");
        }

        TrajectoryExtrapolator.Point3D current = new TrajectoryExtrapolator.Point3D(
                request.getX(), request.getY(), request.getZ());
        TrajectoryExtrapolator.Point3D prev = state.lastPoint;

        IscwsaMwdParameters mwdParams = new IscwsaMwdParameters(
                properties.getIscwsaSigmaMd(),
                Math.toRadians(properties.getIscwsaSigmaIncDeg()),
                Math.toRadians(properties.getIscwsaSigmaAziDeg()));

        WhileDrillingEvaluator.EvaluationResult eval = WhileDrillingEvaluator.evaluate(
                state.designTrajectory,
                state.prevPrevPoint,
                state.wellhead,
                prev,
                current,
                state.lastHorizontalDistance,
                state.alertDistanceM,
                mwdParams,
                properties.getMonteCarloSamples(),
                properties.getMonteCarloStopProbabilityThreshold(),
                properties.getMonteCarloComprehensiveThresholdM());

        state.prevPrevPoint = prev;
        state.lastPoint = current;
        state.lastHorizontalDistance = eval.horizontalDistance;
        state.lastResult = eval;

        WhileDrillingEvaluationResult result = toDto(state, eval);
        WhileDrillingWebSocketNotifier.notifySession(state.sessionId, result);
        return result;
    }

    public SessionState getSessionState(String sessionId) {
        return sessions.get(sessionId);
    }

    private double[][] loadDesignTrajectory(PendingDrillWell well) {
        List<TrajectoryDesignResult.TrajectoryPoint> points = ExcelParser.parseTrajectoryFromExcel(
                well.getTrajectoryFileContent(),
                well.getTrajectoryFileName(),
                well.getWellheadE(),
                well.getWellheadN(),
                well.getWellheadD());
        double[][] trajectory = new double[points.size()][3];
        for (int i = 0; i < points.size(); i++) {
            TrajectoryDesignResult.TrajectoryPoint p = points.get(i);
            trajectory[i][0] = p.getX() != null ? p.getX() : 0;
            trajectory[i][1] = p.getY() != null ? p.getY() : 0;
            trajectory[i][2] = p.getZ() != null ? p.getZ() : 0;
        }
        return trajectory;
    }

    private WhileDrillingEvaluationResult toDto(SessionState state, WhileDrillingEvaluator.EvaluationResult eval) {
        WhileDrillingEvaluationResult dto = new WhileDrillingEvaluationResult();
        dto.setSessionId(state.sessionId);
        dto.setPendingWellId(state.pendingWellId);
        dto.setWellName(state.wellName);
        dto.setCurrentX(eval.currentE);
        dto.setCurrentY(eval.currentN);
        dto.setCurrentZ(eval.currentTvd);
        dto.setDesignX(eval.designE);
        dto.setDesignY(eval.designN);
        dto.setHorizontalDistance(eval.horizontalDistance);
        dto.setAlertDistanceThreshold(eval.alertDistanceThreshold);
        dto.setDistanceExpanding(eval.distanceExpanding);
        dto.setPredictionTriggered(eval.predictionTriggered);
        dto.setShouldStopDrilling(eval.shouldStopDrilling);
        dto.setStatus(eval.status);
        dto.setMessage(eval.message);
        dto.setDoglegDeg(eval.doglegDeg);
        dto.setDlsDegPer30m(eval.dlsDegPer30m);
        dto.setMonteCarloSampleCount(eval.monteCarloSampleCount);
        dto.setMonteCarloComprehensiveCount(eval.monteCarloComprehensiveCount);
        dto.setMonteCarloComprehensiveProbability(eval.monteCarloComprehensiveProbability);
        dto.setMonteCarloMeanSecondStepDistance(eval.monteCarloMeanSecondStepDistance);
        dto.setMonteCarloComprehensiveThresholdM(eval.monteCarloComprehensiveThresholdM);
        dto.setMonteCarloStopRecommended(eval.monteCarloStopRecommended);
        dto.setIscwsaSigmaMd(eval.iscwsaSigmaMd);
        dto.setIscwsaSigmaIncDeg(eval.iscwsaSigmaIncDeg);
        dto.setIscwsaSigmaAziDeg(eval.iscwsaSigmaAziDeg);
        dto.setTimestamp(System.currentTimeMillis());
        return dto;
    }

    public static class SessionState {
        public String sessionId;
        public Long siteId;
        public Long pendingWellId;
        public String wellName;
        public double[][] designTrajectory;
        public double alertDistanceM;
        public boolean active;
        public TrajectoryExtrapolator.Point3D wellhead;
        public TrajectoryExtrapolator.Point3D prevPrevPoint;
        public TrajectoryExtrapolator.Point3D lastPoint;
        public double lastHorizontalDistance;
        public WhileDrillingEvaluator.EvaluationResult lastResult;
    }
}
