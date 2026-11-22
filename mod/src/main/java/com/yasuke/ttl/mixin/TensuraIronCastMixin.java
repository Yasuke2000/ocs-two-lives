package com.yasuke.ttl.mixin;

import com.yasuke.ttl.TtlDimensions;
import io.redspace.ironsspellbooks.api.events.SpellOnCastEvent;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * The Tensura bridge's cast handler (tensura_iron_spells 2.0.0.0 NeoEventsHandler.onSpellCast, SpellOnCastEvent at
 * LOWEST) spends magicules instead of Iron's mana. In the Mortal dimensions it is skipped, so a cast there costs Iron's
 * mana and nothing else (issue #104, see SpellManaMixin). Pseudo: nothing happens when the bridge is not installed.
 */
@Pseudo
@Mixin(targets = "io.github.manasmods.tensura_iron.neoforge.NeoEventsHandler")
public abstract class TensuraIronCastMixin {
    @Inject(method = "onSpellCast", at = @At("HEAD"), cancellable = true, remap = false, require = 0)
    private static void ttl$ironManaInMortal(SpellOnCastEvent event, CallbackInfo ci) {
        if (event.getEntity() != null && TtlDimensions.isMortal(event.getEntity().level().dimension())) ci.cancel();
    }
}
