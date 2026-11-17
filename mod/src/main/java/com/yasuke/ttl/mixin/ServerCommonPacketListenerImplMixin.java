package com.yasuke.ttl.mixin;

import com.yasuke.ttl.bot.BotConnection;
import net.minecraft.network.Connection;
import net.minecraft.network.PacketSendListener;
import net.minecraft.network.protocol.Packet;
import net.minecraft.server.network.ServerCommonPacketListenerImpl;
import org.jetbrains.annotations.Nullable;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * NeoForge rejects modded payloads to a connection that never negotiated channels (it throws), and a
 * test bot never does. Drop everything sent to a bot before that check runs.
 */
@Mixin(ServerCommonPacketListenerImpl.class)
public abstract class ServerCommonPacketListenerImplMixin {
    @Shadow
    @Final
    protected Connection connection;

    @Inject(method = "send(Lnet/minecraft/network/protocol/Packet;Lnet/minecraft/network/PacketSendListener;)V", at = @At("HEAD"), cancellable = true)
    private void ttl$dropBotPackets(Packet<?> packet, @Nullable PacketSendListener listener, CallbackInfo ci) {
        if (connection instanceof BotConnection) ci.cancel();
    }

    @Inject(method = "keepConnectionAlive", at = @At("HEAD"), cancellable = true)
    private void ttl$noBotTimeout(CallbackInfo ci) {
        if (connection instanceof BotConnection) ci.cancel();
    }
}
