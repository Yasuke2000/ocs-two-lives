package com.yasuke.ttl.guide;

import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.ResourceLocation;

import java.util.List;

/**
 * Server → client: one guide page set to show in the guide screen. The text comes from the pack
 * (design/data/guide.toml → TtlData.guide → {@code /ttlguide}), so the client holds no guide text of its own.
 * {@code then} is a command the client runs as the player when it closes the screen ("" for none), so a flow
 * can continue after the reading (the Corridor guide leads on to the Life screen).
 */
public record GuidePayload(String set, List<Page> pages, String then) implements CustomPacketPayload {
    public static final Type<GuidePayload> TYPE = new Type<>(ResourceLocation.fromNamespaceAndPath("ttl", "guide"));

    public record Page(String title, List<String> lines) {
        static final StreamCodec<ByteBuf, Page> CODEC = StreamCodec.composite(
                ByteBufCodecs.STRING_UTF8, Page::title,
                ByteBufCodecs.STRING_UTF8.apply(ByteBufCodecs.list(256)), Page::lines,
                Page::new);
    }

    public static final StreamCodec<ByteBuf, GuidePayload> CODEC = StreamCodec.composite(
            ByteBufCodecs.STRING_UTF8, GuidePayload::set,
            Page.CODEC.apply(ByteBufCodecs.list(64)), GuidePayload::pages,
            ByteBufCodecs.STRING_UTF8, GuidePayload::then,
            GuidePayload::new);

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
