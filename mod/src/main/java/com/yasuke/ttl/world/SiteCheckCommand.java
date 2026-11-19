package com.yasuke.ttl.world;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Locale;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.NoiseColumn;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.RandomState;
import net.minecraft.world.level.material.FluidState;
import net.minecraft.world.level.material.Fluids;
import net.neoforged.neoforge.event.RegisterCommandsEvent;

/**
 * {@code /ttlsite} (op 2), the own world's in-game checks (design/architecture/own-world.md §3.1, §4.3). They ask the
 * Tensura world's generator for the noise terrain of a column (heightmap and the aquifer's fluids), so nothing has to be
 * generated, nothing is changed, and the answer is what the next chunk at that spot will be before features run.
 * <ul>
 *   <li>{@code status}: the design rasters, sites and the structure starts kept out so far;</li>
 *   <li>{@code list}: the sites of sites.json;</li>
 *   <li>{@code check <id>|all}: per site the flatness of its plate (mean |surface - ground| over its radius on a lattice,
 *       must be <= 1.5), its dryness (columns with aquifer water or lava within 16 blocks of its ground over the radius
 *       plus the dry margin, must be 0) and for carve sites the cover over the ground (min/median, >= min_cover);</li>
 *   <li>{@code calibrate}: the calibration gate of WP-W2 on a calibration map (legend {@code calibration.bands}): per
 *       band the mean (y - H), mean |y - H|, spread and max over a 4-block lattice, PASS when within the band's
 *       {@code tol} (flat bands 1.5) and spread limits; and per {@code calibration.seams} the step across the design box
 *       edge (64 blocks inside vs outside, <= 3). Ends with {@code calibration PASS} or {@code calibration FAIL};</li>
 *   <li>{@code at <x> <z>}: every raster at a column and the noise surface there.</li>
 * </ul>
 */
public final class SiteCheckCommand {
    private SiteCheckCommand() {}

    static final double FLAT_TOLERANCE = 1.5, SEAM_TOLERANCE = 3;
    static final int MAX_POINTS = 1200, DRY_BAND = 16;

    public static void registerCommands(RegisterCommandsEvent event) {
        event.getDispatcher().register(Commands.literal("ttlsite")
                .requires(source -> source.hasPermission(2))
                .then(Commands.literal("status").executes(SiteCheckCommand::status))
                .then(Commands.literal("list").executes(SiteCheckCommand::list))
                .then(Commands.literal("calibrate").executes(SiteCheckCommand::calibrate))
                .then(Commands.literal("at").then(Commands.argument("x", IntegerArgumentType.integer())
                        .then(Commands.argument("z", IntegerArgumentType.integer()).executes(SiteCheckCommand::at))))
                .then(Commands.literal("check").then(Commands.argument("id", StringArgumentType.word())
                        .suggests((ctx, builder) -> {
                            List<String> ids = new ArrayList<>(List.of("all"));
                            DesignWorld.Loaded l = DesignWorld.loaded();
                            if (l != null) l.infos().forEach(i -> ids.add(i.id()));
                            return SharedSuggestionProvider.suggest(ids, builder);
                        })
                        .executes(SiteCheckCommand::check))));
    }

    private static void say(CommandContext<CommandSourceStack> ctx, String text) {
        ctx.getSource().sendSuccess(() -> Component.literal(text), false);
    }

    private static int status(CommandContext<CommandSourceStack> ctx) {
        DesignWorld.Loaded l = DesignWorld.loaded();
        if (l == null) {
            say(ctx, "[ttl] own world: no design rasters in " + DesignWorld.dir() + " (terrain, biomes and structures as before)");
            return 0;
        }
        long[] ex = DesignWorld.excludedCounts();
        ServerLevel level = ctx.getSource().getServer().overworld();
        say(ctx, "[ttl] own world: " + l.rasters().describe() + "; " + l.infos().size() + " sites; generator "
                + (DesignWorld.designGenerator(level.getChunkSource().getGenerator()) ? "ttl:canon_biomes (design active)" : "NOT ttl:canon_biomes (design inactive)")
                + String.format(Locale.ROOT, "; structure starts kept out: %d site, %d road, %d cavity", ex[0], ex[1], ex[2]));
        return 1;
    }

    private static int list(CommandContext<CommandSourceStack> ctx) {
        DesignWorld.Loaded l = DesignWorld.loaded();
        if (l == null) {
            say(ctx, "[ttl] own world: no design rasters");
            return 0;
        }
        StringBuilder out = new StringBuilder("[ttl] " + l.infos().size() + " design sites:");
        for (DesignSitesFile.Info i : l.infos())
            out.append(String.format(Locale.ROOT, "\n  %s %s at %.0f %.0f r %.0f ground %s", i.id(), i.kind(), i.x(), i.z(), i.r(), i.ground() == null ? "-" : i.ground()));
        say(ctx, out.toString());
        return l.infos().size();
    }

