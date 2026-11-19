package com.yasuke.ttl.world;

import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.zip.CRC32;
import java.util.zip.Deflater;

/**
 * Offline self-check of the own world's mod side (WP-W2/W3/W4 of design/architecture/own-world.md), runnable without
 * Minecraft: {@code gradlew selfCheck} (part of {@code gradlew build}) or
 * {@code java -cp <runtime classpath> com.yasuke.ttl.world.DesignSelfCheck}. It writes synthetic rasters in every
 * encoding the loader accepts and checks: the fallback (no folder, no legend, no height: no rasters, and the density
 * functions return vanilla to the bit), the loader and samplers, the offset convention against an emulation of
 * vanilla's cell-interpolated final density, factor and jaggedness, the derived masks and the structure exclusion
 * decisions, and the sites file.
 *
 * <p>{@code DesignSelfCheck write-calibration <dir>} writes the calibration map of the WP-W2 gate (flat bands at
 * H 66, 90, 140 and 220, rolling/hills/alpine bands, a lake at 90 with stepped reaches and small falls, a road with a
 * bridge, a flat site on a bump, a carve site with a cavity) into {@code <dir>}, for {@code /ttlsite calibrate} on a
 * local server.
 */
public final class DesignSelfCheck {
    private DesignSelfCheck() {}

    public static void main(String[] args) throws Exception {
        if (args.length >= 2 && args[0].equals("write-calibration")) {
            Path dir = Path.of(args[1]);
            writeCalibration(dir);
            System.out.println("calibration map written to " + dir.toAbsolutePath());
            return;
        }
        Path tmp = Files.createTempDirectory("ttl-design-check");
        try {
            fallback(tmp);
            offsetConvention();
            factorAndJaggedness();
            loader(tmp.resolve("synthetic"));
            encodings(tmp.resolve("encodings"));
            sitesFile();
            calibrationMap(tmp.resolve("calibration"));
            densityFallback();
            if (args.length >= 1 && Files.isDirectory(Path.of(args[0])) && Files.isRegularFile(Path.of(args[0], "index.json"))) realRasters(Path.of(args[0]));
            else System.out.println("real rasters: none given (run tools/world/build.py; gradlew selfCheck then reads world/build/)");
            System.out.println("design self-check passed");
        } finally {
            try (var walk = Files.walk(tmp)) {
                walk.sorted(Comparator.reverseOrder()).forEach(p -> p.toFile().delete());
            }
        }
    }

    // ---- fallback: no rasters, no change ----

    private static void fallback(Path tmp) throws IOException {
        List<String> warnings = new ArrayList<>();
        check(CanonRasters.load(tmp.resolve("missing"), warnings::add) == null && warnings.isEmpty(), "no folder: no rasters, silently");
        Path empty = Files.createDirectories(tmp.resolve("empty"));
        check(CanonRasters.load(empty, warnings::add) == null && warnings.size() == 1, "no legend: no rasters, one warning " + warnings);
        Files.writeString(empty.resolve("legend.json"), "{\"scale\": 4, \"origin_block\": [0, 0]}");
        check(CanonRasters.load(empty, warnings::add) == null && warnings.size() == 2, "no height layer: no rasters " + warnings);
        Files.writeString(empty.resolve("legend.json"), "{broken");
        check(CanonRasters.load(empty, warnings::add) == null && warnings.size() == 3, "broken legend: no rasters " + warnings);
        Files.writeString(empty.resolve("legend.json"), "{}");
        Files.write(empty.resolve("height.png"), new byte[] {1, 2, 3});
        check(CanonRasters.load(empty, warnings::add) == null && warnings.size() == 4, "broken height PNG: no rasters " + warnings);
        check(DesignWorld.load(tmp.resolve("missing")) != null && !(DesignWorld.load(tmp.resolve("missing")) instanceof DesignWorld.Loaded), "DesignWorld: missing folder is MISSING");
        System.out.println("fallback: no folder / no legend / no height / broken files -> no rasters (" + warnings.size() + " warnings)");
    }

    /** The density functions themselves with no rasters: outside returned to the bit (needs Minecraft's classes). */
    private static void densityFallback() {
        try {
            net.minecraft.SharedConstants.tryDetectVersion();
            net.minecraft.server.Bootstrap.bootStrap();
        } catch (Throwable e) {
            System.out.println("density functions without rasters: Minecraft bootstrap failed (" + e + "), trying without it");
        }
        try {
            DesignWorld.setForTest(null);
            net.minecraft.world.level.levelgen.DensityFunction outside = new Probe(0.3712);
            var ctx = new net.minecraft.world.level.levelgen.DensityFunction.SinglePointContext(100, 64, -200);
            var functions = List.of(new DesignDensity.Offset(outside, 0), new DesignDensity.Factor(outside, 8, 5, 3, 1.5, 0.2),
                    new DesignDensity.Jaggedness(outside, 0.6), new DesignDensity.TopSlide(outside, 304, 320));
            for (var f : functions) check(Double.doubleToRawLongBits(f.compute(ctx)) == Double.doubleToRawLongBits(0.3712), "no rasters: " + f.getClass().getSimpleName() + " is vanilla");
            check(new DesignDensity.Dry(outside).compute(ctx) == 0.3712, "no rasters: design_dry is vanilla");
            System.out.println("density functions without rasters return vanilla to the bit (offset, factor, jaggedness, top slide, dry)");
            // With the synthetic rasters: designed inside, vanilla outside, blended over the edge, dry in the masks.
            CanonRasters r = synthetic;
            DesignWorld.setForTest(new DesignWorld.Loaded(r, CanonSites.NONE, List.of()));
            var off = new DesignDensity.Offset(outside, 0);
            var in = new net.minecraft.world.level.levelgen.DensityFunction.SinglePointContext(-20, 64, 10);
            check(Math.abs(off.compute(in) - DesignTerrain.offset(r.height(-20, 10), 0)) < 1e-12, "offset inside the box is the design");
            check(off.compute(new net.minecraft.world.level.levelgen.DensityFunction.SinglePointContext(500, 64, 10)) == 0.3712, "offset outside the box is vanilla");
            double edge = off.compute(new net.minecraft.world.level.levelgen.DensityFunction.SinglePointContext(-120, 64, 10));
            double w = r.weight(-120, 10);
            check(w > 0 && w < 1 && Math.abs(edge - (0.3712 + (DesignTerrain.offset(r.height(-120, 10), 0) - 0.3712) * w)) < 1e-12, "offset blended at the box edge");
            var fac = new DesignDensity.Factor(outside, 8, 5, 3, 1.5, 0.2);
            check(Math.abs(fac.compute(in) - DesignTerrain.factor(r.rugged(-20, 10, 0.2))) < 1e-12, "factor from rugged");
            var dry = new DesignDensity.Dry(outside);
            check(dry.compute(new net.minecraft.world.level.levelgen.DensityFunction.SinglePointContext(40, 64, -68)) == -1
                    && dry.compute(new net.minecraft.world.level.levelgen.DensityFunction.SinglePointContext(-100, 64, 60)) == 0.3712, "design_dry: -1 at the site, vanilla elsewhere");
            var slide = new DesignDensity.TopSlide(outside, 304, 320);
            check(slide.compute(new net.minecraft.world.level.levelgen.DensityFunction.SinglePointContext(-20, 250, 10)) == 1
                    && slide.compute(new net.minecraft.world.level.levelgen.DensityFunction.SinglePointContext(500, 250, 10)) == 0.3712, "top slide raised inside the box only");
            DesignWorld.setForTest(null);
            System.out.println("density functions with rasters: designed inside, vanilla outside, blended at the edge; dry in the site mask; top slide raised inside");
        } catch (LinkageError | RuntimeException e) {
            System.out.println("density functions without rasters: skipped (Minecraft classes not on the class path: " + e + ")");
        }
    }

