package com.yasuke.ttl.mixin;

import com.yasuke.ttl.TtlDimensions;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseFireBlock;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Vanilla lights a Nether portal frame only in minecraft:overworld and minecraft:the_nether (BaseFireBlock
 * inPortalDimension, 1.21.1): fire in an obsidian frame in the Mortal Realm or the Mortal Nether stayed plain fire
 * (issue #85). Their portals already lead to each other (NetherPortalBlockMixin), so the frame lights there too.
 */
@Mixin(BaseFireBlock.class)
public abstract class BaseFireBlockMixin {
    @Inject(method = "inPortalDimension", at = @At("HEAD"), cancellable = true)
    private static void ttl$mortalPortalDimension(Level level, CallbackInfoReturnable<Boolean> cir) {
        if (TtlDimensions.netherPortalTarget(level.dimension()) != null) cir.setReturnValue(true);
    }
}
