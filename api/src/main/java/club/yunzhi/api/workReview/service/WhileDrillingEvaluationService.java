package club.yunzhi.api.workReview.service;

import club.yunzhi.api.workReview.entity.*;

public interface WhileDrillingEvaluationService {

    WhileDrillingSessionInfo startSession(WhileDrillingSessionStartRequest request);

    void stopSession(String sessionId);

    WhileDrillingSessionInfo getSessionInfo(String sessionId);

    WhileDrillingEvaluationResult submitPosition(WhileDrillingPositionRequest request);
}