    /** A constant density function that is not one of vanilla's (no registries needed). */
    private record Probe(double value) implements net.minecraft.world.level.levelgen.DensityFunction {
        public double compute(FunctionContext ctx) { return value; }
        public void fillArray(double[] values, ContextProvider provider) { java.util.Arrays.fill(values, value); }
        public net.minecraft.world.level.levelgen.DensityFunction mapAll(Visitor visitor) { return visitor.apply(this); }
        public double minValue() { return value; }
        public double maxValue() { return value; }
        public net.minecraft.util.KeyDispatchDataCodec<? extends net.minecraft.world.level.levelgen.DensityFunction> codec() { throw new UnsupportedOperationException(); }
    }

    // ---- offset convention ----

    /**
     * Emulates vanilla's final density near the surface for a flat field: depth = (128 - y)/128 + offset, density =
     * 4 * quarter_negative(depth * factor) + noise, evaluated at cell corners (y = -64 + 8k) and interpolated linearly;
     * returns the first air y (block y is solid when the interpolated density at y is > 0).
     */
    static int emulatedSurface(double offset, double factor, double noise) {
        for (int y = 319; y >= -64; y--) {
            int y0 = Math.floorDiv(y + 64, 8) * 8 - 64;
            double d0 = density(offset, factor, noise, y0), d1 = density(offset, factor, noise, y0 + 8);
            double d = d0 + (d1 - d0) * (y - y0) / 8.0;
            if (d > 0) return y + 1;
        }
        return -64;
    }

    private static double density(double offset, double factor, double noise, int y) {
        double depth = (128.0 - y) / 128 + offset, v = depth * factor;
        return 4 * (v > 0 ? v : v * 0.25) + noise;
    }

    private static void offsetConvention() {
        // Vanilla's convention: depth zero at y = 128 * offset + 128.
        for (double h = -20; h <= 300; h += 0.25) {
            double t = DesignTerrain.zeroFor(h);
            check(Math.abs(DesignTerrain.crossingFor(t) - (h - 0.5)) < 1e-9, "crossing inverse at H " + h);
            check(Math.abs(DesignTerrain.offset(h, 0) - (t - 128) / 128) < 1e-12, "offset = (T - 128) / 128 at " + h);
            check(t <= h - 0.5 + 1e-9 && t > h - 0.5 - 8, "the zero lies under the crossing, in its cell, at " + h);
        }
        int worstNaive = 0;
        for (int h = -20; h <= 300; h++) {
            for (double f : new double[] {8, 5, 3, 1.5}) {
                int got = emulatedSurface(DesignTerrain.offset(h, 0), f, 0);
                check(got == h, "emulated first air " + got + " for designed H " + h + " at factor " + f);
                int naive = emulatedSurface((h - 128.0) / 128, f, 0);
                worstNaive = Math.max(worstNaive, naive - h);
            }
        }
        // The 3-D noise lifts the ground more than it lowers it (quarter_negative); bias shifts the whole field.
        StringBuilder lift = new StringBuilder();
        for (double f : new double[] {8, 5, 3, 1.5}) {
            double sum = 0;
            int n = 0;
            for (double b = -0.1; b <= 0.1001; b += 0.02) {
                for (int h = 60; h < 76; h++) {
                    sum += emulatedSurface(DesignTerrain.offset(h, 0), f, b) - h;
                    n++;
                }
            }
            lift.append(String.format(Locale.ROOT, " factor %.1f %+.2f", f, sum / n));
        }
        check(emulatedSurface(DesignTerrain.offset(80, 2), 8, 0) == 78, "bias 2 lowers the field by two blocks");
        System.out.printf(Locale.ROOT, "offset: first air = designed H for H -20..300 at factors 8/5/3/1.5 (the naive (H-128)/128 is up to %d high); mean lift of noise +-0.1:%s%n",
                worstNaive, lift);
    }

    private static void factorAndJaggedness() {
        check(DesignTerrain.factor(0) == 8 && DesignTerrain.factor(0.1) == 8 && DesignTerrain.factor(0.3) == 5 && DesignTerrain.factor(0.6) == 3
                && DesignTerrain.factor(0.8) == 1.5 && DesignTerrain.factor(1) == 1.5, "factor knots of own-world.md 3.8");
        for (double r = 0; r <= 1.0001; r += 0.05)
            check(Math.abs(DesignTerrain.factor(r) - DesignTerrain.curve(DesignTerrain.FACTOR_CURVE, r)) < 1e-12, "factor = the 3.8 curve at " + r);
        double prev = 99;
        for (double r = 0; r <= 1.0001; r += 0.01) {
            double f = DesignTerrain.factor(r);
            check(f <= prev + 1e-12 && f >= 1.5 && f <= 8, "factor falls with ruggedness: " + r + " -> " + f);
            prev = f;
        }
        check(DesignTerrain.factor(-1) == 8 && DesignTerrain.factor(2) == 1.5, "factor clamps");
        check(DesignTerrain.jaggedness(0.8, 100, 0.6) == 0 && DesignTerrain.jaggedness(0.4, 100, 0.6) == 0, "no jaggedness up to rugged 0.8");
        check(Math.abs(DesignTerrain.jaggedness(0.9, 100, 0.6) - 0.3) < 1e-9 && Math.abs(DesignTerrain.jaggedness(1, 100, 0.6) - 0.6) < 1e-9, "jaggedness 0.3 at 0.9, 0.6 at 1");
        check(Math.abs(DesignTerrain.jaggedness(1, 300, 0.6) - 10 / 128.0) < 1e-9 && DesignTerrain.jaggedness(1, 320, 0.6) == 0, "jaggedness capped under y 310");
        check(DesignTerrain.slide(240, 304, 320) == 1 && DesignTerrain.slide(312, 304, 320) == 0.5 && DesignTerrain.slide(330, 304, 320) == 0, "top slide");
        check(DesignTerrain.blend(1, 3, 0) == 1 && DesignTerrain.blend(1, 3, 1) == 3 && DesignTerrain.blend(1, 3, 0.5) == 2, "blend");
        System.out.println("factor: 8/8/5/3/1.5 at rugged 0/0.1/0.3/0.6/0.8, monotone; jaggedness 0 up to 0.8, 0.6 at 1, capped under y 310");
    }

