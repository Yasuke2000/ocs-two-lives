package com.yasuke.ttl.world;

import com.mojang.datafixers.util.Pair;
import com.mojang.logging.LogUtils;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import com.yasuke.ttl.TtlPortals;
import java.lang.invoke.MethodHandle;
import java.lang.invoke.MethodHandles;
import java.lang.invoke.MethodType;
import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.function.Consumer;
import java.util.stream.Stream;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderGetter;
import net.minecraft.core.QuartPos;
import net.minecraft.core.Registry;
import net.minecraft.core.RegistryAccess;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.RegistryOps;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.biome.BiomeSource;
import net.minecraft.world.level.biome.Climate;
import net.minecraft.world.level.biome.MultiNoiseBiomeSourceParameterList;
import net.minecraft.world.level.dimension.LevelStem;
import net.minecraft.world.level.levelgen.NoiseBasedChunkGenerator;
import net.minecraft.world.level.levelgen.NoiseGeneratorSettings;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.ModList;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.server.ServerAboutToStartEvent;
import org.jetbrains.annotations.Nullable;
import org.slf4j.Logger;

/**
 * {@code ttl:canon_biomes}: the Tensura world's biome source. The canon_map density functions still shape the
 * terrain; this picks the biome on top of it, per nation, from the weighted palettes in canon_regions.json.
 *
 * <p>Per quart position: vanilla's choice from the preset (plain {@code findValue}, no TerraBlender) is kept for
 * water, shores, rivers, mushroom fields and cave biomes, and for peaks/slopes unless the nation sets
 * {@code replace_peaks}; ocean picked inside a canon lake ('~') becomes river. Any other land inside a nation
 * (letter at the dithered block, nearest nation for '~' and coastal water) takes a palette biome, laid out in
 * patches of roughly 200-500 blocks by {@link CanonPalette#patch}. Everywhere else (the open sea, the free lands
 * beyond the ring, nations without a palette) it behaves like the normal overworld: TerraBlender's positional
 * lookup when TerraBlender is installed, vanilla otherwise. Missing or broken data means exactly that everywhere.
 *
 * <p>TerraBlender only sets itself up for MultiNoiseBiomeSource, so {@link #onServerAboutToStart} does what its
 * LevelUtils would have: region lookup on a private copy of the parameter list, its region biomes added to the
 * possible biomes, and the OVERWORLD surface-rule category on the generator's noise settings (without it Tensura's
 * biomes would lose their surface rules). It is reached by reflection: TerraBlender is optional at compile time.
 */
@EventBusSubscriber(modid = TtlPortals.MOD_ID)
public final class CanonBiomes extends BiomeSource {
    private static final Logger LOGGER = LogUtils.getLogger();

    public static final MapCodec<CanonBiomes> CODEC = RecordCodecBuilder.mapCodec(i -> i.group(
            MultiNoiseBiomeSourceParameterList.CODEC.fieldOf("preset").forGetter(s -> s.preset),
            RegistryOps.retrieveGetter(Registries.BIOME)
    ).apply(i, CanonBiomes::new));

    static final byte LAND = 0, KEEP = 1, OCEAN = 2, FROZEN_OCEAN = 3, PEAK = 4;
    private static final Map<String, Byte> VANILLA_KINDS = Map.ofEntries(
            Map.entry("ocean", OCEAN), Map.entry("deep_ocean", OCEAN), Map.entry("cold_ocean", OCEAN),
            Map.entry("deep_cold_ocean", OCEAN), Map.entry("lukewarm_ocean", OCEAN), Map.entry("deep_lukewarm_ocean", OCEAN),
            Map.entry("warm_ocean", OCEAN), Map.entry("frozen_ocean", FROZEN_OCEAN), Map.entry("deep_frozen_ocean", FROZEN_OCEAN),
            Map.entry("beach", KEEP), Map.entry("snowy_beach", KEEP), Map.entry("stony_shore", KEEP),
            Map.entry("river", KEEP), Map.entry("frozen_river", KEEP), Map.entry("mushroom_fields", KEEP),
            Map.entry("lush_caves", KEEP), Map.entry("dripstone_caves", KEEP), Map.entry("deep_dark", KEEP),
            Map.entry("jagged_peaks", PEAK), Map.entry("frozen_peaks", PEAK), Map.entry("stony_peaks", PEAK),
            Map.entry("snowy_slopes", PEAK), Map.entry("grove", PEAK));
    private static final Byte LAND_BOXED = LAND;

