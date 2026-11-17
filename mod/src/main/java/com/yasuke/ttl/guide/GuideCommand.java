package com.yasuke.ttl.guide;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import com.mojang.logging.LogUtils;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import org.slf4j.Logger;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

/**
 * {@code /ttlguide <players> <json>} opens the guide screen (guide/client/GuideScreen) on each player's client.
 * The scripts build the JSON from TtlData.guide (life/guide.js):
 * {"set": "main", "then": "ttl life", "pages": [{"title": "...", "lines": ["...", ...]}]} ("body" with \n also works).
 * {@code /ttlguide check <player> <set>} is the bot-test assertion: "ttl: ..." unless that set was the last one
 * sent to the player (bots have no client, so the send is recorded even when nothing can be shown).
 */
@EventBusSubscriber(modid = "ttl")
public final class GuideCommand {
    private static final Logger LOGGER = LogUtils.getLogger();
    private static final Map<UUID, String> LAST = new ConcurrentHashMap<>();

    private GuideCommand() {}

    @SubscribeEvent
    public static void register(RegisterCommandsEvent event) {
        event.getDispatcher().register(Commands.literal("ttlguide")
                .requires(source -> source.hasPermission(2))
                .then(Commands.literal("check")
                        .then(Commands.argument("player", EntityArgument.player())
                                .then(Commands.argument("set", StringArgumentType.word()).executes(GuideCommand::check))))
                .then(Commands.argument("players", EntityArgument.players())
                        .then(Commands.argument("json", StringArgumentType.greedyString()).executes(GuideCommand::open))));
    }

    private static int open(CommandContext<CommandSourceStack> ctx) throws CommandSyntaxException {
        Collection<ServerPlayer> players = EntityArgument.getPlayers(ctx, "players");
        GuidePayload payload;
        try {
            payload = parse(StringArgumentType.getString(ctx, "json"));
        } catch (RuntimeException e) {
            ctx.getSource().sendFailure(Component.literal("ttlguide: bad JSON: " + e.getMessage()));
            return 0;
        }
        if (payload.pages().isEmpty()) {
            ctx.getSource().sendFailure(Component.literal("ttlguide: no pages"));
            return 0;
        }
        int shown = 0;
        for (ServerPlayer player : players) {
            LAST.put(player.getUUID(), payload.set());
            if (player.connection != null && player.connection.hasChannel(GuidePayload.TYPE)) {
                player.connection.send(payload);
                shown++;
            }
        }
        int sent = shown;
        ctx.getSource().sendSuccess(() -> Component.literal("ttlguide: " + payload.set() + " (" + payload.pages().size()
                + " pages) to " + players.size() + " player(s), " + sent + " with the guide screen"), false);
        return Math.max(1, shown);
    }

    private static int check(CommandContext<CommandSourceStack> ctx) throws CommandSyntaxException {
        ServerPlayer player = EntityArgument.getPlayer(ctx, "player");
        String want = StringArgumentType.getString(ctx, "set");
        String last = LAST.get(player.getUUID());
        String name = player.getGameProfile().getName();
        if (!want.equals(last)) {
            ctx.getSource().sendSuccess(() -> Component.literal("ttl: guide " + want + " was not sent to " + name
                    + " (last: " + (last == null ? "none" : last) + ")"), false);
            return 0;
        }
        ctx.getSource().sendSuccess(() -> Component.literal("guide " + want + " was sent to " + name), false);
        return 1;
    }

    static GuidePayload parse(String json) {
        JsonObject spec = JsonParser.parseString(json).getAsJsonObject();
        String set = spec.has("set") ? spec.get("set").getAsString() : "guide";
        String then = spec.has("then") ? spec.get("then").getAsString().replaceFirst("^/", "") : "";
        List<GuidePayload.Page> pages = new ArrayList<>();
        JsonArray list = spec.has("pages") ? spec.getAsJsonArray("pages") : new JsonArray();
        for (JsonElement element : list) {
            if (pages.size() >= 64) {
                LOGGER.warn("[ttl] guide {}: more than 64 pages, the rest is dropped", set);
                break;
            }
            JsonObject page = element.getAsJsonObject();
            List<String> lines = new ArrayList<>();
            if (page.has("lines")) {
                for (JsonElement line : page.getAsJsonArray("lines")) lines.add(line.getAsString());
            } else if (page.has("body")) {
                lines.addAll(List.of(page.get("body").getAsString().split("\r?\n", -1)));
            }
            if (lines.size() > 256) lines = new ArrayList<>(lines.subList(0, 256));
            pages.add(new GuidePayload.Page(page.has("title") ? page.get("title").getAsString() : "", lines));
        }
        return new GuidePayload(set, pages, then);
    }
}
