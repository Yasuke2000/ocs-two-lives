package com.yasuke.ttl.world;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.BlockPos;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.FeaturePlaceContext;
import net.minecraft.world.level.levelgen.feature.configurations.FeatureConfiguration;
import net.minecraft.world.level.material.Fluids;

/**
 * {@code ttl:design_water} (step {@code lakes}, added to every biome by pack/kubejs/data/ttl/neoforge/biome_modifier/
 * design_water.json): fills the designed lakes and stepped river reaches of {@code water.png} in the chunk it is placed
 * for, deterministically per column (pregen, DH and BlueMap see the same water):
 * <ul>
 *   <li>a wet column (level L) gets water sources from its ground up to L - 1; ground sticking up to {@code carve} blocks
 *       above the designed bed is cut away first, its top becomes a bed block (sand/gravel/clay mix), and up to
 *       {@code seal} blocks of cave opening under the bed are closed with stone, so a lake never drains into a cave;</li>
 *   <li>a dry column next to a wet one whose ground is lower than that water is raised to it (a bank), so nothing leaks
 *       where the 3-D noise dipped below the designed rim;</li>
 *   <li>where a reach meets a lower one (a small fall) the upper edge sources get a fluid tick, so they spill over the
 *       step as a one-block waterfall on the first tick of the chunk.</li>
 * </ul>
 * Only in the Tensura world's generator and only with design rasters; elsewhere it places nothing.
 */