    private final Holder<MultiNoiseBiomeSourceParameterList> preset;
    private final HolderGetter<Biome> biomes;
    private final Object lock = new Object();
    private volatile Resolved resolved;
    private volatile long seed;
    @Nullable
    private volatile MethodHandle terraBlender; // (TargetPoint, int, int, int) -> Object, bound to our parameter list

    private CanonBiomes(Holder<MultiNoiseBiomeSourceParameterList> preset, HolderGetter<Biome> biomes) {
        this.preset = preset;
        this.biomes = biomes;
    }

    private Climate.ParameterList<Holder<Biome>> parameters() {
        return preset.value().parameters();
    }

    @Override
    protected MapCodec<? extends BiomeSource> codec() {
        return CODEC;
    }

    @Override
    protected Stream<Holder<Biome>> collectPossibleBiomes() {
        return Stream.concat(parameters().values().stream().map(Pair::getSecond), resolved().paletteBiomes.stream());
    }

    @Override
    public Holder<Biome> getNoiseBiome(int x, int y, int z, Climate.Sampler sampler) {
        return select(x, y, z, sampler, null);
    }

    /** The biome and, when {@code why} is given, the rule that chose it (for /ttlmap). */
    public Holder<Biome> select(int x, int y, int z, Climate.Sampler sampler, @Nullable StringBuilder why) {
        Climate.TargetPoint target = sampler.sample(x, y, z);
        Resolved r = resolved();
        CanonGrid grid = r.grid;
        if (grid == null) return outside(target, x, y, z, why, "canon map not loaded");
        int bx = QuartPos.toBlock(x) + 2, bz = QuartPos.toBlock(z) + 2;
        char owner = grid.ownerAt(bx, bz, seed);
        if (owner == 0) return outside(target, x, y, z, why, "outside the canon land");

        Holder<Biome> vanilla = parameters().findValue(target);
        byte kind = r.kinds.getOrDefault(vanilla, LAND_BOXED);
        if (kind == OCEAN || kind == FROZEN_OCEAN) {
            if (grid.riverWeight(bx, bz) >= 0.5) {
                boolean frozen = owner < r.frozen.length ? r.frozen[owner] || (kind == FROZEN_OCEAN && !r.hasTemperature[owner]) : kind == FROZEN_OCEAN;
                Holder<Biome> river = frozen ? r.frozenRiver : r.river;
                if (river != null) {
                    if (why != null) why.append("lake/river: canon '~' below sea level is river, not ocean");
                    return river;
                }
            }
            if (why != null) why.append("vanilla kept (ocean)");
            return vanilla;
        }
        if (kind == KEEP) {
            if (why != null) why.append("vanilla kept (shore/river/mushroom/cave)");
            return vanilla;
        }
        RegionPalette palette = owner < r.regions.length ? r.regions[owner] : null;
        if (palette == null) return outside(target, x, y, z, why, grid.regionName(owner) + " has no palette");
        boolean peaks = kind == PEAK;
        if (peaks && !palette.replacePeaks) {
            if (why != null) why.append("vanilla kept (peak/slope; ").append(palette.name).append(" has no replace_peaks)");
            return vanilla;
        }
        CanonPalette pick = peaks && palette.peaks != null ? palette.peaks : palette.land;
        Holder<Biome>[] holders = peaks && palette.peaks != null ? palette.peakHolders : palette.landHolders;
        Holder<Biome> chosen = holders[pick.pickAt(seed, owner, peaks, bx, bz)];
        if (why != null) why.append("palette of ").append(palette.name).append(peaks ? " (peaks)" : "").append(", vanilla would be ")
                .append(vanilla.unwrapKey().map(k -> k.location().toString()).orElse("?"));
        return chosen;
    }

    private Holder<Biome> outside(Climate.TargetPoint target, int x, int y, int z, @Nullable StringBuilder why, String reason) {
        MethodHandle tb = terraBlender;
        if (tb != null) {
            try {
                Object biome = (Object) tb.invokeExact(target, x, y, z);
                if (why != null) why.append(reason).append(": TerraBlender regions");
                @SuppressWarnings("unchecked") Holder<Biome> holder = (Holder<Biome>) biome;
                return holder;
            } catch (Throwable t) {
                terraBlender = null;
                LOGGER.error("[ttl] canon biomes: TerraBlender lookup failed, vanilla biomes from now on", t);
            }
        }
        if (why != null) why.append(reason).append(": vanilla (no TerraBlender lookup)");
        return parameters().findValue(target);
    }

