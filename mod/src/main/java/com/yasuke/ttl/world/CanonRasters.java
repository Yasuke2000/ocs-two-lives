package com.yasuke.ttl.world;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.function.Consumer;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.zip.DataFormatException;
import java.util.zip.Inflater;
import org.jetbrains.annotations.Nullable;

/**
 * The designed world rasters of design/architecture/own-world.md (WP-W1 writes them to pack/config/ttl/world/, the
 * mod reads them here): {@code height}, {@code rugged}, {@code water}, {@code road}, {@code biome}, {@code site},
 * optionally {@code exclusion} and {@code cavity}, described by {@code legend.json}. Pure Java (Gson only, its own
 * PNG decoder, no AWT, no Minecraft), so {@link DesignSelfCheck} can test it offline. Immutable once loaded: every
 * worldgen thread reads the same arrays.
 *
 * <p>Geometry: one pixel = {@code scale} blocks (default 4, one quart); pixel (0, 0) starts at block
 * {@code origin_block} (its north-west corner). A layer's own legend entry may override {@code scale} and
 * {@code origin_block} (a road raster at 1:1, say). Pixel values are sampled at pixel centres.
 *
 * <p>Value conventions (the legend's {@code value} text, e.g. {@code "y + 64"}, or numeric {@code offset}/{@code
 * divisor} keys override the defaults):
 * <ul>
 *   <li>{@code height}: 16-bit gray, {@code y + 64}; y is the designed surface = the first air block above the ground
 *       (the {@code ground} convention of {@link CanonSites}).</li>
 *   <li>{@code rugged}: 8-bit gray, {@code rugged * 255} (0 = flat, 1 = alpine).</li>
 *   <li>{@code water}: 16-bit gray, {@code level + 64}, 0 = dry; the level is a sea level: water fills every y below it.</li>
 *   <li>{@code road}: palette or gray indices; {@code classes} names them ({@code none}, {@code main}, {@code trail},
 *       {@code bridge}..., {@code lantern}); default 0 none, 1 main, 2 trail, 3 bridge.</li>
 *   <li>{@code biome}: indices into {@code biomes} ({@code [{index, id}]}, {@code {"1": id}} or a list by position);
 *       0 or {@code auto} = vanilla's choice.</li>
 *   <li>{@code site}: indices (0 = none) into an optional {@code sites} table; {@code cavity}: non-zero = the Dwargon
 *       cavity; {@code exclusion}: bits {@code bits} (default site 1, road 2, cavity 4) when the converter already
 *       wrote the mask.</li>
 * </ul>
 * Unknown keys are ignored, a missing optional layer is simply absent; without {@code legend.json} or a height
 * layer there are no rasters at all, and every design density function, feature and filter returns vanilla.
 *
 * <p>Derived per-pixel mask ({@link #mask}): {@link #SITE} = a site box plus {@code site_margin}, {@link #ROAD} = a
 * road corridor plus {@code road_margin}, {@link #CAVITY}, {@link #DRY} = site or cavity plus {@code dry_margin}
 * (no aquifer fluid). The structure filter reads the first three, {@code ttl:design_dry} the last.
 */
public final class CanonRasters {
    public static final byte SITE = 1, ROAD = 2, CAVITY = 4, DRY = 8;
    public static final int ROAD_NONE = 0, ROAD_MAIN = 1, ROAD_TRAIL = 2, ROAD_LANTERN = 3;
    /** Defaults (blocks) for the derived masks and the box-edge blend. */
    static final int SITE_MARGIN = 16, ROAD_MARGIN = 8, DRY_MARGIN = 24, EDGE_BLEND = 64;
    /** Pixel tile for the coarse "any mask bit here" index (structure boxes are tested against it first). */
    static final int TILE = 16;

    /** One decoded raster in its own geometry. Values are unsigned; {@link #raw} is -1 outside. */
    static final class Layer {
        final String name;
        final int w, h, x0, z0, scale;
        @Nullable final byte[] bytes;
        @Nullable final short[] shorts;

        Layer(String name, int w, int h, int x0, int z0, int scale, @Nullable byte[] bytes, @Nullable short[] shorts) {
            this.name = name;
            this.w = w;
            this.h = h;
            this.x0 = x0;
            this.z0 = z0;
            this.scale = scale;
            this.bytes = bytes;
            this.shorts = shorts;
        }

        int raw(int px, int pz) {
            if (px < 0 || pz < 0 || px >= w || pz >= h) return -1;
            int i = pz * w + px;
            return bytes != null ? bytes[i] & 0xFF : shorts[i] & 0xFFFF;
        }

        int clamped(int px, int pz) {
            int i = Math.max(0, Math.min(h - 1, pz)) * w + Math.max(0, Math.min(w - 1, px));
            return bytes != null ? bytes[i] & 0xFF : shorts[i] & 0xFFFF;
        }

        int px(int blockX) {
            return Math.floorDiv(blockX - x0, scale);
        }

        int pz(int blockZ) {
            return Math.floorDiv(blockZ - z0, scale);
        }

        int at(int blockX, int blockZ) {
            return raw(px(blockX), pz(blockZ));
        }

        boolean sameGeometry(Layer o) {
            return o.w == w && o.h == h && o.x0 == x0 && o.z0 == z0 && o.scale == scale;
        }

        /** True when any pixel overlapping the block rectangle [x0b, x1b) x [z0b, z1b) is non-zero. */
        boolean anyIn(int x0b, int z0b, int x1b, int z1b) {
            int a0 = px(x0b), a1 = px(x1b - 1), b0 = pz(z0b), b1 = pz(z1b - 1);
            for (int b = Math.max(0, b0); b <= Math.min(h - 1, b1); b++)
                for (int a = Math.max(0, a0); a <= Math.min(w - 1, a1); a++)
                    if (raw(a, b) > 0) return true;
            return false;
        }
    }

    /** Linear decoding of a layer's raw value: {@code value = raw / divisor - offset}. */
    record Encoding(double divisor, double offset) {
        double decode(int raw) {
            return raw / divisor - offset;
        }
    }

