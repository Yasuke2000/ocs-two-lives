package com.yasuke.ttl.world;

/**
 * The arithmetic that turns designed rasters into vanilla's terrain shaper values (design/architecture/own-world.md
 * §3.1). Pure Java so {@link DesignSelfCheck} can test it at sample points.
 *
 * <p><b>Offset.</b> Vanilla's {@code overworld/depth} is {@code y_clamped_gradient(-64 -> 1.5, 320 -> -1.5) + offset},
 * zero at {@code y = 128 * offset + 128}; the final density near the surface is {@code 4 * quarter_negative(depth *
 * factor) + base_3d_noise}, interpolated linearly between noise-cell corners 8 blocks apart (y = -64 + 8k). Because
 * {@code quarter_negative} makes the density four times flatter above the zero than below it, linear interpolation
 * moves the solid/air crossing up by up to 2.6 blocks depending on where the zero sits in its cell. {@link #offset}
 * therefore places the zero T so that the interpolated crossing (without 3-D noise) lands half a block under the
 * designed surface H: with a = T - y0 in a cell [y0, y0 + 8) the crossing is y0 + 32a / (3a + 8), whose inverse is
 * {@code a = 8c / (32 - 3c)} for a crossing c above y0. {@code offset = (T - 128) / 128} is vanilla's convention.
 * {@code bias} (blocks) is the measured mean lift of the 3-D noise (the calibration gate reports it).
 *
 * <p><b>Factor</b> (how tightly the ground hugs the offset) from ruggedness, own-world.md §3.8: piecewise-linear
 * 0 -> 8, 0.1 -> 8, 0.3 -> 5, 0.6 -> 3, 0.8 -> 1.5 (flat 8, rolling 5, hills 3, alpine 1.5); <b>jaggedness</b> 0 below
 * rugged 0.8, rising to 0.6 at 1, never enough to push a spike above {@link #JAG_CEILING}. index.json repeats both
 * curves; when it has them, they are used ({@link #curve}).
 */
public final class DesignTerrain {
    private DesignTerrain() {}

    public static final double FLAT = 8, ROLLING = 5, HILLS = 3, ALPINE = 1.5;
    /** Ruggedness knots of the factor curve (values flat, flat, rolling, hills, alpine, alpine). */
    static final double[] RUGGED_KNOTS = {0, 0.1, 0.3, 0.6, 0.8, 1.0};
    /** The default curves of own-world.md §3.8. */
    public static final double[][] FACTOR_CURVE = {{0, 8}, {0.1, 8}, {0.3, 5}, {0.6, 3}, {0.8, 1.5}, {1, 1.5}};
    public static final double[][] JAGGED_CURVE = {{0, 0}, {0.8, 0}, {1, 0.6}};
    /** Highest y a jagged spike may reach (one block of jaggedness lifts the ground by up to 128 * jaggedness). */
    static final double JAG_CEILING = 310;
    static final int CELL = 8, MIN_Y = -64;

    /** Vanilla offset that puts the interpolated surface of a flat field at H (first air y), minus {@code bias} blocks. */
    public static double offset(double h, double bias) {
        return (zeroFor(h - bias) - 128) / 128;
    }

    /** The y where depth is zero so that the cell-interpolated crossing sits at {@code h - 0.5}. */
    static double zeroFor(double h) {
        double c = h - 0.5, y0 = Math.floorDiv((long) Math.floor(c - MIN_Y), CELL) * (double) CELL + MIN_Y;
        double a = c - y0; // 0 <= a < 8: crossing height above the cell bottom
        return y0 + 8 * a / (32 - 3 * a);
    }

    /** The crossing (real y, solid below) of the cell-interpolated density for a zero at T, without 3-D noise. */
    static double crossingFor(double t) {
        double y0 = Math.floorDiv((long) Math.floor(t - MIN_Y), CELL) * (double) CELL + MIN_Y;
        double a = t - y0;
        return y0 + 32 * a / (3 * a + 8);
    }

    /** Factor from ruggedness with the given flat/rolling/hills/alpine values. */
    public static double factor(double rugged, double flat, double rolling, double hills, double alpine) {
        double r = Math.max(0, Math.min(1, rugged));
        double[] v = {flat, flat, rolling, hills, alpine, alpine};
        for (int i = 1; i < RUGGED_KNOTS.length; i++) {
            if (r <= RUGGED_KNOTS[i]) {
                double t = (r - RUGGED_KNOTS[i - 1]) / (RUGGED_KNOTS[i] - RUGGED_KNOTS[i - 1]);
                return v[i - 1] + (v[i] - v[i - 1]) * t;
            }
        }
        return alpine;
    }

    public static double factor(double rugged) {
        return factor(rugged, FLAT, ROLLING, HILLS, ALPINE);
    }

    /** Piecewise-linear curve [[x, y], ...] (x ascending) at x, clamped to its ends. */
    public static double curve(double[][] pts, double x) {
        if (x <= pts[0][0]) return pts[0][1];
        for (int i = 1; i < pts.length; i++) {
            if (x <= pts[i][0]) {
                double span = pts[i][0] - pts[i - 1][0];
                return span <= 0 ? pts[i][1] : pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * (x - pts[i - 1][0]) / span;
            }
        }
        return pts[pts.length - 1][1];
    }

    /** Jaggedness from ruggedness (§3.8 curve scaled to {@code max}), capped so a spike over H stays under {@link #JAG_CEILING}. */
    public static double jaggedness(double rugged, double h, double max) {
        return capJag(curve(JAGGED_CURVE, rugged) * max / 0.6, h);
    }

    /** Caps a jaggedness so a spike over a surface at {@code h} stays under {@link #JAG_CEILING}. */
    public static double capJag(double j, double h) {
        double cap = Math.max(0, (JAG_CEILING - h) / 128);
        return Math.max(0, Math.min(j, cap));
    }

    /** Vanilla's y_clamped_gradient(fromY -> 1, toY -> 0) at y. */
    public static double slide(int y, double fromY, double toY) {
        if (y <= fromY) return 1;
        if (y >= toY) return 0;
        return 1 - (y - fromY) / (toY - fromY);
    }

    /** Linear blend from {@code outside} to {@code design} by weight w (0 = outside). */
    public static double blend(double outside, double design, double w) {
        return w <= 0 ? outside : w >= 1 ? design : outside + (design - outside) * w;
    }
}
