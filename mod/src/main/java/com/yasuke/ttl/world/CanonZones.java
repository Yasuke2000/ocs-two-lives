package com.yasuke.ttl.world;

/**
 * Optional distance gradient inside one nation's palette ({@code "zones"} in canon_regions.json): the nation's
 * land is split into rings, each with its own weighted biome list, so the biome (and with Tensura's per-biome area
 * magicule, how deadly it is) depends on where you stand rather than on a random patch.
 *
 * <p>Rings are tried in listed order; the first whose test passes wins and the last one has no test. A test is
 * either {@code radius} (blocks from {@link #centreX}/{@link #centreZ}) or {@code depth} (blocks inside the
 * nation's border, measured by {@link CanonGrid} to the nearest cell that is neither the nation nor one of the
 * {@link #interior} characters). Every patch of the palette gets its own random offset of up to {@link #fade}
 * blocks, applied to the test value, so a ring edge is a ragged fringe of whole patches instead of a circle; the
 * point itself is first moved by the same border dither as the nation borders. Pure Java.
 */
public final class CanonZones {
    /** One ring; exactly one of radius/depth is set (> 0) unless it is the last ring. */
    public record Ring(String name, double radius, double depth, CanonPalette biomes) {
        boolean tested() {
            return radius > 0 || depth > 0;
        }
    }

    private static final long SALT_ZONE = 0x7F4A7C159E3779B9L;

    private final double centreX, centreZ, fade;
    private final String interior;
    private final Ring[] rings;

    public CanonZones(double centreX, double centreZ, double fade, String interior, Ring[] rings) {
        if (rings.length == 0) throw new IllegalArgumentException("zones need at least one ring");
        for (int i = 0; i < rings.length; i++) {
            Ring ring = rings[i];
            boolean last = i == rings.length - 1;
            if (ring.biomes() == null) throw new IllegalArgumentException("ring " + ring.name() + " has no biomes");
            if (ring.radius() > 0 && ring.depth() > 0) throw new IllegalArgumentException("ring " + ring.name() + " has both radius and depth");
            if (last && ring.tested()) throw new IllegalArgumentException("the last ring (" + ring.name() + ") takes what is left: no radius or depth");
            if (!last && !ring.tested()) throw new IllegalArgumentException("ring " + ring.name() + " needs a radius or a depth");
        }
        this.centreX = centreX;
        this.centreZ = centreZ;
        this.fade = Math.max(0, fade);
        this.interior = interior;
        this.rings = rings.clone();
    }

    public double centreX() {
        return centreX;
    }

    public double centreZ() {
        return centreZ;
    }

    public double fade() {
        return fade;
    }

    /** Cell characters (besides the nation's own letter) that do not count as its border for depth tests. */
    public String interior() {
        return interior;
    }

    public int size() {
        return rings.length;
    }

    public Ring ring(int i) {
        return rings[i];
    }

    /** True when some ring tests depth, so {@link CanonGrid} must precompute the distance to the border. */
    public boolean usesDepth() {
        for (Ring ring : rings) if (ring.depth() > 0) return true;
        return false;
    }

    /** The patch's random shift of every test value, in [-fade, fade). */
    public double jitter(long patchHash) {
        return (CanonPalette.unit(CanonPalette.mix(patchHash ^ SALT_ZONE)) * 2 - 1) * fade;
    }

    /** Ring index for a dithered point, its depth below the border (blocks) and the patch hash. Allocation-free. */
    public int ringFor(double x, double z, double depth, long patchHash) {
        double o = jitter(patchHash);
        double r = Math.hypot(x - centreX, z - centreZ);
        for (int i = 0; i < rings.length - 1; i++) {
            Ring ring = rings[i];
            if (ring.radius() > 0 ? r + o < ring.radius() : depth + o < ring.depth()) return i;
        }
        return rings.length - 1;
    }
}
