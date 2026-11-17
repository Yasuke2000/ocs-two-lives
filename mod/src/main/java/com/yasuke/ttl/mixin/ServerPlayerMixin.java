package com.yasuke.ttl.mixin;

import com.yasuke.ttl.ui.Quiet;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Swallows chat/action-bar messages to players while a {@code /quietly} command runs. */
@Mixin(ServerPlayer.class)
public abstract class ServerPlayerMixin {
    @Inject(method = "sendSystemMessage(Lnet/minecraft/network/chat/Component;Z)V", at = @At("HEAD"), cancellable = true)
    private void ttl$quietSystem(Component message, boolean overlay, CallbackInfo ci) {
        if (Quiet.isActive()) ci.cancel();
    }

    @Inject(method = "displayClientMessage", at = @At("HEAD"), cancellable = true)
    private void ttl$quietClient(Component message, boolean actionBar, CallbackInfo ci) {
        if (Quiet.isActive()) ci.cancel();
    }
}
