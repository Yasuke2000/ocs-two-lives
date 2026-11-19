package com.yasuke.ttl.world;

import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.util.KeyDispatchDataCodec;
import net.minecraft.world.level.levelgen.DensityFunction;
import net.neoforged.neoforge.registries.DeferredRegister;

/**
 * The own world's terrain shaper (design/architecture/own-world.md §3.1): datapack overrides of
 * {@code minecraft:overworld/offset}, {@code factor} and {@code jaggedness} wrap vanilla's definitions ({@code outside})
 * in {@code ttl:design_offset}, {@code ttl:design_factor} and {@code ttl:design_jaggedness}; the noise settings wrap
 * {@code fluid_level_floodedness} in {@code ttl:design_dry} and vanilla's top slide in {@code ttl:design_top_slide}.
 * Inside the design box they return the designed values ({@link DesignTerrain}), blended into vanilla over the box's
 * {@code edge_blend}; outside it, and whenever {@link DesignWorld#rasters()} is absent, they return {@code outside}
 * unchanged, to the bit. Everything else in the router (caves, aquifers, ores, surface rules) stays vanilla.
 */
public final class DesignDensity {
    private DesignDensity() {}

    static void register(DeferredRegister<com.mojang.serialization.MapCodec<? extends DensityFunction>> types) {
        types.register("design_offset", () -> Offset.MAP_CODEC);
        types.register("design_factor", () -> Factor.MAP_CODEC);
        types.register("design_jaggedness", () -> Jaggedness.MAP_CODEC);
        types.register("design_dry", () -> Dry.MAP_CODEC);
        types.register("design_top_slide", () -> TopSlide.MAP_CODEC);
    }

    /** Shared 2-D plumbing: {@code outside} everywhere, the design value blended in by the box weight. */
    private interface Column extends DensityFunction {
        DensityFunction outside();

        /** The designed value at a column (only asked where the weight is > 0). */
        double design(CanonRasters r, int x, int z, double outside);

        @Override
        default double compute(FunctionContext ctx) {
            double o = outside().compute(ctx);
            CanonRasters r = DesignWorld.rasters();
            if (r == null) return o;
            int x = ctx.blockX(), z = ctx.blockZ();
            double w = r.weight(x, z);
            return w <= 0 ? o : DesignTerrain.blend(o, design(r, x, z, o), w);
        }

        @Override
        default void fillArray(double[] values, ContextProvider provider) {
            outside().fillArray(values, provider);
            CanonRasters r = DesignWorld.rasters();
            if (r == null) return;
            for (int i = 0; i < values.length; i++) {
                FunctionContext ctx = provider.forIndex(i);
                int x = ctx.blockX(), z = ctx.blockZ();
                double w = r.weight(x, z);
                if (w > 0) values[i] = DesignTerrain.blend(values[i], design(r, x, z, values[i]), w);
            }
        }
    }

    /** {@code ttl:design_offset}: {@code (T - 128) / 128} for the designed surface (see {@link DesignTerrain#offset}). */
    public record Offset(DensityFunction outside, double bias) implements Column {
        public static final MapCodec<Offset> MAP_CODEC = RecordCodecBuilder.mapCodec(i -> i.group(
                DensityFunction.HOLDER_HELPER_CODEC.fieldOf("outside").forGetter(Offset::outside),
                Codec.DOUBLE.optionalFieldOf("bias", 0.0).forGetter(Offset::bias)
        ).apply(i, Offset::new));
        private static final KeyDispatchDataCodec<Offset> CODEC = KeyDispatchDataCodec.of(MAP_CODEC);

        @Override
        public double design(CanonRasters r, int x, int z, double outside) {
            return DesignTerrain.offset(r.height(x, z), bias);
        }

        @Override
        public DensityFunction mapAll(Visitor visitor) {
            return visitor.apply(new Offset(outside.mapAll(visitor), bias));
        }

        @Override
        public double minValue() {
            return Math.min(outside.minValue(), -1.6);
        }

        @Override
        public double maxValue() {
            return Math.max(outside.maxValue(), 1.6);
        }

        @Override
        public KeyDispatchDataCodec<? extends DensityFunction> codec() {
            return CODEC;
        }
    }

