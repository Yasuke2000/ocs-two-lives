package com.yasuke.ttl.world;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * The canon continent of the Tensura world, precomputed from pack/config/ttl/canon_map.txt (one character
 * per chunk) and canon_regions.json. Pure Java so {@link #main} can check it without Minecraft.
 * All distances are in blocks; every sample is bilinear over cell centres so coasts are not chunk-stepped.
 */
public final class CanonGrid {
    public static final int EROSION = 0, TEMPERATURE = 1, VEGETATION = 2;

    static final double COAST = -0.11;     // vanilla inland starts here
    static final double LAND_RISE = 0.61;  // coast -> 0.5 deep inland
    static final double SEA_DROP = 0.84;   // coast -> -0.95 deep ocean, above the mushroom-fields band (< -1.05)
    static final double FADE = 700;       // blocks over which land rises / sea deepens (e-folding)
    static final double RIVER_VALLEY = 3;  // land rises this much faster away from rivers than from the sea
    static final double SEA_CLIMATE = 300; // blocks over which a nation's climate fades out over the sea
    static final double WIGGLE = 0.08;     // share of vanilla continentalness kept for natural coasts
    static final int BLUR = 3;             // box blur radius (cells), applied twice
    public static final double CONT_MIN = -1.0, CONT_MAX = COAST + LAND_RISE;

    /**
     * One nation: climate knobs, the biome palette for ordinary land ({@code biomes}, null = TerraBlender/vanilla
     * choice), optionally a palette that replaces mountain peaks, and the arrival banner texts (null = default).
     */
    public record Region(String name, Double erosion, Double temperature, Double vegetation, double strength,
                         CanonPalette biomes, boolean replacePeaks, CanonPalette peaks, String bannerTitle, String bannerSubtitle) {
        public Region(String name, Double erosion, Double temperature, Double vegetation, double strength) {
            this(name, erosion, temperature, vegetation, strength, null, false, null, null, null);
        }

        Double knob(int channel) {
            return channel == EROSION ? erosion : channel == TEMPERATURE ? temperature : vegetation;
        }
    }

    /** Sea cells within this many blocks of land belong to the nearest nation (coast wiggle reaches ~90 blocks). */
    static final double TERRITORIAL_WATERS = 128;

    final int w, h, originCol, originRow;
    final char[] cells;
    final float[] signed;     // + inland, - at sea; 0 on the coastline
    final float[] river;      // 1 on '~'
    final float[] riverDepth; // continentalness target * river
    final char[] owner;       // nation letter per cell: itself, nearest nation for '~' and near-coast '.', 0 otherwise
    final float[][] climateWeight = new float[3][], climateValue = new float[3][]; // blurred strength, blurred strength*knob
    final double landX0, landZ0, landX1, landZ1, ring, blend;
    final Map<Character, Region> regions;

    private CanonGrid(int w, int h, int originCol, int originRow, char[] cells, Map<Character, Region> regions, double ring, double blend) {
        this.w = w;
        this.h = h;
        this.originCol = originCol;
        this.originRow = originRow;
        this.cells = cells;
        this.regions = regions;
        this.ring = ring;
        this.blend = Math.max(1, blend);
        int n = w * h;

        int c0 = w, r0 = h, c1 = -1, r1 = -1;
        boolean[] sea = new boolean[n], water = new boolean[n], notSea = new boolean[n], nation = new boolean[n];
        for (int i = 0; i < n; i++) {
            sea[i] = cells[i] == '.';
            water[i] = cells[i] == '~';
            notSea[i] = !sea[i];
            nation[i] = notSea[i] && !water[i];
            if (notSea[i]) {
                c0 = Math.min(c0, i % w);
                c1 = Math.max(c1, i % w);
                r0 = Math.min(r0, i / w);
                r1 = Math.max(r1, i / w);
            }
        }
        if (c1 < 0) throw new IllegalArgumentException("canon map has no land");
        landX0 = (c0 - originCol) * 16.0;
        landX1 = (c1 + 1 - originCol) * 16.0;
        landZ0 = (r0 - originRow) * 16.0;
        landZ1 = (r1 + 1 - originRow) * 16.0;

        float[] toSea = distance(sea, null);
        float[] toLand = distance(notSea, null);
        float[] toWater = distance(water, null);
        int[] nearestNation = new int[n];
        distance(nation, nearestNation);

        owner = new char[n];
        for (int i = 0; i < n; i++) {
            if (nation[i]) owner[i] = cells[i];
            else if (nearestNation[i] >= 0 && (water[i] || toLand[i] <= TERRITORIAL_WATERS)) owner[i] = cells[nearestNation[i]];
        }

        signed = new float[n];
        river = new float[n];
        riverDepth = new float[n];
        for (int i = 0; i < n; i++) {
            if (sea[i]) {
                signed[i] = -(toLand[i] - 8);
            } else if (water[i]) {
                int x = i % w, z = i / w, wet = 0;
                for (int dz = -1; dz <= 1; dz++)
                    for (int dx = -1; dx <= 1; dx++)
                        if (cell(x + dx, z + dz) == '~') wet++;
                river[i] = 1;
                riverDepth[i] = (float) (-0.2 - 0.12 * wet / 9.0);
            } else {
                signed[i] = (float) Math.min(toSea[i] - 8, RIVER_VALLEY * (toWater[i] - 8));
            }
        }

        for (int ch = 0; ch < 3; ch++) {
            float[] a = new float[n], b = new float[n];
            for (int i = 0; i < n; i++) {
                // Rivers and the nearby sea take the climate of the nearest nation, so neither breaks it up.
                int src = nearestNation[i];
                if (src < 0) continue;
                Region region = regions.get(cells[src]);
                Double knob = region == null ? null : region.knob(ch);
                if (knob == null) continue;
                double fade = sea[i] ? Math.exp(-(toLand[i] - 8) / SEA_CLIMATE) : 1;
                a[i] = (float) (region.strength() * fade);
                b[i] = (float) (a[i] * Math.max(-1, Math.min(1, knob)));
            }
            climateWeight[ch] = blur(blur(a));
            climateValue[ch] = blur(blur(b));
        }
    }

    /** Parses the grid file lines. Throws IllegalArgumentException when the file is unusable. */
    public static CanonGrid parse(List<String> lines, Map<Character, Region> regions, double ring, double blend) {
        Integer originCol = null, originRow = null;
        List<String> rows = new ArrayList<>();
        for (String raw : lines) {
            String line = raw.stripTrailing();
            if (line.startsWith("#")) {
                String[] parts = line.substring(1).trim().split("\\s+");
                if (parts.length >= 3 && parts[0].equals("origin")) {
                    originCol = Integer.parseInt(parts[1]);
                    originRow = Integer.parseInt(parts[2]);
                }
                continue;
            }
            if (!line.isEmpty()) rows.add(line);
        }
        if (originCol == null) throw new IllegalArgumentException("canon map has no '# origin <col> <row>' line");
        if (rows.isEmpty()) throw new IllegalArgumentException("canon map has no rows");
        int w = rows.stream().mapToInt(String::length).max().orElse(0), h = rows.size();
        char[] cells = new char[w * h];
        Arrays.fill(cells, '.');
        for (int z = 0; z < h; z++) rows.get(z).getChars(0, rows.get(z).length(), cells, z * w);
        return new CanonGrid(w, h, originCol, originRow, cells, regions, ring, blend);
    }

    public static CanonGrid load(Path grid, Map<Character, Region> regions, double ring, double blend) throws IOException {
        return parse(Files.readAllLines(grid, StandardCharsets.UTF_8), regions, ring, blend);
    }

    char cell(int x, int z) {
        return x < 0 || z < 0 || x >= w || z >= h ? '.' : cells[z * w + x];
    }

    /** Grid character at a block position; '.' outside the grid. */
    public char charAt(int blockX, int blockZ) {
        return cell(Math.floorDiv(blockX, 16) + originCol, Math.floorDiv(blockZ, 16) + originRow);
    }

    /** Nation owning a block column without dithering (0 = none): for banners and commands. */
    public char ownerCell(int blockX, int blockZ) {
        int x = Math.floorDiv(blockX, 16) + originCol, z = Math.floorDiv(blockZ, 16) + originRow;
        return x < 0 || z < 0 || x >= w || z >= h ? 0 : owner[z * w + x];
    }

    /** Nation owning a block column for biome purposes: the lookup point is dithered so borders are not chunk lines. */
    public char ownerAt(int blockX, int blockZ, long seed) {
        double bx = CanonPalette.borderX(seed, blockX, blockZ), bz = CanonPalette.borderZ(seed, blockX, blockZ);
        int x = Math.floorDiv((int) Math.floor(bx), 16) + originCol, z = Math.floorDiv((int) Math.floor(bz), 16) + originRow;
        return x < 0 || z < 0 || x >= w || z >= h ? 0 : owner[z * w + x];
    }

    /** Bilinear share of river/lake cells around a block column (1 in the middle of a lake). */
    public double riverWeight(int blockX, int blockZ) {
        return sample(river, blockX / 16.0 + originCol - 0.5, blockZ / 16.0 + originRow - 0.5, false);
    }

    /** The region of a letter, or null. */
    public Region region(char c) {
        return regions.get(c);
    }

    public Map<Character, Region> regionMap() {
        return regions;
    }

    public String regionName(char c) {
        if (c == '.') return "open sea";
        if (c == '~') return "river/lake";
        Region region = regions.get(c);
        return region == null ? "unknown land '" + c + "'" : region.name();
    }

    /** Weight of the canon area: 1 within the ring around the land, 0 beyond ring + blend. */
    public double canonWeight(double x, double z) {
        double dx = Math.max(Math.max(landX0 - x, x - landX1), 0), dz = Math.max(Math.max(landZ0 - z, z - landZ1), 0);
        double e = Math.sqrt(dx * dx + dz * dz);
        if (e <= ring) return 1;
        if (e >= ring + blend) return 0;
        double t = (e - ring) / blend;
        return 1 - t * t * (3 - 2 * t);
    }

    public double continents(int blockX, int blockZ, double outside) {
        double wc = canonWeight(blockX, blockZ);
        if (wc <= 0) return outside;
        double u = blockX / 16.0 + originCol - 0.5, v = blockZ / 16.0 + originRow - 0.5;
        double gx = Math.max(Math.max(-u - 0.5, u - (w - 0.5)), 0) * 16, gz = Math.max(Math.max(-v - 0.5, v - (h - 0.5)), 0) * 16;
        double s = sample(signed, u, v, true) - Math.sqrt(gx * gx + gz * gz);
        double value = s >= 0 ? COAST + LAND_RISE * (1 - Math.exp(-s / FADE)) : COAST - SEA_DROP * (1 - Math.exp(s / FADE));
        double rw = sample(river, u, v, false), riverBlend = 0;
        if (rw > 0.2) {
            double t = Math.min(1, (rw - 0.2) / 0.4);
            riverBlend = t * t * (3 - 2 * t);
            double depth = sample(riverDepth, u, v, false) / rw;
            value = Math.min(value, value + (depth - value) * riverBlend);
        }
        double canon = Math.max(CONT_MIN, value + WIGGLE * (1 - riverBlend) * outside);
        return outside + (canon - outside) * wc;
    }

    public double climate(int channel, int blockX, int blockZ, double outside) {
        double wc = canonWeight(blockX, blockZ);
        if (wc <= 0) return outside;
        double u = blockX / 16.0 + originCol - 0.5, v = blockZ / 16.0 + originRow - 0.5;
        double a = sample(climateWeight[channel], u, v, false) * wc, b = sample(climateValue[channel], u, v, false) * wc;
        return outside * (1 - a) + b;
    }

    private double sample(float[] grid, double u, double v, boolean clamp) {
        int i = (int) Math.floor(u), j = (int) Math.floor(v);
        double fx = u - i, fz = v - j;
        double a = at(grid, i, j, clamp), b = at(grid, i + 1, j, clamp), c = at(grid, i, j + 1, clamp), d = at(grid, i + 1, j + 1, clamp);
        return (a + (b - a) * fx) * (1 - fz) + (c + (d - c) * fx) * fz;
    }

    private double at(float[] grid, int x, int z, boolean clamp) {
        if (clamp) {
            x = Math.max(0, Math.min(w - 1, x));
            z = Math.max(0, Math.min(h - 1, z));
        } else if (x < 0 || z < 0 || x >= w || z >= h) {
            return 0;
        }
        return grid[z * w + x];
    }

    /** Two-pass 8-neighbour chamfer distance (blocks, cell centre to cell centre) to the nearest source cell. */
    private float[] distance(boolean[] source, int[] nearest) {
        int n = w * h;
        float[] d = new float[n];
        float inf = Float.MAX_VALUE / 4, diag = (float) Math.sqrt(2);
        for (int i = 0; i < n; i++) {
            d[i] = source[i] ? 0 : inf;
            if (nearest != null) nearest[i] = source[i] ? i : -1;
        }
        int[][] forward = {{-1, 0}, {-1, -1}, {0, -1}, {1, -1}}, backward = {{1, 0}, {1, 1}, {0, 1}, {-1, 1}};
        for (int z = 0; z < h; z++)
            for (int x = 0; x < w; x++) relax(d, nearest, x, z, forward, diag);
        for (int z = h - 1; z >= 0; z--)
            for (int x = w - 1; x >= 0; x--) relax(d, nearest, x, z, backward, diag);
        for (int i = 0; i < n; i++) d[i] = d[i] >= inf ? inf : d[i] * 16;
        return d;
    }

    private void relax(float[] d, int[] nearest, int x, int z, int[][] offsets, float diag) {
        int i = z * w + x;
        for (int[] o : offsets) {
            int nx = x + o[0], nz = z + o[1];
            if (nx < 0 || nz < 0 || nx >= w || nz >= h) continue;
            int j = nz * w + nx;
            float cand = d[j] + (o[0] != 0 && o[1] != 0 ? diag : 1);
            if (cand < d[i]) {
                d[i] = cand;
                if (nearest != null) nearest[i] = nearest[j];
            }
        }
    }

    private float[] blur(float[] in) {
        float[] tmp = new float[in.length], out = new float[in.length];
        float norm = 2 * BLUR + 1;
        for (int z = 0; z < h; z++) {
            for (int x = 0; x < w; x++) {
                float sum = 0;
                for (int k = -BLUR; k <= BLUR; k++) {
                    int xx = x + k;
                    if (xx >= 0 && xx < w) sum += in[z * w + xx];
                }
                tmp[z * w + x] = sum / norm;
            }
        }
        for (int z = 0; z < h; z++) {
            for (int x = 0; x < w; x++) {
                float sum = 0;
                for (int k = -BLUR; k <= BLUR; k++) {
                    int zz = z + k;
                    if (zz >= 0 && zz < h) sum += tmp[zz * w + x];
                }
                out[z * w + x] = sum / norm;
            }
        }
        return out;
    }

    public String describe() {
        return String.format("%dx%d cells, origin %d,%d, land x %.0f..%.0f z %.0f..%.0f, ring %.0f, blend %.0f",
                w, h, originCol, originRow, landX0, landX1, landZ0, landZ1, ring, blend);
    }

    /** Self-check: {@code java -cp build/classes/java/main com.yasuke.ttl.world.CanonGrid [canon_map.txt]}. */
    public static void main(String[] args) throws IOException {
        Map<Character, Region> regions = new HashMap<>();
        regions.put('A', new Region("Alpha", -0.9, 0.8, null, 1.0,
                new CanonPalette(new String[] {"t:forest", "t:jungle"}, new int[] {3, 1}), false, null, null, null));
        regions.put('B', new Region("Beta", null, null, null, 1.0,
                new CanonPalette(new String[] {"t:desert"}, new int[] {1}), true, null, null, null));
        List<String> lines = new ArrayList<>();
        lines.add("# synthetic test map");
        lines.add("# origin 20 15  (cell 20,15 starts at block 0,0)");
        for (int z = 0; z < 30; z++) {
            StringBuilder row = new StringBuilder();
            for (int x = 0; x < 40; x++) row.append(z == 15 && x >= 5 && x < 35 ? '~' : x >= 28 && x < 35 && z >= 5 && z < 15 ? 'B' : x >= 5 && x < 35 && z >= 5 && z < 25 ? 'A' : '.');
            lines.add(row.toString());
        }
        CanonGrid g = parse(lines, regions, 1600, 800);
        check(g.charAt(0, 0) == '~' && g.charAt(0, -16) == 'A' && g.charAt(-16 * 20, -16 * 15) == '.', "charAt / origin");
        double inland = g.continents(0, -80, 0);
        check(inland > -0.11 && inland < CONT_MAX, "land is inland: " + inland);
        double river = g.continents(8, 8, 0);
        check(river > -0.33 && river < -0.19, "river is shallow water: " + river);
        double coastWest = g.continents(-16 * 15, -80, 0);
        check(Math.abs(coastWest - COAST) < 0.02, "coastline sits on the cell border: " + coastWest);
        double sea = g.continents(-16 * 20 - 1000, 0, 0);
        check(sea < -0.455 && sea >= CONT_MIN, "far sea is deep ocean: " + sea);
        double beyondRing = g.continents(-16 * 15 - 1600 - 800 - 50, 0, 0.37);
        check(beyondRing == 0.37, "vanilla beyond ring + blend: " + beyondRing);
        double erosion = g.climate(EROSION, 0, -80, 0.3);
        check(Math.abs(erosion - -0.9) < 0.02, "erosion knob wins inland: " + erosion);
        double veg = g.climate(VEGETATION, 0, -80, 0.3);
        check(veg == 0.3, "null knob keeps vanilla: " + veg);
        double farClimate = g.climate(TEMPERATURE, -16 * 15 - 3000, 0, 0.1);
        check(farClimate == 0.1, "vanilla climate beyond the ring: " + farClimate);
        System.out.println("synthetic: " + g.describe());
        paletteChecks(g);

        if (args.length > 0) {
            CanonGrid real = load(Path.of(args[0]), regions, 1600, 800);
            System.out.println("file: " + real.describe());
            int[] counts = new int[4];
            for (int z = 0; z < real.h; z++) {
                for (int x = 0; x < real.w; x++) {
                    double c = real.continents((x - real.originCol) * 16 + 8, (z - real.originRow) * 16 + 8, 0);
                    counts[c < -0.455 ? 0 : c < -0.19 ? 1 : c < -0.11 ? 2 : 3]++;
                }
            }
            System.out.printf("cells by band: deep ocean %d, ocean %d, coast %d, inland %d%n", counts[0], counts[1], counts[2], counts[3]);
            System.out.printf("at 0,0: '%c' continents %.3f%n", real.charAt(0, 0), real.continents(0, 0, 0));
        }
        System.out.println("canon self-check passed");
    }

    /** Palette layout: owner lookup, dithered borders, weights, patch size, determinism. */
    private static void paletteChecks(CanonGrid g) {
        long seed = 12345L;
        check(g.ownerCell(0, -80) == 'A' && g.ownerAt(0, -80, seed) == 'A', "owner inland");
        check(g.ownerCell(8, 8) == 'A', "river cell belongs to the nearest nation: " + (int) g.ownerCell(8, 8));
        check(g.ownerCell(-16 * 15 - 40, -80) == 'A', "coastal water belongs to the nation");
        check(g.ownerCell(-16 * 15 - 600, -80) == 0 && g.ownerAt(-16 * 15 - 600, -80, seed) == 0, "open sea has no owner");
        check(g.riverWeight(8, 8) > 0.5 && g.riverWeight(0, -80) == 0, "river weight");

        // The A|B border sits on the cell line x = 8 * 16 = 128; the dithered switch must not be one straight line.
        java.util.Set<Integer> switches = new java.util.HashSet<>();
        for (int z = -150; z < -20; z += 4) {
            int last = -1;
            for (int x = 40; x < 220; x += 4) {
                char c = g.ownerAt(x, z, seed);
                if (c == 'B') {
                    last = x;
                    break;
                }
            }
            check(last > 128 - 40 && last < 128 + 40, "border stays near its cell line: " + last + " at z " + z);
            switches.add(last);
        }
        check(switches.size() >= 4, "border is dithered, not a chunk line: " + switches);

        CanonPalette a = g.region('A').biomes();
        int[] counts = new int[2];
        java.util.Set<Long> patches = new java.util.HashSet<>();
        for (int z = 0; z < 200; z++)
            for (int x = 0; x < 200; x++) {
                long p = CanonPalette.patch(seed, x * 997, z * 991);
                if (patches.add(p)) counts[a.pick(CanonPalette.mix(p ^ ('A' * 0x632BE59BD9B4E019L)))]++;
            }
        double share = counts[0] / (double) (counts[0] + counts[1]);
        check(patches.size() > 1000 && Math.abs(share - 0.75) < 0.05, "weights 3:1 -> " + share + " over " + patches.size() + " patches");

        int changes = 0, len = 40000;
        long prev = CanonPalette.patch(seed, 0, 777);
        for (int x = 4; x < len; x += 4) {
            long p = CanonPalette.patch(seed, x, 777);
            if (p != prev) changes++;
            prev = p;
        }
        double run = len / (double) Math.max(1, changes);
        check(run > 150 && run < 500, "mean patch run " + run + " blocks");

        check(a.pickAt(seed, 'A', false, 1000, 2000) == a.pickAt(seed, 'A', false, 1000, 2000), "deterministic");
        int differ = 0;
        for (int i = 0; i < 64; i++) if (CanonPalette.patch(seed, i * 600, 0) != CanonPalette.patch(seed + 1, i * 600, 0)) differ++;
        check(differ > 48, "the seed changes the layout: " + differ);
        CanonPalette filtered = a.filter(id -> !id.equals("t:jungle"));
        check(filtered.size() == 1 && filtered.pick(Long.MAX_VALUE) == 0 && a.filter(id -> false) == null, "filter drops unknown ids");
        RegionTitles.Tracker t = new RegionTitles.Tracker();
        boolean shownA = false;
        for (char c : "AAA".toCharArray()) shownA |= t.observe(c);
        check(shownA && t.shown == 'A', "banner after 3 checks");
        int flips = 0;
        for (char c : "BABABAB~BABA".toCharArray()) if (t.observe(c)) flips++;
        check(flips == 0 && t.shown == 'A', "no banner spam along a border");
        check(!t.observe('B') && !t.observe('~') && !t.observe('B') && t.observe('B') && t.shown == 'B', "river ignored, then B confirmed");
        System.out.printf("palette: border switch x %s, weights %.3f, mean patch %.0f blocks%n", switches, share, run);
    }

    private static void check(boolean ok, String what) {
        if (!ok) throw new AssertionError("canon self-check failed: " + what);
    }
}
