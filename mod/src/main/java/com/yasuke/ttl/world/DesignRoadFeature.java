package com.yasuke.ttl.world;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import java.util.HashMap;
import java.util.Map;
import java.util.TreeMap;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.CrossCollisionBlock;
import net.minecraft.world.level.block.SlabBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.SlabType;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.FeaturePlaceContext;
import net.minecraft.world.level.levelgen.feature.configurations.FeatureConfiguration;
import org.jetbrains.annotations.Nullable;

/**
 * {@code ttl:design_road} (step {@code top_layer_modification}, added to every biome by
 * pack/kubejs/data/ttl/neoforge/biome_modifier/design_road.json): lays the designed roads of {@code road.png} in the
 * chunk it is placed for. The corridor is already cut and filled in the height raster (WP-W1), so per road column:
 * <ul>
 *   <li>the road surface sits on the designed surface (first air = the rounded bicubic height): a weighted block of the
 *       zone's palette (the canon region letter under the column, else {@code default}; trails use {@code trail}),
 *       dirt under it down to the ground (at most {@code fill}), and from one block above it up to {@code clear}
 *       blocks (more where the ground was higher, at most {@code cut}) plants, snow, leaves, logs and terrain removed;</li>
 *   <li>a bottom slab of the palette where a neighbouring road column is one block higher, so a grade walks without jumping;</li>
 *   <li>bridges (bridge pixels over water): a deck 2 above the water's top block, fence railings on the edge columns
 *       (connected along the edge), log pillars down to the bed every 5 blocks along it;</li>
 *   <li>a fence post with a lantern beside main roads: every 40 blocks along roads.json's centre lines, sides
 *       alternating; without roads.json at the road raster's {@code lantern} pixels, else the edge column nearest a
 *       hashed point of every {@code lantern_every} x {@code lantern_every} cell the road passes.</li>
 * </ul>
 * Everything is decided from the rasters and the column's own blocks, so chunks agree at their borders whatever order
 * they generate in. Only in the Tensura world's generator and only with design rasters.
 */
