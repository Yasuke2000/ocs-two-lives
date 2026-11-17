package com.yasuke.ttl.mixin;

import com.yasuke.ttl.rebirth.Rebirth;
import io.github.manasmods.manascore.race.api.ManasRace;
import io.github.manasmods.tensura.menu.ReincarnationMenu;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Player;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import java.util.List;

/** Per-player race offers in Tensura's reincarnation menu; see {@link Rebirth}. */
@Mixin(ReincarnationMenu.class)
public abstract class ReincarnationMenuMixin {
    @Shadow
    @Final
    private Player player;

    @Inject(method = "getRacePool", at = @At("HEAD"), cancellable = true)
    private void ttl$offeredRaces(CallbackInfoReturnable<List<ManasRace>> cir) {
        List<String> offers = Rebirth.offersFor(player);
        if (offers != null) cir.setReturnValue(Rebirth.races(offers));
    }

    // "Random" must stay inside the offers too.
    @Inject(method = "getRandomRacePool", at = @At("HEAD"), cancellable = true)
    private void ttl$offeredRandomRaces(CallbackInfoReturnable<List<ManasRace>> cir) {
        List<String> offers = Rebirth.offersFor(player);
        if (offers != null) cir.setReturnValue(Rebirth.races(offers));
    }

    @Inject(method = "setRace", at = @At("TAIL"))
    private static void ttl$reborn(Player player, ManasRace race, boolean a, boolean b, CallbackInfo ci) {
        Rebirth.onRaceSet(player, race);
    }

    @Inject(method = "checkForFirstLogin", at = @At("HEAD"), cancellable = true)
    private static void ttl$noLifeOneMenu(ServerPlayer player, CallbackInfoReturnable<Boolean> cir) {
        if (Rebirth.blockFirstLogin(player)) cir.setReturnValue(false);
    }
}
