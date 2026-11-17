package com.yasuke.ttl.mixin;

import com.yasuke.ttl.TtlDimensions;
import com.yasuke.ttl.world.MortalWorldgen;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.levelgen.placement.PlacedFeature;
import net.minecraft.world.level.levelgen.placement.PlacementContext;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Biome modifiers add Tensura's placed features (ores, palm trees, ...) to the shared vanilla biomes, so they
 * would also decorate Life 1's dimensions. Both {@code place} and {@code placeWithBiomeCheck} go through here.
 */
@Mixin(PlacedFeature.class)
public abstract class PlacedFeatureMixin {
    @Inject(method = "placeWithContext", at = @At("HEAD"), cancellable = true)
    private void ttl$skipBlockedInMortal(PlacementContext context, RandomSource random, BlockPos pos, CallbackInfoReturnable<Boolean> cir) {
        WorldGenLevel level = context.getLevel();
        if (!TtlDimensions.isMortal(level.getLevel().dimension())) return;
        if (MortalWorldgen.isBlocked(level.registryAccess().registryOrThrow(Registries.PLACED_FEATURE).getKey((PlacedFeature) (Object) this))) {
            cir.setReturnValue(false);
        }
    }
}