    private static int at(CommandContext<CommandSourceStack> ctx) {
        int x = IntegerArgumentType.getInteger(ctx, "x"), z = IntegerArgumentType.getInteger(ctx, "z");
        CanonRasters r = DesignWorld.rasters();
        ServerLevel level = ctx.getSource().getServer().overworld();
        Probe p = new Probe(level);
        int h = p.surface(x, z);
        say(ctx, "[ttl] at " + x + " " + z + ": noise surface (first air) y" + h + (r == null ? "; no design rasters" : "; " + r.describe(x, z)
                + String.format(Locale.ROOT, "; surface - designed %+.1f", h - r.height(x + 0.5, z + 0.5))));
        return 1;
    }

    // ---- site check ----

    private static int check(CommandContext<CommandSourceStack> ctx) {
        DesignWorld.Loaded l = DesignWorld.loaded();
        if (l == null) {
            say(ctx, "[ttl] site check: no design rasters");
            return 0;
        }
        String id = StringArgumentType.getString(ctx, "id");
        List<DesignSitesFile.Info> sites = new ArrayList<>();
        for (DesignSitesFile.Info i : l.infos()) if (id.equals("all") || i.id().equals(id)) sites.add(i);
        if (sites.isEmpty()) {
            say(ctx, "[ttl] site check: no site '" + id + "' in sites.json");
            return 0;
        }
        Probe p = new Probe(ctx.getSource().getServer().overworld());
        int failed = 0;
        for (DesignSitesFile.Info s : sites) {
            Result res = checkSite(p, l.rasters(), s, sites.size() > 1 ? MAX_POINTS / 4 : MAX_POINTS);
            if (!res.ok) failed++;
            say(ctx, res.text);
        }
        say(ctx, String.format(Locale.ROOT, "[ttl] site check %s: %d of %d sites OK%s", id, sites.size() - failed, sites.size(), failed == 0 ? "" : ", " + failed + " FAILED"));
        return failed == 0 ? 1 : 0;
    }

    record Result(boolean ok, String text) {}

    static Result checkSite(Probe p, CanonRasters r, DesignSitesFile.Info s, int budget) {
        boolean carve = s.kind().equalsIgnoreCase("carve");
        Integer groundObj = s.ground();
        int ground = groundObj != null ? groundObj : (int) Math.round(r.height(s.x(), s.z()));
        double dryR = s.r() + r.dryMargin;
        int step = lattice(dryR, budget);
        List<Double> devs = new ArrayList<>(), heights = new ArrayList<>();
        int wet = 0, lava = 0, columns = 0;
        for (double dz = -dryR; dz <= dryR; dz += step) {
            for (double dx = -dryR; dx <= dryR; dx += step) {
                double d = Math.hypot(dx, dz);
                if (d > dryR) continue;
                int x = (int) Math.floor(s.x() + dx), z = (int) Math.floor(s.z() + dz);
                NoiseColumn col = p.column(x, z);
                int h = Probe.surface(col, p.minY, p.maxY);
                columns++;
                int[] fluids = Probe.fluids(col, p.minY, ground - DRY_BAND, Math.max(ground, h) + DRY_BAND);
                if (fluids[0] > 0) wet++;
                if (fluids[1] > 0) lava++;
                if (d <= s.r()) {
                    devs.add((double) (h - ground));
                    heights.add((double) h);
                }
            }
        }
        StringBuilder t = new StringBuilder(String.format(Locale.ROOT, "[ttl] site %s (%s, r %.0f, ground %d): ", s.id(), s.kind(), s.r(), ground));
        boolean ok = true;
        if (!carve) {
            double meanAbs = devs.stream().mapToDouble(Math::abs).average().orElse(0), max = devs.stream().mapToDouble(Math::abs).max().orElse(0);
            double mean = devs.stream().mapToDouble(Double::doubleValue).average().orElse(0);
            boolean flat = meanAbs <= FLAT_TOLERANCE;
            ok &= flat;
            t.append(String.format(Locale.ROOT, "flat mean|dy| %.2f (mean %+.2f, max %.0f, n %d) %s", meanAbs, mean, max, devs.size(), flat ? "OK" : "FAIL"));
        } else {
            double[] cover = heights.stream().mapToDouble(h -> h - (s.roof() != null ? s.roof() : ground)).sorted().toArray();
            double min = cover.length == 0 ? 0 : cover[0], median = cover.length == 0 ? 0 : cover[cover.length / 2];
            boolean enough = s.minCover() == null || min >= s.minCover();
            ok &= enough;
            t.append(String.format(Locale.ROOT, "cover over %s %d: min %.0f median %.0f%s %s", s.roof() != null ? "roof" : "ground",
                    s.roof() != null ? s.roof() : ground, min, median, s.minCover() == null ? "" : " (min_cover " + s.minCover() + ")", enough ? "OK" : "FAIL"));
        }
        // Coast and lakeside plates touch water on purpose (their box reaches the shore); only lava fails them.
        boolean shore = s.kind().equalsIgnoreCase("coast") || s.kind().equalsIgnoreCase("lakeside");
        boolean dry = lava == 0 && (shore || wet == 0);
        ok &= dry;
        t.append(String.format(Locale.ROOT, "; dry: wet %d lava %d of %d columns (r %.0f, y %d..%d)%s %s", wet, lava, columns, dryR, ground - DRY_BAND, ground + DRY_BAND,
                shore ? " (shore site: water allowed)" : "", dry ? "OK" : "FAIL"));
        t.append(ok ? " -> OK" : " -> FAIL");
        return new Result(ok, t.toString());
    }

