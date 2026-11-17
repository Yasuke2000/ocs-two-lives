package com.yasuke.ttl;

import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.Level;
import org.jetbrains.annotations.Nullable;

/** The Life 1 dimensions (datapack in pack/kubejs/data/ttl/dimension) and how their portals link. */
public final class TtlDimensions {
    public static final ResourceKey<Level> MORTAL_REALM = key("mortal_realm");
    public static final ResourceKey<Level> MORTAL_NETHER = key("mortal_nether");
    public static final ResourceKey<Level> MORTAL_END = key("mortal_end");

    private TtlDimensions() {}

    public static boolean isMortal(ResourceKey<Level> dimension) {
        return dimension.equals(MORTAL_REALM) || dimension.equals(MORTAL_NETHER) || dimension.equals(MORTAL_END);
    }

    /** Target of a Nether portal used in {@code from}, or null to keep vanilla behaviour. */
    @Nullable
    public static ResourceKey<Level> netherPortalTarget(ResourceKey<Level> from) {
        if (from.equals(MORTAL_REALM)) return MORTAL_NETHER;
        if (from.equals(MORTAL_NETHER)) return MORTAL_REALM;
        return null;
    }

    /** Target of an End portal used in {@code from}, or null to keep vanilla behaviour. */
    @Nullable
    public static ResourceKey<Level> endPortalTarget(ResourceKey<Level> from) {
        if (from.equals(MORTAL_REALM)) return MORTAL_END;
        if (from.equals(MORTAL_END)) return MORTAL_REALM;
        return null;
    }

    private static ResourceKey<Level> key(String path) {
        return ResourceKey.create(Registries.DIMENSION, ResourceLocation.fromNamespaceAndPath(TtlPortals.MOD_ID, path));
    }
}
