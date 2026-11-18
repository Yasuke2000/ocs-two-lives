package com.yasuke.ttl.world;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Predicate;

/**
 * A nation's weighted biome palette from canon_regions.json, plus the deterministic noise that lays it out as
 * patches. Pure Java (no Minecraft types) so {@link CanonGrid#main} can check it; ids stay strings here and
 * {@link CanonBiomes} keeps a holder array parallel to {@link #ids()}.
 */
public final class CanonPalette {
    /** Mean patch spacing in blocks (jittered grid), and the domain warp that keeps patch edges organic. */
    static final double PATCH = 288, PATCH_WARP = 72, PATCH_WARP_SCALE = 224;
    /** Border dither: two octaves of warp (amplitude, scale in blocks) applied before the grid lookup. */
    static final double BORDER_WARP = 20, BORDER_SCALE = 80, BORDER_FINE = 6, BORDER_FINE_SCALE = 20;

    private static final long SALT_PATCH_X = 0x5DEECE66DL, SALT_PATCH_Z = 0x2545F4914F6CDD1DL, SALT_CELLS = 0x9E3779B97F4A7C15L;
    private static final long SALT_BORDER_X = 0xC2B2AE3D27D4EB4FL, SALT_BORDER_Z = 0x165667B19E3779F9L;
    private static final long SALT_FINE_X = 0x27D4EB2F165667C5L, SALT_FINE_Z = 0xFF51AFD7ED558CCDL;
    static final long SALT_PEAKS = 0xC4CEB9FE1A85EC53L;

    private final String[] ids;
    private final int[] cumulative;
    private final int total;

    public CanonPalette(String[] ids, int[] weights) {
        if (ids.length != weights.length || ids.length == 0) throw new IllegalArgumentException("empty palette");
        this.ids = ids.clone();
        this.cumulative = new int[weights.length];
        int sum = 0;
        for (int i = 0; i < weights.length; i++) {
            if (weights[i] <= 0) throw new IllegalArgumentException("weight must be > 0: " + ids[i]);
            sum += weights[i];
            cumulative[i] = sum;
        }
        this.total = sum;
    }

    public String[] ids() {
        return ids.clone();
    }

    public int size() {
        return ids.length;
    }

    public int weight(int i) {
        return cumulative[i] - (i == 0 ? 0 : cumulative[i - 1]);
    }

    /** The palette without the entries {@code keep} rejects, or null when nothing is left. */
    public CanonPalette filter(Predicate<String> keep) {
        List<String> kept = new ArrayList<>();
        List<Integer> w = new ArrayList<>();
        for (int i = 0; i < ids.length; i++) {
            if (keep.test(ids[i])) {
                kept.add(ids[i]);
                w.add(weight(i));
            }
        }
        if (kept.isEmpty()) return null;
        return new CanonPalette(kept.toArray(String[]::new), w.stream().mapToInt(Integer::intValue).toArray());
    }

    /** Weighted index for a hash; allocation-free. */
    public int pick(long hash) {
        int r = (int) ((hash >>> 1) % total);
        for (int i = 0; i < cumulative.length; i++) if (r < cumulative[i]) return i;
        return cumulative.length - 1;
    }

    /** The palette entry at a block column for a nation letter (separate stream for the peaks palette). */
    public int pickAt(long seed, char region, boolean peaks, int blockX, int blockZ) {
        return pickPatch(region, peaks, patch(seed, blockX, blockZ));
    }

    /** {@link #pickAt} for a patch id the caller already has (zoned nations need it for the ring as well). */
    public int pickPatch(char region, boolean peaks, long patchHash) {
        return pick(mix(patchHash ^ (region * 0x632BE59BD9B4E019L) ^ (peaks ? SALT_PEAKS : 0)));
    }

    // ---- noise ----

    static long mix(long z) {
        z = (z ^ (z >>> 30)) * 0xBF58476D1CE4E5B9L;
        z = (z ^ (z >>> 27)) * 0x94D049BB133111EBL;
        return z ^ (z >>> 31);
    }

    static long hash(long seed, int a, int b) {
        return mix(seed ^ mix(a * 0x9E3779B97F4A7C15L + b * 0xC2B2AE3D27D4EB4FL));
    }

    static double unit(long h) {
        return (h >>> 11) * 0x1.0p-53;
    }

    /** Smooth value noise in [-1, 1] with lattice spacing {@code scale} blocks. */
    static double noise(long seed, double x, double z, double scale) {
        double u = x / scale, v = z / scale;
        int i = (int) Math.floor(u), j = (int) Math.floor(v);
        double fx = u - i, fz = v - j;
        fx = fx * fx * (3 - 2 * fx);
        fz = fz * fz * (3 - 2 * fz);
        double a = unit(hash(seed, i, j)), b = unit(hash(seed, i + 1, j)), c = unit(hash(seed, i, j + 1)), d = unit(hash(seed, i + 1, j + 1));
        return 2 * ((a + (b - a) * fx) * (1 - fz) + (c + (d - c) * fx) * fz) - 1;
    }

    /** Block x after the border dither (pair with {@link #borderZ}). */
    static double borderX(long seed, int x, int z) {
        return x + BORDER_WARP * noise(seed ^ SALT_BORDER_X, x, z, BORDER_SCALE) + BORDER_FINE * noise(seed ^ SALT_FINE_X, x, z, BORDER_FINE_SCALE);
    }

    static double borderZ(long seed, int x, int z) {
        return z + BORDER_WARP * noise(seed ^ SALT_BORDER_Z, x, z, BORDER_SCALE) + BORDER_FINE * noise(seed ^ SALT_FINE_Z, x, z, BORDER_FINE_SCALE);
    }

    /**
     * Id of the patch a block column belongs to: nearest point of a jittered {@link #PATCH} grid after a domain
     * warp, so patches are irregular blobs of roughly 200-500 blocks. Allocation-free.
     */
    static long patch(long seed, int x, int z) {
        double px = x + PATCH_WARP * noise(seed ^ SALT_PATCH_X, x, z, PATCH_WARP_SCALE);
        double pz = z + PATCH_WARP * noise(seed ^ SALT_PATCH_Z, x, z, PATCH_WARP_SCALE);
        int ci = (int) Math.floor(px / PATCH), cj = (int) Math.floor(pz / PATCH);
        long best = 0;
        double bestD = Double.MAX_VALUE;
        for (int dj = -1; dj <= 1; dj++) {
            for (int di = -1; di <= 1; di++) {
                long h = hash(seed ^ SALT_CELLS, ci + di, cj + dj);
                double fx = (ci + di + 0.1 + 0.8 * unit(h)) * PATCH - px;
                double fz = (cj + dj + 0.1 + 0.8 * unit(mix(h))) * PATCH - pz;
                double d = fx * fx + fz * fz;
                if (d < bestD) {
                    bestD = d;
                    best = h;
                }
            }
        }
        return best;
    }
}