    // ---- loader, samplers, masks, exclusion ----

    /**
     * 64 x 48 px at 1:4 from block (-128, -96): height = 70 + column (y + 64 in 16 bits), rugged 0..255 by row, a lake
     * at level 80 (px 10..13 x 10..13), a main road along row 30 (px 0..40) with a bridge at px 20..21, a trail along
     * column 50, a site (index 1 'town') at px 40..44 x 5..9, a cavity at px 55..58 x 40..43, biomes by quadrant.
     */
    private static CanonRasters synthetic;

    private static void loader(Path dir) throws IOException {
        Files.createDirectories(dir);
        int w = 64, h = 48;
        int[] height = new int[w * h], rugged = new int[w * h], water = new int[w * h], road = new int[w * h], biome = new int[w * h], site = new int[w * h], cavity = new int[w * h];
        for (int z = 0; z < h; z++) {
            for (int x = 0; x < w; x++) {
                int i = z * w + x;
                height[i] = 70 + x + 64;
                rugged[i] = Math.min(255, z * 6);
                if (x >= 10 && x <= 13 && z >= 10 && z <= 13) water[i] = 80 + 64;
                if (z == 30 && x <= 40) road[i] = x == 20 || x == 21 ? 3 : 1;
                if (x == 50) road[i] = 2;
                biome[i] = (x < w / 2 ? 1 : 2) + (z < h / 2 ? 0 : 2);
                if (x >= 40 && x <= 44 && z >= 5 && z <= 9) site[i] = 1;
                if (x >= 55 && x <= 58 && z >= 40 && z <= 43) cavity[i] = 1;
            }
        }
        if (height[0] < 0) throw new AssertionError();
        writePng(dir.resolve("height.png"), w, h, 16, 0, height);
        writePng(dir.resolve("rugged.png"), w, h, 8, 0, rugged);
        writePng(dir.resolve("water.png"), w, h, 16, 0, water);
        writePng(dir.resolve("road.png"), w, h, 8, 3, road);
        writePng(dir.resolve("biome.png"), w, h, 8, 3, biome);
        writePng(dir.resolve("site.png"), w, h, 8, 3, site);
        writePng(dir.resolve("cavity.png"), w, h, 1, 0, cavity);
        Files.writeString(dir.resolve("preview.png"), "not a raster"); // ignored by name
        Files.writeString(dir.resolve("legend.json"), """
                {"scale": 4, "origin_block": [-128, -96], "edge_blend": 32,
                 "height.png": {"type": "16-bit gray", "value": "y + 64"},
                 "rugged.png": {"type": "8-bit gray", "value": "rugged * 255"},
                 "water.png": {"type": "16-bit gray", "value": "level + 64; 0 = dry"},
                 "road.png": {"type": "8-bit palette", "classes": {"0": "none", "1": "main", "2": "trail", "3": "bridge"}},
                 "biome.png": {"type": "8-bit palette", "biomes": [{"index": 1, "id": "minecraft:plains"}, {"index": 2, "id": "forest"},
                                {"index": 3, "id": "tensura:ancient_forest"}, {"index": 4, "id": "auto"}]},
                 "site.png": {"sites": {"1": "town"}},
                 "exclusion": {"site_margin": 16, "road_margin": 8, "dry_margin": 24},
                 "future_key": {"ignored": true}}
                """);
        List<String> warnings = new ArrayList<>();
        CanonRasters r = CanonRasters.load(dir, warnings::add);
        check(r != null && warnings.isEmpty(), "synthetic rasters load cleanly: " + warnings);
        synthetic = r;
        check(r.boxX0() == -128 && r.boxZ0() == -96 && r.boxX1() == -128 + 256 && r.boxZ1() == -96 + 192, "box from origin and size");
        // Height: exact at pixel centres, linear field -> bicubic reproduces it between centres too.
        for (int px = 2; px < 60; px += 7) {
            double cx = -128 + px * 4 + 2;
            check(Math.abs(r.height(cx, -50) - (70 + px)) < 1e-9, "height at a pixel centre " + px);
            check(Math.abs(r.height(cx + 1, -50) - (70 + px + 0.25)) < 1e-9, "bicubic is exact on a linear field at " + px);
            check(r.heightPx((int) cx, -50) == 70 + px, "pixel height");
        }
        check(Math.abs(r.rugged(-100, -96 + 10 * 4 + 2, 0) - 60 / 255.0) < 1e-9 && r.rugged(0, 1000, 0) <= 1, "rugged decoded and clamped");
        int lakeX = -128 + 11 * 4, lakeZ = -96 + 11 * 4;
        check(r.waterLevel(lakeX, lakeZ) == 80 && r.waterLevel(lakeX + 40, lakeZ) == Integer.MIN_VALUE, "water level 80 in the lake, dry beside it");
        check(r.waterLevelNear(lakeX + 16, lakeZ, 8) == 80 && r.waterLevelNear(lakeX + 40, lakeZ, 8) == Integer.MIN_VALUE, "water near");
        boolean[] bridge = new boolean[1];
        int roadZ = -96 + 30 * 4;
        check(r.road(-128 + 5 * 4 + 1, roadZ + 1, bridge) == CanonRasters.ROAD_MAIN && !bridge[0], "main road");
        check(r.road(-128 + 20 * 4 + 2, roadZ + 2, bridge) == CanonRasters.ROAD_MAIN && bridge[0], "bridge pixel");
        check(r.road(-128 + 5 * 4, roadZ + 12, bridge) == -1, "no road two pixels off");
        check(r.road(-128 + 50 * 4 + 2, 0, bridge) == CanonRasters.ROAD_TRAIL, "trail");
        // The smoothed edge: the corridor is about one pixel (4 blocks) wide, not a staircase of whole pixels.
        int wide = 0;
        for (int dz = -8; dz <= 8; dz++) if (r.road(-100, roadZ + dz, bridge) >= 0) wide++;
        check(wide >= 3 && wide <= 5, "road width at 1:4 about 4 blocks: " + wide);
        check(r.biomeIndexAtQuart(Math.floorDiv(-120, 4), Math.floorDiv(-90, 4)) == 1 && "minecraft:plains".equals(r.biomeId(1)) && "minecraft:forest".equals(r.biomeId(2))
                && "tensura:ancient_forest".equals(r.biomeId(3)) && r.biomeId(4) == null && r.biomeIdList().size() == 3, "biome table: " + r.biomeIdList());
        check(r.biomeIndexAtQuart(1000, 1000) == -1, "biome outside the box: -1");
        check("town".equals(r.siteAt(-128 + 42 * 4, -96 + 7 * 4)) && r.siteAt(0, 0) == null, "site ids");
        // Masks: the site plus 16 blocks (4 px), the road plus 8 (2 px), the cavity, dry = site/cavity plus 24 (6 px).
        int sx = -128 + 42 * 4, sz = -96 + 7 * 4;
        check((r.mask(sx, sz) & CanonRasters.SITE) != 0 && (r.mask(sx, sz) & CanonRasters.DRY) != 0, "site and dry at the site");
        check((r.mask(-128 + 48 * 4 + 1, sz) & CanonRasters.SITE) != 0 && (r.mask(-128 + 49 * 4 + 1, sz) & CanonRasters.SITE) == 0, "site margin 4 px");
        check((r.mask(-128 + 50 * 4 + 1, sz) & CanonRasters.DRY) != 0 && (r.mask(-128 + 51 * 4 + 1, sz) & CanonRasters.DRY) == 0, "dry margin 6 px");
        check((r.mask(-100, -96 + 32 * 4 + 1) & CanonRasters.ROAD) != 0 && (r.mask(-100, -96 + 33 * 4 + 1) & CanonRasters.ROAD) == 0, "road margin 2 px");
        int cx = -128 + 56 * 4, cz = -96 + 41 * 4;
        check((r.mask(cx, cz) & (CanonRasters.CAVITY | CanonRasters.DRY)) == (CanonRasters.CAVITY | CanonRasters.DRY), "cavity is dry");
        check(r.mask(5000, 5000) == 0 && r.mask(-100, -96 + 40 * 4) == 0, "no mask elsewhere");
        // Edge weight.
        check(r.weight(0, 0) == 1 && r.weight(-128, 0) == 0 && r.weight(-129, 0) == 0 && r.weight(-112, 0) > 0 && r.weight(-112, 0) < 1, "edge blend");

        // Structure exclusion decisions (inclusive block boxes, depth 16 under the designed surface).
        int ground = (int) r.heightPx(sx, sz);
        check(r.excludes(sx - 5, ground - 4, sz - 5, sx + 5, ground + 20, sz + 5, 16) == CanonRasters.SITE, "a village on the site: out");
        check(r.excludes(sx + 20, ground - 4, sz - 5, sx + 26, ground + 20, sz + 5, 16) == CanonRasters.SITE && r.excludes(sx + 56, ground - 4, sz - 5, sx + 60, ground + 20, sz + 5, 16) == 0, "a box in the site margin: out");
        check(r.excludes(sx - 5, -50, sz - 5, sx + 5, ground - 20, sz + 5, 16) == 0, "a mineshaft deep under the site: allowed");
        check(r.excludes(sx - 5, -50, sz - 5, sx + 5, ground - 16, sz + 5, 16) == CanonRasters.SITE, "reaching 16 under the plate: out");
        int rg = (int) r.heightPx(-100, roadZ);
        check(r.excludes(-110, rg - 3, roadZ - 20, -90, rg + 10, roadZ - 3, 16) == CanonRasters.ROAD, "a house on the road corridor: out");
        check(r.excludes(-110, rg - 3, roadZ - 40, -90, rg + 10, roadZ - 25, 16) == 0, "a house beside the road: allowed");
        check(r.excludes(cx - 2, -60, cz - 2, cx + 2, -40, cz + 2, 16) == CanonRasters.CAVITY, "anything in the cavity column, at any depth: out");
        check(r.excludes(2000, 0, 2000, 2100, 90, 2100, 16) == 0 && r.excludes(-400, 60, -300, -129, 90, -97, 16) == 0, "outside the box: allowed");
        check(r.excludes(-1000, 60, sz - 2, 1000, 90, sz + 2, 16) == CanonRasters.SITE, "a box larger than the raster still finds the site");
        long t0 = System.nanoTime();
        int hits = 0;
        for (int k = 0; k < 20000; k++) {
            int x = -128 + (k * 37) % 256, z = -96 + (k * 53) % 192;
            if (r.excludes(x, 60, z, x + 60, 120, z + 60, 16) != 0) hits++;
        }
        System.out.printf(Locale.ROOT, "loader: %s; 20000 structure boxes tested in %.1f ms (%d excluded)%n", r.describe(), (System.nanoTime() - t0) / 1e6, hits);
        System.out.println("loader: " + r.describe(sx, sz));
    }

