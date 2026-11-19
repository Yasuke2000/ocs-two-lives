package com.yasuke.ttl.world;

import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import com.yasuke.ttl.TtlPortals;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetActionBarTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitlesAnimationPacket;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.level.Level;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

/**
 * Anime-style arrival banners in the Tensura world (minecraft:overworld): entering a nation of the canon map
 * shows its name (gold, as the subtitle under an empty title, so it is normal-sized) and {@code banner_subtitle}
 * (gray, on the action bar) from canon_regions.json with a soft chime; leaving the
 * land shows "The Open Sea", passing the ring "Uncharted Lands". Checked once a second per player; a new region
 * must hold for {@link #CONFIRM} checks so walking along a border doesn't spam. {@code /ttlregion <player>} reports, including
 * the distance ring (zone) of a nation that has them; on Lerfing's imported map the ring is named from the stored
 * biome, since the import tool painted the rings into the chunks.
 */
@EventBusSubscriber(modid = TtlPortals.MOD_ID)
public final class RegionTitles {
    static final int PERIOD = 20, CONFIRM = 3;
    static final char NONE = 0, SEA = '.', UNCHARTED = '*';
    /** Canon weight below which the open sea counts as the free lands beyond the ring. */
    static final double UNCHARTED_WEIGHT = 0.5;

    private static final Map<UUID, Tracker> TRACKERS = new HashMap<>();

    private RegionTitles() {}

    /** Per player: the region whose banner was shown last, and a candidate waiting for confirmation. */
    static final class Tracker {
        char shown = NONE, pending = NONE;
        int count;

        /** Feeds one observation; returns true when {@code key} becomes the shown region. '~' and NONE never confirm. */
        boolean observe(char key) {
            if (key == NONE || key == '~') return false; // rivers and lakes neither confirm nor interrupt
            if (key == shown) {
                pending = NONE;
                count = 0;
                return false;
            }
            if (key != pending) {
                pending = key;
                count = 0;
            }
            if (++count < CONFIRM) return false;
            shown = key;
            pending = NONE;
            count = 0;
            return true;
        }
    }

    /** Region key at a block column: a nation letter, SEA, UNCHARTED, '~' (ignored) or NONE when no grid. */
    static char regionAt(CanonGrid grid, int x, int z) {
        char cell = grid.charAt(x, z);
        if (cell == '~') return '~';
        if (cell != '.') return grid.region(cell) != null ? cell : SEA;
        char owner = grid.ownerCell(x, z); // coastal water belongs to its nation
        if (owner != 0 && grid.region(owner) != null) return owner;
        return grid.canonWeight(x, z) < UNCHARTED_WEIGHT ? UNCHARTED : SEA;
    }

    /** Jura's ring from a stored biome's magicule class (design/architecture/lerfing-import.md §3.6). */
    static String storedRing(String biome) {
        return switch (biome) {
            case "tensura:ancient_forest" -> "core (deadly, ancient forest)";
            case "minecraft:dark_forest" -> "dark band (dark forest)";
            default -> "rim (safe)";
        };
    }

    static String title(CanonGrid grid, char key) {
        if (key == SEA) return "The Open Sea";
        if (key == UNCHARTED) return "Uncharted Lands";
        CanonGrid.Region region = grid.region(key);
        if (region == null) return "Unknown Land";
        return region.bannerTitle() != null ? region.bannerTitle() : region.name();
    }

    static String subtitle(CanonGrid grid, char key) {
        if (key == SEA) return "Beyond the shores of the known nations";
        if (key == UNCHARTED) return "Lands no map of the nations has named";
        CanonGrid.Region region = grid.region(key);
        return region != null && region.bannerSubtitle() != null ? region.bannerSubtitle() : "A nation of the Tensura world";
    }

    @SubscribeEvent
    public static void onServerTick(ServerTickEvent.Post event) {
        if (event.getServer().getTickCount() % PERIOD != 0) return;
        CanonGrid grid = CanonMap.grid();
        if (grid == null) return;
        for (ServerPlayer player : event.getServer().overworld().players()) {
            if (player.isSpectator()) continue;
            Tracker tracker = TRACKERS.computeIfAbsent(player.getUUID(), id -> new Tracker());
            char key = regionAt(grid, player.getBlockX(), player.getBlockZ());
            if (tracker.observe(key)) show(player, grid, key);
        }
    }

