package com.yasuke.ttl.bridge;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.logging.LogUtils;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.event.server.ServerStoppingEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import org.slf4j.Logger;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Collection;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.function.Supplier;

/**
 * The AI build bridge (docs/dev/build-bridge.md): a token-protected HTTP API on 127.0.0.1 that the
 * {@code tools/forge} MCP sidecar uses to read terrain, the block/biome registry and to queue undoable builds.
 * Off unless {@code config/ttl/bridge.json} says {@code "enabled": true}. HTTP runs on its own threads; every world
 * access is handed to the server thread, writes run in a per-tick budget (BridgeJobs). There is no command endpoint.
 */
public final class Bridge {
    private static final Logger LOGGER = LogUtils.getLogger();
    private static final int MAX_BODY = 64 * 1024 * 1024;

    private static MinecraftServer server;
    private static BridgeConfig config;
    private static BridgeJobs jobs;
    private static HttpServer http;
    private static ExecutorService pool;

    private Bridge() {}

    // --- lifecycle --------------------------------------------------------------------------------------------------

    public static void onServerStarted(ServerStartedEvent event) {
        server = event.getServer();
        start();
    }

    public static void onServerStopping(ServerStoppingEvent event) {
        stop();
        if (jobs != null) jobs.shutdown();
        jobs = null;
        server = null;
    }

    public static void onServerTick(ServerTickEvent.Post event) {
        if (jobs != null) jobs.tick();
    }

    private static void start() {
        config = BridgeConfig.load();
        if (jobs == null) jobs = new BridgeJobs(server, config);
        else jobs.config(config);
        if (!config.enabled) {
            LOGGER.info("[ttl] bridge: disabled (config/ttl/bridge.json)");
            return;
        }
        if (config.token.isEmpty()) {
            LOGGER.error("[ttl] bridge: no token, not starting");
            return;
        }
        try {
            http = HttpServer.create(new InetSocketAddress(config.bind, config.port), 16);
            pool = Executors.newFixedThreadPool(2, r -> {
                Thread t = new Thread(r, "ttl-bridge-http");
                t.setDaemon(true);
                return t;
            });
            http.setExecutor(pool);
            http.createContext("/v1/", Bridge::handle);
            http.start();
            LOGGER.info("[ttl] bridge: listening on {}:{} ({} zones, {} protected, allow_anywhere={})", config.bind, config.port,
                    config.zones.size(), config.protect.size(), config.allowAnywhere);
        } catch (IOException e) {
            LOGGER.error("[ttl] bridge: cannot listen on {}:{}: {}", config.bind, config.port, e.toString());
            http = null;
        }
    }

    private static void stop() {
        if (http != null) http.stop(0);
        if (pool != null) pool.shutdownNow();
        http = null;
        pool = null;
    }

    // --- HTTP -------------------------------------------------------------------------------------------------------

    static final class BadRequest extends RuntimeException {
        BadRequest(String m) { super(m); }
    }

    static final class Forbidden extends RuntimeException {
        Forbidden(String m) { super(m); }
    }

    static final class NotFound extends RuntimeException {
        NotFound(String m) { super(m); }
    }

    private static void handle(HttpExchange ex) throws IOException {
        int status = 200;
        String body;
        try {
            if (!authorised(ex)) {
                status = 401;
                body = error("missing or wrong bearer token");
            } else {
                body = route(ex).toString();
            }
        } catch (BadRequest e) {
            status = 400;
            body = error(e.getMessage());
        } catch (Forbidden e) {
            status = 403;
            body = error(e.getMessage());
        } catch (NotFound e) {
            status = 404;
            body = error(e.getMessage());
        } catch (TimeoutException e) {
            status = 503;
            body = error("server thread did not answer in time");
        } catch (Exception e) {
            status = 500;
            body = error(e.toString());
            LOGGER.error("[ttl] bridge: {} {} failed", ex.getRequestMethod(), ex.getRequestURI(), e);
        }
        byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
        ex.getResponseHeaders().set("Content-Type", "application/json; charset=utf-8");
        ex.sendResponseHeaders(status, bytes.length);
        try (OutputStream out = ex.getResponseBody()) {
            out.write(bytes);
        }
    }