    /** The same data in the other encodings a converter may write: offsets as keys, a list biome table, reversed classes, an exclusion layer. */
    private static void encodings(Path dir) throws IOException {
        Files.createDirectories(dir);
        int w = 16, h = 16;
        int[] height = new int[w * h], rugged = new int[w * h], road = new int[w * h], biome = new int[w * h], ex = new int[w * h];
        for (int i = 0; i < w * h; i++) {
            height[i] = 100 + 75; // offset 100: y 75
            rugged[i] = 50;       // max 100: 0.5
            road[i] = i % w == 3 ? 7 : 0;
            biome[i] = 2;
            ex[i] = i / w == 12 ? 4 : i / w == 13 ? 2 : 0;
        }
        writePng(dir.resolve("height16.png"), w, h, 16, 0, height);
        writePng(dir.resolve("rugged.png"), w, h, 8, 0, rugged);
        writePng(dir.resolve("roads.png"), w, h, 8, 0, road);
        writePng(dir.resolve("biomes.png"), w, h, 8, 3, biome);
        writePng(dir.resolve("exclusion.png"), w, h, 8, 0, ex);
        Files.writeString(dir.resolve("legend.json"), """
                {"layers": {"height": {"file": "height16.png", "offset": 100}, "rugged": {"file": "rugged.png", "max": 100},
                            "road": {"file": "roads.png", "classes": {"trail": 7}}, "biome": {"file": "biomes.png", "biomes": ["auto", "minecraft:desert", "minecraft:savanna"]},
                            "exclusion": {"file": "exclusion.png", "bits": {"cavity": 4, "road": 2}}},
                 "design_box": [0, 0, 64, 64], "scale": 4}
                """);
        List<String> warnings = new ArrayList<>();
        CanonRasters r = CanonRasters.load(dir, warnings::add);
        check(r != null && warnings.isEmpty(), "other encodings load: " + warnings);
        check(r.boxX0() == 0 && r.boxZ0() == 0 && r.boxX1() == 64, "origin from design_box");
        check(Math.abs(r.height(30, 30) - 75) < 1e-9 && Math.abs(r.rugged(30, 30, 0) - 0.5) < 1e-9, "offset 100 / max 100");
        boolean[] b = new boolean[1];
        check(r.road(14, 30, b) == CanonRasters.ROAD_TRAIL && r.road(40, 30, b) == -1, "reversed class map {trail: 7}");
        check("minecraft:savanna".equals(r.biomeId(2)) && r.biomeId(0) == null, "biome list by position");
        check((r.mask(30, 12 * 4 + 1) & CanonRasters.CAVITY) != 0 && (r.mask(30, 12 * 4 + 1) & CanonRasters.DRY) != 0 && (r.mask(30, 13 * 4 + 1) & CanonRasters.ROAD) != 0,
                "exclusion bits (cavity 4 -> dry too, road 2)");
        check(r.excludes(10, 70, 0, 14, 80, 20, 16) == CanonRasters.ROAD && r.excludes(28, 70, 0, 40, 80, 20, 16) == 0, "road column 3 from road.png excludes too");
        // No legend entries at all: defaults by file name, origin centred on 0, 0.
        Path bare = Files.createDirectories(dir.resolve("bare"));
        writePng(bare.resolve("height.png"), w, h, 16, 0, height);
        Files.writeString(bare.resolve("legend.json"), "{}");
        CanonRasters d = CanonRasters.load(bare, warnings::add);
        check(d != null && d.boxX0() == -32 && d.boxZ1() == 32 && Math.abs(d.height(0, 0) - 111) < 1e-9 && !d.hasWater() && !d.hasRoads() && d.rugged(0, 0, 0.2) == 0.2,
                "bare legend: defaults (y + 64, centred, no optional layers)");
        System.out.println("encodings: layers/files map, offset/max keys, design_box, list biomes, reversed classes, exclusion bits, bare legend");
    }

