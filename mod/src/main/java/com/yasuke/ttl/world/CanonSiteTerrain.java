package com.yasuke.ttl.world;

import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.util.KeyDispatchDataCodec;
import net.minecraft.world.level.levelgen.DensityFunction;

/**
 * Density function {@code ttl:canon_sites}: wraps the overworld's {@code final_density} (threshold 0) and
 * {@code initial_density_without_jaggedness} (threshold 0.390625, the level vanilla reads the preliminary surface
 * from) and pulls them toward the flat ground of the {@link CanonSites} with terrain {@code flat}. Both are wrapped so
 * the aquifers see the same surface as the blocks: a mountain cut away for a plain does not leave its old surface
 * behind as a floating water or lava table. Outside every flat site (and when the canon map is not loaded) it returns
 * the argument unchanged. Registered in {@link CanonMap#TYPES}; wired in pack/kubejs/data/minecraft/worldgen/noise_settings/overworld.json.
 */
public record CanonSiteTerrain(DensityFunction argument, double threshold) implements DensityFunction {
    public static final MapCodec<CanonSiteTerrain> MAP_CODEC = RecordCodecBuilder.mapCodec(i -> i.group(
            DensityFunction.HOLDER_HELPER_CODEC.fieldOf("argument").forGetter(CanonSiteTerrain::argument),
            Codec.DOUBLE.optionalFieldOf("threshold", 0.0).forGetter(CanonSiteTerrain::threshold)
    ).apply(i, CanonSiteTerrain::new));
    private static final KeyDispatchDataCodec<CanonSiteTerrain> CODEC = KeyDispatchDataCodec.of(MAP_CODEC);

    /** Per-thread memo of the last column: the density is asked for every y of a column in a row. */
    private static final class Column {
        int x = Integer.MIN_VALUE, z = Integer.MIN_VALUE;
        CanonSites sites;
        final double[] flat = new double[2];
    }

    private static final ThreadLocal<Column> COLUMN = ThreadLocal.withInitial(Column::new);

    @Override
    public double compute(FunctionContext ctx) {
        double v = argument.compute(ctx);
        CanonGrid grid = CanonMap.grid();
        if (grid == null || !grid.sites().anyFlat()) return v;
        int x = ctx.blockX(), z = ctx.blockZ();
        Column c = COLUMN.get();
        if (c.x != x || c.z != z || c.sites != grid.sites()) {
            grid.sites().flat(x, z, c.flat);
            c.x = x;
            c.z = z;
            c.sites = grid.sites();
        }
        return c.flat[0] <= 0 ? v : CanonSites.flatten(v, threshold, c.flat[0], c.flat[1], ctx.blockY());
    }

    @Override
    public void fillArray(double[] values, ContextProvider provider) {
        provider.fillAllDirectly(values, this);
    }

    @Override
    public DensityFunction mapAll(Visitor visitor) {
        return visitor.apply(new CanonSiteTerrain(argument.mapAll(visitor), threshold));
    }

    @Override
    public double minValue() {
        return Math.min(argument.minValue(), threshold - 1);
    }

    @Override
    public double maxValue() {
        return Math.max(argument.maxValue(), threshold + 1);
    }

    @Override
    public KeyDispatchDataCodec<? extends DensityFunction> codec() {
        return CODEC;
    }
}
