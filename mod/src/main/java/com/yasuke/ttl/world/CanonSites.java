package com.yasuke.ttl.world;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * Per-build sites of the canon continent ({@code "sites"} in canon_regions.json): a centre, a radius and a fade per
 * canon build or landmark, with the biome list and the terrain intent that fit it. They sit on top of the nation
 * palettes: inside a site its own biomes win, and its terrain intent steers the ground, so a build never stands in a
 * biome or on terrain that contradicts it (Dwargon on a plain, not on frozen peaks). Pure Java, like {@link CanonGrid}.
 *
 * <p>Every site has a weight per block column: 1 within {@code radius}, a smoothstep down to 0 over {@code fade}
 * blocks. The distance is measured after the nation-border dither and a per-site radial wobble (two octaves of value
 * noise, salted with the site's name), so a site edge is an organic blob rather than a circle, and it is the same for
 * every seed (the terrain density functions do not know the world seed). The biome edge sits half-way through the
 * fade; the terrain fades over the whole of it.
 *
 * <p>Terrain intents:
 * <ul>
 *   <li>{@code keep}: biomes only;</li>
 *   <li>{@code flat}: the ground is blended toward a flat surface at {@code ground} (y of the first air block;
 *       default {@link #DEFAULT_GROUND}) by {@link CanonSiteTerrain}, which wraps the final density and the density
 *       the preliminary surface (aquifers) is read from, so neither floating water nor carved-away mountains
 *       remain. The whole column below the ground is pulled solid, so raised ground never floats over the old
 *       valley; the noise caves under the site's middle fill up (carver caves, ores and cave biomes deeper than
 *       {@link #SOLID_BAND} below the ground stay);</li>
 *   <li>{@code lowland}, {@code hills}, {@code mountain}: climate presets on the erosion / continentalness / ridges
 *       channels of the noise router (vanilla then builds the matching landform), blended by the site weight.</li>
 * </ul>
 * Explicit {@code erosion}, {@code continents} and {@code ridges} values override a preset. Sites are applied in
 * listed order: for biomes the first site whose biome area contains the column wins; for climate every site lerps the
 * value toward its target in turn (later sites win where they overlap); for the flat ground the strongest site wins.
 * Outside every site nothing changes, to the bit.
 */
public final class CanonSites {
    public static final int CONTINENTS = 0, EROSION = 1, RIDGES = 2;
    public static final int DEFAULT_GROUND = 70;
    /** Below this many blocks under a flat site's ground, vanilla's cave biomes are kept (above it the site's biome). */
    static final int SOLID_BAND = 16;
    /** Density change per block of the flat target surface (vanilla's own terrain slopes about 1/8 to 1/4 per block). */
    static final double TARGET_SLOPE = 0.25;
    /** Radial wobble as a share of the fade: coarse and fine octave, with their scales in blocks. */
    static final double WOBBLE = 0.35, WOBBLE_FINE = 0.12, WOBBLE_SCALE = 72, WOBBLE_FINE_SCALE = 22;
    static final int TILE = 128;

    public enum Terrain {
        KEEP("keep", null, null, null),
        FLAT("flat", null, null, null),
        LOWLAND("lowland", null, 0.5, null),
        HILLS("hills", null, -0.1, null),
        MOUNTAIN("mountain", 0.75, -0.9, 0.62);

        final String id;
        final Double continents, erosion, ridges;

        Terrain(String id, Double continents, Double erosion, Double ridges) {
            this.id = id;
            this.continents = continents;
            this.erosion = erosion;
            this.ridges = ridges;
        }

        public String id() {
            return id;
        }

        public static Terrain of(String id) {
            for (Terrain t : values()) if (t.id.equals(id)) return t;
            throw new IllegalArgumentException("unknown terrain '" + id + "' (keep, flat, lowland, hills, mountain)");
        }
    }

    /**
     * One site. {@code biomes} may be null (terrain only: the nation palette, Jura's rings for instance, stays);
     * {@code climate} holds the continents/erosion/ridges targets (null = untouched), {@code ground} is only used by
     * {@link Terrain#FLAT}.
     */
    public record Site(String name, double x, double z, double radius, double fade, CanonPalette biomes, Terrain terrain,
                       int ground, Double[] climate) {
        public Site {
            if (radius <= 0) throw new IllegalArgumentException("site " + name + ": radius must be > 0");
            if (fade < 0) throw new IllegalArgumentException("site " + name + ": fade must be >= 0");
            if (climate == null || climate.length != 3) throw new IllegalArgumentException("site " + name + ": climate needs 3 slots");
            if (biomes == null && terrain == Terrain.KEEP && climate[0] == null && climate[1] == null && climate[2] == null)
                throw new IllegalArgumentException("site " + name + ": keeps biomes and terrain, so it does nothing");
            climate = climate.clone();
        }

        public static Site of(String name, double x, double z, double radius, double fade, CanonPalette biomes, Terrain terrain,
                              Integer ground, Double continents, Double erosion, Double ridges) {
            return new Site(name, x, z, radius, fade, biomes, terrain, ground == null ? DEFAULT_GROUND : ground, new Double[] {
                    continents != null ? continents : terrain.continents,
                    erosion != null ? erosion : terrain.erosion,
                    ridges != null ? ridges : terrain.ridges});
        }

        /** Furthest block from the centre any effect can reach (radius + fade + the largest wobble). */
        double reach() {
            return radius + fade + (WOBBLE + WOBBLE_FINE) * Math.max(fade, 16) + CanonPalette.BORDER_WARP + CanonPalette.BORDER_FINE + 1;
        }

        boolean flat() {
            return terrain == Terrain.FLAT;
        }

        long salt() {
            long h = 0x9E3779B97F4A7C15L;
            for (int i = 0; i < name.length(); i++) h = CanonPalette.mix(h ^ name.charAt(i));
            return h;
        }
    }

    public static final CanonSites NONE = new CanonSites(new Site[0]);

    private final Site[] sites;
    private final long[] salts;
    private final int tileX0, tileZ0, tilesW, tilesH;
    private final int[][] tiles; // site indices per TILE x TILE square, in listed order; null = none
    private final boolean[] anyClimate = new boolean[3];
    private final boolean anyFlat;

    public CanonSites(Site[] sites) {
        this.sites = sites.clone();
        this.salts = new long[sites.length];
        boolean flat = false;
        double x0 = Double.MAX_VALUE, z0 = Double.MAX_VALUE, x1 = -Double.MAX_VALUE, z1 = -Double.MAX_VALUE;
        for (int i = 0; i < sites.length; i++) {
            Site s = sites[i];
            salts[i] = s.salt();
            flat |= s.flat();
            for (int c = 0; c < 3; c++) anyClimate[c] |= s.climate()[c] != null;
            double r = s.reach();
            x0 = Math.min(x0, s.x() - r);
            z0 = Math.min(z0, s.z() - r);
            x1 = Math.max(x1, s.x() + r);
            z1 = Math.max(z1, s.z() + r);
        }
        this.anyFlat = flat;
        if (sites.length == 0) {
            tileX0 = tileZ0 = tilesW = tilesH = 0;
            tiles = new int[0][];
            return;
        }
        tileX0 = Math.floorDiv((int) Math.floor(x0), TILE);
        tileZ0 = Math.floorDiv((int) Math.floor(z0), TILE);
        tilesW = Math.floorDiv((int) Math.ceil(x1), TILE) - tileX0 + 1;
        tilesH = Math.floorDiv((int) Math.ceil(z1), TILE) - tileZ0 + 1;
        List<List<Integer>> lists = new ArrayList<>();
        for (int i = 0; i < tilesW * tilesH; i++) lists.add(null);
        for (int i = 0; i < sites.length; i++) {
            Site s = sites[i];
            double r = s.reach();
            int a0 = Math.floorDiv((int) Math.floor(s.x() - r), TILE) - tileX0, a1 = Math.floorDiv((int) Math.ceil(s.x() + r), TILE) - tileX0;
            int b0 = Math.floorDiv((int) Math.floor(s.z() - r), TILE) - tileZ0, b1 = Math.floorDiv((int) Math.ceil(s.z() + r), TILE) - tileZ0;
            for (int b = b0; b <= b1; b++) {
                for (int a = a0; a <= a1; a++) {
                    int k = b * tilesW + a;
                    if (lists.get(k) == null) lists.set(k, new ArrayList<>());
                    lists.get(k).add(i);
                }
            }
        }
        tiles = new int[tilesW * tilesH][];
        for (int k = 0; k < tiles.length; k++) {
            List<Integer> l = lists.get(k);
            if (l != null) tiles[k] = l.stream().mapToInt(Integer::intValue).toArray();
        }
    }

    public int size() {
        return sites.length;
    }

    public Site site(int i) {
        return sites[i];
    }

    /** Random-stream salt of site i (from its name), for its biome pick. */
    public long salt(int i) {
        return salts[i];
    }

    public boolean isEmpty() {
        return sites.length == 0;
    }

    public boolean anyFlat() {
        return anyFlat;
    }

    /** Site indices whose reach may cover the column, or null. */
    private int[] candidates(int x, int z) {
        if (sites.length == 0) return null;
        int a = Math.floorDiv(x, TILE) - tileX0, b = Math.floorDiv(z, TILE) - tileZ0;
        if (a < 0 || b < 0 || a >= tilesW || b >= tilesH) return null;
        return tiles[b * tilesW + a];
    }

    /** Wobbled distance of a column from site i's centre (blocks). */
    double distance(int i, int x, int z) {
        Site s = sites[i];
        long salt = salts[i];
        double bx = CanonPalette.borderX(salt, x, z), bz = CanonPalette.borderZ(salt, x, z);
        double f = Math.max(s.fade(), 16);
        double wobble = WOBBLE * f * CanonPalette.noise(salt ^ 0x51ED270B27A5C3F1L, x, z, WOBBLE_SCALE)
                + WOBBLE_FINE * f * CanonPalette.noise(salt ^ 0x2F2D8C1B6A9E43D7L, x, z, WOBBLE_FINE_SCALE);
        return Math.hypot(bx - s.x(), bz - s.z()) + wobble;
    }

    /** Linear position in the fade: 1 inside the radius, 0 at radius + fade and beyond. */
    double ramp(int i, double d) {
        Site s = sites[i];
        if (d <= s.radius()) return 1;
        if (s.fade() <= 0 || d >= s.radius() + s.fade()) return 0;
        return 1 - (d - s.radius()) / s.fade();
    }

    static double smooth(double t) {
        return t * t * (3 - 2 * t);
    }

    /** Terrain weight of site i at a column, 0..1 (smoothstep over the fade). */
    public double weight(int i, int x, int z) {
        return smooth(ramp(i, distance(i, x, z)));
    }

    /** First site (listed order) with biomes whose biome area contains the column, or -1. */
    public int biomeSite(int x, int z) {
        int[] c = candidates(x, z);
        if (c == null) return -1;
        for (int i : c) if (sites[i].biomes() != null && ramp(i, distance(i, x, z)) > 0.5) return i;
        return -1;
    }

    /** A climate channel value with every site's target lerped in, in listed order; {@code value} unchanged outside. */
    public double climate(int channel, int x, int z, double value) {
        if (!anyClimate[channel]) return value;
        int[] c = candidates(x, z);
        if (c == null) return value;
        for (int i : c) {
            Double target = sites[i].climate()[channel];
            if (target == null) continue;
            double w = weight(i, x, z);
            if (w > 0) value += (target - value) * w;
        }
        return value;
    }

    /**
     * The flat-ground pull at a column: {@code out[0]} = weight 0..1, {@code out[1]} = ground y. Weight 0 (and
     * {@code out} untouched otherwise) where no flat site reaches. The strongest flat site wins.
     */
    public void flat(int x, int z, double[] out) {
        out[0] = 0;
        if (!anyFlat) return;
        int[] c = candidates(x, z);
        if (c == null) return;
        for (int i : c) {
            if (!sites[i].flat()) continue;
            double w = weight(i, x, z);
            if (w > out[0]) {
                out[0] = w;
                out[1] = sites[i].ground();
            }
        }
    }

    /**
     * The flat-site density at one block: {@code density} (whose surface sits at {@code threshold}) pulled toward a
     * flat surface at {@code ground} with weight {@code w}. Pure, so the self-check can test it.
     */
    public static double flatten(double density, double threshold, double w, double ground, int y) {
        if (w <= 0) return density;
        double below = ground - 0.5 - y; // > 0 inside the ground
        double target = threshold + Math.max(-1, Math.min(1, below * TARGET_SLOPE));
        return density + (target - density) * w;
    }

    /** Debug text for /ttlmap: every site that reaches the column. */
    public String describe(int x, int z) {
        int[] c = candidates(x, z);
        if (c == null) return null;
        StringBuilder out = new StringBuilder();
        for (int i : c) {
            double d = distance(i, x, z), w = smooth(ramp(i, d));
            if (w <= 0 && ramp(i, d) <= 0) continue;
            Site s = sites[i];
            if (out.length() > 0) out.append("; ");
            out.append(String.format("site '%s' (%s%s): %.0f blocks from its centre (radius %.0f, fade %.0f), weight %.2f%s",
                    s.name(), s.terrain().id(), s.flat() ? " y" + s.ground() : "", d, s.radius(), s.fade(), w,
                    s.biomes() == null ? ", biomes from the nation" : ramp(i, d) > 0.5 ? ", its biomes" : ", outside its biome edge"));
        }
        return out.length() == 0 ? null : out.toString();
    }

    @Override
    public String toString() {
        return sites.length + " sites " + Arrays.stream(sites).map(Site::name).toList();
    }
}
