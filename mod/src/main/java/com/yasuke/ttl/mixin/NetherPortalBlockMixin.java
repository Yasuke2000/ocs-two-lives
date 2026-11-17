package com.yasuke.ttl.mixin;

import com.yasuke.ttl.TtlDimensions;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.NetherPortalBlock;
import net.minecraft.world.level.border.WorldBorder;
import net.minecraft.world.level.dimension.DimensionType;
import net.minecraft.world.level.portal.DimensionTransition;
import org.jetbrains.annotations.Nullable;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Vanilla hardcodes "not the Nether → the Nether, the Nether → the Overworld". This mirrors
 * getPortalDestination (1.21.1) with the Mortal pair as target; everything else stays vanilla.
 */
@Mixin(NetherPortalBlock.class)
public abstract class NetherPortalBlockMixin {
    @Shadow
    @Nullable
    private DimensionTransition getExitPortal(ServerLevel level, Entity entity, BlockPos pos, BlockPos exitPos, boolean isNether, WorldBorder border) {
        throw new AssertionError();
    }

    @Inject(method = "getPortalDestination", at = @At("HEAD"), cancellable = true)
    private void ttl$mortalNether(ServerLevel level, Entity entity, BlockPos pos, CallbackInfoReturnable<DimensionTransition> cir) {
        ResourceKey<Level> target = TtlDimensions.netherPortalTarget(level.dimension());
        if (target == null) return;
        ServerLevel destination = level.getServer().getLevel(target);
        if (destination == null) {
            cir.setReturnValue(null);
            return;
        }
        boolean toNether = target.equals(TtlDimensions.MORTAL_NETHER);
        WorldBorder border = destination.getWorldBorder();
        double scale = DimensionType.getTeleportationScale(level.dimensionType(), destination.dimensionType());
        BlockPos exitPos = border.clampToBounds(entity.getX() * scale, entity.getY(), entity.getZ() * scale);
        cir.setReturnValue(getExitPortal(destination, entity, pos, exitPos, toNether, border));
    }
}