    // ---- loaded data ----
    final Layer height;
    @Nullable final Layer rugged, water, road, biome, site;
    final Encoding heightEnc, ruggedEnc, waterEnc;
    /** Road class per raw road value (ROAD_*), bridge flag per raw value. */
    final int[] roadClass = new int[65536];
    final boolean[] roadBridge = new boolean[65536];
    /** Biome id per raw biome value, null = auto (vanilla). */
    final String[] biomeIds;
    /** Site id per raw site value (may be null: only the mask is known). */
    final Map<Integer, String> siteIds;
    /** Derived masks on the height layer's geometry, and a coarse OR per TILE x TILE pixels. */
    final byte[] mask;
    final byte[] tiles;
    final int tilesW, tilesH;
    final int boxX0, boxZ0, boxX1, boxZ1, edgeBlend;
    final int siteMargin, roadMargin, dryMargin;
    /** The raw legend (calibration bands and anything else a command wants to read). */
    final JsonObject legend;
    final String summary;

    private CanonRasters(JsonObject legend, Layer height, Encoding heightEnc, @Nullable Layer rugged, Encoding ruggedEnc,
                         @Nullable Layer water, Encoding waterEnc, @Nullable Layer road, @Nullable Layer biome, String[] biomeIds,
                         @Nullable Layer site, Map<Integer, String> siteIds, @Nullable Layer exclusion, int[] exclusionBits,
                         @Nullable Layer cavity, Consumer<String> warn) {
        this.legend = legend;
        this.height = height;
        this.heightEnc = heightEnc;
        this.rugged = rugged;
        this.ruggedEnc = ruggedEnc;
        this.water = water;
        this.waterEnc = waterEnc;
        this.road = road;
        this.biome = biome;
        this.biomeIds = biomeIds;
        this.site = site;
        this.siteIds = siteIds;
        this.boxX0 = height.x0;
        this.boxZ0 = height.z0;
        this.boxX1 = height.x0 + height.w * height.scale;
        this.boxZ1 = height.z0 + height.h * height.scale;
        this.edgeBlend = Math.max(0, intKey(legend, "edge_blend", EDGE_BLEND));
        JsonObject ex = legend.has("exclusion") && legend.get("exclusion").isJsonObject() ? legend.getAsJsonObject("exclusion") : new JsonObject();
        this.siteMargin = Math.max(0, intKey(ex, "site_margin", intKey(legend, "site_margin", SITE_MARGIN)));
        this.roadMargin = Math.max(0, intKey(ex, "road_margin", intKey(legend, "road_margin", ROAD_MARGIN)));
        this.dryMargin = Math.max(0, intKey(ex, "dry_margin", intKey(legend, "dry_margin", DRY_MARGIN)));
        configureRoadClasses(road == null ? null : entry(legend, road.name), warn);

        int w = height.w, h = height.h, n = w * h;
        boolean[] siteSrc = new boolean[n], roadSrc = new boolean[n], cavitySrc = new boolean[n];
        int s = height.scale;
        for (int pz = 0; pz < h; pz++) {
            for (int px = 0; px < w; px++) {
                int i = pz * w + px, bx = height.x0 + px * s, bz = height.z0 + pz * s;
                siteSrc[i] = site != null && covers(site, height, px, pz, bx, bz, s);
                cavitySrc[i] = cavity != null && covers(cavity, height, px, pz, bx, bz, s);
                if (road != null) roadSrc[i] = roadCovers(road, height, px, pz, bx, bz, s);
                if (exclusion != null) {
                    int v = exclusion.sameGeometry(height) ? exclusion.raw(px, pz) : exclusion.at(bx + s / 2, bz + s / 2);
                    if (v > 0) {
                        boolean known = false;
                        if ((v & exclusionBits[0]) != 0) { siteSrc[i] = true; known = true; }
                        if ((v & exclusionBits[1]) != 0) { roadSrc[i] = true; known = true; }
                        if ((v & exclusionBits[2]) != 0) { cavitySrc[i] = true; known = true; }
                        if (!known) siteSrc[i] = true; // an unknown class still excludes structures
                    }
                }
            }
        }
        boolean[] siteM = dilate(siteSrc, w, h, pixels(siteMargin, s));
        boolean[] roadM = dilate(roadSrc, w, h, pixels(roadMargin, s));
        boolean[] dryM = new boolean[n];
        for (int i = 0; i < n; i++) dryM[i] = siteSrc[i] || cavitySrc[i];
        dryM = dilate(dryM, w, h, pixels(dryMargin, s));
        mask = new byte[n];
        int[] counts = new int[4];
        for (int i = 0; i < n; i++) {
            int m = (siteM[i] ? SITE : 0) | (roadM[i] ? ROAD : 0) | (cavitySrc[i] ? CAVITY : 0) | (dryM[i] ? DRY : 0);
            mask[i] = (byte) m;
            for (int b = 0; b < 4; b++) if ((m & (1 << b)) != 0) counts[b]++;
        }
        tilesW = (w + TILE - 1) / TILE;
        tilesH = (h + TILE - 1) / TILE;
        tiles = new byte[tilesW * tilesH];
        for (int pz = 0; pz < h; pz++)
            for (int px = 0; px < w; px++) tiles[(pz / TILE) * tilesW + px / TILE] |= mask[pz * w + px];
        long biomeKinds = biomeIds == null ? 0 : java.util.Arrays.stream(biomeIds).filter(java.util.Objects::nonNull).distinct().count();
        summary = String.format(Locale.ROOT, "%dx%d px at 1:%d, box x %d..%d z %d..%d; layers height%s%s%s%s%s%s%s; %d biome ids; mask px site %d road %d cavity %d dry %d",
                w, h, s, boxX0, boxX1, boxZ0, boxZ1, rugged == null ? "" : " rugged", water == null ? "" : " water", road == null ? "" : " road",
                biome == null ? "" : " biome", site == null ? "" : " site", exclusion == null ? "" : " exclusion", cavity == null ? "" : " cavity",
                biomeKinds, counts[0], counts[1], counts[2], counts[3]);
    }

    private static boolean covers(Layer src, Layer base, int px, int pz, int bx, int bz, int s) {
        if (src.sameGeometry(base)) return src.raw(px, pz) > 0;
        return src.anyIn(bx, bz, bx + s, bz + s);
    }

    private boolean roadCovers(Layer src, Layer base, int px, int pz, int bx, int bz, int s) {
        if (src.sameGeometry(base)) {
            int v = src.raw(px, pz);
            return v > 0 && (roadClass[v] != ROAD_NONE && roadClass[v] != ROAD_LANTERN || roadBridge[v]);
        }
        int a0 = src.px(bx), a1 = src.px(bx + s - 1), b0 = src.pz(bz), b1 = src.pz(bz + s - 1);
        for (int b = b0; b <= b1; b++)
            for (int a = a0; a <= a1; a++) {
                int v = src.raw(a, b);
                if (v > 0 && (roadClass[v] != ROAD_NONE && roadClass[v] != ROAD_LANTERN || roadBridge[v])) return true;
            }
        return false;
    }

