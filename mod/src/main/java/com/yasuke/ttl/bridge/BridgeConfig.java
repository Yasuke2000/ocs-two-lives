package com.yasuke.ttl.bridge;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.mojang.logging.LogUtils;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.neoforged.fml.loading.FMLPaths;
import org.slf4j.Logger;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.SecureRandom;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;

/**
 * {@code config/ttl/bridge.json}: the build bridge's settings. Off unless {@code enabled} is true; writes only inside a
 * {@code zones} box and never into a {@code protect} box. The token is {@code TTL_BRIDGE_TOKEN} when set, otherwise
 * {@code config/ttl/bridge.token} (made with 32 random bytes on first start).
 */
public final class BridgeConfig {
    private static final Logger LOGGER = LogUtils.getLogger();
    static final Gson GSON = new GsonBuilder().setPrettyPrinting().disableHtmlEscaping().create();

    public record Zone(String name, String dim, BoundingBox box) {
        boolean contains(String d, BoundingBox b) {
            return dim.equals(d) && box.minX() <= b.minX() && box.minY() <= b.minY() && box.minZ() <= b.minZ()
                    && box.maxX() >= b.maxX() && box.maxY() >= b.maxY() && box.maxZ() >= b.maxZ();
        }

        boolean overlaps(String d, BoundingBox b) {
            return dim.equals(d) && box.intersects(b);
        }

        JsonObject json() {
            JsonObject o = new JsonObject();
            o.addProperty("name", name);
            o.addProperty("dim", dim);
            o.add("from", Bridge.arr(box.minX(), box.minY(), box.minZ()));
            o.add("to", Bridge.arr(box.maxX(), box.maxY(), box.maxZ()));
            return o;
        }
    }

    boolean enabled = false;
    String bind = "127.0.0.1";
    int port = 25599;
    /** Milliseconds of each server tick the job queue may use. */
    double budgetMs = 3.0;
    /** Skip the queue for a tick while the server's average tick is slower than this. */
    double pauseMspt = 45.0;
    /** Largest box a job may cover (cells, air and kept cells included). */
    int maxJobCells = 4_194_304;
    /** Largest box /v1/region reads in blocks mode, in summary mode, and the largest heightmap (columns). */
    int maxReadCells = 262_144;
    int maxSummaryCells = 1_048_576;
    int maxHeightmapColumns = 262_144;
    /** Local test servers only: any box is writable (protect boxes still apply). */
    boolean allowAnywhere = false;
    final List<Zone> zones = new ArrayList<>();
    final List<Zone> protect = new ArrayList<>();
    String token = "";

    static Path dir() {
        return FMLPaths.CONFIGDIR.get().resolve("ttl");
    }

    static BridgeConfig load() {
        BridgeConfig c = new BridgeConfig();
        Path file = dir().resolve("bridge.json");
        try {
            if (!Files.exists(file)) {
                Files.createDirectories(file.getParent());
                Files.writeString(file, GSON.toJson(defaults()), StandardCharsets.UTF_8);
                LOGGER.info("[ttl] bridge: wrote default {} (disabled)", file);
            }
            JsonObject o = GSON.fromJson(Files.readString(file, StandardCharsets.UTF_8), JsonObject.class);
            c.enabled = bool(o, "enabled", c.enabled);
            c.bind = o.has("bind") ? o.get("bind").getAsString() : c.bind;
            c.port = o.has("port") ? o.get("port").getAsInt() : c.port;
            c.budgetMs = o.has("budget_ms") ? o.get("budget_ms").getAsDouble() : c.budgetMs;
            c.pauseMspt = o.has("pause_mspt") ? o.get("pause_mspt").getAsDouble() : c.pauseMspt;
            c.maxJobCells = o.has("max_job_cells") ? o.get("max_job_cells").getAsInt() : c.maxJobCells;
            c.maxReadCells = o.has("max_read_cells") ? o.get("max_read_cells").getAsInt() : c.maxReadCells;
            c.maxSummaryCells = o.has("max_summary_cells") ? o.get("max_summary_cells").getAsInt() : c.maxSummaryCells;
            c.maxHeightmapColumns = o.has("max_heightmap_columns") ? o.get("max_heightmap_columns").getAsInt() : c.maxHeightmapColumns;
            c.allowAnywhere = bool(o, "allow_anywhere", c.allowAnywhere);
            readZones(o.getAsJsonArray("zones"), c.zones);
            readZones(o.getAsJsonArray("protect"), c.protect);
        } catch (Exception e) {
            LOGGER.error("[ttl] bridge: {} unreadable, bridge stays off: {}", file, e.toString());
            c.enabled = false;
        }
        c.token = token();
        return c;
    }

