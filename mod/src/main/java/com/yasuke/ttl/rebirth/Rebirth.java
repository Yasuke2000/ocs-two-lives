package com.yasuke.ttl.rebirth;

import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import com.mojang.logging.LogUtils;
import dev.architectury.registry.menu.MenuRegistry;
import io.github.manasmods.manascore.race.api.ManasRace;
import io.github.manasmods.manascore.race.api.RaceAPI;
import io.github.manasmods.tensura.menu.ReincarnationMenu;
import io.github.manasmods.tensura.storage.TensuraStorages;
import io.github.manasmods.tensura.storage.player.ITensuraPlayer;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.entity.player.Player;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import org.jetbrains.annotations.Nullable;
import org.slf4j.Logger;

import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Life 2 rebirth through Tensura's own reincarnation menu, so the Great Sage addon plays its scene on top.
 * The scripts decide the race offers; ReincarnationMenuMixin makes the menu show exactly those, and when
 * the player confirms, {@code /ttl reborn <player> <race>} hands control back to the scripts.
 * Outside that rebirth nobody gets Tensura's menu at login: the scripts make Life 1 players Human.
 */
public final class Rebirth {
    private static final Logger LOGGER = LogUtils.getLogger();
    private static final Map<UUID, List<String>> OFFERS = new ConcurrentHashMap<>();
    private static volatile List<String> clientOffers = List.of();

    private Rebirth() {}

    public static void setClientOffers(List<String> races) {
        clientOffers = List.copyOf(races);
    }

    /** Race ids this menu's player must see, or null to keep Tensura's configured lists. */
    @Nullable
    public static List<String> offersFor(Player player) {
        if (player.level().isClientSide()) return clientOffers.isEmpty() ? null : clientOffers;
        return OFFERS.get(player.getUUID());
    }

    public static List<ManasRace> races(List<String> ids) {
        return ids.stream().map(id -> RaceAPI.getRaceRegistry().get(ResourceLocation.parse(id))).filter(Objects::nonNull).toList();
    }

    // Tensura reopens its menu at every login while its reset-in-progress flag is set, and only the menu's
    // submit button clears it. Races set by command (Life 1, reset) leave it set, which sent players through
    // the Great Sage scene, its wishes and a teleport to the Tensura world on login. Only our own rebirth may
    // show the menu, so anything else is blocked and the stale flag cleared.
    public static boolean blockFirstLogin(ServerPlayer player) {
        if (OFFERS.containsKey(player.getUUID())) return false;
        ITensuraPlayer data = TensuraStorages.getPlayerDataFrom(player);
        if (data.getInResetProgress() != 0) {
            data.setInResetProgress(0);
            player.setInvulnerable(false);
            LOGGER.info("[ttl] rebirth: cleared Tensura's pending reincarnation for {}", player.getGameProfile().getName());
        }
        return true;
    }

    public static void onRaceSet(Player player, ManasRace race) {
        if (!(player instanceof ServerPlayer serverPlayer) || OFFERS.remove(player.getUUID()) == null) return;
        sendOffers(serverPlayer, List.of());
        ResourceLocation id = RaceAPI.getRaceRegistry().getId(race);
        String name = serverPlayer.getGameProfile().getName();
        LOGGER.info("[ttl] rebirth: {} chose {}", name, id);
        MinecraftServer server = serverPlayer.getServer();
        // Next tick: the menu click that called setRace is still being handled.
        server.execute(() -> server.getCommands().performPrefixedCommand(
                server.createCommandSourceStack().withSuppressedOutput(), "ttl reborn " + name + " \"" + id + "\""));
    }

    public static void registerCommands(RegisterCommandsEvent event) {
        event.getDispatcher().register(Commands.literal("ttlrebirth")
                .requires(source -> source.hasPermission(2))
                .then(Commands.literal("open")
                        .then(Commands.argument("player", EntityArgument.player())
                                .then(Commands.argument("races", StringArgumentType.greedyString()).executes(Rebirth::open))))
                .then(Commands.literal("submit")
                        .then(Commands.argument("player", EntityArgument.player())
                                .then(Commands.argument("index", IntegerArgumentType.integer(0)).executes(Rebirth::submit))))
                .then(Commands.literal("cancel")
                        .then(Commands.argument("player", EntityArgument.player()).executes(Rebirth::cancel))));
    }

    private static int open(CommandContext<CommandSourceStack> ctx) throws CommandSyntaxException {
        ServerPlayer player = EntityArgument.getPlayer(ctx, "player");
        List<String> races = Arrays.stream(StringArgumentType.getString(ctx, "races").split("[,\\s]+"))
                .filter(s -> !s.isBlank()).map(s -> s.contains(":") ? s : "tensura:" + s).toList();
        if (races(races).isEmpty()) {
            ctx.getSource().sendFailure(Component.literal("ttlrebirth: no valid race in " + races));
            return 0;
        }
        OFFERS.put(player.getUUID(), races);
        sendOffers(player, races);
        // Same opening data Tensura uses at first login: full reincarnation, starting pool, no AP/MP override.
        MenuRegistry.openExtendedMenu(player,
                new SimpleMenuProvider((id, inventory, p) -> new ReincarnationMenu(id, inventory, p), Component.translatable("tensura.reincarnation")),
                buf -> {
                    buf.writeBoolean(false);
                    buf.writeInt(0);
                    buf.writeFloat(0f);
                    buf.writeFloat(0f);
                });
        LOGGER.info("[ttl] rebirth: menu opened for {} with {}", player.getGameProfile().getName(), races);
        return 1;
    }

    /** Test hook: confirm race {@code index} as if the player clicked it. */
    private static int submit(CommandContext<CommandSourceStack> ctx) throws CommandSyntaxException {
        ServerPlayer player = EntityArgument.getPlayer(ctx, "player");
        if (!(player.containerMenu instanceof ReincarnationMenu menu)) {
            ctx.getSource().sendFailure(Component.literal("ttlrebirth: no reincarnation menu open"));
            return 0;
        }
        menu.selectedManasRaceIndex.set(IntegerArgumentType.getInteger(ctx, "index"));
        menu.clickMenuButton(player, ReincarnationMenu.SUBMIT_BUTTON_ID);
        return 1;
    }

    private static int cancel(CommandContext<CommandSourceStack> ctx) throws CommandSyntaxException {
        ServerPlayer player = EntityArgument.getPlayer(ctx, "player");
        OFFERS.remove(player.getUUID());
        sendOffers(player, List.of());
        player.closeContainer();
        return 1;
    }

    private static void sendOffers(ServerPlayer player, List<String> races) {
        if (player.connection != null && player.connection.hasChannel(RebirthOffersPayload.TYPE)) {
            player.connection.send(new RebirthOffersPayload(races));
        }
    }
}
