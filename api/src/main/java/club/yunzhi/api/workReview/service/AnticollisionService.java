package club.yunzhi.api.workReview.service;

import club.yunzhi.api.workReview.entity.AnticollisionScanRequest;
import club.yunzhi.api.workReview.entity.AnticollisionScanResult;

public interface AnticollisionService {
    AnticollisionScanResult scan(AnticollisionScanRequest request);
}
