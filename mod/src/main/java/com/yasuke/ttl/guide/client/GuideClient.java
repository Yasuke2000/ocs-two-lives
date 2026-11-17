package com.yasuke.ttl.guide.client;

import com.yasuke.ttl.guide.GuidePayload;
import net.minecraft.client.Minecraft;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ClientTickEvent;

/**
 * Client side of the guide. A guide that arrives while another screen is open (the loading screen right after
 * joining or a teleport, a chest menu, chat, the Great Sage ceremony) waits until that screen is closed, so it
 * never replaces a menu the server still thinks is open and never gets closed by a loading screen.
 */
@EventBusSubscriber(modid = "ttl", value = Dist.CLIENT)
public final class GuideClient {
    private static GuidePayload pending;

    private GuideClient() {}

    public static void receive(GuidePayload payload) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player != null && (mc.screen == null || mc.screen instanceof GuideScreen)) {
            pending = null;
            mc.setScreen(new GuideScreen(payload));
        } else {
            pending = payload;
        }
    }

    @SubscribeEvent
    public static void onTick(ClientTickEvent.Post event) {
        if (pending == null) return;
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null) {
            if (mc.level == null && mc.getConnection() == null) pending = null;
            return;
        }
        if (mc.screen == null && mc.getOverlay() == null) {
            GuidePayload payload = pending;
            pending = null;
            mc.setScreen(new GuideScreen(payload));
        }
    }
}