    private static boolean authorised(HttpExchange ex) {
        String header = ex.getRequestHeaders().getFirst("Authorization");
        if (header == null || !header.startsWith("Bearer ")) return false;
        return MessageDigest.isEqual(header.substring(7).trim().getBytes(StandardCharsets.UTF_8),
                config.token.getBytes(StandardCharsets.UTF_8));
    }

    private static Object route(HttpExchange ex) throws Exception {
        String method = ex.getRequestMethod();
        String path = ex.getRequestURI().getPath();
        Map<String, String> q = query(ex.getRequestURI().getRawQuery());
        String[] parts = path.substring("/v1/".length()).split("/");
        String head = parts[0];
        if (method.equals("POST") && head.equals("jobs") && parts.length == 3) {
            if (parts[2].equals("undo")) return onMain(() -> jobs.undo(parts[1]));
            if (parts[2].equals("cancel")) return onMain(() -> jobs.cancel(parts[1]));
            throw new NotFound("no endpoint " + method + " " + path);
        }
        if (method.equals("POST") && parts.length != 1) throw new NotFound("no endpoint " + method + " " + path);
        switch (method + " " + head) {
            case "GET health": return onMain(Bridge::health);
            case "GET registry": return onMain(() -> BridgeWorld.registry(server));
            case "GET zones": return zones();
            case "GET region": return onMain(() -> region(q));
            case "POST biome": {
                JsonObject req = body(ex);
                return onMain(() -> biome(req));
            }
            case "POST jobs": {
                JsonObject req = body(ex);
                return onMain(() -> jobs.submit(req));
            }
            case "GET jobs": {
                if (parts.length == 1) {
                    int limit = Integer.parseInt(q.getOrDefault("limit", "20"));
                    return onMain(() -> wrap("jobs", jobs.list(limit)));
                }
                return onMain(() -> jobs.get(parts[1]));
            }
            default:
                break;
        }
        throw new NotFound("no endpoint " + method + " " + path);
    }

    private static <T> T onMain(Supplier<T> task) throws Exception {
        try {
            return server.submit(task).get(60, TimeUnit.SECONDS);
        } catch (java.util.concurrent.ExecutionException e) {
            if (e.getCause() instanceof Exception cause) throw cause;
            throw e;
        }
    }

    private static JsonObject health() {
        JsonObject o = new JsonObject();
        o.addProperty("ok", true);
        o.addProperty("mod", "ttl-portals");
        o.addProperty("players", server.getPlayerCount());
        o.addProperty("mspt", Math.round(server.getAverageTickTimeNanos() / 10_000.0) / 100.0);
        o.addProperty("queued_jobs", jobs.queued());
        o.addProperty("budget_ms", config.budgetMs);
        o.addProperty("pause_mspt", config.pauseMspt);
        return o;
    }

    private static JsonObject zones() {
        JsonObject o = new JsonObject();
        JsonArray z = new JsonArray();
        config.zones.forEach(zone -> z.add(zone.json()));
        JsonArray p = new JsonArray();
        config.protect.forEach(zone -> p.add(zone.json()));
        o.add("zones", z);
        o.add("protect", p);
        o.addProperty("allow_anywhere", config.allowAnywhere);
        o.addProperty("max_job_cells", config.maxJobCells);
        return o;
    }