    // ---- palette data, resolved once per biome source ----

    private record RegionPalette(String name, CanonPalette land, Holder<Biome>[] landHolders, boolean replacePeaks,
                                 @Nullable CanonPalette peaks, @Nullable Holder<Biome>[] peakHolders) {}

    private static final class Resolved {
        @Nullable final CanonGrid grid;
        final IdentityHashMap<Holder<Biome>, Byte> kinds = new IdentityHashMap<>();
        final RegionPalette[] regions = new RegionPalette[128];
        final boolean[] frozen = new boolean[128], hasTemperature = new boolean[128]; // temperature knob < -0.45: frozen_river
        final List<Holder<Biome>> paletteBiomes = new ArrayList<>();
        @Nullable Holder<Biome> river, frozenRiver;

        Resolved(@Nullable CanonGrid grid) {
            this.grid = grid;
        }
    }

    private Resolved resolved() {
        Resolved r = resolved;
        if (r == null) {
            synchronized (lock) {
                r = resolved;
                if (r == null) resolved = r = resolve();
            }
        }
        return r;
    }

    private Resolved resolve() {
        Resolved vanillaOnly = new Resolved(null);
        try {
            CanonGrid grid = CanonMap.grid();
            Resolved r = grid == null ? vanillaOnly : new Resolved(grid);
            for (Pair<Climate.ParameterPoint, Holder<Biome>> entry : parameters().values()) {
                Holder<Biome> biome = entry.getSecond();
                Optional<ResourceKey<Biome>> key = biome.unwrapKey();
                if (key.isEmpty()) continue;
                ResourceLocation id = key.get().location();
                byte kind = id.getNamespace().equals("minecraft") ? VANILLA_KINDS.getOrDefault(id.getPath(), LAND) : LAND;
                r.kinds.put(biome, kind);
                if (id.getPath().equals("river") && id.getNamespace().equals("minecraft")) r.river = biome;
                if (id.getPath().equals("frozen_river") && id.getNamespace().equals("minecraft")) r.frozenRiver = biome;
            }
            if (grid == null) return r;
            List<String> nations = new ArrayList<>();
            Set<String> unknown = new java.util.TreeSet<>();
            for (Map.Entry<Character, CanonGrid.Region> e : grid.regionMap().entrySet()) {
                char c = e.getKey();
                CanonGrid.Region region = e.getValue();
                if (c >= r.regions.length) continue;
                r.hasTemperature[c] = region.temperature() != null;
                r.frozen[c] = region.temperature() != null && region.temperature() < -0.45;
                if (region.biomes() == null) continue;
                CanonPalette land = known(region.biomes(), unknown);
                if (land == null) continue;
                CanonPalette peaks = region.peaks() == null ? null : known(region.peaks(), unknown);
                Holder<Biome>[] landHolders = holders(land, r), peakHolders = peaks == null ? null : holders(peaks, r);
                r.regions[c] = new RegionPalette(region.name(), land, landHolders, region.replacePeaks(), peaks, peakHolders);
                nations.add(c + "=" + land.size() + (region.replacePeaks() ? "+peaks" : ""));
            }
            if (!unknown.isEmpty()) LOGGER.warn("[ttl] canon biomes: unknown biome ids skipped: {}", unknown);
            LOGGER.info("[ttl] canon biomes: palettes for {} nations {}", nations.size(), nations);
            return r;
        } catch (RuntimeException e) {
            LOGGER.error("[ttl] canon biomes: palette data unusable, the Tensura world gets normal overworld biomes", e);
            return vanillaOnly;
        }
    }

    @Nullable
    private CanonPalette known(CanonPalette palette, Set<String> unknown) {
        return palette.filter(id -> {
            boolean ok = lookup(id).isPresent();
            if (!ok) unknown.add(id);
            return ok;
        });
    }

    private Optional<? extends Holder<Biome>> lookup(String id) {
        ResourceLocation location = ResourceLocation.tryParse(id);
        return location == null ? Optional.empty() : biomes.get(ResourceKey.create(Registries.BIOME, location));
    }

