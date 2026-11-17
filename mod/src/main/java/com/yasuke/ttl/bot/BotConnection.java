package com.yasuke.ttl.bot;

import io.netty.channel.embedded.EmbeddedChannel;
import net.minecraft.network.Connection;
import net.minecraft.network.PacketSendListener;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.PacketFlow;
import org.jetbrains.annotations.Nullable;

/**
 * A connection with no client behind it. The embedded channel only exists because protocol setup
 * writes to the pipeline; every packet to the bot is dropped.
 */
public final class BotConnection extends Connection {
    public BotConnection() {
        super(PacketFlow.SERVERBOUND);
        new EmbeddedChannel(this);
    }

    @Override
    public void send(Packet<?> packet, @Nullable PacketSendListener listener, boolean flush) {}

    @Override
    public void setReadOnly() {}

    @Override
    public void handleDisconnection() {}
}