    static int pixels(int blocks, int scale) {
        return (blocks + scale - 1) / scale;
    }

    /** Square (Chebyshev) dilation by r pixels, separable with running counts. */
    static boolean[] dilate(boolean[] in, int w, int h, int r) {
        if (r <= 0) return in.clone();
        boolean[] tmp = new boolean[in.length], out = new boolean[in.length];
        for (int z = 0; z < h; z++) {
            int count = 0, row = z * w;
            for (int x = 0; x < Math.min(r, w); x++) if (in[row + x]) count++;
            for (int x = 0; x < w; x++) {
                int add = x + r, drop = x - r - 1;
                if (add < w && in[row + add]) count++;
                if (drop >= 0 && in[row + drop]) count--;
                tmp[row + x] = count > 0;
            }
        }
        for (int x = 0; x < w; x++) {
            int count = 0;
            for (int z = 0; z < Math.min(r, h); z++) if (tmp[z * w + x]) count++;
            for (int z = 0; z < h; z++) {
                int add = z + r, drop = z - r - 1;
                if (add < h && tmp[add * w + x]) count++;
                if (drop >= 0 && tmp[drop * w + x]) count--;
                out[z * w + x] = count > 0;
            }
        }
        return out;
    }

    private void configureRoadClasses(@Nullable JsonObject entry, Consumer<String> warn) {
        Map<Integer, String> classes = new LinkedHashMap<>();
        if (entry != null && entry.has("classes")) {
            JsonElement c = entry.get("classes");
            if (c.isJsonObject()) {
                for (Map.Entry<String, JsonElement> e : c.getAsJsonObject().entrySet()) {
                    Integer k = parseInt(e.getKey());
                    String name = e.getValue().isJsonPrimitive() ? e.getValue().getAsString()
                            : e.getValue().isJsonObject() && e.getValue().getAsJsonObject().has("name") ? e.getValue().getAsJsonObject().get("name").getAsString() : null;
                    // {"main": 1} as well as {"1": "main"}
                    if (k == null && e.getValue().isJsonPrimitive() && e.getValue().getAsJsonPrimitive().isNumber()) {
                        classes.put(e.getValue().getAsInt(), e.getKey());
                    } else if (k != null && name != null) {
                        classes.put(k, name);
                    }
                }
            } else if (c.isJsonArray()) {
                JsonArray a = c.getAsJsonArray();
                for (int i = 0; i < a.size(); i++) {
                    JsonElement e = a.get(i);
                    if (e.isJsonPrimitive()) classes.put(i, e.getAsString());
                    else if (e.isJsonObject() && e.getAsJsonObject().has("index"))
                        classes.put(e.getAsJsonObject().get("index").getAsInt(), text(e.getAsJsonObject(), "name", text(e.getAsJsonObject(), "class", "")));
                }
            }
        }
        if (classes.isEmpty()) {
            classes.put(0, "none");
            classes.put(1, "main");
            classes.put(2, "trail");
            classes.put(3, "bridge");
        }
        for (Map.Entry<Integer, String> e : classes.entrySet()) {
            int k = e.getKey();
            if (k < 0 || k >= roadClass.length) continue;
            String name = e.getValue().toLowerCase(Locale.ROOT);
            roadBridge[k] = name.contains("bridge");
            roadClass[k] = name.contains("lantern") || name.contains("post") ? ROAD_LANTERN
                    : name.contains("trail") || name.contains("path") ? ROAD_TRAIL
                    : name.contains("main") || name.contains("paved") || name.contains("road") || name.contains("bridge") ? ROAD_MAIN
                    : ROAD_NONE;
            if (roadClass[k] == ROAD_NONE && !roadBridge[k] && !name.isEmpty() && !name.equals("none") && k != 0)
                warn.accept("design rasters: road class " + k + " '" + e.getValue() + "' is not understood (none/main/trail/bridge/lantern); treated as none");
        }
        roadClass[0] = ROAD_NONE;
        roadBridge[0] = false;
    }

    // ---- geometry and samplers (block coordinates) ----

    public int boxX0() { return boxX0; }
    public int boxZ0() { return boxZ0; }
    public int boxX1() { return boxX1; }
    public int boxZ1() { return boxZ1; }

    public boolean inBox(double x, double z) {
        return x >= boxX0 && z >= boxZ0 && x < boxX1 && z < boxZ1;
    }

    /** 1 inside the box, a smoothstep to 0 over {@code edge_blend} blocks at its edge, 0 outside. */
    public double weight(double x, double z) {
        double d = Math.min(Math.min(x - boxX0, boxX1 - x), Math.min(z - boxZ0, boxZ1 - z));
        if (d <= 0) return 0;
        if (edgeBlend <= 0 || d >= edgeBlend) return 1;
        double t = d / edgeBlend;
        return t * t * (3 - 2 * t);
    }

    /** Designed surface y (first air) at a block position: Catmull-Rom bicubic over pixel centres. */
    public double height(double x, double z) {
        Layer l = height;
        double u = (x - l.x0) / l.scale - 0.5, v = (z - l.z0) / l.scale - 0.5;
        int i = (int) Math.floor(u), j = (int) Math.floor(v);
        double fx = u - i, fz = v - j;
        double[] col = new double[4];
        for (int b = 0; b < 4; b++) {
            double p0 = heightEnc.decode(l.clamped(i - 1, j - 1 + b)), p1 = heightEnc.decode(l.clamped(i, j - 1 + b)),
                    p2 = heightEnc.decode(l.clamped(i + 1, j - 1 + b)), p3 = heightEnc.decode(l.clamped(i + 2, j - 1 + b));
            col[b] = cubic(p0, p1, p2, p3, fx);
        }
        return cubic(col[0], col[1], col[2], col[3], fz);
    }

    /** Designed surface of the pixel holding the block (no interpolation). */
    public double heightPx(int x, int z) {
        Layer l = height;
        return heightEnc.decode(l.clamped(l.px(x), l.pz(z)));
    }

