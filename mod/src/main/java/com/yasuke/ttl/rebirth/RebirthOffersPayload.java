package com.yasuke.ttl.rebirth;

import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.ResourceLocation;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;

import java.util.List;

/**
 * Server → client: the race ids Tensura's reincarnation menu (and the Great Sage scene on top of it)
 * must show. The client builds its own race list from config, so it has to be told; empty clears it.
 */
public record RebirthOffersPayload(List<String> races) implements CustomPacketPayload {
    public static final Type<RebirthOffersPayload> TYPE = new Type<>(ResourceLocation.fromNamespaceAndPath("ttl", "rebirth_offers"));
    public static final StreamCodec<ByteBuf, RebirthOffersPayload> CODEC =
            ByteBufCodecs.STRING_UTF8.apply(ByteBufCodecs.list()).map(RebirthOffersPayload::new, RebirthOffersPayload::races);

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }

    public static void register(RegisterPayloadHandlersEvent event) {
        // Optional: a client without the mod can still join; it just gets Tensura's own race list.
        event.registrar("1").optional().playToClient(TYPE, CODEC,
                (payload, context) -> context.enqueueWork(() -> Rebirth.setClientOffers(payload.races())));
    }
}
