package com.yasuke.ttl.guide;

import com.yasuke.ttl.guide.client.GuideClient;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.network.event.RegisterPayloadHandlersEvent;

/** Registers the guide payload (a mod-bus event; NeoForge picks the bus from the event type). The handler only runs on the client, so the client class is never loaded on a server. */
@EventBusSubscriber(modid = "ttl")
public final class GuideNetwork {
    private GuideNetwork() {}

    @SubscribeEvent
    public static void register(RegisterPayloadHandlersEvent event) {
        event.registrar("1").optional().playToClient(GuidePayload.TYPE, GuidePayload.CODEC,
                (payload, context) -> context.enqueueWork(() -> GuideClient.receive(payload)));
    }
}
