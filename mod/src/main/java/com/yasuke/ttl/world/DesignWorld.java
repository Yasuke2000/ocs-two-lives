package com.yasuke.ttl.world;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.logging.LogUtils;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.NoiseBasedChunkGenerator;
import net.neoforged.fml.loading.FMLPaths;
import net.neoforged.neoforge.event.server.ServerAboutToStartEvent;
import org.jetbrains.annotations.Nullable;
import org.slf4j.Logger;

/**
 * The own world's design data for this server start: {@link CanonRasters} from config/ttl/world/ and the sites of
 * {@code sites.json} next to them. Loaded once (lazily, or eagerly at server start), shared read-only by every worldgen
 * thread. Without a usable raster set it is absent and the world generates exactly as before (the canon map ring and
 * vanilla): every design density function, feature, biome branch and structure filter checks {@link #rasters()} first.
 */
public final class DesignWorld {
    private static final Logger LOGGER = LogUtils.getLogger();
    private static final Object LOCK = new Object();
    private static final Object MISSING = new Object();
    private static volatile Object state;

    /** Loaded design: rasters, the extra flat sites for {@link CanonSites}, and the site list for /ttlsite. */
    public record Loaded(CanonRasters rasters, CanonSites sites, List<DesignSitesFile.Info> infos) {}

    private DesignWorld() {}

    public static Path dir() {
        return FMLPaths.CONFIGDIR.get().resolve("ttl").resolve("world");
    }

    @Nullable
    public static Loaded loaded() {
        Object s = state;
        if (s == null) {
            synchronized (LOCK) {
                s = state;
                if (s == null) state = s = load(dir());
            }
        }
        return s instanceof Loaded l ? l : null;
    }

    @Nullable
    public static CanonRasters rasters() {
        Loaded l = loaded();
        return l == null ? null : l.rasters();
    }

    /** Self-check hook: pretend this load result (null = no rasters) without touching the config folder. */
    static void setForTest(@Nullable Loaded loaded) {
        state = loaded == null ? MISSING : loaded;
    }

    /** Server start: forget the last load and read the files again (before CanonMap's grid, which merges our sites). */
    public static void onServerAboutToStart(ServerAboutToStartEvent event) {
        state = null;
        for (int i = 0; i < 3; i++) EXCLUDED.set(i, 0);
        LOGGED.clear();
        loaded();
    }

    /** Blocks under the designed surface below which a structure may pass under a site or a road (mineshafts, dungeons). */
    public static final int EXCLUSION_DEPTH = 16;
    private static final java.util.concurrent.atomic.AtomicLongArray EXCLUDED = new java.util.concurrent.atomic.AtomicLongArray(3);
    private static final java.util.Set<String> LOGGED = java.util.concurrent.ConcurrentHashMap.newKeySet();

    /**
     * The structure filter (mixin.ChunkGeneratorMixin): true when a valid start of the Tensura world's generator would
     * touch a site box, a road corridor or the Dwargon cavity of the design (see {@link CanonRasters#excludes}).
     */
    public static boolean excludesStart(ChunkGenerator generator, net.minecraft.world.level.levelgen.structure.StructureStart start) {
        CanonRasters r = rasters();
        if (r == null || !designGenerator(generator)) return false;
        net.minecraft.world.level.levelgen.structure.BoundingBox box = start.getBoundingBox();
        int why = r.excludes(box.minX(), box.minY(), box.minZ(), box.maxX(), box.maxY(), box.maxZ(), EXCLUSION_DEPTH);
        if (why == 0) return false;
        int k = (why & CanonRasters.CAVITY) != 0 ? 2 : (why & CanonRasters.SITE) != 0 ? 0 : 1;
        EXCLUDED.incrementAndGet(k);
        String id = start.getStructure() == null ? "?" : String.valueOf(net.minecraft.core.registries.BuiltInRegistries.STRUCTURE_TYPE.getKey(start.getStructure().type()));
        if (LOGGED.size() < 64 && LOGGED.add(id + k)) {
            LOGGER.info("[ttl] own world: a {} start at {} {} kept out of a designed {} (box {}..{}, {}..{}); further ones counted in /ttlsite status",
                    id, box.getCenter().getX(), box.getCenter().getZ(), k == 0 ? "site" : k == 1 ? "road" : "cavity", box.minX(), box.maxX(), box.minZ(), box.maxZ());
        }
        return true;
    }

    /** Structure starts dropped since the server started: {site, road, cavity}. */
    public static long[] excludedCounts() {
        return new long[] {EXCLUDED.get(0), EXCLUDED.get(1), EXCLUDED.get(2)};
    }

    /** True for the Tensura world's generator (biome source ttl:canon_biomes), never for Life 1's dimensions. */
    public static boolean designGenerator(ChunkGenerator generator) {
        return generator instanceof NoiseBasedChunkGenerator && generator.getBiomeSource() instanceof CanonBiomes;
    }

    static Object load(Path dir) {
        long start = System.nanoTime();
        CanonRasters rasters = CanonRasters.load(dir, msg -> LOGGER.warn("[ttl] {}", msg));
        if (rasters == null) {
            LOGGER.info("[ttl] own world: no design rasters in {}; terrain, biomes and structures as before", dir);
            return MISSING;
        }
        CanonSites sites = CanonSites.NONE;
        List<DesignSitesFile.Info> infos = List.of();
        Path file = dir.resolve("sites.json");
        if (Files.isRegularFile(file)) {
            try {
                JsonObject json = DesignSitesFile.normalise(JsonParser.parseString(Files.readString(file, StandardCharsets.UTF_8)), msg -> LOGGER.warn("[ttl] {}", msg));
                sites = CanonConfig.sites(DesignSitesFile.forCanonSites(json), msg -> LOGGER.warn("[ttl] {}", msg));
                infos = DesignSitesFile.infos(json, msg -> LOGGER.warn("[ttl] {}", msg));
            } catch (Exception e) {
                LOGGER.warn("[ttl] own world: sites.json unreadable ({}); no design sites", e.toString());
            }
        }
        List<DesignSitesFile.Info> indexed = DesignSitesFile.infosFromIndex(rasters.legend(), msg -> LOGGER.warn("[ttl] {}", msg));
        if (!indexed.isEmpty()) infos = indexed; // index.json also lists the carve sites
        LOGGER.info("[ttl] own world: design rasters loaded in {} ms: {}; {} sites ({} flat plates)",
                (System.nanoTime() - start) / 1_000_000, rasters.describe(), infos.size(), countFlat(sites));
        return new Loaded(rasters, sites, infos);
    }

    private static int countFlat(CanonSites sites) {
        int n = 0;
        for (int i = 0; i < sites.size(); i++) if (sites.site(i).terrain() == CanonSites.Terrain.FLAT) n++;
        return n;
    }
}
