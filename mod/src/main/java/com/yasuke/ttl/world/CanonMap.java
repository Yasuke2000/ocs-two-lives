package com.yasuke.ttl.world;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.logging.LogUtils;
import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import com.yasuke.ttl.TtlPortals;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import net.minecraft.core.registries.Registries;
import net.minecraft.util.KeyDispatchDataCodec;
import net.minecraft.util.StringRepresentable;
import net.minecraft.world.level.levelgen.DensityFunction;
import net.neoforged.fml.loading.FMLPaths;
import net.neoforged.neoforge.event.server.ServerAboutToStartEvent;
import net.neoforged.neoforge.registries.DeferredRegister;
import org.jetbrains.annotations.Nullable;
import org.slf4j.Logger;

/**
 * Density function {@code ttl:canon_map}: inside the canon continent (pack/config/ttl/canon_map.txt) it
 * steers one climate channel of the overworld noise router, and returns {@code outside} (vanilla) beyond
 * the open-sea ring; per-build {@link CanonSites}, when the file still has any, steer it further around canon builds
 * (ridges only there). Inside Lerfing's imported area ({@link CanonGrid#imported}) the chunks exist on disk and none
 * of this is asked: it only shapes the generated ring round the import and blends into vanilla beyond it.
 * The vanilla overworld router is wrapped through pack/kubejs/data/minecraft/worldgen.
 */
public record CanonMap(Channel channel, DensityFunction outside) implements DensityFunction {
    private static final Logger LOGGER = LogUtils.getLogger();

    public static final MapCodec<CanonMap> MAP_CODEC = RecordCodecBuilder.mapCodec(i -> i.group(
            Channel.CODEC.fieldOf("channel").forGetter(CanonMap::channel),
            DensityFunction.HOLDER_HELPER_CODEC.fieldOf("outside").forGetter(CanonMap::outside)
    ).apply(i, CanonMap::new));
    private static final KeyDispatchDataCodec<CanonMap> CODEC = KeyDispatchDataCodec.of(MAP_CODEC);

    public static final DeferredRegister<MapCodec<? extends DensityFunction>> TYPES =
            DeferredRegister.create(Registries.DENSITY_FUNCTION_TYPE, TtlPortals.MOD_ID);

    static {
        TYPES.register("canon_map", () -> MAP_CODEC);
        TYPES.register("canon_sites", () -> CanonSiteTerrain.MAP_CODEC);
        DesignDensity.register(TYPES);
    }

    public enum Channel implements StringRepresentable {
        CONTINENTS("continents", -1),
        EROSION("erosion", CanonGrid.EROSION),
        TEMPERATURE("temperature", CanonGrid.TEMPERATURE),
        VEGETATION("vegetation", CanonGrid.VEGETATION),
        /** Weirdness: only the canon sites steer it (mountain intents), everywhere else it is vanilla's. */
        RIDGES("ridges", -2);

        public static final Codec<Channel> CODEC = StringRepresentable.fromEnum(Channel::values);
        private final String name;
        final int index;

        Channel(String name, int index) {
            this.name = name;
            this.index = index;
        }

        @Override
        public String getSerializedName() {
            return name;
        }
    }

    @Override
    public double compute(FunctionContext ctx) {
        double o = outside.compute(ctx);
        CanonGrid grid = grid();
        return grid == null ? o : apply(grid, ctx.blockX(), ctx.blockZ(), o);
    }

    @Override
    public void fillArray(double[] values, ContextProvider provider) {
        outside.fillArray(values, provider);
        CanonGrid grid = grid();
        if (grid == null) return;
        for (int i = 0; i < values.length; i++) {
            FunctionContext ctx = provider.forIndex(i);
            values[i] = apply(grid, ctx.blockX(), ctx.blockZ(), values[i]);
        }
    }

    public double apply(CanonGrid grid, int x, int z, double o) {
        return switch (channel) {
            case CONTINENTS -> grid.continents(x, z, o);
            case RIDGES -> grid.ridges(x, z, o);
            default -> grid.climate(channel.index, x, z, o);
        };
    }

    @Override
    public DensityFunction mapAll(Visitor visitor) {
        return visitor.apply(new CanonMap(channel, outside.mapAll(visitor)));
    }

    // Static bounds: they are read when the router is built, possibly before the grid has loaded.
    @Override
    public double minValue() {
        double o = outside.minValue();
        return channel == Channel.CONTINENTS ? Math.min(o, CanonGrid.CONT_MIN) : Math.min(o, -1);
    }

    @Override
    public double maxValue() {
        double o = outside.maxValue();
        // Mountain sites may lift continentalness up to 1 (CanonSites.Terrain.MOUNTAIN targets 0.75).
        return channel == Channel.CONTINENTS ? Math.max(o, Math.max(1, CanonGrid.CONT_MAX + CanonGrid.WIGGLE * Math.max(0, o))) : Math.max(o, 1);
    }

    @Override
    public KeyDispatchDataCodec<? extends DensityFunction> codec() {
        return CODEC;
    }

    // ---- grid data: loaded lazily once per server start, shared by all worldgen threads ----

    private static final Object MISSING = new Object();
    private static final Object LOCK = new Object();
    private static volatile Object state;

    @Nullable
    public static CanonGrid grid() {
        Object s = state;
        if (s == null) {
            synchronized (LOCK) {
                s = state;
                if (s == null) state = s = load();
            }
        }
        return s instanceof CanonGrid grid ? grid : null;
    }

    public static void onServerAboutToStart(ServerAboutToStartEvent event) {
        state = null;
    }

    private static Object load() {
        Path dir = FMLPaths.CONFIGDIR.get().resolve("ttl");
        try {
            JsonObject json = JsonParser.parseString(Files.readString(dir.resolve("canon_regions.json"), StandardCharsets.UTF_8)).getAsJsonObject();
            Map<Character, CanonGrid.Region> regions = CanonConfig.regions(json, msg -> LOGGER.warn("[ttl] {}", msg));
            CanonSites sites = CanonConfig.sites(json, msg -> LOGGER.warn("[ttl] {}", msg));
            double ring = json.has("ring") ? json.get("ring").getAsDouble() : 1600;
            double blend = json.has("blend") ? json.get("blend").getAsDouble() : 800;
            long start = System.nanoTime();
            int[] inner = CanonConfig.importBox(json, msg -> LOGGER.warn("[ttl] {}", msg));
            DesignWorld.Loaded design = DesignWorld.loaded(); // the own world's site plates (sites.json), when its rasters are present
            if (design != null) sites = DesignSitesFile.merge(sites, design.sites());
            CanonGrid grid = CanonGrid.load(dir.resolve("canon_map.txt"), regions, ring, blend).withSites(sites).withImport(inner);
            LOGGER.info("[ttl] canon map loaded in {} ms: {}", (System.nanoTime() - start) / 1_000_000, grid.describe());
            return grid;
        } catch (Exception e) {
            LOGGER.warn("[ttl] canon map not loaded from {} ({}); the Tensura world generates vanilla terrain", dir, e.toString());
            return MISSING;
        }
    }
}
