package club.yunzhi.api.workReview.service;

import club.yunzhi.api.workReview.entity.Well;
import club.yunzhi.api.workReview.repository.WellRepository;
import club.yunzhi.api.workReview.repository.sepcs.WellSpecs;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

import javax.persistence.EntityNotFoundException;
import java.util.List;

/**
 * 井服务实现
 */
@Service
public class WellServiceImpl implements WellService {

    private final WellRepository wellRepository;

    public WellServiceImpl(WellRepository wellRepository) {
        this.wellRepository = wellRepository;
    }

    @Override
    public List<Well> getAll() {
        return (List<Well>) wellRepository.findAll();
    }

    @Override
    public Long getAllNumber() {
        return wellRepository.count();
    }

    @Override
    public Well getById(String wellId) {
        try {
            Long id = Long.parseLong(wellId);
            return wellRepository.findById(id)
                    .orElseThrow(() -> new EntityNotFoundException("井不存在"));
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("无效的井ID");
        }
    }

    @Override
    public Page<Well> page(String wellId, Pageable pageable) {
        return wellRepository.findAll(WellSpecs.equalWellId(wellId), pageable);
    }

    @Override
    public String add(Well well) {
        wellRepository.save(well);
        return "添加成功";
    }

    @Override
    public String update(Well well) {
        if (well.getId() == null) {
            throw new IllegalArgumentException("井ID不能为空");
        }
        if (!wellRepository.existsById(well.getId())) {
            throw new EntityNotFoundException("井不存在");
        }
        wellRepository.save(well);
        return "更新成功";
    }

    @Override
    public String delete(Long id) {
        if (!wellRepository.existsById(id)) {
            throw new EntityNotFoundException("井不存在");
        }
        wellRepository.deleteById(id);
        return "删除成功";
    }
}
