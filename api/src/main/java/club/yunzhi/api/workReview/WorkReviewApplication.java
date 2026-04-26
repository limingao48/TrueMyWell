package club.yunzhi.api.workReview;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.servlet.ServletComponentScan;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.*;

import static java.lang.Math.pow;
import static java.lang.Math.tan;

@SpringBootApplication
@EnableJpaAuditing
@EnableAsync
@EnableScheduling
@EnableGlobalMethodSecurity(securedEnabled = true)
@ServletComponentScan //webSocket
public class WorkReviewApplication {
    public static void main(String[] args) throws FileNotFoundException, IOException {
        SpringApplication.run(WorkReviewApplication.class, args);
    }
}