    /** {@code ttl:design_factor}: from the rugged raster: index.json's curve, else flat 8, rolling 5, hills 3, alpine 1.5 at 0.1/0.3/0.6/0.8. */
    public record Factor(DensityFunction outside, double flat, double rolling, double hills, double alpine, double fallback) implements Column {
        public static final MapCodec<Factor> MAP_CODEC = RecordCodecBuilder.mapCodec(i -> i.group(
                DensityFunction.HOLDER_HELPER_CODEC.fieldOf("outside").forGetter(Factor::outside),
                Codec.DOUBLE.optionalFieldOf("flat", DesignTerrain.FLAT).forGetter(Factor::flat),
                Codec.DOUBLE.optionalFieldOf("rolling", DesignTerrain.ROLLING).forGetter(Factor::rolling),
                Codec.DOUBLE.optionalFieldOf("hills", DesignTerrain.HILLS).forGetter(Factor::hills),
                Codec.DOUBLE.optionalFieldOf("alpine", DesignTerrain.ALPINE).forGetter(Factor::alpine),
                Codec.DOUBLE.optionalFieldOf("missing_rugged", 0.2).forGetter(Factor::fallback)
        ).apply(i, Factor::new));
        private static final KeyDispatchDataCodec<Factor> CODEC = KeyDispatchDataCodec.of(MAP_CODEC);

        @Override
        public double design(CanonRasters r, int x, int z, double outside) {
            double rugged = r.rugged(x, z, fallback);
            double[][] curve = r.factorCurve();
            return curve != null ? DesignTerrain.curve(curve, rugged) : DesignTerrain.factor(rugged, flat, rolling, hills, alpine);
        }

        @Override
        public DensityFunction mapAll(Visitor visitor) {
            return visitor.apply(new Factor(outside.mapAll(visitor), flat, rolling, hills, alpine, fallback));
        }

        @Override
        public double minValue() {
            return Math.min(outside.minValue(), Math.min(Math.min(flat, rolling), Math.min(hills, alpine)));
        }

        @Override
        public double maxValue() {
            return Math.max(outside.maxValue(), Math.max(Math.max(flat, rolling), Math.max(hills, alpine)));
        }

        @Override
        public KeyDispatchDataCodec<? extends DensityFunction> codec() {
            return CODEC;
        }
    }

    /** {@code ttl:design_jaggedness}: 0 except on peaks (rugged >= 0.8), up to {@code max}, capped under y 310. */
    public record Jaggedness(DensityFunction outside, double max) implements Column {
        public static final MapCodec<Jaggedness> MAP_CODEC = RecordCodecBuilder.mapCodec(i -> i.group(
                DensityFunction.HOLDER_HELPER_CODEC.fieldOf("outside").forGetter(Jaggedness::outside),
                Codec.DOUBLE.optionalFieldOf("max", 0.6).forGetter(Jaggedness::max)
        ).apply(i, Jaggedness::new));
        private static final KeyDispatchDataCodec<Jaggedness> CODEC = KeyDispatchDataCodec.of(MAP_CODEC);

        @Override
        public double design(CanonRasters r, int x, int z, double outside) {
            double rugged = r.rugged(x, z, 0);
            double[][] curve = r.jaggedCurve();
            double j = curve != null ? Math.min(max, DesignTerrain.curve(curve, rugged)) : DesignTerrain.jaggedness(rugged, 0, max);
            return j <= 0 ? 0 : DesignTerrain.capJag(j, r.height(x, z));
        }

        @Override
        public DensityFunction mapAll(Visitor visitor) {
            return visitor.apply(new Jaggedness(outside.mapAll(visitor), max));
        }

        @Override
        public double minValue() {
            return Math.min(outside.minValue(), 0);
        }

        @Override
        public double maxValue() {
            return Math.max(outside.maxValue(), max);
        }

        @Override
        public KeyDispatchDataCodec<? extends DensityFunction> codec() {
            return CODEC;
        }
    }

