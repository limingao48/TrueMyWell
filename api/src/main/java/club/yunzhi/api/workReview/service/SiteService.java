package club.yunzhi.api.workReview.service;

import club.yunzhi.api.workReview.entity.Site;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

import java.util.List;


public interface SiteService {
    List<Site> getAll();

    Site getById(String siteId);

    Page<Site> page(String siteId, Pageable pageable);

    String add(Site site);

    String update(Site site);

    String delete(Long id);
}