    static void show(ServerPlayer player, CanonGrid grid, char key) {
        boolean nation = key != SEA && key != UNCHARTED;
        player.connection.send(new ClientboundSetTitlesAnimationPacket(20, 70, 30));
        // The name is the subtitle (normal size) under an empty title: a vanilla title is drawn at a fixed large scale
        // and long names ("Elmine - Terrace of the Divine Tree") were cut off at both screen edges.
        player.connection.send(new ClientboundSetSubtitleTextPacket(Component.literal(title(grid, key))
                .withStyle(nation ? ChatFormatting.GOLD : ChatFormatting.AQUA)));
        player.connection.send(new ClientboundSetTitleTextPacket(Component.empty()));
        player.connection.send(new ClientboundSetActionBarTextPacket(Component.literal(subtitle(grid, key))
                .withStyle(ChatFormatting.GRAY, ChatFormatting.ITALIC)));
        player.playNotifySound(nation ? SoundEvents.AMETHYST_BLOCK_RESONATE : SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.AMBIENT, 0.6f, 0.8f);
    }

    @SubscribeEvent
    public static void onLogin(PlayerEvent.PlayerLoggedInEvent event) {
        TRACKERS.remove(event.getEntity().getUUID());
    }

    @SubscribeEvent
    public static void onLogout(PlayerEvent.PlayerLoggedOutEvent event) {
        TRACKERS.remove(event.getEntity().getUUID());
    }

    @SubscribeEvent
    public static void onChangedDimension(PlayerEvent.PlayerChangedDimensionEvent event) {
        TRACKERS.remove(event.getEntity().getUUID());
    }

    @SubscribeEvent
    public static void registerCommands(RegisterCommandsEvent event) {
        event.getDispatcher().register(Commands.literal("ttlregion")
                .requires(source -> source.hasPermission(2))
                .then(Commands.argument("player", EntityArgument.player()).executes(RegionTitles::report)));
    }

    private static int report(CommandContext<CommandSourceStack> ctx) throws CommandSyntaxException {
        ServerPlayer player = EntityArgument.getPlayer(ctx, "player");
        CanonGrid grid = CanonMap.grid();
        StringBuilder out = new StringBuilder("[ttl] region of ").append(player.getGameProfile().getName())
                .append(" at ").append(player.getBlockX()).append(' ').append(player.getBlockZ()).append(": ");
        if (player.level().dimension() != Level.OVERWORLD) {
            out.append("not in the Tensura world (").append(player.level().dimension().location()).append(')');
        } else if (grid == null) {
            out.append("canon map NOT LOADED");
        } else {
            char key = regionAt(grid, player.getBlockX(), player.getBlockZ());
            out.append(key == '~' ? "river/lake (keeps the previous banner)" : title(grid, key) + " / " + subtitle(grid, key))
                    .append(", cell '").append(grid.charAt(player.getBlockX(), player.getBlockZ())).append('\'');
            long seed = ((ServerLevel) player.level()).getSeed();
            char owner = grid.ownerAt(player.getBlockX(), player.getBlockZ(), seed);
            if (grid.imported(player.getBlockX(), player.getBlockZ())) {
                // Lerfing's chunks carry the rings the import tool painted: name them from the stored biome, which is what hurts.
                String biome = player.level().getBiome(player.blockPosition()).unwrapKey().map(k -> k.location().toString()).orElse("?");
                out.append(", stored biome ").append(biome);
                CanonGrid.Region region = grid.region(grid.ownerCell(player.getBlockX(), player.getBlockZ()));
                if (region != null && region.zones() != null) out.append(", zone ").append(storedRing(biome));
            } else {
                String ring = grid.zoneInfo(owner, player.getBlockX(), player.getBlockZ(), seed);
                if (ring != null) out.append(", zone ").append(ring);
            }
            Tracker tracker = TRACKERS.get(player.getUUID());
            if (tracker != null) {
                out.append(", banner shown: ").append(tracker.shown == NONE ? "none yet" : title(grid, tracker.shown));
                if (tracker.pending != NONE) out.append(", pending ").append(title(grid, tracker.pending)).append(' ').append(tracker.count).append('/').append(CONFIRM);
            }
        }
        String text = out.toString();
        ctx.getSource().sendSuccess(() -> Component.literal(text), false);
        return 1;
    }
}