    private static void sitesFile() {
        List<String> warnings = new ArrayList<>();
        JsonObject json = DesignSitesFile.normalise(JsonParser.parseString("""
                [{"id": "tempest", "x": 0, "z": 0, "r": 110, "fade": 48, "ground": 70, "kind": "clearing"},
                 {"name": "dwargon", "centre": [0, -1400], "radius": 90, "kind": "carve", "ground": 142, "min_cover": 6},
                 {"name": "spirit_gate", "x": 300, "z": 200, "radius": 40, "terrain": "fixed", "ground": 75, "site": "lakeside"},
                 {"name": "pin", "x": 5, "z": 5}]
                """), warnings::add);
        List<DesignSitesFile.Info> infos = DesignSitesFile.infos(json, warnings::add);
        check(infos.size() == 3 && warnings.size() == 1, "three usable sites, one skipped: " + warnings);
        check(infos.get(0).id().equals("tempest") && infos.get(0).ground() == 70 && infos.get(1).kind().equals("carve") && infos.get(1).minCover() == 6
                && infos.get(2).kind().equals("lakeside"), "aliases id/r/site, x/z");
        List<String> w2 = new ArrayList<>();
        CanonSites sites = CanonConfig.sites(DesignSitesFile.forCanonSites(json), w2::add);
        check(sites.size() == 2 && sites.anyFlat() && sites.site(0).ground() == 70 && sites.site(1).name().equals("spirit_gate") && sites.site(1).terrain() == CanonSites.Terrain.FLAT,
                "flat plates for the clearing and the 'fixed' lakeside, the carve site left out: " + sites + " " + w2);
        CanonSites merged = DesignSitesFile.merge(new CanonSites(new CanonSites.Site[] {CanonSites.Site.of("tempest", 9, 9, 10, 0, null, CanonSites.Terrain.FLAT, 60, null, null, null)}), sites);
        check(merged.size() == 2 && merged.site(0).x() == 9, "merge keeps the first of a name");
        System.out.println("sites.json: aliases, terrain defaults, carve sites kept out of CanonSites, merge");
    }

    private static void calibrationMap(Path dir) throws IOException {
        writeCalibration(dir);
        List<String> warnings = new ArrayList<>();
        CanonRasters r = CanonRasters.load(dir, warnings::add);
        check(r != null && warnings.isEmpty(), "the calibration map loads: " + warnings);
        JsonArray bands = r.legend().getAsJsonObject("calibration").getAsJsonArray("bands");
        check(bands.size() == 7, "seven calibration bands");
        for (var e : bands) {
            JsonObject b = e.getAsJsonObject();
            if (b.get("rugged").getAsDouble() != 0) continue;
            JsonArray box = b.getAsJsonArray("box");
            double want = b.get("y").getAsDouble();
            for (int z = box.get(1).getAsInt() + 32; z < box.get(3).getAsInt() - 32; z += 48)
                for (int x = box.get(0).getAsInt() + 32; x < box.get(2).getAsInt() - 32; x += 48)
                    check(Math.abs(r.height(x, z) - want) < 1e-6 && r.rugged(x, z, 1) == 0, "flat band " + b.get("name") + " is flat at " + x + "," + z + ": " + r.height(x, z));
        }
        check(r.waterLevel(-400, -384) == 90 && r.waterLevel(-280, -384) == 89 && r.waterLevel(-230, -384) == 88 && r.waterLevel(-180, -384) == 86
                && r.waterLevel(-140, -384) == 85, "lake and stepped reaches");
        check(r.height(-400, -384) < 88 && r.height(-400, -384 + 106) >= 92, "lake basin under the level, rim above it");
        boolean[] b = new boolean[1];
        check(r.road(-234, -800, b) == CanonRasters.ROAD_MAIN && !b[0] && r.road(-234, -384, b) == CanonRasters.ROAD_MAIN && b[0], "the road and its bridge");
        check((r.mask(-600, 100) & (CanonRasters.SITE | CanonRasters.DRY)) != 0 && (r.mask(-300, 100) & CanonRasters.CAVITY) != 0, "site and cavity masks");
        check(r.road(-234 + 8, -800, b) == -1 && (r.mask(-234 + 8, -800) & CanonRasters.ROAD) != 0, "the corridor: no surface, but no structures either");
        check(r.height(-600, 100) > 145, "the flat site stands on a bump the plate must level");
        check(r.factorCurve() != null && r.jaggedCurve() != null && r.seaLevel() == 63 && "calib_site".equals(r.siteAt(-600, 100)), "index.json curves, sea level, site names");
        check(r.lanternCount() >= 15 && r.lanternCount() <= 20 && !r.lanternAt(-234, -800), "lantern posts every 40 blocks off the centre line: " + r.lanternCount());
        int left = 0;
        for (int z = -1050; z <= -250; z++) if (r.lanternAt(-234 - 4, z)) left++;
        check(left > 5 && r.lanternCount() - left > 5, "lanterns alternate sides: " + left + " west of " + r.lanternCount());
        System.out.println("calibration map: " + r.describe());
    }