    /**
     * {@code ttl:design_dry} around {@code fluid_level_floodedness}: -1 (never flooded: no aquifer water or lava) in
     * every pixel of the derived {@link CanonRasters#DRY} mask (site boxes and the Dwargon cavity plus {@code dry_margin}).
     */
    public record Dry(DensityFunction argument) implements DensityFunction {
        public static final MapCodec<Dry> MAP_CODEC = RecordCodecBuilder.mapCodec(i -> i.group(
                DensityFunction.HOLDER_HELPER_CODEC.fieldOf("argument").forGetter(Dry::argument)
        ).apply(i, Dry::new));
        private static final KeyDispatchDataCodec<Dry> CODEC = KeyDispatchDataCodec.of(MAP_CODEC);

        static boolean dry(CanonRasters r, int x, int z) {
            return (r.mask(x, z) & CanonRasters.DRY) != 0;
        }

        @Override
        public double compute(FunctionContext ctx) {
            CanonRasters r = DesignWorld.rasters();
            if (r != null && dry(r, ctx.blockX(), ctx.blockZ())) return -1;
            return argument.compute(ctx);
        }

        @Override
        public void fillArray(double[] values, ContextProvider provider) {
            argument.fillArray(values, provider);
            CanonRasters r = DesignWorld.rasters();
            if (r == null) return;
            for (int i = 0; i < values.length; i++) {
                FunctionContext ctx = provider.forIndex(i);
                if (dry(r, ctx.blockX(), ctx.blockZ())) values[i] = -1;
            }
        }

        @Override
        public DensityFunction mapAll(Visitor visitor) {
            return visitor.apply(new Dry(argument.mapAll(visitor)));
        }

        @Override
        public double minValue() {
            return Math.min(argument.minValue(), -1);
        }

        @Override
        public double maxValue() {
            return Math.max(argument.maxValue(), -1);
        }

        @Override
        public KeyDispatchDataCodec<? extends DensityFunction> codec() {
            return CODEC;
        }
    }

    /**
     * {@code ttl:design_top_slide} in place of vanilla's top slide gradient (y 240 -> 1, 256 -> 0, {@code outside}):
     * inside the design box the slide starts at {@code from_y} instead, so designed crests up to y 300 (the Canaat,
     * the Dragon's Nest shoulder) are not cut off at 256. Blended by the box weight; vanilla outside.
     */
    public record TopSlide(DensityFunction outside, int fromY, int toY) implements DensityFunction {
        public static final MapCodec<TopSlide> MAP_CODEC = RecordCodecBuilder.mapCodec(i -> i.group(
                DensityFunction.HOLDER_HELPER_CODEC.fieldOf("outside").forGetter(TopSlide::outside),
                Codec.INT.optionalFieldOf("from_y", 304).forGetter(TopSlide::fromY),
                Codec.INT.optionalFieldOf("to_y", 320).forGetter(TopSlide::toY)
        ).apply(i, TopSlide::new));
        private static final KeyDispatchDataCodec<TopSlide> CODEC = KeyDispatchDataCodec.of(MAP_CODEC);

        @Override
        public double compute(FunctionContext ctx) {
            double o = outside.compute(ctx);
            CanonRasters r = DesignWorld.rasters();
            if (r == null) return o;
            double w = r.weight(ctx.blockX(), ctx.blockZ());
            return w <= 0 ? o : DesignTerrain.blend(o, DesignTerrain.slide(ctx.blockY(), fromY, toY), w);
        }

        @Override
        public void fillArray(double[] values, ContextProvider provider) {
            outside.fillArray(values, provider);
            CanonRasters r = DesignWorld.rasters();
            if (r == null) return;
            for (int i = 0; i < values.length; i++) {
                FunctionContext ctx = provider.forIndex(i);
                double w = r.weight(ctx.blockX(), ctx.blockZ());
                if (w > 0) values[i] = DesignTerrain.blend(values[i], DesignTerrain.slide(ctx.blockY(), fromY, toY), w);
            }
        }

        @Override
        public DensityFunction mapAll(Visitor visitor) {
            return visitor.apply(new TopSlide(outside.mapAll(visitor), fromY, toY));
        }

        @Override
        public double minValue() {
            return Math.min(outside.minValue(), 0);
        }

        @Override
        public double maxValue() {
            return Math.max(outside.maxValue(), 1);
        }

        @Override
        public KeyDispatchDataCodec<? extends DensityFunction> codec() {
            return CODEC;
        }
    }
}
