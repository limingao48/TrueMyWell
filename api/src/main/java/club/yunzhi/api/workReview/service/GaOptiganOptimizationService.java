package club.yunzhi.api.workReview.service;

import club.yunzhi.api.workReview.config.TrajectoryOptimizationProperties;
import club.yunzhi.api.workReview.entity.TrajectoryDesignRequest;
import club.yunzhi.api.workReview.entity.TrajectoryDesignResult;
import club.yunzhi.api.workReview.trajectory.optimizer.ProgressCallback;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;

@Service
public class GaOptiganOptimizationService {

    private final TrajectoryOptimizationProperties properties;
    private final NeighborWellTrajectoryService neighborWellTrajectoryService;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public GaOptiganOptimizationService(TrajectoryOptimizationProperties properties,
                                          NeighborWellTrajectoryService neighborWellTrajectoryService) {
        this.properties = properties;
        this.neighborWellTrajectoryService = neighborWellTrajectoryService;
    }

    public static boolean isGaOptiganAlgorithm(String algorithmType) {
        if (algorithmType == null || algorithmType.isEmpty()) {
            return false;
        }
        String normalized = algorithmType.trim().toUpperCase().replace("_", "-");
        return "GA-OPTIGAN".equals(normalized);
    }

    public TrajectoryDesignResult runOptimization(TrajectoryDesignRequest request,
                                                  ProgressCallback progressCallback) throws IOException, InterruptedException {
        Path scriptDir = properties.resolveScriptDir();
        Path cliScript = properties.resolveCliScript();
        if (!Files.isRegularFile(cliScript)) {
            throw new IOException("未找到 GA-optiGAN CLI 脚本: " + cliScript.toAbsolutePath()
                    + "，请配置 trajectory.optimization.script-dir");
        }

        Path workDir = Files.createTempDirectory("ga-optigan-design-");
        Path inputJson = workDir.resolve("input.json");
        Path outputJson = workDir.resolve("output.json");
        Path progressJson = workDir.resolve("progress.json");

        List<Path> tempNeighborFiles = new ArrayList<>();
        try {
            ObjectNode payload = buildPayload(request, workDir, tempNeighborFiles);
            objectMapper.writerWithDefaultPrettyPrinter().writeValue(inputJson.toFile(), payload);

            List<String> command = new ArrayList<>();
            command.add(properties.getPythonExecutable());
            command.add(cliScript.toString());
            command.add("--input");
            command.add(inputJson.toString());
            command.add("--output");
            command.add(outputJson.toString());
            command.add("--progress");
            command.add(progressJson.toString());

            ProcessBuilder pb = new ProcessBuilder(command);
            pb.directory(scriptDir.toFile());
            pb.redirectErrorStream(true);
            Map<String, String> env = pb.environment();
            env.put("PYTHONIOENCODING", "utf-8");
            env.put("PYTHONUTF8", "1");

            Process process = pb.start();
            StringBuilder processLog = new StringBuilder();
            Thread logDrainer = startProcessLogDrainer(process, processLog);

            AtomicBoolean stopPoller = new AtomicBoolean(false);
            Thread poller = startProgressPoller(progressJson, progressCallback, stopPoller);

            boolean finished = process.waitFor(properties.getGaOptiganTimeoutSeconds(), TimeUnit.SECONDS);
            stopPoller.set(true);
            if (poller != null) {
                poller.join(2000L);
            }
            if (logDrainer != null) {
                logDrainer.join(5000L);
            }
            String log = processLog.toString();

            if (!finished) {
                process.destroyForcibly();
                throw new IOException("GA-optiGAN 优化超时（超过 " + properties.getGaOptiganTimeoutSeconds() + " 秒）\n" + tailLog(log));
            }

            int exitCode = process.exitValue();
            if (!Files.isRegularFile(outputJson)) {
                throw new IOException(
                        "GA-optiGAN 未生成结果文件，退出码=" + exitCode
                                + "。请确认 application.yml 中 python-executable 指向已安装 numpy、torch 的 Python。\n"
                                + tailLog(log));
            }

            JsonNode resultNode = objectMapper.readTree(outputJson.toFile());
            if (!resultNode.path("success").asBoolean(false)) {
                String err = resultNode.path("error").asText("GA-optiGAN 优化失败");
                String trace = resultNode.path("traceback").asText("");
                throw new IOException(err + (trace.isEmpty() ? "" : "\n" + trace));
            }

            return mapToDesignResult(request, resultNode);
        } finally {
            for (Path p : tempNeighborFiles) {
                try {
                    Files.deleteIfExists(p);
                } catch (IOException ignored) {
                }
            }
            try {
                Files.deleteIfExists(inputJson);
                Files.deleteIfExists(outputJson);
                Files.deleteIfExists(progressJson);
                Files.deleteIfExists(workDir);
            } catch (IOException ignored) {
            }
        }
    }