    private static JsonObject region(Map<String, String> q) {
        ServerLevel level = BridgeWorld.level(server, q.getOrDefault("dim", "minecraft:overworld"));
        String mode = q.getOrDefault("mode", "summary");
        boolean load = !"false".equals(q.get("load"));
        int x1 = num(q, "x1"), z1 = num(q, "z1"), x2 = num(q, "x2"), z2 = num(q, "z2");
        if (mode.equals("heightmap")) {
            long cols = (long) (Math.abs(x2 - x1) + 1) * (Math.abs(z2 - z1) + 1);
            if (cols > config.maxHeightmapColumns) throw new BadRequest(cols + " columns, limit " + config.maxHeightmapColumns);
            return BridgeWorld.heightmap(level, Math.min(x1, x2), Math.min(z1, z2), Math.max(x1, x2), Math.max(z1, z2), load);
        }
        int y1 = num(q, "y1"), y2 = num(q, "y2");
        BoundingBox box = new BoundingBox(Math.min(x1, x2), Math.max(Math.min(y1, y2), level.getMinBuildHeight()), Math.min(z1, z2),
                Math.max(x1, x2), Math.min(Math.max(y1, y2), level.getMaxBuildHeight() - 1), Math.max(z1, z2));
        long cells = (long) box.getXSpan() * box.getYSpan() * box.getZSpan();
        if (mode.equals("blocks")) {
            if (cells > config.maxReadCells) throw new BadRequest(cells + " cells, limit " + config.maxReadCells + " in blocks mode");
            return BridgeWorld.readBlocks(level, box, load, "true".equals(q.get("nbt")));
        }
        if (mode.equals("summary")) {
            if (cells > config.maxSummaryCells) throw new BadRequest(cells + " cells, limit " + config.maxSummaryCells + " in summary mode");
            return BridgeWorld.summary(level, box, load);
        }
        throw new BadRequest("mode must be summary, blocks or heightmap");
    }

    private static JsonObject biome(JsonObject req) {
        ServerLevel level = BridgeWorld.level(server, str(req, "dim", "minecraft:overworld"));
        int[] a = ints(req.getAsJsonArray("from"), 3), b = ints(req.getAsJsonArray("to"), 3);
        BoundingBox box = new BoundingBox(Math.min(a[0], b[0]), Math.max(Math.min(a[1], b[1]), level.getMinBuildHeight()), Math.min(a[2], b[2]),
                Math.max(a[0], b[0]), Math.min(Math.max(a[1], b[1]), level.getMaxBuildHeight() - 1), Math.max(a[2], b[2]));
        long columns = (long) box.getXSpan() * box.getZSpan();
        if (columns > 1024L * 1024L) throw new BadRequest("biome box larger than 1024 x 1024 columns");
        String refusal = config.writeRefusal(level.dimension().location().toString(), box);
        if (refusal != null) throw new Forbidden(refusal);
        boolean dry = req.has("dry_run") && req.get("dry_run").getAsBoolean();
        JsonObject out = BridgeWorld.fillBiome(level, box, str(req, "biome", ""), dry);
        if (!dry) LOGGER.info("[ttl] bridge: biome {} set in {} {}", out.get("biome").getAsString(), level.dimension().location(), box);
        return out;
    }

    // --- small JSON helpers -----------------------------------------------------------------------------------------

    private static JsonObject body(HttpExchange ex) throws IOException {
        try (InputStream in = ex.getRequestBody()) {
            byte[] bytes = in.readNBytes(MAX_BODY + 1);
            if (bytes.length > MAX_BODY) throw new BadRequest("body larger than " + MAX_BODY + " bytes");
            JsonObject o = BridgeConfig.GSON.fromJson(new String(bytes, StandardCharsets.UTF_8), JsonObject.class);
            if (o == null) throw new BadRequest("empty body");
            return o;
        } catch (com.google.gson.JsonParseException e) {
            throw new BadRequest("body is not JSON: " + e.getMessage());
        }
    }

    private static Map<String, String> query(String raw) {
        Map<String, String> out = new HashMap<>();
        if (raw == null) return out;
        for (String pair : raw.split("&")) {
            int eq = pair.indexOf('=');
            if (eq > 0) out.put(URLDecoder.decode(pair.substring(0, eq), StandardCharsets.UTF_8),
                    URLDecoder.decode(pair.substring(eq + 1), StandardCharsets.UTF_8));
        }
        return out;
    }

