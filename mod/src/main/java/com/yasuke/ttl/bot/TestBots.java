package com.yasuke.ttl.bot;

import com.mojang.authlib.GameProfile;
import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.logging.LogUtils;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.UUIDUtil;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ClientInformation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.CommonListenerCookie;
import net.minecraft.world.level.storage.LevelResource;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;
import org.slf4j.Logger;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * Staging-only test players: a real ServerPlayer on a dead connection, so login, death, stages and
 * every script hook run exactly as for a person. Drive them with {@code execute as <bot> run ...}.
 * Bots skip the whitelist and don't tick movement, so they never walk, fall or use portals by themselves.
 * Every spawn starts from a fresh player file: a bot never respawns, so a saved dead bot stays dead.
 */
public final class TestBots {
    private static final Logger LOGGER = LogUtils.getLogger();

    private TestBots() {}

    public static void registerCommands(RegisterCommandsEvent event) {
        CommandDispatcher<CommandSourceStack> dispatcher = event.getDispatcher();
        dispatcher.register(Commands.literal("ttlbot")
                .requires(source -> source.hasPermission(2))
                .then(Commands.literal("spawn")
                        .then(Commands.argument("name", StringArgumentType.word()).executes(TestBots::spawn)))
                .then(Commands.literal("remove")
                        .then(Commands.argument("name", StringArgumentType.word()).executes(TestBots::remove)))
                .then(Commands.literal("list").executes(TestBots::list)));
    }

    /**
     * A player stays invulnerable after a dimension change until its client confirms arrival
     * (ServerPlayer.isInvulnerableTo checks isChangingDimension). A bot has no client, so confirm for it.
     */
    public static void onChangedDimension(PlayerEvent.PlayerChangedDimensionEvent event) {
        if (event.getEntity() instanceof ServerPlayer player && isBot(player)) player.hasChangedDimension();
    }

    public static boolean isBot(ServerPlayer player) {
        return player.connection != null && player.connection.getConnection() instanceof BotConnection;
    }

    private static int spawn(CommandContext<CommandSourceStack> ctx) {
        MinecraftServer server = ctx.getSource().getServer();
        String name = StringArgumentType.getString(ctx, "name");
        if (name.length() > 16) {
            ctx.getSource().sendFailure(Component.literal("Name is longer than 16 characters"));
            return 0;
        }
        if (server.getPlayerList().getPlayerByName(name) != null) {
            ctx.getSource().sendFailure(Component.literal(name + " is already online"));
            return 0;
        }
        UUID id = UUIDUtil.createOfflinePlayerUUID(name);
        Path playerData = server.getWorldPath(LevelResource.PLAYER_DATA_DIR);
        try {
            Files.deleteIfExists(playerData.resolve(id + ".dat"));
            Files.deleteIfExists(playerData.resolve(id + ".dat_old"));
        } catch (IOException e) {
            ctx.getSource().sendFailure(Component.literal("Could not reset " + name + ": " + e.getMessage()));
            return 0;
        }
        GameProfile profile = new GameProfile(id, name);
        ServerPlayer bot = new ServerPlayer(server, server.overworld(), profile, ClientInformation.createDefault());
        server.getPlayerList().placeNewPlayer(new BotConnection(), bot, CommonListenerCookie.createInitial(profile, false));
        LOGGER.info("[ttl] test bot {} joined", name);
        ctx.getSource().sendSuccess(() -> Component.literal("Spawned test bot " + name), true);
        return 1;
    }

    private static int remove(CommandContext<CommandSourceStack> ctx) {
        MinecraftServer server = ctx.getSource().getServer();
        String name = StringArgumentType.getString(ctx, "name");
        ServerPlayer player = server.getPlayerList().getPlayerByName(name);
        if (player == null || !isBot(player)) {
            ctx.getSource().sendFailure(Component.literal(name + " is not an online test bot"));
            return 0;
        }
        server.getPlayerList().remove(player);
        LOGGER.info("[ttl] test bot {} left", name);
        ctx.getSource().sendSuccess(() -> Component.literal("Removed test bot " + name), true);
        return 1;
    }

    private static int list(CommandContext<CommandSourceStack> ctx) {
        String bots = ctx.getSource().getServer().getPlayerList().getPlayers().stream()
                .filter(TestBots::isBot)
                .map(p -> p.getGameProfile().getName())
                .collect(Collectors.joining(", "));
        ctx.getSource().sendSuccess(() -> Component.literal("Test bots: " + (bots.isEmpty() ? "none" : bots)), false);
        return 1;
    }
}