    private ObjectNode buildPayload(TrajectoryDesignRequest request, Path workDir, List<Path> tempFiles) throws IOException {
        ObjectNode root = objectMapper.createObjectNode();
        root.set("target", toPointNode(request.getTarget()));
        root.set("wellhead", toPointNode(request.getWellhead()));
        root.set("landingRequirement", toLandingNode(request.getLandingRequirement()));
        root.set("algorithm", toAlgorithmNode(request.getAlgorithm()));

        ArrayNode neighbors = objectMapper.createArrayNode();
        List<NeighborWellTrajectoryService.NeighborExcelExport> exports =
                neighborWellTrajectoryService.exportNeighborExcelFiles(request, workDir);
        for (NeighborWellTrajectoryService.NeighborExcelExport exp : exports) {
            tempFiles.add(exp.getExcelPath());
            ObjectNode nb = objectMapper.createObjectNode();
            nb.put("excelPath", exp.getExcelPath().toAbsolutePath().toString());
            ObjectNode wh = objectMapper.createObjectNode();
            wh.put("e", exp.getWellheadE());
            wh.put("n", exp.getWellheadN());
            wh.put("d", exp.getWellheadD());
            nb.set("wellhead", wh);
            neighbors.add(nb);
        }
        root.set("neighborWells", neighbors);
        return root;
    }

    private ObjectNode toPointNode(TrajectoryDesignRequest.Target t) {
        ObjectNode n = objectMapper.createObjectNode();
        if (t != null) {
            if (t.getE() != null) n.put("e", t.getE());
            if (t.getN() != null) n.put("n", t.getN());
            if (t.getD() != null) n.put("d", t.getD());
        }
        return n;
    }

    private ObjectNode toPointNode(TrajectoryDesignRequest.Wellhead w) {
        ObjectNode n = objectMapper.createObjectNode();
        if (w != null) {
            if (w.getE() != null) n.put("e", w.getE());
            if (w.getN() != null) n.put("n", w.getN());
            if (w.getD() != null) n.put("d", w.getD());
        }
        return n;
    }

    private ObjectNode toLandingNode(TrajectoryDesignRequest.LandingRequirement lr) {
        ObjectNode n = objectMapper.createObjectNode();
        if (lr == null) {
            return n;
        }
        if (lr.getInclinationMin() != null) n.put("inclinationMin", lr.getInclinationMin());
        if (lr.getInclinationMax() != null) n.put("inclinationMax", lr.getInclinationMax());
        if (lr.getAzimuthMin() != null) n.put("azimuthMin", lr.getAzimuthMin());
        if (lr.getAzimuthMax() != null) n.put("azimuthMax", lr.getAzimuthMax());
        if (lr.getVerticalTolerance() != null) n.put("verticalTolerance", lr.getVerticalTolerance());
        if (lr.getHorizontalTolerance() != null) n.put("horizontalTolerance", lr.getHorizontalTolerance());
        return n;
    }