    static int lattice(double radius, int budget) {
        double area = Math.PI * radius * radius;
        int step = 4;
        while (area / (step * step) > budget) step += 4;
        return step;
    }

    // ---- calibration gate ----

    private static int calibrate(CommandContext<CommandSourceStack> ctx) {
        CanonRasters r = DesignWorld.rasters();
        if (r == null) {
            say(ctx, "[ttl] calibration: no design rasters (nothing to calibrate)");
            return 0;
        }
        Probe p = new Probe(ctx.getSource().getServer().overworld());
        if (!DesignWorld.designGenerator(p.generator)) {
            say(ctx, "[ttl] calibration FAIL: the overworld generator is not ttl:canon_biomes");
            return 0;
        }
        JsonObject cal = r.legend().has("calibration") && r.legend().get("calibration").isJsonObject() ? r.legend().getAsJsonObject("calibration") : new JsonObject();
        int failed = 0, total = 0;
        double biasSum = 0;
        int biasN = 0;
        if (cal.has("bands")) {
            for (JsonElement e : cal.getAsJsonArray("bands")) {
                JsonObject b = e.getAsJsonObject();
                Band band = band(p, r, b);
                total++;
                if (!band.pass) failed++;
                if (band.flat) {
                    biasSum += band.mean * band.n;
                    biasN += band.n;
                }
                say(ctx, band.text);
            }
        } else {
            say(ctx, "[ttl] calibration: the legend has no calibration.bands (a real map); only the seams are checked");
        }
        JsonArray seams = cal.has("seams") ? cal.getAsJsonArray("seams") : defaultSeams(r);
        for (JsonElement e : seams) {
            JsonArray a = e.getAsJsonArray();
            String text = seam(p, a.get(0).getAsInt(), a.get(1).getAsInt(), a.get(2).getAsInt(), a.get(3).getAsInt());
            total++;
            if (text.endsWith("FAIL")) failed++;
            say(ctx, text);
        }
        if (biasN > 0) say(ctx, String.format(Locale.ROOT, "[ttl] calibration: mean (y - H) over the flat bands %+.2f blocks (the 'bias' of ttl:design_offset corrects a systematic lift)", biasSum / biasN));
        say(ctx, failed == 0 ? "[ttl] calibration PASS (" + total + " checks)" : "[ttl] calibration FAIL (" + failed + " of " + total + " checks)");
        return failed == 0 ? 1 : 0;
    }

    record Band(boolean pass, boolean flat, double mean, int n, String text) {}

