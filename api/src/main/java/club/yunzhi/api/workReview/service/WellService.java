package club.yunzhi.api.workReview.service;

import club.yunzhi.api.workReview.entity.Well;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

import java.util.List;


public interface WellService {
    List<Well> getAll();

    Long getAllNumber();

    Well getById(String wellId);

    Page<Well> page(String wellId, Pageable pageable);

    String add(Well well);
}