    /** WP-W1's real output (world/build/ from tools/world/build.py): loads, is fast and small enough, and agrees with index.json. */
    private static void realRasters(Path dir) throws IOException {
        Runtime rt = Runtime.getRuntime();
        System.gc();
        long before = rt.totalMemory() - rt.freeMemory(), t0 = System.nanoTime();
        List<String> warnings = new ArrayList<>();
        CanonRasters r = CanonRasters.load(dir, warnings::add);
        long ms = (System.nanoTime() - t0) / 1_000_000;
        System.gc();
        long mb = (rt.totalMemory() - rt.freeMemory() - before) >> 20;
        check(r != null && warnings.isEmpty(), "world/build loads cleanly: " + warnings);
        JsonObject box = r.legend().getAsJsonObject("box");
        check(r.boxX0() == box.get("x0").getAsInt() && r.boxZ0() == box.get("z0").getAsInt() && r.boxX1() == box.get("x1").getAsInt() && r.boxZ1() == box.get("z1").getAsInt(),
                "the box of index.json: " + r.describe());
        check(r.factorCurve() != null && r.jaggedCurve() != null && r.biomeTableSize() > 1 && r.biomeId(0) == null, "curves and the biome table (0 = #ocean = auto)");
        List<String> problems = new ArrayList<>();
        int plates = 0;
        for (var e : r.legend().getAsJsonArray("sites")) {
            JsonObject site = e.getAsJsonObject();
            if (!site.get("plated").getAsBoolean() || site.get("kind").getAsString().equals("carve")) continue;
            double x = site.get("x").getAsDouble(), z = site.get("z").getAsDouble(), y = site.get("y").getAsDouble();
            plates++;
            if (Math.abs(r.height(x, z) - y) > 0.5) problems.add(site.get("id").getAsString() + " plate y " + y + " but height " + r.height(x, z));
            if ((r.mask((int) x, (int) z) & (CanonRasters.SITE | CanonRasters.DRY)) != (CanonRasters.SITE | CanonRasters.DRY)) problems.add(site.get("id").getAsString() + " not site+dry in the mask");
            if (r.excludes((int) x - 4, (int) y - 2, (int) z - 4, (int) x + 4, (int) y + 10, (int) z + 4, 16) == 0) problems.add(site.get("id").getAsString() + " allows a structure start");
            String id = r.siteAt((int) x, (int) z);
            if (!site.get("id").getAsString().equals(id)) problems.add(site.get("id").getAsString() + " named " + id + " in sites.png");
        }
        check(problems.isEmpty() && plates > 20, plates + " plated sites agree with the rasters: " + problems);
        // The sea at the box edge is the raster's deep floor, blended into CanonGrid's ocean over most of the sea margin.
        check(r.height(r.boxX0() + 2, r.boxZ0() + 2) < 0 && r.weight(r.boxX0() + 2, r.boxZ0() + 500) < 0.05 && r.weight(r.boxX0() + 1100, r.boxZ0() + 1100) == 1,
                "edge: deep sea, blend over " + r.edgeBlend + " blocks");
        double[][] fc = r.factorCurve();
        int jag = 0, dry = 0, ex = 0, n = 0;
        for (int z = r.boxZ0() + 2; z < r.boxZ1(); z += 64) {
            for (int x = r.boxX0() + 2; x < r.boxX1(); x += 64) {
                double rug = r.rugged(x, z, 0), f = DesignTerrain.curve(fc, rug);
                check(f >= 1.5 && f <= 8, "factor in range at " + x + "," + z);
                double h = r.height(x, z);
                check(h > -64 && h < 320, "height in the world at " + x + "," + z + ": " + h);
                if (DesignTerrain.curve(r.jaggedCurve(), rug) > 0) jag++;
                if ((r.mask(x, z) & CanonRasters.DRY) != 0) dry++;
                if ((r.mask(x, z) & (CanonRasters.SITE | CanonRasters.ROAD | CanonRasters.CAVITY)) != 0) ex++;
                n++;
            }
        }
        int roads = 0;
        boolean[] b = new boolean[1];
        for (var e : JsonParser.parseString(Files.readString(dir.resolve("roads.json"), StandardCharsets.UTF_8)).getAsJsonObject().getAsJsonArray("roads")) {
            JsonArray pts = e.getAsJsonObject().getAsJsonArray("points");
            for (int i = 2; i < pts.size() - 2; i += 10) {
                JsonArray pt = pts.get(i).getAsJsonArray();
                int x = (int) Math.floor(pt.get(0).getAsDouble()), z = (int) Math.floor(pt.get(1).getAsDouble());
                if (r.road(x, z, b) >= 0 || r.road(x + 1, z, b) >= 0 || r.road(x, z + 1, b) >= 0) roads++;
                else problems.add("no road surface at " + x + "," + z + " of " + e.getAsJsonObject().get("id").getAsString());
                if (Math.abs(r.height(x, z) - pt.get(2).getAsDouble()) > 1.5) problems.add("road " + e.getAsJsonObject().get("id").getAsString() + " at " + x + "," + z + ": height " + r.height(x, z) + " vs profile " + pt.get(2));
            }
        }
        // Map content, not format: report (a carve massif drawn over a road lifts the corridor there, for instance).
        check(problems.stream().noneMatch(t -> t.startsWith("no road surface")), "roads.json centre lines lie on road pixels: " + problems);
        if (!problems.isEmpty()) System.out.println("real rasters: road profile vs height raster differs by > 1.5 at " + problems);
        System.out.printf(Locale.ROOT, "real rasters (%s): loaded in %d ms, ~%d MB; %s; %d plated sites agree; %d road points on the raster (%d off); lattice 64: jagged %d, dry %d, excluded %d of %d; %d lantern posts%n",
                dir, ms, mb, r.describe(), plates, roads, problems.size(), jag, dry, ex, n, r.lanternCount());
    }

    // ---- the calibration map of the WP-W2 gate ----

    static final int CAL_X0 = -1536, CAL_Z0 = -1536, CAL_PX = 768, LAND = 1100;

    /** West strips (x < -64): flat 66, 90, 140, 220; east strips (x >= 64): rolling 100, hills 110, alpine 160. */
    static double[] calStrip(double x, double z) {
        double[][] west = {{-1100, -640, 66, 0}, {-576, -192, 90, 0}, {-128, 320, 140, 0}, {384, 1100, 220, 0}};
        double[][] east = {{-1100, -384, 100, 0.3}, {-320, 320, 110, 0.6}, {384, 1100, 160, 0.9}};
        double[] wv = strip(west, z), ev = strip(east, z);
        double t = Math.max(0, Math.min(1, (x + 64) / 128));
        return new double[] {wv[0] + (ev[0] - wv[0]) * t, wv[1] + (ev[1] - wv[1]) * t};
    }