    static Band band(Probe p, CanonRasters r, JsonObject b) {
        String name = b.has("name") ? b.get("name").getAsString() : "band";
        JsonArray box = b.getAsJsonArray("box");
        int x0 = box.get(0).getAsInt(), z0 = box.get(1).getAsInt(), x1 = box.get(2).getAsInt(), z1 = box.get(3).getAsInt();
        int inset = b.has("inset") ? b.get("inset").getAsInt() : 32;
        double tol = b.has("tol") ? b.get("tol").getAsDouble() : FLAT_TOLERANCE;
        Double minSd = b.has("min_sd") ? b.get("min_sd").getAsDouble() : null, maxSd = b.has("max_sd") ? b.get("max_sd").getAsDouble() : null;
        boolean flat = b.has("rugged") ? b.get("rugged").getAsDouble() == 0 : maxSd == null && minSd == null;
        int w = Math.max(1, x1 - x0 - 2 * inset), h = Math.max(1, z1 - z0 - 2 * inset);
        int step = 4;
        while ((double) w * h / (step * step) > 600) step += 4;
        List<Double> d = new ArrayList<>();
        for (int z = z0 + inset; z < z1 - inset; z += step)
            for (int x = x0 + inset; x < x1 - inset; x += step) d.add(p.surface(x, z) - r.height(x + 0.5, z + 0.5));
        double[] v = d.stream().mapToDouble(Double::doubleValue).toArray();
        double mean = Arrays.stream(v).average().orElse(0), meanAbs = Arrays.stream(v).map(Math::abs).average().orElse(0);
        double sd = Math.sqrt(Arrays.stream(v).map(x -> (x - mean) * (x - mean)).average().orElse(0)), max = Arrays.stream(v).map(Math::abs).max().orElse(0);
        boolean pass = meanAbs <= tol && (minSd == null || sd >= minSd) && (maxSd == null || sd <= maxSd);
        String text = String.format(Locale.ROOT, "[ttl] calibration band %s: n %d, mean (y-H) %+.2f, mean |y-H| %.2f (tol %.1f), sd %.2f%s, max |y-H| %.0f -> %s",
                name, v.length, mean, meanAbs, tol, sd, minSd == null && maxSd == null ? "" : " (" + (minSd == null ? "" : ">= " + minSd) + (maxSd == null ? "" : " <= " + maxSd) + ")",
                max, pass ? "PASS" : "FAIL");
        return new Band(pass, flat, mean, v.length, text);
    }

    /** The box edge's four midpoints, outward normals. */
    static JsonArray defaultSeams(CanonRasters r) {
        JsonArray out = new JsonArray();
        int cx = (r.boxX0() + r.boxX1()) / 2, cz = (r.boxZ0() + r.boxZ1()) / 2;
        int[][] s = {{r.boxX0(), cz, -1, 0}, {r.boxX1(), cz, 1, 0}, {cx, r.boxZ0(), 0, -1}, {cx, r.boxZ1(), 0, 1}};
        for (int[] e : s) {
            JsonArray a = new JsonArray();
            for (int v : e) a.add(v);
            out.add(a);
        }
        return out;
    }

    /** The floor (ocean floor heightmap) 64 blocks inside vs 64 outside the box edge, and the largest 4-block step across it. */
    static String seam(Probe p, int x, int z, int nx, int nz) {
        double inside = 0, outside = 0;
        int prev = Integer.MIN_VALUE, worstStep = 0;
        for (int t = -64; t <= 64; t += 4) {
            int h = p.surface(x + nx * t, z + nz * t);
            if (t < 0) inside += h;
            else if (t > 0) outside += h;
            if (prev != Integer.MIN_VALUE) worstStep = Math.max(worstStep, Math.abs(h - prev));
            prev = h;
        }
        inside /= 16;
        outside /= 16;
        double diff = Math.abs(inside - outside);
        boolean ok = diff <= SEAM_TOLERANCE && worstStep <= SEAM_TOLERANCE;
        return String.format(Locale.ROOT, "[ttl] calibration seam at %d %d: floor %.1f inside vs %.1f outside (diff %.1f), largest 4-block step %d -> %s",
                x, z, inside, outside, diff, worstStep, ok ? "PASS" : "FAIL");
    }

    /** Noise-only column probes of the overworld's generator. */
    static final class Probe {
        final ServerLevel level;
        final ChunkGenerator generator;
        final RandomState random;
        final int minY, maxY;

        Probe(ServerLevel level) {
            this.level = level;
            this.generator = level.getChunkSource().getGenerator();
            this.random = level.getChunkSource().randomState();
            this.minY = level.getMinBuildHeight();
            this.maxY = level.getMaxBuildHeight();
        }

        /** First air (not counting fluids as ground) above the solid noise terrain. */
        int surface(int x, int z) {
            return generator.getBaseHeight(x, z, Heightmap.Types.OCEAN_FLOOR_WG, level, random);
        }

        NoiseColumn column(int x, int z) {
            return generator.getBaseColumn(x, z, level, random);
        }

        static int surface(NoiseColumn col, int minY, int maxY) {
            for (int y = maxY - 1; y >= minY; y--) {
                BlockState s = col.getBlock(y);
                if (!s.isAir() && s.getFluidState().isEmpty()) return y + 1;
            }
            return minY;
        }

        /** {water, lava} block counts in [y0, y1]. */
        static int[] fluids(NoiseColumn col, int minY, int y0, int y1) {
            int[] out = new int[2];
            for (int y = Math.max(minY, y0); y <= y1; y++) {
                FluidState f = col.getBlock(y).getFluidState();
                if (f.isEmpty()) continue;
                if (f.is(Fluids.LAVA) || f.is(Fluids.FLOWING_LAVA)) out[1]++;
                else out[0]++;
            }
            return out;
        }
    }
}