    static double cubic(double p0, double p1, double p2, double p3, double t) {
        return p1 + 0.5 * t * (p2 - p0 + t * (2 * p0 - 5 * p1 + 4 * p2 - p3 + t * (3 * (p1 - p2) + p3 - p0)));
    }

    /** Ruggedness 0..1 (bilinear); {@code fallback} without a rugged layer. */
    public double rugged(double x, double z, double fallback) {
        Layer l = rugged;
        if (l == null) return fallback;
        double u = (x - l.x0) / l.scale - 0.5, v = (z - l.z0) / l.scale - 0.5;
        int i = (int) Math.floor(u), j = (int) Math.floor(v);
        double fx = u - i, fz = v - j;
        double a = ruggedEnc.decode(l.clamped(i, j)), b = ruggedEnc.decode(l.clamped(i + 1, j)),
                c = ruggedEnc.decode(l.clamped(i, j + 1)), d = ruggedEnc.decode(l.clamped(i + 1, j + 1));
        double r = (a + (b - a) * fx) * (1 - fz) + (c + (d - c) * fx) * fz;
        return Math.max(0, Math.min(1, r));
    }

    public boolean hasWater() {
        return water != null;
    }

    public boolean hasRoads() {
        return road != null;
    }

    /** Water level (sea-level convention: water fills y below it) of the pixel holding the block, or Integer.MIN_VALUE when dry. */
    public int waterLevel(int x, int z) {
        if (water == null) return Integer.MIN_VALUE;
        int v = water.at(x, z);
        return v <= 0 ? Integer.MIN_VALUE : (int) Math.round(waterEnc.decode(v));
    }

    /** Highest water level within {@code radius} blocks (pixel steps), or Integer.MIN_VALUE. */
    public int waterLevelNear(int x, int z, int radius) {
        if (water == null) return Integer.MIN_VALUE;
        int best = Integer.MIN_VALUE;
        for (int dz = -radius; dz <= radius; dz += water.scale)
            for (int dx = -radius; dx <= radius; dx += water.scale) best = Math.max(best, waterLevel(x + dx, z + dz));
        return best;
    }

    /**
     * Road at a block column: ROAD_* class, or -1 when none; {@code bridge[0]} is set for a bridge. The corridor edge
     * is smoothed (bilinear road-ness >= 0.5) so a diagonal road at 1:4 is not a staircase of whole pixels.
     */
    public int road(int x, int z, boolean[] bridge) {
        bridge[0] = false;
        Layer l = road;
        if (l == null) return -1;
        if (l.scale == 1) {
            int v = l.at(x, z);
            if (v <= 0 || roadClass[v] == ROAD_LANTERN) return -1;
            bridge[0] = roadBridge[v];
            return roadClass[v] == ROAD_NONE ? (roadBridge[v] ? ROAD_MAIN : -1) : roadClass[v];
        }
        double u = (x + 0.5 - l.x0) / l.scale - 0.5, v = (z + 0.5 - l.z0) / l.scale - 0.5;
        int i = (int) Math.floor(u), j = (int) Math.floor(v);
        double fx = u - i, fz = v - j, sum = 0, bestW = -1;
        int best = 0;
        for (int k = 0; k < 4; k++) {
            int a = i + (k & 1), b = j + (k >> 1);
            double wgt = ((k & 1) == 1 ? fx : 1 - fx) * ((k >> 1) == 1 ? fz : 1 - fz);
            int raw = l.raw(a, b);
            if (raw <= 0) continue;
            boolean isRoad = roadBridge[raw] || roadClass[raw] == ROAD_MAIN || roadClass[raw] == ROAD_TRAIL;
            if (!isRoad) continue;
            sum += wgt;
            if (wgt > bestW) {
                bestW = wgt;
                best = raw;
            }
        }
        if (sum < 0.5 || best == 0) return -1;
        bridge[0] = roadBridge[best];
        return roadClass[best] == ROAD_NONE ? ROAD_MAIN : roadClass[best];
    }

    /** True when the road raster marks a lantern post at this pixel (a converter that knows the arc length). */
    public boolean lanternMarked(int x, int z) {
        if (road == null) return false;
        int v = road.at(x, z);
        return v > 0 && roadClass[v] == ROAD_LANTERN;
    }

    /** True when the road raster has explicit lantern pixels anywhere (then no heuristic lanterns). */
    public boolean hasLanternClass() {
        if (road == null) return false;
        for (int k = 1; k < roadClass.length; k++) if (roadClass[k] == ROAD_LANTERN) return true;
        return false;
    }

    /** Raw biome index at a quart (4-block) position, 0 = auto, -1 outside the biome raster. */
    public int biomeIndexAtQuart(int qx, int qz) {
        if (biome == null) return -1;
        return biome.at(qx * 4 + 2, qz * 4 + 2);
    }

    @Nullable
    public String biomeId(int index) {
        return biomeIds == null || index < 0 || index >= biomeIds.length ? null : biomeIds[index];
    }

    /** Length of the biome table (indices 0 .. size - 1; 0 when there is no biome layer). */
    public int biomeTableSize() {
        return biomeIds == null ? 0 : biomeIds.length;
    }

    /** Every biome id the raster may produce (for the biome source's possible biomes). */
    public List<String> biomeIdList() {
        List<String> out = new ArrayList<>();
        if (biomeIds != null) for (String id : biomeIds) if (id != null && !out.contains(id)) out.add(id);
        return out;
    }

    /** Derived mask bits of the pixel holding the block (0 outside). */
    public int mask(int x, int z) {
        int px = height.px(x), pz = height.pz(z);
        if (px < 0 || pz < 0 || px >= height.w || pz >= height.h) return 0;
        return mask[pz * height.w + px];
    }

    /** Site id painted at the block (null when none or not named). */
    @Nullable
    public String siteAt(int x, int z) {
        if (site == null) return null;
        int v = site.at(x, z);
        return v <= 0 ? null : siteIds.getOrDefault(v, "#" + v);
    }