    private static double[] strip(double[][] strips, double z) {
        if (z <= strips[0][0]) return new double[] {strips[0][2], strips[0][3]};
        for (int i = 0; i < strips.length; i++) {
            if (z < strips[i][1]) return new double[] {strips[i][2], strips[i][3]};
            if (i + 1 < strips.length && z < strips[i + 1][0]) {
                double t = (z - strips[i][1]) / (strips[i + 1][0] - strips[i][1]);
                return new double[] {strips[i][2] + (strips[i + 1][2] - strips[i][2]) * t, strips[i][3] + (strips[i + 1][3] - strips[i][3]) * t};
            }
        }
        double[] last = strips[strips.length - 1];
        return new double[] {last[2], last[3]};
    }

    /**
     * The calibration map, in WP-W1's own format (own-world.md §3.8, index.json): height {@code round((H + 64) * 16)},
     * rugged {@code * 255}, water {@code level + 64}, road classes 0 none, 1 corridor, 2 trail, 3 main, 4/5 bridges,
     * biome indices into {@code files.biome.biomes} (0 = {@code #ocean}), sites.png 1-based into {@code sites},
     * exclude.png bits (1 site r + 48, 2 road corridor + 8, 4 cavity), sites.json (flat sites only).
     */
    static void writeCalibration(Path dir) throws IOException {
        Files.createDirectories(dir);
        int n = CAL_PX * CAL_PX;
        int[] height = new int[n], rugged = new int[n], water = new int[n], road = new int[n], biome = new int[n], site = new int[n], exclude = new int[n];
        int[][] reaches = {{-310, -260, 89}, {-260, -210, 88}, {-210, -160, 86}, {-160, -110, 85}};
        for (int pz = 0; pz < CAL_PX; pz++) {
            for (int px = 0; px < CAL_PX; px++) {
                int i = pz * CAL_PX + px;
                double x = CAL_X0 + px * 4 + 2, z = CAL_Z0 + pz * 4 + 2;
                double[] s = calStrip(x, z);
                double hgt = s[0], rug = s[1];
                int lvl = 0, bio, ex = 0;
                // Biomes by strip: plains, forest, meadow, snowy plains | Tensura ancient forest, windswept forest, stony peaks.
                if (x < 0) bio = z < -608 ? 1 : z < -160 ? 2 : z < 352 ? 3 : 4;
                else bio = z < -352 ? 8 : z < 352 ? 5 : 6;
                // The lake at 90 (r 90, rim to 122 at 92) and the river's stepped reaches (bed level - 4, banks level + 2).
                double dl = Math.hypot(x + 400, z + 384);
                if (dl < 122) {
                    hgt = dl < 82 ? 84 : dl < 90 ? 84 + (dl - 82) : 92;
                    if (dl < 90) lvl = 90;
                }
                double dp = Math.hypot(x + 90, z + 384);
                if (dp < 36) {
                    hgt = dp < 20 ? 81 : Math.max(hgt, 87);
                    if (dp < 20) lvl = 85;
                }
                for (int[] reach : reaches) {
                    if (x >= reach[0] && x < reach[1] && Math.abs(z + 384) < 14) {
                        boolean bed = Math.abs(z + 384) < 6;
                        hgt = bed ? reach[2] - 4 : Math.max(hgt, reach[2] + 2);
                        if (bed) lvl = reach[2];
                    }
                }
                if (lvl > 0) bio = 7;
                // The flat site's bump (the plate must level it) and the carve site's cavity.
                double ds = Math.hypot(x + 600, z - 100);
                if (ds < 100) hgt += 8 * (0.5 + 0.5 * Math.cos(Math.PI * ds / 100));
                if (ds < 64) {
                    site[i] = 1;
                    bio = 1;
                }
                if (ds < 64 + 48) ex |= 1;
                double dc = Math.hypot(x + 300, z - 100);
                if (dc < 40) site[i] = 2;
                if (dc < 40 + 48) ex |= 1;
                if (dc < 40 + 8) ex |= 4;
                // The road: north-south at x -234 from z -1050 to -250 (main, a bridge over the river), corridor 2 px each side.
                double dr = Math.abs(x + 234);
                if (z >= -1050 && z <= -250) {
                    if (dr <= 3) road[i] = lvl > 0 ? 5 : 3;
                    else if (dr <= 11) road[i] = 1;
                    if (dr <= 11 + 8) ex |= 2;
                }
                // Coast: the land rectangle |x|, |z| <= 1100 falls to 63 over its outer 96 blocks, the sea to -20 over 300.
                double e = Math.min(LAND - Math.abs(x), LAND - Math.abs(z));
                if (e < 96) {
                    if (e >= 0) {
                        double t = e / 96;
                        hgt = 63 + (hgt - 63) * t * t * (3 - 2 * t);
                    } else {
                        hgt = 63 - 83 * Math.min(1, -e / 300);
                    }
                    rug = e < 0 ? 0.2 : rug;
                    bio = e < 0 ? 0 : bio;
                    road[i] = e < 0 ? 0 : road[i];
                }
                height[i] = (int) Math.round((hgt + 64) * 16);
                rugged[i] = (int) Math.round(Math.max(0, Math.min(1, rug)) * 255);
                water[i] = lvl > 0 ? lvl + 64 : 0;
                biome[i] = bio;
                exclude[i] = ex;
            }
        }
        writePng(dir.resolve("height.png"), CAL_PX, CAL_PX, 16, 0, height);
        writePng(dir.resolve("rugged.png"), CAL_PX, CAL_PX, 8, 0, rugged);
        writePng(dir.resolve("water.png"), CAL_PX, CAL_PX, 16, 0, water);
        writePng(dir.resolve("road.png"), CAL_PX, CAL_PX, 8, 0, road);
        writePng(dir.resolve("biome.png"), CAL_PX, CAL_PX, 8, 3, biome);
        writePng(dir.resolve("sites.png"), CAL_PX, CAL_PX, 8, 0, site);
        writePng(dir.resolve("exclude.png"), CAL_PX, CAL_PX, 8, 0, exclude);
        JsonObject index = JsonParser.parseString("""
                {"what": "WP-W2 calibration map (DesignSelfCheck write-calibration), in the format of own-world.md 3.8: not a world design",
                 "version": 1,
                 "box": {"x0": -1536, "z0": -1536, "x1": 1536, "z1": 1536, "width_px": 768, "height_px": 768, "sea_margin": 436},
                 "pixel": {"blocks": 4, "sample": "centre"},
                 "sea_level": 63,
                 "edge_blend": 256,
                 "files": {
                   "height": {"file": "height.png", "format": "gray16", "value": "round((H + 64) * 16)", "scale": 16, "offset": 64},
                   "rugged": {"file": "rugged.png", "format": "gray8", "value": "round(rugged * 255)",
                              "factor": [[0.0, 8.0], [0.1, 8.0], [0.3, 5.0], [0.6, 3.0], [0.8, 1.5], [1.0, 1.5]],
                              "jaggedness": [[0.0, 0.0], [0.8, 0.0], [1.0, 0.6]]},
                   "water": {"file": "water.png", "format": "gray16", "value": "0 = dry, else level + 64", "offset": 64},
                   "road": {"file": "road.png", "format": "gray8", "classes": {"none": 0, "corridor": 1, "trail": 2, "main": 3, "trail_bridge": 4, "main_bridge": 5}},
                   "biome": {"file": "biome.png", "format": "palette8", "biomes": ["#ocean", "minecraft:plains", "minecraft:forest", "minecraft:meadow",
                             "minecraft:snowy_plains", "minecraft:windswept_forest", "minecraft:stony_peaks", "minecraft:river", "tensura:ancient_forest"]},
                   "sites": {"file": "sites.png", "format": "gray8", "value": "1-based index into sites"},
                   "exclude": {"file": "exclude.png", "format": "gray8", "bits": {"site": 1, "road": 2, "cavity": 4}}},
                 "sites": [
                   {"id": "calib_site", "kind": "clearing", "x": -600, "z": 100, "r": 64, "plated": true, "y": 140, "index": 1, "fade": 32},
                   {"id": "calib_cave", "kind": "carve", "x": -300, "z": 100, "r": 40, "plated": true, "y": 120, "index": 2, "fade": 20, "cover": 6}],
                 "calibration": {"bands": [
                    {"name": "flat66", "box": [-1030, -1030, -300, -660], "y": 66, "rugged": 0, "tol": 1.5},
                    {"name": "flat90", "box": [-1030, -560, -560, -210], "y": 90, "rugged": 0, "tol": 1.5},
                    {"name": "flat140", "box": [-1030, -100, -720, 300], "y": 140, "rugged": 0, "tol": 1.5},
                    {"name": "flat220", "box": [-1030, 420, -100, 1030], "y": 220, "rugged": 0, "tol": 1.5},
                    {"name": "rolling100", "box": [100, -1030, 1030, -420], "y": 100, "rugged": 0.3, "tol": 3, "max_sd": 4},
                    {"name": "hills110", "box": [100, -280, 1030, 280], "y": 110, "rugged": 0.6, "tol": 6, "max_sd": 8},
                    {"name": "alpine160", "box": [100, 420, 1030, 1030], "y": 160, "rugged": 0.9, "tol": 40, "min_sd": 3}]}}
                """).getAsJsonObject();
        Files.writeString(dir.resolve("index.json"), new GsonBuilder().setPrettyPrinting().create().toJson(index));
        Files.writeString(dir.resolve("sites.json"), """
                {"_doc": "flat sites (CanonSites schema); carve sites are left out",
                 "sites": [{"name": "calib_site", "centre": [-600, 100], "radius": 64, "fade": 32, "terrain": "flat", "ground": 140,
                            "biomes": [["minecraft:plains", 1]]}]}
                """);
        Files.writeString(dir.resolve("roads.json"), """
                {"roads": [{"id": "calib_road", "kind": "main", "half": 2, "corridor": 5, "points": [[-234, -1050, 66, 0], [-234, -640, 66, 0],
                  [-234, -576, 90, 0], [-234, -390, 90, 1], [-234, -378, 90, 1], [-234, -250, 90, 0]]}]}
                """);
    }

