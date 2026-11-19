package com.yasuke.ttl.world;

import com.yasuke.ttl.TtlPortals;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.neoforged.neoforge.registries.DeferredRegister;

/** Feature types of the own world: {@code ttl:design_water} and {@code ttl:design_road} (configured/placed in the pack). */
public final class DesignFeatures {
    private DesignFeatures() {}

    public static final DeferredRegister<Feature<?>> FEATURES = DeferredRegister.create(Registries.FEATURE, TtlPortals.MOD_ID);

    static {
        FEATURES.register("design_water", DesignWaterFeature::new);
        FEATURES.register("design_road", DesignRoadFeature::new);
    }
}
