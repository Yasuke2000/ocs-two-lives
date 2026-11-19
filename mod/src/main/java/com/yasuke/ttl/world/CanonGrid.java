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
     * choice), optionally a palette that replaces mountain peaks, the arrival banner texts (null = default) and
     * optionally {@link CanonZones} (distance rings that replace the single land palette).
     */
    public record Region(String name, Double erosion, Double temperature, Double vegetation, double strength,
                         CanonPalette biomes, boolean replacePeaks, CanonPalette peaks, String bannerTitle, String bannerSubtitle,
                         CanonZones zones) {
        public Region(String name, Double erosion, Double temperature, Double vegetation, double strength,
                      CanonPalette biomes, boolean replacePeaks, CanonPalette peaks, String bannerTitle, String bannerSubtitle) {
            this(name, erosion, temperature, vegetation, strength, biomes, replacePeaks, peaks, bannerTitle, bannerSubtitle, null);
        }

        public Region(String name, Double erosion, Double temperature, Double vegetation, double strength) {
            this(name, erosion, temperature, vegetation, strength, null, false, null, null, null, null);
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
    final Map<Character, float[]> zoneDepth = new HashMap<>(); // per nation with depth rings: blocks inside its border, per cell
    final float[][] climateWeight = new float[3][], climateValue = new float[3][]; // blurred strength, blurred strength*knob
    final double landX0, landZ0, landX1, landZ1, ring, blend;
    final Map<Character, Region> regions;
    private CanonSites sites = CanonSites.NONE; // set once by withSites, before the grid is published
    private int[] inner; // imported area {x0, z0, x1, z1} (half-open, blocks), set once by withImport; null = none

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

        for (Map.Entry<Character, Region> e : regions.entrySet()) {
            CanonZones zones = e.getValue().zones();
            if (zones == null || !zones.usesDepth()) continue;
            // Border = any cell that is neither the nation nor one of the zones' interior characters (rivers, say).
            boolean[] border = new boolean[n];
            boolean any = false;
            for (int i = 0; i < n; i++) {
                border[i] = cells[i] != e.getKey() && zones.interior().indexOf(cells[i]) < 0;
                any |= border[i];
            }
            float[] depth = new float[n];
            if (any) {
                depth = distance(border, null);
                for (int i = 0; i < n; i++) depth[i] -= 8; // cell centre to the cell edge
            } else {
                Arrays.fill(depth, 1e6f);
            }
            zoneDepth.put(e.getKey(), depth);
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

    /** Attaches the per-build sites (call before the grid is shared); returns this. */
    public CanonGrid withSites(CanonSites sites) {
        this.sites = sites == null ? CanonSites.NONE : sites;
        return this;
    }

    public CanonSites sites() {
        return sites;
    }

    /**
     * Attaches the imported area (Lerfing's map, {@code lerfing.inner} in canon_regions.json; null = none); call before
     * the grid is shared; returns this. Its chunks exist on disk, so the generator is never asked for them.
     */
    public CanonGrid withImport(int[] inner) {
        this.inner = inner == null ? null : inner.clone();
        return this;
    }

    /** True inside the imported area: the terrain and biomes there are Lerfing's stored chunks, not this grid's. */
    public boolean imported(int blockX, int blockZ) {
        return inner != null && blockX >= inner[0] && blockZ >= inner[1] && blockX < inner[2] && blockZ < inner[3];
    }

    /** The imported area {x0, z0, x1, z1} or null. */
    public int[] importBox() {
        return inner == null ? null : inner.clone();
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

    /** Blocks inside the border of a nation with depth rings, at a (dithered) point; 0 at or beyond the border. */
    public double depthBelowBorder(char owner, double x, double z) {
        float[] depth = zoneDepth.get(owner);
        if (depth == null) return 0;
        return Math.max(0, sample(depth, x / 16.0 + originCol - 0.5, z / 16.0 + originRow - 0.5, false));
    }

    /**
     * Ring of a nation's {@link CanonZones} for a block column: the index into its rings, or -1 when the nation has
     * none. {@code patchHash} is {@link CanonPalette#patch} of the same column. Allocation-free.
     */
    public int zoneAt(char owner, int blockX, int blockZ, long seed, long patchHash) {
        Region region = regions.get(owner);
        CanonZones zones = region == null ? null : region.zones();
        if (zones == null) return -1;
        double x = CanonPalette.borderX(seed, blockX, blockZ), z = CanonPalette.borderZ(seed, blockX, blockZ);
        return zones.ringFor(x, z, zones.usesDepth() ? depthBelowBorder(owner, x, z) : 0, patchHash);
    }

    /** Human-readable ring of a block column for the debug commands, or null when its nation has no zones. */
    public String zoneInfo(char owner, int blockX, int blockZ, long seed) {
        Region region = regions.get(owner);
        CanonZones zones = region == null ? null : region.zones();
        if (zones == null) return null;
        long patch = CanonPalette.patch(seed, blockX, blockZ);
        double x = CanonPalette.borderX(seed, blockX, blockZ), z = CanonPalette.borderZ(seed, blockX, blockZ);
        double depth = zones.usesDepth() ? depthBelowBorder(owner, x, z) : 0;
        int ring = zones.ringFor(x, z, depth, patch);
        return String.format("ring '%s' (%d of %d): %.0f blocks from the centre, %.0f inside the border, patch shift %+.0f of +-%.0f",
                zones.ring(ring).name(), ring + 1, zones.size(), Math.hypot(x - zones.centreX(), z - zones.centreZ()), depth, zones.jitter(patch), zones.fade());
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
        return sites.climate(CanonSites.CONTINENTS, blockX, blockZ, canonContinents(blockX, blockZ, outside));
    }

    /** Weirdness (the router's ridges): vanilla, steered only by the sites. */
    public double ridges(int blockX, int blockZ, double outside) {
        return sites.climate(CanonSites.RIDGES, blockX, blockZ, outside);
    }

    private double canonContinents(int blockX, int blockZ, double outside) {
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
        double value = canonClimate(channel, blockX, blockZ, outside);
        return channel == EROSION ? sites.climate(CanonSites.EROSION, blockX, blockZ, value) : value;
    }

    private double canonClimate(int channel, int blockX, int blockZ, double outside) {
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
        return String.format("%dx%d cells, origin %d,%d, land x %.0f..%.0f z %.0f..%.0f, ring %.0f, blend %.0f, %d sites%s",
                w, h, originCol, originRow, landX0, landX1, landZ0, landZ1, ring, blend, sites.size(),
                inner == null ? "" : String.format(", imported x %d..%d z %d..%d", inner[0], inner[2], inner[1], inner[3]));
    }

    /**
     * Self-check: {@code java -cp build/classes/java/main com.yasuke.ttl.world.CanonGrid [canon_map.txt
     * [canon_regions.json [arrival-x arrival-z [anchors.toml]]]]}. The JSON (needs Gson on the class path, like the
     * build's) also checks Jura's real zones against the real map, and the Life 2 arrival point when it is given. Both
     * formats are understood: the old generated continent (sites, Jura's depth rim) and Lerfing's imported map
     * ({@code lerfing} block, no sites, radius rings, landmarks with {@code at}, the anchors file of gen_data).
     */
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
        zoneChecks();
        siteChecks();
        lerfingSynthetic();
        if (args.length > 1) {
            int[] arrival = args.length > 3 ? new int[] {Integer.parseInt(args[2]), Integer.parseInt(args[3])} : null;
            realZoneChecks(args[0], args[1], arrival, args.length > 4 ? args[4] : null);
        }
        System.out.println("canon self-check passed");
    }

    /** Synthetic zoned nation Z: a 35x40-chunk block (x -320..+240, z +-320) with core radius 80, rim depth 90, fade 30. */
    private static void zoneChecks() {
        CanonPalette core = new CanonPalette(new String[] {"t:core"}, new int[] {1});
        CanonPalette rim = new CanonPalette(new String[] {"t:rim"}, new int[] {1});
        CanonPalette middle = new CanonPalette(new String[] {"t:middle"}, new int[] {1});
        CanonZones zones = new CanonZones(0, 0, 30, "~", new CanonZones.Ring[] {
                new CanonZones.Ring("core", 80, 0, core), new CanonZones.Ring("rim", 0, 90, rim), new CanonZones.Ring("middle", 0, 0, middle)});
        Map<Character, Region> regions = new HashMap<>();
        regions.put('Z', new Region("Zeta", null, null, null, 1.0, middle, false, null, null, null, zones));
        regions.put('A', new Region("Alpha", null, null, null, 1.0, middle, false, null, null, null));
        List<String> lines = new ArrayList<>();
        lines.add("# origin 25 25");
        for (int z = 0; z < 50; z++) {
            StringBuilder row = new StringBuilder();
            for (int x = 0; x < 50; x++) row.append(x >= 5 && x < 45 && z >= 5 && z < 45 ? (x >= 40 ? 'A' : 'Z') : '.');
            lines.add(row.toString());
        }
        CanonGrid g = parse(lines, regions, 1600, 800);
        check(g.zoneAt('A', 0, 0, 1, 1) == -1 && g.zoneAt('?', 0, 0, 1, 1) == -1, "no zones, no ring");
        // Z spans x -320..+240 (A takes x >= 240), so its border is 240 blocks east of the centre at the A side too.
        double centreDepth = g.depthBelowBorder('Z', 0, 0);
        check(Math.abs(centreDepth - 240) < 1, "depth at the centre: " + centreDepth);
        int[] fringe = new int[3];
        for (long seed = 1; seed <= 300; seed++) {
            for (int k = 0; k < 6; k++) {
                int dz = -250 + 83 * k + (int) (seed % 7);
                check(g.zoneAt('Z', 0, 0, seed, CanonPalette.patch(seed, 0, 0)) == 0, "the centre is core (seed " + seed + ")");
                // r 150 > 80 + fade + dither, depth 170 - fade - dither > 90: middle for every patch.
                check(g.zoneAt('Z', -150, 0, seed, CanonPalette.patch(seed, -150, 0)) == 2, "outside the core, deep: middle (seed " + seed + ")");
                // depth 30 + fade + dither < 90: rim for every patch.
                check(g.zoneAt('Z', -290, dz % 100, seed, CanonPalette.patch(seed, -290, dz % 100)) == 1, "at the border: rim (seed " + seed + ")");
                fringe[g.zoneAt('Z', -230, dz % 100, seed, CanonPalette.patch(seed, -230, dz % 100))]++; // depth ~90: the fringe
            }
        }
        check(fringe[1] > 300 && fringe[2] > 300 && fringe[0] == 0, "the rim edge is a ragged fringe, not a line: " + java.util.Arrays.toString(fringe));
        long p = CanonPalette.patch(7, -150, 5);
        check(g.zoneAt('Z', -150, 5, 7, p) == g.zoneAt('Z', -150, 5, 7, p), "deterministic");
        String info = g.zoneInfo('Z', -290, 0, 7);
        check(info != null && info.startsWith("ring 'rim' (2 of 3)") && g.zoneInfo('A', 0, 0, 7) == null, "debug text: " + info);
        System.out.printf("zones: at depth ~90 the rim and the middle mix %s (core, rim, middle) over 1800 samples%n", java.util.Arrays.toString(fringe));
        try {
            new CanonZones(0, 0, 10, "~", new CanonZones.Ring[] {new CanonZones.Ring("a", 0, 0, rim), new CanonZones.Ring("b", 0, 0, rim)});
            check(false, "a ring without a test in front of the last one must be rejected");
        } catch (IllegalArgumentException expected) {
            // fine
        }
    }

    /** Jura's real rings on the real map: safe rim along the whole border, core at Tempest, arrival point safe. */
    private static void realZoneChecks(String mapFile, String regionsFile, int[] arrival, String anchorsFile) throws IOException {
        com.google.gson.JsonObject json = com.google.gson.JsonParser.parseString(Files.readString(Path.of(regionsFile), StandardCharsets.UTF_8)).getAsJsonObject();
        List<String> warnings = new ArrayList<>();
        Map<Character, Region> real = CanonConfig.regions(json, warnings::add);
        check(warnings.isEmpty(), "canon_regions.json parses cleanly: " + warnings);
        CanonGrid g = load(Path.of(mapFile), real, json.get("ring").getAsDouble(), json.get("blend").getAsDouble());
        if (json.has("lerfing")) {
            lerfingChecks(json, g, arrival, anchorsFile == null ? null : Files.readAllLines(Path.of(anchorsFile), StandardCharsets.UTF_8));
            return;
        }
        check(anchorsFile == null, "an anchors file is only checked against the Lerfing grid");
        Region j = g.region('J');
        check(j != null && j.zones() != null, "J has zones");
        CanonZones zones = j.zones();
        double rimDepth = zones.ring(1).depth(), coreRadius = zones.ring(0).radius(), fade = zones.fade();
        double sure = rimDepth - fade - 2 * CanonPalette.BORDER_WARP - 2 * CanonPalette.BORDER_FINE; // depth that is rim for every patch
        long seed = 99L;
        check(g.ownerAt(0, 0, seed) == 'J', "Tempest is in J");
        for (long s = 1; s <= 200; s++) check(g.zoneAt('J', 0, 0, s, CanonPalette.patch(s, 0, 0)) == 0, "Tempest is core (seed " + s + ")");

        int dirs = 72, measured = 0;
        double[] rimThickness = new double[dirs], middleThickness = new double[dirs];
        for (int k = 0; k < dirs; k++) {
            double a = 2 * Math.PI * k / dirs, dx = Math.cos(a), dz = Math.sin(a);
            double rimStart = -1, edge = -1;
            for (double r = 0; r < 6000; r += 8) {
                double x = r * dx, z = r * dz;
                char c = g.charAt((int) Math.floor(x), (int) Math.floor(z));
                if (c != 'J' && c != '~' && c != 'W') {
                    edge = r;
                    break;
                }
                if (rimStart < 0 && g.depthBelowBorder('J', x, z) < rimDepth) rimStart = r;
            }
            if (edge < 0 || rimStart < 0) continue; // the ray meets no border within 6000 blocks
            rimThickness[measured] = edge - rimStart;
            middleThickness[measured] = rimStart - coreRadius;
            measured++;
        }
        double[] rt = java.util.Arrays.copyOf(rimThickness, measured), mt = java.util.Arrays.copyOf(middleThickness, measured);
        java.util.Arrays.sort(rt);
        java.util.Arrays.sort(mt);
        System.out.printf("jura rings (%d rays from Tempest, nominal): rim along the ray min %.0f median %.0f p90 %.0f; dark middle min %.0f median %.0f max %.0f blocks%n",
                measured, rt[0], rt[measured / 2], rt[measured * 9 / 10], mt[0], mt[measured / 2], mt[measured - 1]);
        check(rt[0] >= rimDepth - 16, "the rim is at least its depth wide along every ray: " + rt[0]);
        check(mt[0] >= 100, "a dark middle of at least 100 blocks on every side: " + mt[0]);

        int checked = 0;
        for (int z = -3000; z < 3000; z += 53) {
            for (int x = -3000; x < 3000; x += 59) {
                if (g.ownerCell(x, z) != 'J' || Math.hypot(x, z) <= coreRadius + fade + 60 || g.depthBelowBorder('J', x, z) > sure) continue;
                for (long s = 1; s <= 20; s++) check(g.zoneAt('J', x, z, s, CanonPalette.patch(s, x, z)) == 1, "the outer band is rim at " + x + "," + z);
                checked++;
            }
        }
        check(checked > 500, "enough border columns sampled: " + checked);
        System.out.println("jura: " + checked + " sampled columns within " + (int) sure + " blocks of the border are rim for every patch");

        if (arrival != null) {
            int x = arrival[0], z = arrival[1];
            check(g.ownerCell(x, z) == 'J', "arrival is in Jura");
            for (int dz = -128; dz <= 128; dz += 16)
                for (int dx = -128; dx <= 128; dx += 16)
                    check("~.W".indexOf(g.charAt(x + dx, z + dz)) < 0, "no water within 128 blocks of the arrival: '" + g.charAt(x + dx, z + dz) + "' at " + (x + dx) + "," + (z + dz));
            double depth = g.depthBelowBorder('J', x, z);
            check(depth + 68 <= sure, "the arrival and 48 blocks around it are inside the guaranteed rim band: depth " + depth + " (limit " + (sure - 68) + ")");
            for (long s = 1; s <= 500; s++)
                for (int dz = -48; dz <= 48; dz += 16)
                    for (int dx = -48; dx <= 48; dx += 16)
                        check(g.zoneAt('J', x + dx, z + dz, s, CanonPalette.patch(s, x + dx, z + dz)) == 1, "rim around the arrival (seed " + s + ")");
            System.out.printf("arrival %d,%d: Jura, %.0f blocks inside the border, %.0f from Tempest, rim for 500 seeds within 48 blocks%n", x, z, depth, Math.hypot(x, z));
        }
        realSiteChecks(json, g, arrival);
    }

    /** Synthetic sites on a synthetic map: byte-identical outside, organic edges, flat ground, climate presets, config. */
    private static void siteChecks() {
        Map<Character, Region> regions = new HashMap<>();
        regions.put('A', new Region("Alpha", -0.5, 0.2, 0.1, 1.0, new CanonPalette(new String[] {"t:forest"}, new int[] {1}), false, null, null, null));
        List<String> lines = new ArrayList<>();
        lines.add("# origin 40 40");
        for (int z = 0; z < 80; z++) lines.add((z < 4 || z >= 76) ? ".".repeat(80) : "...." + "A".repeat(72) + "....");
        CanonPalette plains = new CanonPalette(new String[] {"t:plains"}, new int[] {1});
        CanonSites.Site flat = CanonSites.Site.of("town", 0, 0, 80, 60, plains, CanonSites.Terrain.FLAT, 72, null, null, null);
        CanonSites.Site peak = CanonSites.Site.of("peak", 300, 0, 60, 100, null, CanonSites.Terrain.MOUNTAIN, null, null, null, null);
        CanonSites.Site marsh = CanonSites.Site.of("marsh", -300, 0, 50, 40, plains, CanonSites.Terrain.KEEP, null, null, null, null);
        CanonSites sites = new CanonSites(new CanonSites.Site[] {flat, peak, marsh});
        CanonGrid plain = parse(lines, regions, 1600, 800), sited = parse(lines, regions, 1600, 800).withSites(sites);
        check(plain.sites().isEmpty() && sited.sites().size() == 3, "sites attached");

        // Outside every reach the grid is the same to the bit; inside it is not.
        int same = 0;
        for (int z = -600; z <= 600; z += 37)
            for (int x = -600; x <= 600; x += 41) {
                boolean far = true;
                for (int i = 0; i < 3; i++) far &= Math.hypot(x - sites.site(i).x(), z - sites.site(i).z()) > sites.site(i).reach();
                if (!far) continue;
                double o = (x * 31 + z * 17) % 100 / 100.0;
                check(Double.doubleToRawLongBits(plain.continents(x, z, o)) == Double.doubleToRawLongBits(sited.continents(x, z, o))
                        && Double.doubleToRawLongBits(plain.climate(EROSION, x, z, o)) == Double.doubleToRawLongBits(sited.climate(EROSION, x, z, o))
                        && Double.doubleToRawLongBits(plain.climate(TEMPERATURE, x, z, o)) == Double.doubleToRawLongBits(sited.climate(TEMPERATURE, x, z, o))
                        && Double.doubleToRawLongBits(sited.ridges(x, z, o)) == Double.doubleToRawLongBits(o), "byte-identical outside the sites at " + x + "," + z);
                double[] f = {9, 9};
                sites.flat(x, z, f);
                check(f[0] == 0 && sites.biomeSite(x, z) == -1, "no flat pull and no site biome outside at " + x + "," + z);
                same++;
            }
        check(same > 500, "enough columns outside the sites: " + same);

        // Mountain: climate pulled to its preset at the centre; keep sites and temperature untouched.
        check(Math.abs(sited.continents(300, 0, 0.1) - 0.75) < 1e-9 && Math.abs(sited.climate(EROSION, 300, 0, 0.3) - -0.9) < 1e-9
                && Math.abs(sited.ridges(300, 0, -0.4) - 0.62) < 1e-9, "mountain preset at its centre");
        check(sited.climate(EROSION, -300, 0, 0.3) == plain.climate(EROSION, -300, 0, 0.3), "a keep site leaves the climate alone");
        check(sited.climate(TEMPERATURE, 300, 0, 0.3) == plain.climate(TEMPERATURE, 300, 0, 0.3), "sites never touch temperature");

        // Biome edges: inside the radius always the site, beyond the reach never; the edge is ragged, not a circle.
        java.util.Set<Integer> edges = new java.util.HashSet<>();
        int inside = (int) Math.floor(80 - CanonPalette.BORDER_WARP - CanonPalette.BORDER_FINE - (CanonSites.WOBBLE + CanonSites.WOBBLE_FINE) * 60 - 1);
        for (int k = 0; k < 64; k++) {
            double a = 2 * Math.PI * k / 64, dx = Math.cos(a), dz = Math.sin(a);
            check(sites.biomeSite((int) Math.round(dx * inside), (int) Math.round(dz * inside)) == 0, "the site's own biome well inside (angle " + k + ")");
            int edge = -1;
            for (int r = inside; r < 400; r++) {
                if (sites.biomeSite((int) Math.round(dx * r), (int) Math.round(dz * r)) != 0) {
                    edge = r;
                    break;
                }
            }
            check(edge > 0 && edge < flat.reach(), "the biome edge lies inside the reach: " + edge);
            edges.add(edge / 4);
        }
        check(edges.size() >= 6, "the biome edge is ragged, not a circle: " + edges);
        check(sites.biomeSite(300, 0) == -1, "a site without biomes leaves the nation's");
        check(sites.biomeSite(-300, 0) == 2, "keep site biomes");

        // Flat ground: full pull inside the radius, the surface exactly at the ground, solid underneath.
        double[] f = new double[2];
        sites.flat(5, 5, f);
        check(f[0] == 1 && f[1] == 72, "full flat pull near the centre: " + java.util.Arrays.toString(f));
        for (double v : new double[] {-2, -0.3, 0, 0.4, 3}) {
            check(CanonSites.flatten(v, 0, 1, 72, 71) > 0 && CanonSites.flatten(v, 0, 1, 72, 72) < 0, "final density surface at y 72 for " + v);
            check(CanonSites.flatten(v, 0.390625, 1, 72, 71) > 0.390625 && CanonSites.flatten(v, 0.390625, 1, 72, 72) < 0.390625, "preliminary surface at y 72 for " + v);
            for (int y = -64; y < 72; y += 7)
                check(CanonSites.flatten(v, 0, 1, 72, y) > 0, "solid all the way down at full weight (raised ground never floats) for " + v + " at y " + y);
            for (int y = 72; y < 320; y += 7) check(CanonSites.flatten(v, 0, 1, 72, y) < 0, "open sky above the ground for " + v + " at y " + y);
            check(CanonSites.flatten(v, 0, 0, 72, 90) == v, "weight 0 changes nothing");
        }
        double half = CanonSites.flatten(1.0, 0, 0.5, 72, 100);
        check(half < 1.0 && half > -1.0, "half weight blends: " + half);
        for (int r = 0; r < 400; r += 4) {
            double w = sites.weight(0, r, 0);
            check(w >= 0 && w <= 1, "weight in 0..1");
        }
        check(sites.weight(0, 0, 0) == 1 && sites.weight(0, 400, 0) == 0, "weight 1 at the centre, 0 beyond the reach");
        long a1 = Double.doubleToRawLongBits(sites.weight(0, 97, -33)), a2 = Double.doubleToRawLongBits(new CanonSites(new CanonSites.Site[] {flat}).weight(0, 97, -33));
        check(a1 == a2, "deterministic, independent of the other sites");
        check(sites.describe(0, 0).startsWith("site 'town' (flat y72)") && sites.describe(5000, 5000) == null, "debug text: " + sites.describe(0, 0));

        // Config: malformed sites are skipped with a warning, the rest load.
        com.google.gson.JsonObject json = com.google.gson.JsonParser.parseString("""
                {"sites": [
                  {"name": "a", "centre": [0, 0], "radius": 50, "fade": 20, "terrain": "flat", "ground": 70},
                  {"name": "a", "centre": [9, 9], "radius": 50, "terrain": "flat"},
                  {"name": "b", "centre": [0, 0], "radius": 50, "terrain": "volcano"},
                  {"name": "c", "centre": [0, 0], "radius": 50},
                  {"name": "d", "centre": [0, 0], "radius": 30, "terrain": "lowland", "erosion": 0.2, "biomes": [["t:x", 2]]}
                ]}""").getAsJsonObject();
        List<String> warnings = new ArrayList<>();
        CanonSites parsed = CanonConfig.sites(json, warnings::add);
        check(parsed.size() == 2 && warnings.size() == 3, "sites parse: " + parsed + " " + warnings);
        check(parsed.site(1).climate()[CanonSites.EROSION] == 0.2 && parsed.site(1).climate()[CanonSites.CONTINENTS] == null, "explicit knob over preset");
        check(CanonConfig.sites(new com.google.gson.JsonObject(), warnings::add).isEmpty(), "no sites key, no sites");
        System.out.printf("sites: %d synthetic columns outside are byte-identical; biome edge spread over %d 4-block buckets%n", same, edges.size());
    }

    /** The real sites: parse cleanly, sane values, and the Life 2 arrival keeps a safe biome. */
    private static void realSiteChecks(com.google.gson.JsonObject json, CanonGrid g, int[] arrival) {
        List<String> warnings = new ArrayList<>();
        CanonSites sites = CanonConfig.sites(json, warnings::add);
        check(warnings.isEmpty(), "sites parse cleanly: " + warnings);
        check(sites.size() > 0 && json.getAsJsonArray("sites").size() == sites.size(), "every site loads");
        g.withSites(sites);
        int flats = 0;
        for (int i = 0; i < sites.size(); i++) {
            CanonSites.Site s = sites.site(i);
            if (s.flat()) {
                flats++;
                check(s.ground() >= 64 && s.ground() <= 240, "site " + s.name() + ": ground " + s.ground() + " must be 64..240 (no sea floods it)");
            }
            check(g.ownerCell((int) s.x(), (int) s.z()) != 0, "site " + s.name() + " stands on canon land");
            check(sites.weight(i, (int) s.x(), (int) s.z()) == 1, "site " + s.name() + ": full weight at its centre");
        }
        if (arrival != null) {
            for (int dz = -48; dz <= 48; dz += 8)
                for (int dx = -48; dx <= 48; dx += 8) {
                    int i = sites.biomeSite(arrival[0] + dx, arrival[1] + dz);
                    if (i < 0) continue;
                    for (String id : sites.site(i).biomes().ids())
                        check(id.startsWith("minecraft:") && !id.contains("dark_forest"), "the arrival keeps a safe biome: site " + sites.site(i).name() + " brings " + id);
                }
        }
        System.out.printf("real sites: %d (%d flat) parse cleanly; the arrival area has only safe site biomes%n", sites.size(), flats);
    }

    /**
     * Lerfing's map (design/architecture/lerfing-import.md): the grid is his land mask over the imported inner tiles,
     * nothing of ours generates inside, the generated ring round it is deep ocean at the seam and blends into vanilla
     * beyond; no sites; Jura's rings are radius rings round Tempest (the import tool paints them; the grid keeps the
     * geometry for /ttlregion and this check); every landmark ({@code at}) and anchor lies on the continent.
     */
    private static void lerfingChecks(com.google.gson.JsonObject json, CanonGrid g, int[] arrival, List<String> anchors) {
        List<String> warnings = new ArrayList<>();
        int[] box = CanonConfig.importBox(json, warnings::add);
        check(warnings.isEmpty() && box != null, "lerfing.inner parses: " + warnings);
        g.withImport(box);
        CanonSites sites = CanonConfig.sites(json, warnings::add);
        check(warnings.isEmpty() && sites.isEmpty(), "the Lerfing grid has no sites (nothing of ours generates under a build): " + sites + " " + warnings);
        for (String gone : List.of("reference", "width", "paint_width", "origin", "paint", "seeds"))
            check(!json.has(gone), "'" + gone + "' belongs to the old traced plate, not the Lerfing grid");

        // The grid covers the imported area; the seam is open, deep, canon-weighted sea.
        int gx0 = -g.originCol * 16, gz0 = -g.originRow * 16, gx1 = (g.w - g.originCol) * 16, gz1 = (g.h - g.originRow) * 16;
        check(gx0 <= box[0] && gz0 <= box[1] && gx1 >= box[2] && gz1 >= box[3], "the grid (x " + gx0 + ".." + gx1 + ", z " + gz0 + ".." + gz1
                + ") covers the imported area " + Arrays.toString(box));
        check(g.landX0 > box[0] && g.landZ0 > box[1] && g.landX1 < box[2] && g.landZ1 < box[3], "all land lies inside the imported area");
        check(g.imported(box[0], box[1]) && !g.imported(box[2], box[3]) && !g.imported(box[0] - 1, box[1]), "imported() is the half-open box");
        int seam = 0;
        double worst = -2;
        for (int k = 0; k < 4; k++) {
            boolean alongX = k < 2;
            int fixed = k == 0 ? box[1] - 1 : k == 1 ? box[3] : k == 2 ? box[0] - 1 : box[2];
            for (int t = alongX ? box[0] : box[1]; t < (alongX ? box[2] : box[3]); t += 64) {
                int x = alongX ? t : fixed, z = alongX ? fixed : t;
                check(g.charAt(x, z) == '.' && g.ownerCell(x, z) == 0, "open sea just outside the import at " + x + "," + z);
                check(g.canonWeight(x, z) == 1, "the full canon ring (not yet vanilla) at the seam " + x + "," + z);
                double c = g.continents(x, z, 0);
                worst = Math.max(worst, c);
                check(c < -0.455, "deep ocean is generated at the seam " + x + "," + z + ": " + c);
                seam++;
            }
        }
        double far = g.ring + g.blend + 16;
        check(g.canonWeight(g.landX1 + far, 0) == 0 && g.continents((int) (g.landX1 + far), 0, 0.37) == 0.37, "vanilla beyond ring + blend");
        System.out.printf("lerfing: imported x %d..%d z %d..%d, land x %.0f..%.0f z %.0f..%.0f; %d seam points deep ocean (worst %.3f); vanilla from %.0f blocks beyond the land bbox%n",
                box[0], box[2], box[1], box[3], g.landX0, g.landX1, g.landZ0, g.landZ1, seam, worst, g.ring + g.blend);

        // Jura: radius rings round Tempest, the core deadly at Tempest, the arrival in the safe outer ring.
        Region j = g.region('J');
        check(j != null && j.zones() != null && !j.zones().usesDepth() && j.zones().size() >= 2, "J has radius-only zones");
        CanonZones zones = j.zones();
        double cx = zones.centreX(), cz = zones.centreZ(), dither = zones.fade() + (CanonPalette.BORDER_WARP + CanonPalette.BORDER_FINE) * Math.sqrt(2) + 2;
        check(g.ownerCell((int) cx, (int) cz) == 'J' && "~.".indexOf(g.charAt((int) cx, (int) cz)) < 0, "Tempest (zones centre " + cx + "," + cz + ") stands on Jura land");
        for (long s = 1; s <= 200; s++) check(g.zoneAt('J', (int) cx, (int) cz, s, CanonPalette.patch(s, (int) cx, (int) cz)) == 0, "Tempest is core (seed " + s + ")");
        int last = zones.size() - 1, sampled = 0;
        for (int k = 0; k < 72; k++) {
            double a = 2 * Math.PI * k / 72;
            for (int i = 0; i < last; i++) {
                double inner = i == 0 ? 0 : zones.ring(i - 1).radius() + dither, outer = zones.ring(i).radius() - dither;
                if (outer <= inner) continue;
                double r = (inner + outer) / 2;
                int x = (int) Math.round(cx + r * Math.cos(a)), z = (int) Math.round(cz + r * Math.sin(a));
                for (long s = 1; s <= 20; s++) check(g.zoneAt('J', x, z, s, CanonPalette.patch(s, x, z)) == i, "ring " + zones.ring(i).name() + " at r " + (int) r + " (" + x + "," + z + ")");
                sampled++;
            }
            double r = zones.ring(last - 1).radius() + dither + 8;
            int x = (int) Math.round(cx + r * Math.cos(a)), z = (int) Math.round(cz + r * Math.sin(a));
            for (long s = 1; s <= 20; s++) check(g.zoneAt('J', x, z, s, CanonPalette.patch(s, x, z)) == last, "outer ring " + zones.ring(last).name() + " at " + x + "," + z);
            sampled++;
        }
        StringBuilder rings = new StringBuilder();
        for (int i = 0; i < zones.size(); i++) rings.append(i == 0 ? "" : ", ").append(zones.ring(i).name()).append(i < last ? " r" + (int) zones.ring(i).radius() : "");
        System.out.printf("jura: rings %s round %.0f,%.0f; %d ring samples x 20 seeds land in their ring%n", rings, cx, cz, sampled);
        if (arrival != null) {
            int x = arrival[0], z = arrival[1];
            check(g.imported(x, z), "the arrival lies on the imported map");
            check(g.ownerCell(x, z) == 'J' && "~.".indexOf(g.charAt(x, z)) < 0, "the arrival stands on Jura land: '" + g.charAt(x, z) + "'");
            for (long s = 1; s <= 500; s++)
                for (int dz = -48; dz <= 48; dz += 16)
                    for (int dx = -48; dx <= 48; dx += 16)
                        check(g.zoneAt('J', x + dx, z + dz, s, CanonPalette.patch(s, x + dx, z + dz)) == last, "the safe outer ring round the arrival (seed " + s + ")");
            System.out.printf("arrival %d,%d: Jura land, %.0f blocks from Tempest, outer ring for 500 seeds within 48 blocks%n", x, z, Math.hypot(x - cx, z - cz));
        }

        // Landmarks carry world coordinates; anchors (gen_data) likewise; both lie on the continent.
        int marks = 0, onWater = 0;
        com.google.gson.JsonArray landmarks = json.has("landmarks") ? json.getAsJsonArray("landmarks") : new com.google.gson.JsonArray();
        for (com.google.gson.JsonElement e : landmarks) {
            com.google.gson.JsonObject m = e.getAsJsonObject();
            String name = m.has("name") ? m.get("name").getAsString() : "?";
            check(m.has("at") && !m.has("ref"), "landmark " + name + " has 'at' [x, z] (not the old 'ref')");
            int x = m.getAsJsonArray("at").get(0).getAsInt(), z = m.getAsJsonArray("at").get(1).getAsInt();
            check(g.imported(x, z) && g.ownerCell(x, z) != 0, "landmark " + name + " at " + x + "," + z + " lies on the continent ('" + g.charAt(x, z) + "')");
            if ("~.".indexOf(g.charAt(x, z)) >= 0) onWater++;
            marks++;
        }
        int anchorCount = 0;
        if (anchors != null) {
            Map<String, int[]> points = anchorPoints(anchors);
            check(!points.isEmpty(), "the anchors file holds anchors (x/z keys, [x, z] or {x, z})");
            for (Map.Entry<String, int[]> e : points.entrySet()) {
                int x = e.getValue()[0], z = e.getValue()[1];
                check(g.imported(x, z) && g.ownerCell(x, z) != 0, "anchor " + e.getKey() + " at " + x + "," + z + " lies on the continent ('" + g.charAt(x, z) + "')");
                if ("~.".indexOf(g.charAt(x, z)) >= 0) onWater++;
                anchorCount++;
            }
        }
        System.out.printf("lerfing: %d landmarks and %d anchors on the continent (%d of them on lake/river/coastal water cells)%n", marks, anchorCount, onWater);
    }

    private static final java.util.regex.Pattern TOML_PAIR = java.util.regex.Pattern.compile(
            "^([A-Za-z0-9_.\"-]+)\\s*=\\s*\\[\\s*(-?\\d+(?:\\.\\d+)?)\\s*,\\s*(-?\\d+(?:\\.\\d+)?)\\s*\\]");
    private static final java.util.regex.Pattern TOML_INLINE = java.util.regex.Pattern.compile("^([A-Za-z0-9_.\"-]+)\\s*=\\s*\\{(.*)\\}");
    private static final java.util.regex.Pattern TOML_XZ = java.util.regex.Pattern.compile("(?:^|[\\s,{])([xz])\\s*=\\s*(-?\\d+(?:\\.\\d+)?)");

    /**
     * Points of a small TOML file (the anchor table gen_data writes): a {@code [table]} with {@code x} and {@code z}
     * keys, {@code name = [x, z]} or {@code name = { x = .., z = .. }}; everything else is ignored. Keys are
     * "table" or "table.name".
     */
    static Map<String, int[]> anchorPoints(List<String> lines) {
        Map<String, int[]> out = new java.util.LinkedHashMap<>();
        String table = "";
        Double tx = null, tz = null;
        for (String raw : lines) {
            String line = raw.replaceAll("#.*$", "").strip();
            if (line.isEmpty()) continue;
            if (line.startsWith("[")) {
                if (tx != null && tz != null) out.put(table, new int[] {(int) Math.round(tx), (int) Math.round(tz)});
                table = line.replaceAll("^\\[+|\\]+$", "").strip();
                tx = tz = null;
                continue;
            }
            String prefix = table.isEmpty() ? "" : table + ".";
            java.util.regex.Matcher m = TOML_PAIR.matcher(line);
            if (m.find()) {
                out.put(prefix + m.group(1).replace("\"", ""), new int[] {(int) Math.round(Double.parseDouble(m.group(2))), (int) Math.round(Double.parseDouble(m.group(3)))});
                continue;
            }
            m = TOML_INLINE.matcher(line);
            if (m.find()) {
                Double ix = null, iz = null;
                java.util.regex.Matcher k = TOML_XZ.matcher(m.group(2));
                while (k.find()) {
                    if (k.group(1).equals("x")) ix = Double.parseDouble(k.group(2));
                    else iz = Double.parseDouble(k.group(2));
                }
                if (ix != null && iz != null) out.put(prefix + m.group(1).replace("\"", ""), new int[] {(int) Math.round(ix), (int) Math.round(iz)});
                continue;
            }
            java.util.regex.Matcher k = TOML_XZ.matcher(line);
            if (k.find() && k.start(1) == 0) {
                if (k.group(1).equals("x")) tx = Double.parseDouble(k.group(2));
                else tz = Double.parseDouble(k.group(2));
            }
        }
        if (tx != null && tz != null) out.put(table, new int[] {(int) Math.round(tx), (int) Math.round(tz)});
        return out;
    }

    /** The Lerfing checks on synthetic data in the new canon_regions.json format (no files needed). */
    private static void lerfingSynthetic() {
        com.google.gson.JsonObject json = com.google.gson.JsonParser.parseString("""
                {"_doc": "synthetic Lerfing-format test data",
                 "ring": 1000, "blend": 400,
                 "lerfing": {"inner": [-1120, -880, 1120, 880], "polygons": {"J": [[-320, -400], [640, -400], [640, 400], [-320, 400]]}},
                 "regions": {
                   "J": {"name": "Jura", "colour": "#2e7d32", "zones": {"centre": [200, 0], "fade": 30, "interior": "~", "rings": [
                     {"name": "core", "radius": 100, "biomes": [["tensura:ancient_forest", 1]]},
                     {"name": "band", "radius": 300, "biomes": [["minecraft:dark_forest", 1]]},
                     {"name": "rim", "biomes": [["minecraft:plains", 1]]}]}},
                   "R": {"name": "Blumund", "colour": "#1565c0"}},
                 "landmarks": [
                   {"name": "Tempest", "kind": "capital", "at": [200, 0]},
                   {"name": "Lake", "kind": "lake", "at": [350, -200]},
                   {"name": "Londo", "kind": "capital", "at": [-500, 100]}]}
                """).getAsJsonObject();
        List<String> warnings = new ArrayList<>();
        Map<Character, Region> regions = CanonConfig.regions(json, warnings::add);
        check(warnings.isEmpty() && CanonConfig.sites(json, warnings::add).isEmpty(), "new format parses without sites: " + warnings);
        check(Arrays.equals(CanonConfig.importBox(json, warnings::add), new int[] {-1120, -880, 1120, 880}), "import box");
        List<String> bad = new ArrayList<>();
        check(CanonConfig.importBox(com.google.gson.JsonParser.parseString("{\"lerfing\": {\"inner\": [1, 2, 0, 9]}}").getAsJsonObject(), bad::add) == null && bad.size() == 1,
                "a malformed box is ignored with a warning");
        check(CanonConfig.importBox(new com.google.gson.JsonObject(), bad::add) == null && bad.size() == 1, "no lerfing block, no box, no warning");
        // 140 x 110 chunks, origin 70 55 (blocks x -1120..1120, z -880..880); land x -640..640, z -400..400 (R west
        // of x -320, J east of it), a lake at x 320..384, z -240..-176.
        List<String> lines = new ArrayList<>();
        lines.add("# origin 70 55");
        for (int z = 0; z < 110; z++) {
            StringBuilder row = new StringBuilder();
            for (int x = 0; x < 140; x++) {
                boolean land = x >= 30 && x < 110 && z >= 30 && z < 80;
                row.append(!land ? '.' : x >= 90 && x < 94 && z >= 40 && z < 44 ? '~' : x < 50 ? 'R' : 'J');
            }
            lines.add(row.toString());
        }
        CanonGrid g = parse(lines, regions, json.get("ring").getAsDouble(), json.get("blend").getAsDouble());
        check(!g.imported(0, 0), "no import box before withImport");
        lerfingChecks(json, g, new int[] {-250, 300}, List.of(
                "# generated", "[tempest]", "x = 200", "z = 0", "[dwargon]", "x = 400", "z = -350",
                "[builds]", "londo = [-500, 100]", "lake_camp = { x = 360, z = -210, survey = 64 }"));
        Map<String, int[]> points = anchorPoints(List.of("[a]", "x = 1", "z = -2", "[b]", "c = [3, 4]", "d = {x = 5, z = 6}", "e = 7", "[f]", "x = 9"));
        check(points.size() == 3 && points.get("a")[1] == -2 && points.get("b.c")[0] == 3 && points.get("b.d")[1] == 6 && !points.containsKey("f"), "anchors parser: " + points.keySet());
        com.google.gson.JsonObject withSites = json.deepCopy();
        withSites.add("sites", com.google.gson.JsonParser.parseString("[{\"name\": \"x\", \"centre\": [0, 0], \"radius\": 50, \"terrain\": \"flat\"}]"));
        try {
            lerfingChecks(withSites, parse(lines, regions, 1000, 400), null, null);
            throw new IllegalStateException("sites in the Lerfing format must fail the check");
        } catch (AssertionError expected) {
            check(expected.getMessage().contains("no sites"), "sites rejected: " + expected.getMessage());
        }
        System.out.println("lerfing synthetic: the new canon_regions.json format passes (and sites in it are rejected)");
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
