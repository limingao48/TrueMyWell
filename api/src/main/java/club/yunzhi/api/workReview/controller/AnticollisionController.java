package club.yunzhi.api.workReview.controller;

import club.yunzhi.api.workReview.entity.AnticollisionScanRequest;
import club.yunzhi.api.workReview.entity.AnticollisionScanResult;
import club.yunzhi.api.workReview.service.AnticollisionService;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("anticollision")
public class AnticollisionController {

    private final AnticollisionService anticollisionService;

    public AnticollisionController(AnticollisionService anticollisionService) {
        this.anticollisionService = anticollisionService;
    }

    @PostMapping("scan")
    public AnticollisionScanResult scan(@RequestBody AnticollisionScanRequest request) {
        return anticollisionService.scan(request);
    }
}
