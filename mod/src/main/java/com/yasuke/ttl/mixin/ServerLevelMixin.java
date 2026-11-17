package com.yasuke.ttl.mixin;

import com.yasuke.ttl.MortalDragonFightData;
import com.yasuke.ttl.TtlDimensions;
import com.yasuke.ttl.world.MortalWorldgen;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.chunk.ChunkGeneratorStructureState;
import net.minecraft.world.level.dimension.end.EndDragonFight;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * Vanilla only creates a dragon fight for minecraft:the_end and saves it into level.dat. The Mortal
 * End gets its own fight, loaded from and saved to its own data file so the two Ends never overwrite
 * each other's dragon, exit portal and gateways.
 * Life 1's dimensions also drop Tensura's structure sets before the constructor computes structure placements,
 * so those structures neither generate nor show up in /locate there.
 */
@Mixin(ServerLevel.class)
public abstract class ServerLevelMixin {
    @Inject(method = "<init>", at = @At("RETURN"))
    private void ttl$createMortalDragonFight(CallbackInfo ci) {
        ServerLevel self = (ServerLevel) (Object) this;
        if (!self.dimension().equals(TtlDimensions.MORTAL_END)) return;
        self.setDragonFight(new EndDragonFight(self, self.getSeed(), MortalDragonFightData.get(self).data()));
    }

    @Inject(method = "<init>", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/world/level/chunk/ChunkGeneratorStructureState;ensureStructuresGenerated()V"))
    private void ttl$dropBlockedStructures(CallbackInfo ci) {
        ServerLevel self = (ServerLevel) (Object) this;
        if (!TtlDimensions.isMortal(self.dimension())) return;
        ChunkGeneratorStructureState state = self.getChunkSource().getGeneratorState();
        ((ChunkGeneratorStructureStateAccessor) state).ttl$setPossibleStructureSets(MortalWorldgen.filterStructureSets(state.possibleStructureSets()));
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
