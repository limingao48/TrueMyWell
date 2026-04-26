package club.yunzhi.api.workReview.service;

import club.yunzhi.api.workReview.entity.Site;
import club.yunzhi.api.workReview.repository.SiteRepository;
import club.yunzhi.api.workReview.repository.sepcs.SiteSpecs;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

import javax.persistence.EntityNotFoundException;
import java.util.List;

/**
 * 井场服务实现
 */
@Service
public class SiteServiceImpl implements SiteService {

    private final SiteRepository siteRepository;

    public SiteServiceImpl(SiteRepository siteRepository) {
        this.siteRepository = siteRepository;
    }

    @Override
    public List<Site> getAll() {
        return (List<Site>) siteRepository.findAll();
    }

    @Override
    public Site getById(String siteId) {
        try {
            Long id = Long.parseLong(siteId);
            return siteRepository.findById(id)
                    .orElseThrow(() -> new EntityNotFoundException("井场不存在"));
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("无效的井场ID");
        }
    }

    @Override
    public Page<Site> page(String siteId, Pageable pageable) {
        return siteRepository.findAll(SiteSpecs.equalSiteId(siteId), pageable);
    }

    @Override
    public String add(Site site) {
        siteRepository.save(site);
        return "添加成功";
    }

    @Override
    public String update(Site site) {
        if (site.getId() == null) {
            throw new IllegalArgumentException("井场ID不能为空");
        }
        if (!siteRepository.existsById(site.getId())) {
            throw new EntityNotFoundException("井场不存在");
        }
        siteRepository.save(site);
        return "更新成功";
    }

    @Override
    public String delete(Long id) {
        if (!siteRepository.existsById(id)) {
            throw new EntityNotFoundException("井场不存在");
        }
        siteRepository.deleteById(id);
        return "删除成功";
    }
}