    // ---- a small PNG writer (every filter type, gray 1/8/16 bits and palette) ----

    static void writePng(Path file, int w, int h, int depth, int type, int[] values) throws IOException {
        int rowBytes = (w * depth + 7) / 8, bpp = Math.max(1, depth / 8);
        ByteArrayOutputStream raw = new ByteArrayOutputStream();
        byte[] prev = new byte[rowBytes];
        for (int y = 0; y < h; y++) {
            byte[] row = new byte[rowBytes];
            for (int x = 0; x < w; x++) {
                int v = values[y * w + x];
                if (depth == 16) {
                    row[x * 2] = (byte) (v >> 8);
                    row[x * 2 + 1] = (byte) v;
                } else if (depth == 8) {
                    row[x] = (byte) v;
                } else {
                    int bit = x * depth, shift = 8 - depth - (bit & 7);
                    row[bit >> 3] |= (byte) ((v & ((1 << depth) - 1)) << shift);
                }
            }
            int filter = y % 5;
            raw.write(filter);
            for (int i = 0; i < rowBytes; i++) {
                int a = i >= bpp ? row[i - bpp] & 0xFF : 0, b = prev[i] & 0xFF, c = i >= bpp ? prev[i - bpp] & 0xFF : 0, x = row[i] & 0xFF;
                int p = a + b - c, pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c);
                int pred = switch (filter) {
                    case 1 -> a;
                    case 2 -> b;
                    case 3 -> (a + b) >> 1;
                    case 4 -> pa <= pb && pa <= pc ? a : pb <= pc ? b : c;
                    default -> 0;
                };
                raw.write((x - pred) & 0xFF);
            }
            prev = row;
        }
        Deflater deflater = new Deflater(6);
        deflater.setInput(raw.toByteArray());
        deflater.finish();
        ByteArrayOutputStream z = new ByteArrayOutputStream();
        byte[] buf = new byte[65536];
        while (!deflater.finished()) z.write(buf, 0, deflater.deflate(buf));
        deflater.end();
        ByteArrayOutputStream png = new ByteArrayOutputStream();
        png.write(new byte[] {(byte) 0x89, 'P', 'N', 'G', '\r', '\n', 0x1A, '\n'});
        chunk(png, "IHDR", new byte[] {(byte) (w >> 24), (byte) (w >> 16), (byte) (w >> 8), (byte) w, (byte) (h >> 24), (byte) (h >> 16), (byte) (h >> 8), (byte) h,
                (byte) depth, (byte) type, 0, 0, 0});
        if (type == 3) {
            byte[] plte = new byte[256 * 3];
            for (int i = 0; i < 256; i++) {
                plte[i * 3] = (byte) (i * 37);
                plte[i * 3 + 1] = (byte) (i * 91);
                plte[i * 3 + 2] = (byte) (i * 13);
            }
            chunk(png, "PLTE", plte);
        }
        chunk(png, "IDAT", z.toByteArray());
        chunk(png, "IEND", new byte[0]);
        Files.write(file, png.toByteArray());
    }

    private static void chunk(ByteArrayOutputStream out, String type, byte[] data) {
        byte[] t = type.getBytes(StandardCharsets.ISO_8859_1);
        int len = data.length;
        out.write(len >> 24);
        out.write(len >> 16);
        out.write(len >> 8);
        out.write(len);
        out.writeBytes(t);
        out.writeBytes(data);
        CRC32 crc = new CRC32();
        crc.update(t);
        crc.update(data);
        long c = crc.getValue();
        out.write((int) (c >> 24));
        out.write((int) (c >> 16));
        out.write((int) (c >> 8));
        out.write((int) c);
    }

    private static void check(boolean ok, String what) {
        if (!ok) throw new AssertionError("design self-check failed: " + what);
    }
}