public final class DesignWaterFeature extends Feature<DesignWaterFeature.Config> {
    public record Config(int carve, int seal, int bank) implements FeatureConfiguration {
        public static final Codec<Config> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.intRange(0, 16).optionalFieldOf("carve", 4).forGetter(Config::carve),
                Codec.intRange(0, 16).optionalFieldOf("seal", 4).forGetter(Config::seal),
                Codec.intRange(0, 16).optionalFieldOf("bank", 8).forGetter(Config::bank)
        ).apply(i, Config::new));
    }

    public DesignWaterFeature() {
        super(Config.CODEC);
    }

    @Override
    public boolean place(FeaturePlaceContext<Config> ctx) {
        CanonRasters r = DesignWorld.rasters();
        if (r == null || !r.hasWater() || !DesignWorld.designGenerator(ctx.chunkGenerator())) return false;
        WorldGenLevel level = ctx.level();
        int x0 = ctx.origin().getX() & ~15, z0 = ctx.origin().getZ() & ~15;
        if (x0 + 16 <= r.boxX0() || z0 + 16 <= r.boxZ0() || x0 >= r.boxX1() || z0 >= r.boxZ1()) return false;
        Config c = ctx.config();
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        boolean any = false;
        int minY = level.getMinBuildHeight();
        for (int dz = 0; dz < 16; dz++) {
            for (int dx = 0; dx < 16; dx++) {
                int x = x0 + dx, z = z0 + dz;
                int level0 = r.waterLevel(x, z);
                if (level0 == Integer.MIN_VALUE) {
                    any |= bank(level, r, pos, x, z, c, minY);
                    continue;
                }
                any |= fill(level, r, pos, x, z, level0, c, minY);
            }
        }
        return any;
    }

    /** A wet column: carve, fill, bed, seal, fall ticks. */
    private static boolean fill(WorldGenLevel level, CanonRasters r, BlockPos.MutableBlockPos pos, int x, int z, int lvl, Config c, int minY) {
        int top = lvl - 1; // highest water block
        int ground = groundBelow(level, pos, x, z, top + c.carve() + 2, minY);
        int bed = (int) Math.floor(Math.min(r.height(x + 0.5, z + 0.5), lvl - 1)) - 1; // designed bed top block
        if (ground > top) {
            if (ground - Math.max(bed, top - 1) > c.carve()) return false; // an island the noise made: keep it
            for (int y = ground; y > Math.max(bed, minY); y--) {
                if (y > top) set(level, pos, x, y, z, Blocks.AIR.defaultBlockState());
                else set(level, pos, x, y, z, Blocks.WATER.defaultBlockState());
            }
            ground = Math.max(bed, minY);
        }
        boolean placed = false;
        for (int y = ground + 1; y <= top; y++) {
            BlockState s = level.getBlockState(pos.set(x, y, z));
            if (s.isAir() || replaceable(s)) {
                level.setBlock(pos, Blocks.WATER.defaultBlockState(), 2);
                placed = true;
            } else if (s.getFluidState().is(Fluids.WATER) || s.getFluidState().is(Fluids.FLOWING_WATER)) {
                if (!s.getFluidState().isSource()) level.setBlock(pos, Blocks.WATER.defaultBlockState(), 2);
            } else if (s.getFluidState().is(Fluids.LAVA) || s.getFluidState().is(Fluids.FLOWING_LAVA)) {
                level.setBlock(pos, Blocks.WATER.defaultBlockState(), 2);
            }
        }
        if (ground < top) {
            BlockState floor = level.getBlockState(pos.set(x, ground, z));
            if (floor.is(Blocks.GRASS_BLOCK) || floor.is(Blocks.DIRT) || floor.is(Blocks.PODZOL) || floor.is(Blocks.MYCELIUM)
                    || floor.is(Blocks.COARSE_DIRT) || floor.is(Blocks.SNOW_BLOCK) || floor.is(Blocks.ROOTED_DIRT) || floor.is(Blocks.MUD)) {
                level.setBlock(pos, bedBlock(x, z), 2);
            }
            for (int y = ground - 1; y >= Math.max(minY + 1, ground - c.seal()); y--) {
                BlockState s = level.getBlockState(pos.set(x, y, z));
                if (s.isAir() || !s.getFluidState().isEmpty()) level.setBlock(pos, Blocks.STONE.defaultBlockState(), 2);
                else break;
            }
        }
        // A small fall: this reach is higher than a neighbouring wet column, so its edge spills over the step.
        for (int k = 0; k < 4; k++) {
            int nx = x + (k == 0 ? 1 : k == 1 ? -1 : 0), nz = z + (k == 2 ? 1 : k == 3 ? -1 : 0);
            int other = r.waterLevel(nx, nz);
            if (other != Integer.MIN_VALUE && other < lvl) {
                level.scheduleTick(pos.set(x, top, z), Fluids.WATER, 0);
                break;
            }
        }
        return placed;
    }

    /** A dry column beside water: raise its ground to that water's level so nothing spills (at most {@code bank} blocks). */
    private static boolean bank(WorldGenLevel level, CanonRasters r, BlockPos.MutableBlockPos pos, int x, int z, Config c, int minY) {
        int need = Integer.MIN_VALUE;
        for (int dz = -1; dz <= 1; dz++)
            for (int dx = -1; dx <= 1; dx++)
                if (dx != 0 || dz != 0) need = Math.max(need, r.waterLevel(x + dx, z + dz));
        if (need == Integer.MIN_VALUE) return false;
        int top = need - 1; // the bank's top block must be at least the highest water block next to it
        int ground = groundBelow(level, pos, x, z, top + 1, minY);
        if (ground >= top || top - ground > c.bank()) return false;
        // Already water above its ground (the sea at a river mouth, an aquifer pond): joined to the water, no dam.
        if (!level.getBlockState(pos.set(x, ground + 1, z)).getFluidState().isEmpty()) return false;
        BlockState surface = level.getBlockState(pos.set(x, ground, z));
        BlockState fill = surface.is(Blocks.SAND) || surface.is(Blocks.RED_SAND) || surface.is(Blocks.GRAVEL) || surface.is(Blocks.STONE) ? surface : Blocks.DIRT.defaultBlockState();
        for (int y = ground + 1; y <= top; y++) set(level, pos, x, y, z, y == top && fill.is(Blocks.DIRT) ? Blocks.GRASS_BLOCK.defaultBlockState() : fill);
        if (fill.is(Blocks.DIRT) && surface.is(Blocks.GRASS_BLOCK)) set(level, pos, x, ground, z, Blocks.DIRT.defaultBlockState());
        return true;
    }

    /** Top terrain block at or below {@code from} (air, fluids, plants, snow layers, leaves and logs do not count), or minY. */
    static int groundBelow(WorldGenLevel level, BlockPos.MutableBlockPos pos, int x, int z, int from, int minY) {
        for (int y = from; y > minY; y--) {
            BlockState s = level.getBlockState(pos.set(x, y, z));
            if (s.isAir() || !s.getFluidState().isEmpty() || replaceable(s) || s.is(BlockTags.LEAVES) || s.is(BlockTags.LOGS)) continue;
            return y;
        }
        return minY;
    }

    /** Plants and other soft blocks water may replace. */
    static boolean replaceable(BlockState s) {
        return s.canBeReplaced() && s.getFluidState().isEmpty() || s.is(BlockTags.REPLACEABLE_BY_TREES) || s.is(Blocks.SNOW);
    }

    private static void set(WorldGenLevel level, BlockPos.MutableBlockPos pos, int x, int y, int z, BlockState state) {
        level.setBlock(pos.set(x, y, z), state, 2);
    }

    /** Deterministic bed mix: sand 55 %, gravel 30 %, clay 15 %. */
    static BlockState bedBlock(int x, int z) {
        int h = (int) ((CanonPalette.mix(x * 0x9E3779B97F4A7C15L ^ z * 0xC2B2AE3D27D4EB4FL) >>> 33) % 100);
        return h < 55 ? Blocks.SAND.defaultBlockState() : h < 85 ? Blocks.GRAVEL.defaultBlockState() : Blocks.CLAY.defaultBlockState();
    }
}