    /**
     * Structure exclusion of an inclusive block box: the mask bits (SITE, ROAD, CAVITY) of the first excluded pixel,
     * or 0. SITE and ROAD only count where the box reaches within {@code depth} blocks of the designed surface (a
     * mineshaft under a city or a road is fine); CAVITY counts at any depth.
     */
    public int excludes(int minX, int minY, int minZ, int maxX, int maxY, int maxZ, int depth) {
        Layer l = height;
        int a0 = Math.max(0, l.px(minX)), a1 = Math.min(l.w - 1, l.px(maxX)), b0 = Math.max(0, l.pz(minZ)), b1 = Math.min(l.h - 1, l.pz(maxZ));
        if (a0 > a1 || b0 > b1) return 0;
        for (int tb = b0 / TILE; tb <= b1 / TILE; tb++) {
            for (int ta = a0 / TILE; ta <= a1 / TILE; ta++) {
                if ((tiles[tb * tilesW + ta] & (SITE | ROAD | CAVITY)) == 0) continue;
                for (int b = Math.max(b0, tb * TILE); b <= Math.min(b1, tb * TILE + TILE - 1); b++) {
                    for (int a = Math.max(a0, ta * TILE); a <= Math.min(a1, ta * TILE + TILE - 1); a++) {
                        int m = mask[b * l.w + a];
                        if ((m & CAVITY) != 0) return CAVITY;
                        if ((m & (SITE | ROAD)) != 0 && maxY >= heightEnc.decode(l.raw(a, b)) - depth) return m & (SITE | ROAD);
                    }
                }
            }
        }
        return 0;
    }

    public JsonObject legend() {
        return legend;
    }

    public String describe() {
        return summary;
    }

    /** One-line report of every layer at a block column (for /ttlmap). */
    public String describe(int x, int z) {
        boolean[] bridge = new boolean[1];
        int rc = road(x, z, bridge);
        int wl = waterLevel(x, z), bi = biome == null ? -1 : biome.at(x, z);
        int m = mask(x, z);
        return String.format(Locale.ROOT, "design: %s, surface y %.1f (px %.0f), rugged %.2f, water %s, road %s, biome %s, site %s, mask%s%s%s%s%s, edge weight %.2f",
                inBox(x, z) ? "inside the box" : "outside the box", height(x, z), heightPx(x, z), rugged(x, z, 0),
                wl == Integer.MIN_VALUE ? "dry" : "level " + wl, rc < 0 ? "none" : (rc == ROAD_TRAIL ? "trail" : "main") + (bridge[0] ? " bridge" : ""),
                bi < 0 ? "-" : bi == 0 || biomeId(bi) == null ? "auto" : biomeId(bi), siteAt(x, z) == null ? "-" : siteAt(x, z),
                m == 0 ? " none" : "", (m & SITE) != 0 ? " site" : "", (m & ROAD) != 0 ? " road" : "", (m & CAVITY) != 0 ? " cavity" : "",
                (m & DRY) != 0 ? " dry" : "", weight(x, z));
    }

    // ---- loading ----

    /**
     * Loads the rasters from {@code dir}; null (with the reason through {@code warn}) when there is no usable set:
     * no directory, no legend, no height layer, or a broken one. Optional layers that fail are dropped with a warning.
     */
    @Nullable
    public static CanonRasters load(Path dir, Consumer<String> warn) {
        if (!Files.isDirectory(dir)) return null;
        Path legendFile = dir.resolve("legend.json");
        if (!Files.isRegularFile(legendFile)) {
            warn.accept("design rasters: " + dir + " has no legend.json; not used");
            return null;
        }
        JsonObject legend;
        try {
            legend = JsonParser.parseString(Files.readString(legendFile, StandardCharsets.UTF_8)).getAsJsonObject();
        } catch (IOException | RuntimeException e) {
            warn.accept("design rasters: legend.json unreadable (" + e + "); not used");
            return null;
        }
        Map<String, String> files = layerFiles(dir, legend);
        if (!files.containsKey("height")) {
            warn.accept("design rasters: no height layer in " + dir + "; not used");
            return null;
        }
        int scale = intKey(legend, "scale", 4);
        int[] origin = origin(legend);
        try {
            Layer height = layer(dir, legend, files.get("height"), "height", scale, origin);
            if (origin == null) origin = new int[] {height.x0, height.z0};
            Layer rugged = optional(dir, legend, files.get("rugged"), "rugged", scale, origin, warn);
            Layer water = optional(dir, legend, files.get("water"), "water", scale, origin, warn);
            Layer road = optional(dir, legend, files.get("road"), "road", scale, origin, warn);
            Layer biome = optional(dir, legend, files.get("biome"), "biome", scale, origin, warn);
            Layer site = optional(dir, legend, files.get("site"), "site", scale, origin, warn);
            Layer exclusion = optional(dir, legend, files.get("exclusion"), "exclusion", scale, origin, warn);
            Layer cavity = optional(dir, legend, files.get("cavity"), "cavity", scale, origin, warn);
            Encoding he = encoding(entry(legend, height.name), 1, 64);
            Encoding re = encoding(rugged == null ? null : entry(legend, rugged.name), 255, 0);
            Encoding we = encoding(water == null ? null : entry(legend, water.name), 1, 64);
            String[] biomeIds = biome == null ? null : biomeTable(entry(legend, biome.name), legend, warn);
            Map<Integer, String> siteIds = site == null ? Map.of() : siteTable(entry(legend, site.name), legend);
            int[] bits = exclusionBits(exclusion == null ? null : entry(legend, exclusion.name));
            return new CanonRasters(legend, height, he, rugged, re, water, we, road, biome, biomeIds, site, siteIds, exclusion, bits, cavity, warn);
        } catch (IOException | RuntimeException e) {
            warn.accept("design rasters: " + e.getMessage() + "; not used");
            return null;
        }
    }

    /** Layer role -> file name: from the legend's keys ({@code "height.png": {...}}, {@code "files": {...}}), else the files present. */
    static Map<String, String> layerFiles(Path dir, JsonObject legend) {
        Map<String, String> out = new LinkedHashMap<>();
        if (legend.has("files") && legend.get("files").isJsonObject()) {
            for (Map.Entry<String, JsonElement> e : legend.getAsJsonObject("files").entrySet()) {
                String role = role(e.getKey());
                if (role != null && e.getValue().isJsonPrimitive()) out.putIfAbsent(role, e.getValue().getAsString());
            }
        }
        if (legend.has("layers") && legend.get("layers").isJsonObject()) {
            for (Map.Entry<String, JsonElement> e : legend.getAsJsonObject("layers").entrySet()) {
                String role = role(e.getKey());
                if (role == null) continue;
                JsonElement v = e.getValue();
                String file = v.isJsonPrimitive() ? v.getAsString() : v.isJsonObject() && v.getAsJsonObject().has("file")
                        ? v.getAsJsonObject().get("file").getAsString() : e.getKey().endsWith(".png") ? e.getKey() : null;
                if (file != null) out.putIfAbsent(role, file);
            }
        }
        for (String key : legend.keySet()) {
            if (!key.toLowerCase(Locale.ROOT).endsWith(".png")) continue;
            String role = role(key);
            if (role != null) out.putIfAbsent(role, key);
        }
        try (var stream = Files.list(dir)) {
            stream.map(p -> p.getFileName().toString()).filter(n -> n.toLowerCase(Locale.ROOT).endsWith(".png")).sorted().forEach(n -> {
                String role = role(n);
                if (role != null) out.putIfAbsent(role, n);
            });
        } catch (IOException ignored) {
            // the legend's names are enough
        }
        out.values().removeIf(f -> !Files.isRegularFile(dir.resolve(f)));
        return out;
    }

