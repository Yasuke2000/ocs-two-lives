package com.yasuke.ttl.world;

import com.mojang.datafixers.util.Pair;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import com.yasuke.ttl.TtlPortals;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.stream.Stream;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.biome.BiomeSource;
import net.minecraft.world.level.biome.Climate;
import net.minecraft.world.level.biome.MultiNoiseBiomeSourceParameterList;
import net.minecraft.world.level.levelgen.structure.StructureSet;
import net.neoforged.neoforge.registries.DeferredRegister;
import org.jetbrains.annotations.Nullable;

/**
 * Life 1's dimensions are a world without Tensura: no Tensura biomes, structures or placed features.
 * Biomes: the Mortal Realm uses {@link VanillaMultiNoise} instead of minecraft:multi_noise, because
 * TerraBlender injects its regions into every MultiNoiseBiomeSource (and the overworld preset's parameter
 * list is one shared object, so the Tensura world's TerraBlender setup would leak into any dimension using it).
 * Structures: ServerLevelMixin filters the level's structure sets. Features: PlacedFeatureMixin.
 */
public final class MortalWorldgen {
    /** Namespaces whose worldgen never appears in Life 1 (the Tensura addons in the pack ship no worldgen data). */
    public static final Set<String> BLOCKED_NAMESPACES = Set.of("tensura");

    public static final DeferredRegister<MapCodec<? extends BiomeSource>> BIOME_SOURCES =
            DeferredRegister.create(Registries.BIOME_SOURCE, TtlPortals.MOD_ID);

    static {
        BIOME_SOURCES.register("vanilla_multi_noise", () -> VanillaMultiNoise.CODEC);
        BIOME_SOURCES.register("canon_biomes", () -> CanonBiomes.CODEC); // the Tensura world's per-nation biomes
    }

    private MortalWorldgen() {}

    public static boolean isBlocked(@Nullable ResourceLocation id) {
        return id != null && BLOCKED_NAMESPACES.contains(id.getNamespace());
    }

    /** The structure sets without blocked structures; sets left empty are dropped. */
    public static List<Holder<StructureSet>> filterStructureSets(List<Holder<StructureSet>> sets) {
        List<Holder<StructureSet>> kept = new ArrayList<>(sets.size());
        for (Holder<StructureSet> set : sets) {
            if (set.unwrapKey().map(key -> isBlocked(key.location())).orElse(false)) continue;
            List<StructureSet.StructureSelectionEntry> entries = set.value().structures().stream()
                    .filter(entry -> !entry.structure().unwrapKey().map(key -> isBlocked(key.location())).orElse(false))
                    .toList();
            if (entries.isEmpty()) continue;
            kept.add(entries.size() == set.value().structures().size() ? set : Holder.direct(new StructureSet(entries, set.value().placement())));
        }
        return List.copyOf(kept);
    }

    /**
     * {@code ttl:vanilla_multi_noise}: minecraft:multi_noise from a preset, but a separate class so TerraBlender
     * (which only touches MultiNoiseBiomeSource) leaves it alone, and it always uses vanilla's own lookup.
     */
    public static final class VanillaMultiNoise extends BiomeSource {
        public static final MapCodec<VanillaMultiNoise> CODEC = RecordCodecBuilder.mapCodec(i -> i.group(
                MultiNoiseBiomeSourceParameterList.CODEC.fieldOf("preset").forGetter(s -> s.preset)
        ).apply(i, VanillaMultiNoise::new));

        private final Holder<MultiNoiseBiomeSourceParameterList> preset;

        private VanillaMultiNoise(Holder<MultiNoiseBiomeSourceParameterList> preset) {
            this.preset = preset;
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
            return parameters().values().stream().map(Pair::getSecond)
                    .filter(biome -> !biome.unwrapKey().map(key -> isBlocked(key.location())).orElse(false));
        }

        @Override
        public Holder<Biome> getNoiseBiome(int x, int y, int z, Climate.Sampler sampler) {
            return parameters().findValue(sampler.sample(x, y, z));
        }
    }
}
