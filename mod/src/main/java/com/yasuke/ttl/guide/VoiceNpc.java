package com.yasuke.ttl.guide;

import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Entity;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.entity.living.LivingIncomingDamageEvent;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;

import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

/**
 * The Voice of the World NPC in the Spirit Corridor hall (placed and kept by life/voice_npc.js, entity tag
 * {@value #TAG}). Right-click runs {@code /ttl talk} as the player: the current Corridor step, or the guide
 * elsewhere. Its own interaction (an allay taking or giving items) never happens, and only damage that
 * bypasses invulnerability ({@code /kill}, the void) can hurt it; creative players' hits are ignored too.
 */
@EventBusSubscriber(modid = "ttl")
public final class VoiceNpc {
    public static final String TAG = "ttl.voice_npc";
    private static final Map<UUID, Long> LAST_TALK = new ConcurrentHashMap<>();

    private VoiceNpc() {}

    private static boolean isNpc(Entity entity) {
        return entity != null && entity.getTags().contains(TAG);
    }

    @SubscribeEvent(priority = EventPriority.HIGH)
    public static void onInteractAt(PlayerInteractEvent.EntityInteractSpecific event) {
        if (event.getLevel().isClientSide() || !isNpc(event.getTarget())) return;
        event.setCanceled(true);
        event.setCancellationResult(InteractionResult.SUCCESS);
        talk(event.getEntity());
    }

    @SubscribeEvent(priority = EventPriority.HIGH)
    public static void onInteract(PlayerInteractEvent.EntityInteract event) {
        if (event.getLevel().isClientSide() || !isNpc(event.getTarget())) return;
        event.setCanceled(true);
        event.setCancellationResult(InteractionResult.SUCCESS);
        talk(event.getEntity());
    }

    @SubscribeEvent(priority = EventPriority.HIGHEST)
    public static void onDamage(LivingIncomingDamageEvent event) {
        if (isNpc(event.getEntity()) && !event.getSource().is(DamageTypeTags.BYPASSES_INVULNERABILITY)) event.setCanceled(true);
    }

    // One right-click can arrive as several interact packets (both hands, interactAt + interact): talk once.
    private static void talk(net.minecraft.world.entity.player.Player player) {
        if (!(player instanceof ServerPlayer serverPlayer)) return;
        long now = serverPlayer.serverLevel().getGameTime();
        Long last = LAST_TALK.get(serverPlayer.getUUID());
        if (last != null && now - last < 10 && now >= last) return;
        LAST_TALK.put(serverPlayer.getUUID(), now);
        serverPlayer.getServer().getCommands().performPrefixedCommand(serverPlayer.createCommandSourceStack(), "ttl talk");
    }
}
