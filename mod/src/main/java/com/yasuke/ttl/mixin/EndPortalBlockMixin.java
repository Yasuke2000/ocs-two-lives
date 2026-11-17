package com.yasuke.ttl.mixin;

import com.yasuke.ttl.TtlDimensions;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.EndPortalBlock;
import net.minecraft.world.level.levelgen.feature.EndPlatformFeature;
import net.minecraft.world.level.portal.DimensionTransition;
import net.minecraft.world.phys.Vec3;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Mirrors EndPortalBlock.getPortalDestination (1.21.1) for the Mortal Realm ↔ Mortal End pair. */
@Mixin(EndPortalBlock.class)
public abstract class EndPortalBlockMixin {
    @Inject(method = "getPortalDestination", at = @At("HEAD"), cancellable = true)
    private void ttl$mortalEnd(ServerLevel level, Entity entity, BlockPos pos, CallbackInfoReturnable<DimensionTransition> cir) {
        ResourceKey<Level> target = TtlDimensions.endPortalTarget(level.dimension());
        if (target == null) return;
        ServerLevel destination = level.getServer().getLevel(target);
        if (destination == null) {
            cir.setReturnValue(null);
            return;
        }

        float yRot = entity.getYRot();
        Vec3 arrival;
        if (target.equals(TtlDimensions.MORTAL_END)) {
            arrival = ServerLevel.END_SPAWN_POINT.getBottomCenter();
            EndPlatformFeature.createEndPlatform(destination, BlockPos.containing(arrival).below(), true);
            yRot = Direction.WEST.toYRot();
            if (entity instanceof ServerPlayer) arrival = arrival.subtract(0.0, 1.0, 0.0);
        } else {
            // Vanilla sends players to their respawn point, which may be in the Tensura world;
            // only use it when it is in the Mortal Realm.
            if (entity instanceof ServerPlayer player && target.equals(player.getRespawnDimension()) && player.getRespawnPosition() != null) {
                DimensionTransition respawn = player.findRespawnPositionAndUseSpawnBlock(false, DimensionTransition.DO_NOTHING);
                if (respawn.newLevel() == destination && !respawn.missingRespawnBlock()) {
                    cir.setReturnValue(respawn);
                    return;
                }
            }
            arrival = entity.adjustSpawnLocation(destination, destination.getSharedSpawnPos()).getBottomCenter();
        }
        cir.setReturnValue(new DimensionTransition(destination, arrival, entity.getDeltaMovement(), yRot, entity.getXRot(),
                DimensionTransition.PLAY_PORTAL_SOUND.then(DimensionTransition.PLACE_PORTAL_TICKET)));
    }
}