    @SuppressWarnings("unchecked")
    private Holder<Biome>[] holders(CanonPalette palette, Resolved r) {
        String[] ids = palette.ids();
        Holder<Biome>[] out = new Holder[ids.length];
        for (int i = 0; i < ids.length; i++) {
            out[i] = lookup(ids[i]).orElseThrow();
            r.paletteBiomes.add(out[i]);
        }
        return out;
    }

    // ---- server start: seed + TerraBlender wiring ----

    @SubscribeEvent(priority = EventPriority.LOW) // after CanonMap's reset (NORMAL), before any level exists
    public static void onServerAboutToStart(ServerAboutToStartEvent event) {
        MinecraftServer server = event.getServer();
        long seed = server.getWorldData().worldGenOptions().seed();
        for (LevelStem stem : server.registryAccess().registryOrThrow(Registries.LEVEL_STEM)) {
            if (stem.generator() instanceof NoiseBasedChunkGenerator generator && generator.getBiomeSource() instanceof CanonBiomes source) {
                source.initialize(server.registryAccess(), seed, generator.generatorSettings().value());
            }
        }
    }

    private void initialize(RegistryAccess access, long seed, NoiseGeneratorSettings settings) {
        this.seed = seed;
        this.terraBlender = null;
        if (!ModList.get().isLoaded("terrablender")) {
            LOGGER.info("[ttl] canon biomes: no TerraBlender, vanilla biomes outside the palettes");
            return;
        }
        ClassLoader loader = CanonBiomes.class.getClassLoader();
        try {
            Class<?> category = Class.forName("terrablender.api.SurfaceRuleManager$RuleCategory", true, loader);
            Class.forName("terrablender.worldgen.IExtendedNoiseGeneratorSettings", true, loader)
                    .getMethod("setRuleCategory", category).invoke(settings, enumConstant(category, "OVERWORLD"));
        } catch (ReflectiveOperationException | RuntimeException e) {
            LOGGER.error("[ttl] canon biomes: could not enable TerraBlender surface rules; Tensura biomes get plain overworld surfaces", e);
        }
        try {
            Class<?> regionType = Class.forName("terrablender.api.RegionType", true, loader);
            Object overworld = enumConstant(regionType, "OVERWORLD");
            Class<?> extended = Class.forName("terrablender.worldgen.IExtendedParameterList", true, loader);
            Climate.ParameterList<Holder<Biome>> list = new Climate.ParameterList<>(parameters().values());
            extended.getMethod("initializeForTerraBlender", RegistryAccess.class, regionType, long.class).invoke(list, access, overworld, seed);
            MethodHandle find = MethodHandles.publicLookup().findVirtual(extended, "findValuePositional",
                    MethodType.methodType(Object.class, Climate.TargetPoint.class, int.class, int.class, int.class)).bindTo(list);

            Registry<Biome> registry = access.registryOrThrow(Registries.BIOME);
            List<Holder<Biome>> regionBiomes = new ArrayList<>();
            Consumer<Pair<Climate.ParameterPoint, ResourceKey<Biome>>> add = pair -> registry.getHolder(pair.getSecond()).ifPresent(regionBiomes::add);
            java.lang.reflect.Method addBiomes = Class.forName("terrablender.api.Region", true, loader).getMethod("addBiomes", Registry.class, Consumer.class);
            for (Object region : (List<?>) Class.forName("terrablender.api.Regions", true, loader).getMethod("get", regionType).invoke(null, overworld)) {
                addBiomes.invoke(region, registry, add);
            }
            Class.forName("terrablender.worldgen.IExtendedBiomeSource", true, loader)
                    .getMethod("appendDeferredBiomesList", List.class).invoke(this, regionBiomes);
            this.terraBlender = find;
            LOGGER.info("[ttl] canon biomes: TerraBlender regions outside the palettes ({} region biomes)", regionBiomes.size());
        } catch (ReflectiveOperationException | RuntimeException e) {
            LOGGER.error("[ttl] canon biomes: TerraBlender setup failed, vanilla biomes outside the palettes", e);
        }
    }

    private static Object enumConstant(Class<?> type, String name) {
        for (Object constant : type.getEnumConstants()) if (((Enum<?>) constant).name().equals(name)) return constant;
        throw new IllegalArgumentException(type.getName() + "." + name);
    }
}