    /** The layer a file or key name stands for, from its stem (height16.png, sites.png, road_mask.png ...), or null. */
    @Nullable
    static String role(String name) {
        String n = name.toLowerCase(Locale.ROOT);
        int slash = Math.max(n.lastIndexOf('/'), n.lastIndexOf('\\'));
        if (slash >= 0) n = n.substring(slash + 1);
        if (n.startsWith("preview") || n.startsWith("hillshade")) return null;
        if (n.startsWith("height") || n.startsWith("relief") || n.startsWith("elevation")) return "height";
        if (n.startsWith("rugged")) return "rugged";
        if (n.startsWith("water") || n.startsWith("lake")) return "water";
        if (n.startsWith("road")) return "road";
        if (n.startsWith("biome")) return "biome";
        if (n.startsWith("exclu") || n.startsWith("keepout") || n.startsWith("no_struct")) return "exclusion";
        if (n.startsWith("cavity") || n.startsWith("carve")) return "cavity";
        if (n.startsWith("site")) return "site";
        return null;
    }

    @Nullable
    private static Layer optional(Path dir, JsonObject legend, @Nullable String file, String role, int scale, int[] origin, Consumer<String> warn) {
        if (file == null) return null;
        try {
            return layer(dir, legend, file, role, scale, origin);
        } catch (IOException | RuntimeException e) {
            warn.accept("design rasters: " + role + " layer " + file + " dropped (" + e.getMessage() + ")");
            return null;
        }
    }

    private static Layer layer(Path dir, JsonObject legend, String file, String role, int scale, @Nullable int[] origin) throws IOException {
        JsonObject e = entry(legend, file);
        int s = e != null ? intKey(e, "scale", scale) : scale;
        int[] o = e != null && origin(e) != null ? origin(e) : origin;
        Png png = Png.decode(Files.readAllBytes(dir.resolve(file)), file);
        if (s <= 0) throw new IllegalArgumentException(role + ": scale must be > 0");
        int x0 = o != null ? o[0] : -(png.w * s) / 2, z0 = o != null ? o[1] : -(png.h * s) / 2;
        return new Layer(file, png.w, png.h, x0, z0, s, png.bytes, png.shorts);
    }

    /** The legend entry of a layer: its own key, or under "layers"/"files" by its role. */
    @Nullable
    static JsonObject entry(JsonObject legend, String file) {
        if (legend.has(file) && legend.get(file).isJsonObject()) return legend.getAsJsonObject(file);
        String role = role(file);
        for (String group : new String[] {"layers", "rasters"}) {
            if (!legend.has(group) || !legend.get(group).isJsonObject()) continue;
            for (Map.Entry<String, JsonElement> e : legend.getAsJsonObject(group).entrySet()) {
                if (e.getValue().isJsonObject() && (e.getKey().equals(file) || role != null && role.equals(role(e.getKey())))) return e.getValue().getAsJsonObject();
            }
        }
        for (Map.Entry<String, JsonElement> e : legend.entrySet()) {
            if (e.getValue().isJsonObject() && role != null && e.getKey().toLowerCase(Locale.ROOT).endsWith(".png") && role.equals(role(e.getKey())))
                return e.getValue().getAsJsonObject();
        }
        return null;
    }

    @Nullable
    static int[] origin(JsonObject o) {
        for (String key : new String[] {"origin_block", "origin", "block_origin"}) {
            if (o.has(key) && o.get(key).isJsonArray() && o.getAsJsonArray(key).size() >= 2)
                return new int[] {o.getAsJsonArray(key).get(0).getAsInt(), o.getAsJsonArray(key).get(1).getAsInt()};
        }
        for (String key : new String[] {"box", "design_box", "bbox"}) {
            if (o.has(key) && o.get(key).isJsonArray() && o.getAsJsonArray(key).size() >= 4)
                return new int[] {o.getAsJsonArray(key).get(0).getAsInt(), o.getAsJsonArray(key).get(1).getAsInt()};
        }
        return null;
    }

    private static final Pattern PLUS = Pattern.compile("([+-])\\s*(\\d+(?:\\.\\d+)?)");
    private static final Pattern TIMES = Pattern.compile("[*×]\\s*(\\d+(?:\\.\\d+)?)");

    /**
     * {@code raw = value * divisor + offset}, so {@code value = raw / divisor - offset}: from the value text before any
     * ';' ({@code "y + 64"}, {@code "rugged * 255"}), overridden by numeric {@code divisor}/{@code multiplier}/{@code max}
     * and {@code offset} keys.
     */
    static Encoding encoding(@Nullable JsonObject e, double divisor, double offset) {
        if (e != null) {
            String value = e.has("value") && e.get("value").isJsonPrimitive() ? e.get("value").getAsString() : "";
            int cut = value.indexOf(';');
            String head = cut >= 0 ? value.substring(0, cut) : value;
            Matcher times = TIMES.matcher(head);
            if (times.find()) divisor = Double.parseDouble(times.group(1));
            Matcher plus = PLUS.matcher(head);
            if (plus.find()) offset = Double.parseDouble(plus.group(2)) * (plus.group(1).equals("-") ? -1 : 1);
            if (e.has("max")) divisor = e.get("max").getAsDouble();
            if (e.has("multiplier")) divisor = e.get("multiplier").getAsDouble();
            if (e.has("divisor")) divisor = e.get("divisor").getAsDouble();
            if (e.has("offset")) offset = e.get("offset").getAsDouble();
        }
        return new Encoding(divisor == 0 ? 1 : divisor, offset);
    }