    private ObjectNode toAlgorithmNode(TrajectoryDesignRequest.Algorithm algo) {
        ObjectNode n = objectMapper.createObjectNode();
        if (algo == null) {
            return n;
        }
        if (algo.getPopulation() != null) n.put("population", algo.getPopulation());
        if (algo.getIterations() != null) n.put("iterations", algo.getIterations());
        if (algo.getMaxEvaluations() != null) n.put("maxEvaluations", algo.getMaxEvaluations());
        if (algo.getMinKickoffDepth() != null) n.put("minKickoffDepth", algo.getMinKickoffDepth());
        if (algo.getDoglegMin() != null) n.put("doglegMin", algo.getDoglegMin());
        if (algo.getDoglegMax() != null) n.put("doglegMax", algo.getDoglegMax());
        if (algo.getSafeRadius() != null) n.put("safeRadius", algo.getSafeRadius());
        if (algo.getMinSafetyFactor() != null) n.put("minSafetyFactor", algo.getMinSafetyFactor());
        if (algo.getAnticollisionMethod() != null) n.put("anticollisionMethod", algo.getAnticollisionMethod());
        n.put("optiganDir", properties.resolveScriptDir().resolve("GA-optiGAN").toString());
        return n;
    }

    private TrajectoryDesignResult mapToDesignResult(TrajectoryDesignRequest request, JsonNode node) {
        TrajectoryDesignResult result = new TrajectoryDesignResult();

        JsonNode dict = node.get("best_solution_dict");
        if (dict != null && dict.isObject()) {
            Map<String, Double> best = new LinkedHashMap<>();
            dict.fields().forEachRemaining(e -> best.put(e.getKey(), e.getValue().asDouble()));
            result.setBest_solution_dict(best);
        }

        if (node.has("final_deviation") && !node.get("final_deviation").isNull()) {
            result.setFinal_deviation(node.get("final_deviation").asDouble());
        }
        if (node.has("optimization_time")) {
            result.setOptimization_time(node.get("optimization_time").asDouble());
        }

        JsonNode trajPoints = node.get("trajectory_points");
        if (trajPoints != null && trajPoints.isArray()) {
            List<TrajectoryDesignResult.TrajectoryPoint> points = new ArrayList<>();
            for (JsonNode p : trajPoints) {
                points.add(new TrajectoryDesignResult.TrajectoryPoint(
                        p.path("x").asDouble(),
                        p.path("y").asDouble(),
                        p.path("z").asDouble()
                ));
            }
            result.setTrajectory_points(points);
        }

        result.setNeighbor_wells(neighborWellTrajectoryService.loadNeighborTrajectories(request));
        return result;
    }

    private Thread startProgressPoller(Path progressJson, ProgressCallback callback, AtomicBoolean stop) {
        if (callback == null) {
            return null;
        }
        Thread t = new Thread(() -> {
            while (!stop.get()) {
                try {
                    if (Files.isRegularFile(progressJson)) {
                        JsonNode prog = objectMapper.readTree(progressJson.toFile());
                        int iteration = prog.path("iteration").asInt(0);
                        int total = prog.path("totalIterations").asInt(200);
                        double percent = prog.path("progressPercent").asDouble(0);
                        String message = prog.path("message").asText("GA-optiGAN 运行中...");
                        double currentBest = prog.has("currentBest") && !prog.get("currentBest").isNull()
                                ? prog.get("currentBest").asDouble() : Double.NaN;
                        callback.onProgress(iteration, total, currentBest, message);
                        if (percent >= 100 || prog.path("completed").asBoolean(false)) {
                            break;
                        }
                    }
                    Thread.sleep(800L);
                } catch (Exception ignored) {
                    try {
                        Thread.sleep(800L);
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                        break;
                    }
                }
            }
        }, "ga-optigan-progress");
        t.setDaemon(true);
        t.start();
        return t;
    }

    private Thread startProcessLogDrainer(Process process, StringBuilder sink) {
        Thread t = new Thread(() -> {
            try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    synchronized (sink) {
                        sink.append(line).append('\n');
                        if (sink.length() > 64_000) {
                            sink.delete(0, sink.length() - 48_000);
                        }
                    }
                }
            } catch (IOException ignored) {
            }
        }, "ga-optigan-log");
        t.setDaemon(true);
        t.start();
        return t;
    }

    private static String tailLog(String log) {
        if (log == null || log.isEmpty()) {
            return "(无 Python 输出，请在本机命令行执行: python run_ga_optigan_design_cli.py --help)";
        }
        String trimmed = log.trim();
        if (trimmed.length() <= 4000) {
            return trimmed;
        }
        return trimmed.substring(trimmed.length() - 4000);
    }
}
