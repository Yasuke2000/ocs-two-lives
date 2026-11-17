package com.yasuke.ttl.mixin.client;

import com.yasuke.ttl.rebirth.Rebirth;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Escape twice within 3 s declines the Great Sage ceremony: the addon falls back to Tensura's plain menu and the
 * wishes are lost. In our Life 2 rebirth the ceremony is the way through, so Escape is swallowed while the
 * scripts' race offers are held. Targeted by name so the mod needs no compile-time dependency on the addon.
 */
@Pseudo
@Mixin(targets = "dev.dedek.greatsage.client.ReincarnationScene", remap = false)
public abstract class GreatSageSceneMixin {
    @Inject(method = "keyPressed(III)Z", at = @At("HEAD"), cancellable = true, require = 0)
    private void ttl$noEscapeDuringRebirth(int key, int scanCode, int modifiers, CallbackInfoReturnable<Boolean> cir) {
        if (key == 256 && Rebirth.rebirthOnClient()) cir.setReturnValue(true);
    }
}