    private static JsonObject defaults() {
        JsonObject o = new JsonObject();
        o.addProperty("enabled", false);
        o.addProperty("bind", "127.0.0.1");
        o.addProperty("port", 25599);
        o.addProperty("budget_ms", 3.0);
        o.addProperty("pause_mspt", 45.0);
        o.addProperty("max_job_cells", 4_194_304);
        o.addProperty("allow_anywhere", false);
        o.add("zones", new JsonArray());
        o.add("protect", new JsonArray());
        return o;
    }

    private static boolean bool(JsonObject o, String key, boolean fallback) {
        return o.has(key) ? o.get(key).getAsBoolean() : fallback;
    }

    private static void readZones(JsonArray array, List<Zone> out) {
        if (array == null) return;
        for (JsonElement e : array) {
            JsonObject z = e.getAsJsonObject();
            int[] a = Bridge.ints(z.getAsJsonArray("from"), 3);
            int[] b = Bridge.ints(z.getAsJsonArray("to"), 3);
            String name = z.has("name") ? z.get("name").getAsString() : "zone" + out.size();
            String dim = z.has("dim") ? z.get("dim").getAsString() : "minecraft:overworld";
            out.add(new Zone(name, dim, BoundingBox.fromCorners(new net.minecraft.core.Vec3i(a[0], a[1], a[2]),
                    new net.minecraft.core.Vec3i(b[0], b[1], b[2]))));
        }
    }

    private static String token() {
        String env = System.getenv("TTL_BRIDGE_TOKEN");
        if (env != null && !env.isBlank()) return env.trim();
        Path file = dir().resolve("bridge.token");
        try {
            if (Files.exists(file)) {
                String t = Files.readString(file, StandardCharsets.UTF_8).trim();
                if (t.length() >= 16) return t;
            }
            byte[] bytes = new byte[32];
            new SecureRandom().nextBytes(bytes);
            String t = HexFormat.of().formatHex(bytes);
            Files.createDirectories(file.getParent());
            Files.writeString(file, t + "\n", StandardCharsets.UTF_8);
            try {
                Files.setPosixFilePermissions(file, java.nio.file.attribute.PosixFilePermissions.fromString("rw-------"));
            } catch (UnsupportedOperationException | IOException ignored) {
                // Windows: no POSIX permissions
            }
            LOGGER.info("[ttl] bridge: new token in {}", file);
            return t;
        } catch (IOException e) {
            LOGGER.error("[ttl] bridge: cannot read or write {}: {}", file, e.toString());
            return "";
        }
    }

    /** Null when the box may be written, otherwise the reason it may not. */
    String writeRefusal(String dim, BoundingBox box) {
        for (Zone p : protect) {
            if (p.overlaps(dim, box)) return "box touches protected area '" + p.name() + "'";
        }
        if (allowAnywhere) return null;
        for (Zone z : zones) {
            if (z.contains(dim, box)) return null;
        }
        return zones.isEmpty() ? "no build zones configured (config/ttl/bridge.json \"zones\")"
                : "box is not inside any build zone of config/ttl/bridge.json";
    }
}