    /** Biome table: entry {@code biomes} or the legend's top-level {@code biomes}; index 0 is auto unless named. */
    static String[] biomeTable(@Nullable JsonObject entry, JsonObject legend, Consumer<String> warn) {
        JsonElement v = entry != null && entry.has("biomes") ? entry.get("biomes") : entry != null && entry.has("classes") ? entry.get("classes") : legend.get("biomes");
        Map<Integer, String> ids = new HashMap<>();
        int max = 0;
        if (v != null && v.isJsonArray()) {
            JsonArray a = v.getAsJsonArray();
            for (int i = 0; i < a.size(); i++) {
                JsonElement e = a.get(i);
                if (e.isJsonPrimitive()) ids.put(i, e.getAsString());
                else if (e.isJsonObject()) {
                    JsonObject o = e.getAsJsonObject();
                    int index = o.has("index") ? o.get("index").getAsInt() : i;
                    String id = text(o, "id", text(o, "biome", null));
                    if (id != null) ids.put(index, id);
                }
            }
        } else if (v != null && v.isJsonObject()) {
            for (Map.Entry<String, JsonElement> e : v.getAsJsonObject().entrySet()) {
                Integer k = parseInt(e.getKey());
                if (k != null && e.getValue().isJsonPrimitive()) ids.put(k, e.getValue().getAsString());
                else if (k != null && e.getValue().isJsonObject() && e.getValue().getAsJsonObject().has("id")) ids.put(k, e.getValue().getAsJsonObject().get("id").getAsString());
                else if (k == null && e.getValue().isJsonPrimitive() && e.getValue().getAsJsonPrimitive().isNumber()) ids.put(e.getValue().getAsInt(), e.getKey());
            }
        } else {
            warn.accept("design rasters: the biome layer has no 'biomes' table; every pixel is auto (vanilla)");
        }
        for (int k : ids.keySet()) max = Math.max(max, k);
        String[] out = new String[Math.max(1, Math.min(65535, max) + 1)];
        for (Map.Entry<Integer, String> e : ids.entrySet()) {
            if (e.getKey() < 0 || e.getKey() >= out.length) continue;
            String id = e.getValue().trim();
            if (id.isEmpty() || id.equalsIgnoreCase("auto") || id.equalsIgnoreCase("none") || id.equalsIgnoreCase("vanilla")) continue;
            out[e.getKey()] = id.contains(":") ? id : "minecraft:" + id;
        }
        return out;
    }

    static Map<Integer, String> siteTable(@Nullable JsonObject entry, JsonObject legend) {
        Map<Integer, String> out = new HashMap<>();
        JsonElement v = entry != null && entry.has("sites") ? entry.get("sites") : entry != null && entry.has("ids") ? entry.get("ids") : null;
        if (v == null) return out;
        if (v.isJsonArray()) {
            JsonArray a = v.getAsJsonArray();
            for (int i = 0; i < a.size(); i++) {
                JsonElement e = a.get(i);
                if (e.isJsonPrimitive()) out.put(i, e.getAsString());
                else if (e.isJsonObject()) {
                    JsonObject o = e.getAsJsonObject();
                    String id = text(o, "id", text(o, "name", null));
                    if (id != null) out.put(o.has("index") ? o.get("index").getAsInt() : i, id);
                }
            }
        } else if (v.isJsonObject()) {
            for (Map.Entry<String, JsonElement> e : v.getAsJsonObject().entrySet()) {
                Integer k = parseInt(e.getKey());
                if (k != null && e.getValue().isJsonPrimitive()) out.put(k, e.getValue().getAsString());
                else if (k == null && e.getValue().isJsonPrimitive() && e.getValue().getAsJsonPrimitive().isNumber()) out.put(e.getValue().getAsInt(), e.getKey());
            }
        }
        out.remove(0);
        return out;
    }

    /** {site, road, cavity} bit values of an exclusion layer. */
    static int[] exclusionBits(@Nullable JsonObject entry) {
        int[] bits = {SITE, ROAD, CAVITY};
        if (entry == null) return bits;
        JsonElement v = entry.has("bits") ? entry.get("bits") : entry.get("classes");
        if (v == null || !v.isJsonObject()) return bits;
        for (Map.Entry<String, JsonElement> e : v.getAsJsonObject().entrySet()) {
            Integer k = parseInt(e.getKey());
            String name = (k != null && e.getValue().isJsonPrimitive() ? e.getValue().getAsString() : e.getKey()).toLowerCase(Locale.ROOT);
            int value = k != null ? k : e.getValue().isJsonPrimitive() && e.getValue().getAsJsonPrimitive().isNumber() ? e.getValue().getAsInt() : 0;
            if (value <= 0) continue;
            if (name.startsWith("site")) bits[0] = value;
            else if (name.startsWith("road")) bits[1] = value;
            else if (name.startsWith("cavity") || name.startsWith("carve") || name.startsWith("dwargon")) bits[2] = value;
        }
        return bits;
    }

    static int intKey(JsonObject o, String key, int fallback) {
        try {
            return o.has(key) && o.get(key).isJsonPrimitive() ? o.get(key).getAsInt() : fallback;
        } catch (RuntimeException e) {
            return fallback;
        }
    }

    @Nullable
    private static String text(JsonObject o, String key, @Nullable String fallback) {
        return o.has(key) && o.get(key).isJsonPrimitive() ? o.get(key).getAsString() : fallback;
    }

    @Nullable
    private static Integer parseInt(String s) {
        try {
            return Integer.parseInt(s.trim());
        } catch (NumberFormatException e) {
            return null;
        }
    }

    // ---- PNG ----

    /** A decoded PNG: one unsigned value per pixel (gray, palette index, or 0xRRGGBB for colour types). */
    static final class Png {
        final int w, h;
        @Nullable final byte[] bytes;
        @Nullable final short[] shorts;

        private Png(int w, int h, @Nullable byte[] bytes, @Nullable short[] shorts) {
            this.w = w;
            this.h = h;
            this.bytes = bytes;
            this.shorts = shorts;
        }