public final class DesignRoadFeature extends Feature<DesignRoadFeature.Config> {
    public record Palette(Map<String, Integer> surface, String slab) {
        public static final Codec<Palette> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.unboundedMap(Codec.STRING, Codec.intRange(1, 10000)).fieldOf("surface").forGetter(Palette::surface),
                Codec.STRING.optionalFieldOf("slab", "minecraft:cobblestone_slab").forGetter(Palette::slab)
        ).apply(i, Palette::new));
    }

    public record Bridge(String deck, String railing, String pillar) {
        public static final Codec<Bridge> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.STRING.optionalFieldOf("deck", "minecraft:spruce_planks").forGetter(Bridge::deck),
                Codec.STRING.optionalFieldOf("railing", "minecraft:spruce_fence").forGetter(Bridge::railing),
                Codec.STRING.optionalFieldOf("pillar", "minecraft:spruce_log").forGetter(Bridge::pillar)
        ).apply(i, Bridge::new));
    }

    public record Config(Map<String, Palette> palettes, String post, String lantern, int lanternEvery, int clear, int cut, int fill, Bridge bridge)
            implements FeatureConfiguration {
        public static final Codec<Config> CODEC = RecordCodecBuilder.create(i -> i.group(
                Codec.unboundedMap(Codec.STRING, Palette.CODEC).fieldOf("palettes").forGetter(Config::palettes),
                Codec.STRING.optionalFieldOf("post", "minecraft:spruce_fence").forGetter(Config::post),
                Codec.STRING.optionalFieldOf("lantern", "minecraft:lantern").forGetter(Config::lantern),
                Codec.intRange(0, 512).optionalFieldOf("lantern_every", 40).forGetter(Config::lanternEvery),
                Codec.intRange(1, 16).optionalFieldOf("clear", 4).forGetter(Config::clear),
                Codec.intRange(1, 32).optionalFieldOf("cut", 8).forGetter(Config::cut),
                Codec.intRange(0, 32).optionalFieldOf("fill", 12).forGetter(Config::fill),
                Bridge.CODEC.optionalFieldOf("bridge", new Bridge("minecraft:spruce_planks", "minecraft:spruce_fence", "minecraft:spruce_log")).forGetter(Config::bridge)
        ).apply(i, Config::new));
    }

    /** Resolved blocks of a config (cached per config instance). */
    private static final class Blocks2 {
        final Map<String, BlockState[]> surface = new HashMap<>();
        final Map<String, int[]> weights = new HashMap<>();
        final Map<String, BlockState> slab = new HashMap<>();
        BlockState post, lantern, deck, railing, pillar;
    }

    private static final Map<Config, Blocks2> RESOLVED = new java.util.concurrent.ConcurrentHashMap<>();

    public DesignRoadFeature() {
        super(Config.CODEC);
    }

    @Override
    public boolean place(FeaturePlaceContext<Config> ctx) {
        CanonRasters r = DesignWorld.rasters();
        if (r == null || !r.hasRoads() || !DesignWorld.designGenerator(ctx.chunkGenerator())) return false;
        int x0 = ctx.origin().getX() & ~15, z0 = ctx.origin().getZ() & ~15;
        if (x0 + 16 <= r.boxX0() || z0 + 16 <= r.boxZ0() || x0 >= r.boxX1() || z0 >= r.boxZ1()) return false;
        Config c = ctx.config();
        Blocks2 b = RESOLVED.computeIfAbsent(c, DesignRoadFeature::resolve);
        WorldGenLevel level = ctx.level();
        CanonGrid grid = CanonMap.grid();
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        int minY = level.getMinBuildHeight();
        boolean[] bridge = new boolean[1];
        boolean any = false;
        boolean fromRoads = r.hasRoadLanterns(), marked = !fromRoads && r.hasLanternClass();
        Map<Long, Long> lanternCells = new HashMap<>();
        for (int dz = 0; dz < 16; dz++) {
            for (int dx = 0; dx < 16; dx++) {
                int x = x0 + dx, z = z0 + dz;
                int kind = r.road(x, z, bridge);
                if (kind < 0) {
                    boolean lantern = fromRoads ? r.lanternAt(x, z) : marked ? r.lanternMarked(x, z)
                            : c.lanternEvery() > 0 && heuristicLantern(r, c.lanternEvery(), x, z, lanternCells);
                    if (lantern) any |= post(level, r, b, pos, x, z, minY);
                    continue;
                }
                if (bridge[0] && bridgeColumn(level, r, b, c, pos, x, z, minY)) {
                    any = true;
                    continue;
                }
                String zone = kind == CanonRasters.ROAD_TRAIL && b.surface.containsKey("trail") ? "trail" : zone(grid, b, x, z);
                any |= roadColumn(level, r, b, c, pos, x, z, zone, minY);
            }
        }
        return any;
    }

    /** First air y of the road surface at a column (the designed corridor height, rounded). */
    static int roadY(CanonRasters r, int x, int z) {
        return (int) Math.floor(r.height(x + 0.5, z + 0.5) + 0.5);
    }

    private static boolean roadColumn(WorldGenLevel level, CanonRasters r, Blocks2 b, Config c, BlockPos.MutableBlockPos pos, int x, int z, String zone, int minY) {
        int ry = roadY(r, x, z), s = ry - 1;
        if (s <= minY + 1 || ry >= level.getMaxBuildHeight() - c.clear() - 1) return false;
        int ground = DesignWaterFeature.groundBelow(level, pos, x, z, s + c.cut(), minY);
        if (ground < s) {
            for (int y = Math.max(ground + 1, s - c.fill()); y < s; y++) level.setBlock(pos.set(x, y, z), net.minecraft.world.level.block.Blocks.DIRT.defaultBlockState(), 2);
        }
        level.setBlock(pos.set(x, s, z), pick(b, zone, x, z), 2);
        int top = Math.max(s + c.clear(), Math.min(ground, s + c.cut()));
        boolean slab = false;
        boolean[] nb = new boolean[1];
        for (int k = 0; k < 4 && !slab; k++) {
            int nx = x + (k == 0 ? 1 : k == 1 ? -1 : 0), nz = z + (k == 2 ? 1 : k == 3 ? -1 : 0);
            if (r.road(nx, nz, nb) >= 0 && !nb[0] && roadY(r, nx, nz) == ry + 1) slab = true;
        }
        for (int y = s + 1; y <= top; y++) {
            BlockState want = y == ry && slab ? b.slab.getOrDefault(zone, b.slab.get("default")) : net.minecraft.world.level.block.Blocks.AIR.defaultBlockState();
            if (!level.getBlockState(pos.set(x, y, z)).equals(want)) level.setBlock(pos, want, 2);
        }
        // A trunk standing on the road goes entirely (no log floating over the road); its leaves decay on their own.
        for (int y = top + 1; y <= Math.min(top + 24, level.getMaxBuildHeight() - 1); y++) {
            if (!level.getBlockState(pos.set(x, y, z)).is(net.minecraft.tags.BlockTags.LOGS)) break;
            level.setBlock(pos, net.minecraft.world.level.block.Blocks.AIR.defaultBlockState(), 2);
        }
        return true;
    }

    /** A bridge column: deck 2 above the water's top block, railing on the edge, a pillar every 5 blocks of edge. */
    private static boolean bridgeColumn(WorldGenLevel level, CanonRasters r, Blocks2 b, Config c, BlockPos.MutableBlockPos pos, int x, int z, int minY) {
        int water = r.waterLevelNear(x, z, 8);
        if (water == Integer.MIN_VALUE) return false; // no water by it: an ordinary road column
        int deck = water + 1;
        if (deck >= level.getMaxBuildHeight() - c.clear() - 1) return false;
        level.setBlock(pos.set(x, deck, z), b.deck, 2);
        boolean edge = railing(r, x, z);
        for (int y = deck + 1; y <= deck + c.clear(); y++) {
            BlockState want = y == deck + 1 && edge ? fence(b.railing, r, x, z) : net.minecraft.world.level.block.Blocks.AIR.defaultBlockState();
            if (!level.getBlockState(pos.set(x, y, z)).equals(want)) level.setBlock(pos, want, 2);
        }
        if (edge && Math.floorMod(x + z, 5) == 0) {
            for (int y = deck - 1; y > Math.max(minY, deck - 48); y--) {
                BlockState s = level.getBlockState(pos.set(x, y, z));
                if (!s.isAir() && s.getFluidState().isEmpty() && !DesignWaterFeature.replaceable(s)) break;
                level.setBlock(pos, b.pillar, 2);
            }
        }
        return true;
    }

    /** A bridge column on the corridor's edge (a non-road column beside it). */
    static boolean railing(CanonRasters r, int x, int z) {
        boolean[] br = new boolean[1];
        if (r.road(x, z, br) < 0 || !br[0]) return false;
        for (int k = 0; k < 4; k++) {
            int nx = x + (k == 0 ? 1 : k == 1 ? -1 : 0), nz = z + (k == 2 ? 1 : k == 3 ? -1 : 0);
            if (r.road(nx, nz, new boolean[1]) < 0) return true;
        }
        return false;
    }

    /** The railing fence with its connections to the neighbouring railing columns (decided from the raster). */
    private static BlockState fence(BlockState base, CanonRasters r, int x, int z) {
        if (!(base.getBlock() instanceof CrossCollisionBlock)) return base;
        return base.setValue(CrossCollisionBlock.EAST, railing(r, x + 1, z)).setValue(CrossCollisionBlock.WEST, railing(r, x - 1, z))
                .setValue(CrossCollisionBlock.SOUTH, railing(r, x, z + 1)).setValue(CrossCollisionBlock.NORTH, railing(r, x, z - 1));
    }

    /** Fence post with a lantern on the ground of a column (not on water). */
    private static boolean post(WorldGenLevel level, CanonRasters r, Blocks2 b, BlockPos.MutableBlockPos pos, int x, int z, int minY) {
        int from = (int) Math.ceil(r.height(x + 0.5, z + 0.5)) + 8;
        int ground = DesignWaterFeature.groundBelow(level, pos, x, z, Math.min(from, level.getMaxBuildHeight() - 4), minY);
        if (ground <= minY + 1 || ground + 3 >= level.getMaxBuildHeight()) return false;
        if (!level.getBlockState(pos.set(x, ground + 1, z)).getFluidState().isEmpty()) return false;
        level.setBlock(pos.set(x, ground + 1, z), b.post, 2);
        level.setBlock(pos.set(x, ground + 2, z), b.post, 2);
        level.setBlock(pos.set(x, ground + 3, z), b.lantern, 2);
        return true;
    }

    /** A lantern candidate: not road, beside a main (non-bridge) road column. */
    static boolean candidate(CanonRasters r, int x, int z) {
        boolean[] br = new boolean[1];
        if (r.road(x, z, br) >= 0) return false;
        for (int k = 0; k < 4; k++) {
            int nx = x + (k == 0 ? 1 : k == 1 ? -1 : 0), nz = z + (k == 2 ? 1 : k == 3 ? -1 : 0);
            if (r.road(nx, nz, br) == CanonRasters.ROAD_MAIN && !br[0]) return true;
        }
        return false;
    }

    /**
     * True when the column is its cell's lantern: of all candidates in its {@code every} x {@code every} cell, the one
     * nearest the cell's hashed target (ties: smaller x, then z). The pick per cell is memoised for the chunk.
     */
    static boolean heuristicLantern(CanonRasters r, int every, int x, int z, Map<Long, Long> memo) {
        if (!candidate(r, x, z)) return false;
        int cx = Math.floorDiv(x, every), cz = Math.floorDiv(z, every);
        long key = ((long) cx << 32) ^ (cz & 0xFFFFFFFFL);
        Long chosen = memo.get(key);
        if (chosen == null) {
            long h = CanonPalette.mix(cx * 0x9E3779B97F4A7C15L ^ cz * 0xC2B2AE3D27D4EB4FL ^ 0x1A2B3C4D5E6F7788L);
            int tx = cx * every + (int) ((h >>> 8) % every), tz = cz * every + (int) ((h >>> 40) % every);
            long best = Long.MAX_VALUE, bestD = Long.MAX_VALUE;
            for (int zz = cz * every; zz < cz * every + every; zz++) {
                for (int xx = cx * every; xx < cx * every + every; xx++) {
                    long d = (long) (xx - tx) * (xx - tx) + (long) (zz - tz) * (zz - tz);
                    if (d >= bestD || !candidate(r, xx, zz)) continue;
                    bestD = d;
                    best = ((long) xx << 32) ^ (zz & 0xFFFFFFFFL);
                }
            }
            memo.put(key, chosen = best);
        }
        return chosen == (((long) x << 32) ^ (z & 0xFFFFFFFFL));
    }

    private static String zone(@Nullable CanonGrid grid, Blocks2 b, int x, int z) {
        if (grid == null) return "default";
        char owner = grid.ownerCell(x, z);
        String key = owner == 0 ? "default" : String.valueOf(owner);
        return b.surface.containsKey(key) ? key : "default";
    }

    private static BlockState pick(Blocks2 b, String zone, int x, int z) {
        BlockState[] states = b.surface.getOrDefault(zone, b.surface.get("default"));
        int[] weights = b.weights.getOrDefault(zone, b.weights.get("default"));
        int total = weights[weights.length - 1];
        int h = (int) ((CanonPalette.mix(x * 0x632BE59BD9B4E019L ^ z * 0x9E3779B97F4A7C15L ^ 0x5BD1E995L) >>> 33) % total);
        for (int i = 0; i < weights.length; i++) if (h < weights[i]) return states[i];
        return states[states.length - 1];
    }

    private static Blocks2 resolve(Config c) {
        Blocks2 b = new Blocks2();
        for (Map.Entry<String, Palette> e : c.palettes().entrySet()) {
            Map<String, Integer> sorted = new TreeMap<>(e.getValue().surface());
            BlockState[] states = new BlockState[sorted.size()];
            int[] cumulative = new int[sorted.size()];
            int i = 0, sum = 0;
            for (Map.Entry<String, Integer> s : sorted.entrySet()) {
                states[i] = block(s.getKey(), net.minecraft.world.level.block.Blocks.DIRT_PATH);
                sum += s.getValue();
                cumulative[i++] = sum;
            }
            if (states.length == 0) continue;
            b.surface.put(e.getKey(), states);
            b.weights.put(e.getKey(), cumulative);
            BlockState slab = block(e.getValue().slab(), net.minecraft.world.level.block.Blocks.COBBLESTONE_SLAB);
            if (slab.getBlock() instanceof SlabBlock) slab = slab.setValue(SlabBlock.TYPE, SlabType.BOTTOM);
            b.slab.put(e.getKey(), slab);
        }
        if (!b.surface.containsKey("default")) {
            b.surface.put("default", new BlockState[] {net.minecraft.world.level.block.Blocks.DIRT_PATH.defaultBlockState()});
            b.weights.put("default", new int[] {1});
            b.slab.put("default", net.minecraft.world.level.block.Blocks.COBBLESTONE_SLAB.defaultBlockState());
        }
        b.post = block(c.post(), net.minecraft.world.level.block.Blocks.SPRUCE_FENCE);
        b.lantern = block(c.lantern(), net.minecraft.world.level.block.Blocks.LANTERN);
        b.deck = block(c.bridge().deck(), net.minecraft.world.level.block.Blocks.SPRUCE_PLANKS);
        b.railing = block(c.bridge().railing(), net.minecraft.world.level.block.Blocks.SPRUCE_FENCE);
        b.pillar = block(c.bridge().pillar(), net.minecraft.world.level.block.Blocks.SPRUCE_LOG);
        return b;
    }

    private static BlockState block(String id, Block fallback) {
        ResourceLocation key = ResourceLocation.tryParse(id);
        Block block = key == null ? null : BuiltInRegistries.BLOCK.getOptional(key).orElse(null);
        return (block == null || block == net.minecraft.world.level.block.Blocks.AIR ? fallback : block).defaultBlockState();
    }
}
