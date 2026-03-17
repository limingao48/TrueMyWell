package club.yunzhi.api.workReview.controller;

import club.yunzhi.api.workReview.entity.Well;
import com.fasterxml.jackson.annotation.JsonView;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 这个接口主要是用于测试请求远程的订阅和取消订阅功能
 */
@RestController
@RequestMapping("subscribe")
public class SubscribeController {

    @GetMapping("/{uniqueKey}")
    public void getAll(@PathVariable String uniqueKey, @RequestParam String status) {
        System.out.println(uniqueKey);
        System.out.println(status);
    }
}