        static Png decode(byte[] data, String name) throws IOException {
            if (data.length < 8 || (data[0] & 0xFF) != 0x89 || data[1] != 'P' || data[2] != 'N' || data[3] != 'G')
                throw new IOException(name + " is not a PNG");
            int pos = 8, w = -1, h = -1, depth = 0, type = -1, interlace = 0;
            ByteArrayOutputStream idat = new ByteArrayOutputStream();
            while (pos + 8 <= data.length) {
                int len = readInt(data, pos);
                String chunk = new String(data, pos + 4, 4, StandardCharsets.ISO_8859_1);
                int body = pos + 8;
                if (len < 0 || body + len > data.length) throw new IOException(name + ": truncated chunk " + chunk);
                switch (chunk) {
                    case "IHDR" -> {
                        w = readInt(data, body);
                        h = readInt(data, body + 4);
                        depth = data[body + 8] & 0xFF;
                        type = data[body + 9] & 0xFF;
                        interlace = data[body + 12] & 0xFF;
                    }
                    case "IDAT" -> idat.write(data, body, len);
                    default -> { }
                }
                pos = body + len + 4;
                if (chunk.equals("IEND")) break;
            }
            if (w <= 0 || h <= 0) throw new IOException(name + ": no IHDR");
            if (interlace != 0) throw new IOException(name + ": interlaced PNGs are not supported");
            int channels = switch (type) {
                case 0, 3 -> 1;
                case 2 -> 3;
                case 4 -> 2;
                case 6 -> 4;
                default -> throw new IOException(name + ": PNG colour type " + type + " not supported");
            };
            if (depth != 1 && depth != 2 && depth != 4 && depth != 8 && depth != 16) throw new IOException(name + ": bit depth " + depth);
            if (channels > 1 && depth < 8) throw new IOException(name + ": bit depth " + depth + " with colour type " + type);
            int bitsPerPixel = channels * depth, rowBytes = (w * bitsPerPixel + 7) / 8, bpp = Math.max(1, bitsPerPixel / 8);
            long need = (long) h * (rowBytes + 1);
            if (need > Integer.MAX_VALUE - 16) throw new IOException(name + ": too large");
            byte[] raw = new byte[(int) need];
            Inflater inflater = new Inflater();
            try {
                inflater.setInput(idat.toByteArray());
                int got = 0;
                while (got < raw.length) {
                    int n = inflater.inflate(raw, got, raw.length - got);
                    if (n == 0) {
                        if (inflater.finished() || inflater.needsInput()) break;
                        if (inflater.needsDictionary()) throw new IOException(name + ": needs a dictionary");
                    }
                    got += n;
                }
                if (got < raw.length) throw new IOException(name + ": image data too short (" + got + " < " + raw.length + ")");
            } catch (DataFormatException e) {
                throw new IOException(name + ": bad image data (" + e.getMessage() + ")");
            } finally {
                inflater.end();
            }
            boolean wide = depth == 16 || channels >= 3;
            byte[] bytes = wide ? null : new byte[w * h];
            short[] shorts = wide && channels == 1 || wide && channels == 2 ? new short[w * h] : null;
            int[] rgb = channels >= 3 ? new int[w * h] : null;
            byte[] prev = new byte[rowBytes], cur = new byte[rowBytes];
            for (int y = 0; y < h; y++) {
                int off = y * (rowBytes + 1), filter = raw[off] & 0xFF;
                System.arraycopy(raw, off + 1, cur, 0, rowBytes);
                unfilter(filter, cur, prev, bpp, name);
                for (int x = 0; x < w; x++) {
                    int i = y * w + x;
                    if (channels == 1 || channels == 2) {
                        int v;
                        if (depth == 16) v = ((cur[x * channels * 2] & 0xFF) << 8) | (cur[x * channels * 2 + 1] & 0xFF);
                        else if (depth == 8) v = cur[x * channels] & 0xFF;
                        else {
                            int bit = x * depth, b = cur[bit >> 3] & 0xFF, shift = 8 - depth - (bit & 7);
                            v = (b >> shift) & ((1 << depth) - 1);
                        }
                        if (shorts != null) shorts[i] = (short) v;
                        else bytes[i] = (byte) v;
                    } else {
                        int step = depth / 8, base = x * channels * step;
                        rgb[i] = ((cur[base] & 0xFF) << 16) | ((cur[base + step] & 0xFF) << 8) | (cur[base + 2 * step] & 0xFF);
                    }
                }
                byte[] t = prev;
                prev = cur;
                cur = t;
            }
            if (rgb != null) {
                // Colour images: only a palette of a few colours makes sense as data; index them in order of appearance.
                Map<Integer, Integer> index = new LinkedHashMap<>();
                index.put(0, 0);
                short[] out = new short[w * h];
                for (int i = 0; i < rgb.length; i++) {
                    Integer k = index.get(rgb[i]);
                    if (k == null) {
                        if (index.size() > 65535) throw new IOException(name + ": too many colours for a data raster");
                        k = index.size();
                        index.put(rgb[i], k);
                    }
                    out[i] = (short) (int) k;
                }
                return new Png(w, h, null, out);
            }
            return new Png(w, h, bytes, shorts);
        }

        private static void unfilter(int filter, byte[] cur, byte[] prev, int bpp, String name) throws IOException {
            switch (filter) {
                case 0 -> { }
                case 1 -> {
                    for (int i = bpp; i < cur.length; i++) cur[i] = (byte) (cur[i] + cur[i - bpp]);
                }
                case 2 -> {
                    for (int i = 0; i < cur.length; i++) cur[i] = (byte) (cur[i] + prev[i]);
                }
                case 3 -> {
                    for (int i = 0; i < cur.length; i++) {
                        int left = i >= bpp ? cur[i - bpp] & 0xFF : 0;
                        cur[i] = (byte) (cur[i] + ((left + (prev[i] & 0xFF)) >> 1));
                    }
                }
                case 4 -> {
                    for (int i = 0; i < cur.length; i++) {
                        int a = i >= bpp ? cur[i - bpp] & 0xFF : 0, b = prev[i] & 0xFF, c = i >= bpp ? prev[i - bpp] & 0xFF : 0;
                        int p = a + b - c, pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c);
                        cur[i] = (byte) (cur[i] + (pa <= pb && pa <= pc ? a : pb <= pc ? b : c));
                    }
                }
                default -> throw new IOException(name + ": unknown PNG filter " + filter);
            }
        }

        private static int readInt(byte[] d, int p) {
            return ((d[p] & 0xFF) << 24) | ((d[p + 1] & 0xFF) << 16) | ((d[p + 2] & 0xFF) << 8) | (d[p + 3] & 0xFF);
        }
    }
}