    private static int num(Map<String, String> q, String key) {
        String v = q.get(key);
        if (v == null) throw new BadRequest("missing query parameter " + key);
        try {
            return Integer.parseInt(v);
        } catch (NumberFormatException e) {
            throw new BadRequest(key + " is not a number: " + v);
        }
    }

    private static String error(String message) {
        JsonObject o = new JsonObject();
        o.addProperty("error", message);
        return o.toString();
    }

    private static JsonObject wrap(String key, JsonArray array) {
        JsonObject o = new JsonObject();
        o.add(key, array);
        return o;
    }

    static JsonArray arr(int... values) {
        JsonArray a = new JsonArray();
        for (int v : values) a.add(v);
        return a;
    }

    static JsonArray strings(Collection<String> values) {
        JsonArray a = new JsonArray();
        values.forEach(a::add);
        return a;
    }

    static int[] ints(JsonArray a, int n) {
        if (a == null || a.size() != n) throw new BadRequest("expected an array of " + n + " integers");
        int[] out = new int[n];
        for (int i = 0; i < n; i++) out[i] = a.get(i).getAsInt();
        return out;
    }

    static String str(JsonObject o, String key, String fallback) {
        return o.has(key) && !o.get(key).isJsonNull() ? o.get(key).getAsString() : fallback;
    }

    // --- /ttlbridge -------------------------------------------------------------------------------------------------

    public static void registerCommands(RegisterCommandsEvent event) {
        event.getDispatcher().register(Commands.literal("ttlbridge")
                .requires(source -> source.hasPermission(3))
                .then(Commands.literal("status").executes(ctx -> status(ctx.getSource())))
                .then(Commands.literal("jobs").executes(ctx -> listJobs(ctx.getSource())))
                .then(Commands.literal("reload").executes(ctx -> reload(ctx.getSource())))
                .then(Commands.literal("undo").then(Commands.argument("id", StringArgumentType.word())
                        .executes(ctx -> jobCommand(ctx.getSource(), "undo", StringArgumentType.getString(ctx, "id")))))
                .then(Commands.literal("cancel").then(Commands.argument("id", StringArgumentType.word())
                        .executes(ctx -> jobCommand(ctx.getSource(), "cancel", StringArgumentType.getString(ctx, "id"))))));
    }

    private static int status(CommandSourceStack source) {
        if (jobs == null) {
            source.sendFailure(Component.literal("ttlbridge: not running"));
            return 0;
        }
        String line = http == null ? "HTTP off (enabled=" + config.enabled + ")" : "listening on " + config.bind + ":" + config.port;
        source.sendSuccess(() -> Component.literal("ttlbridge: " + line + ", " + jobs.queued() + " queued, "
                + config.zones.size() + " zones, " + config.protect.size() + " protected, allow_anywhere=" + config.allowAnywhere), false);
        return 1;
    }

    private static int listJobs(CommandSourceStack source) {
        if (jobs == null) return 0;
        JsonArray list = jobs.list(10);
        if (list.isEmpty()) source.sendSuccess(() -> Component.literal("ttlbridge: no jobs"), false);
        list.forEach(e -> {
            JsonObject j = e.getAsJsonObject();
            source.sendSuccess(() -> Component.literal(j.get("id").getAsString() + " " + j.get("phase").getAsString() + " "
                    + j.get("changed").getAsInt() + "/" + j.get("cells").getAsInt() + " " + j.get("dim").getAsString() + " "
                    + j.get("from") + ".." + j.get("to") + " " + str(j, "label", "")), false);
        });
        return list.size();
    }

    private static int reload(CommandSourceStack source) {
        stop();
        start();
        return status(source);
    }

    private static int jobCommand(CommandSourceStack source, String what, String id) {
        if (jobs == null) return 0;
        try {
            JsonObject j = what.equals("undo") ? jobs.undo(id) : jobs.cancel(id);
            source.sendSuccess(() -> Component.literal("ttlbridge " + what + ": " + j), true);
            return 1;
        } catch (RuntimeException e) {
            source.sendFailure(Component.literal("ttlbridge " + what + ": " + e.getMessage()));
            return 0;
        }
    }
}
