package com.yasuke.ttl.mixin;

import com.yasuke.ttl.MortalDragonFightData;
import com.yasuke.ttl.TtlDimensions;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.dimension.end.EndDragonFight;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * Vanilla only creates a dragon fight for minecraft:the_end and saves it into level.dat. The Mortal
 * End gets its own fight, loaded from and saved to its own data file so the two Ends never overwrite
 * each other's dragon, exit portal and gateways.
 */
@Mixin(ServerLevel.class)
public abstract class ServerLevelMixin {
    @Inject(method = "<init>", at = @At("RETURN"))
    private void ttl$createMortalDragonFight(CallbackInfo ci) {
        ServerLevel self = (ServerLevel) (Object) this;
        if (!self.dimension().equals(TtlDimensions.MORTAL_END)) return;
        self.setDragonFight(new EndDragonFight(self, self.getSeed(), MortalDragonFightData.get(self).data()));
    }

    @Inject(method = "saveLevelData", at = @At("HEAD"), cancellable = true)
    private void ttl$saveMortalDragonFight(CallbackInfo ci) {
        ServerLevel self = (ServerLevel) (Object) this;
        if (!self.dimension().equals(TtlDimensions.MORTAL_END)) return;
        EndDragonFight fight = self.getDragonFight();
        if (fight != null) MortalDragonFightData.get(self).update(fight.saveData());
        self.getChunkSource().getDataStorage().save();
        ci.cancel();
    }
}
