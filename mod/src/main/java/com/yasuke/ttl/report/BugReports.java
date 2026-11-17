package com.yasuke.ttl.report;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.logging.LogUtils;
import com.yasuke.ttl.bot.TestBots;
import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSource;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.Style;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import org.slf4j.Logger;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.time.format.DateTimeFormatter;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

/**
 * {@code /bug <text>}: anyone can report a problem in one command. The report bundles the player's Two
 * Lives state (via {@code /ttl inspect}), position, health, TPS, the pack version and the recent [ttl]
 * and ERROR log lines. It is always saved to {@code ttl-reports/} on the server, and becomes a GitHub
 * issue (labels bug, from-game, triage) when TTL_GITHUB_TOKEN and TTL_REPORT_REPO are set.
 */
public final class BugReports {
    private static final Logger LOGGER = LogUtils.getLogger();
    private static final long COOLDOWN_MS = 60_000;
    private static final Map<UUID, Long> LAST = new ConcurrentHashMap<>();
    private static final HttpClient HTTP = HttpClient.newHttpClient();

    private BugReports() {}

    public static void registerCommands(RegisterCommandsEvent event) {
        event.getDispatcher().register(Commands.literal("bug")
                .then(Commands.argument("text", StringArgumentType.greedyString()).executes(BugReports::report)));
    }

    private static int report(CommandContext<CommandSourceStack> ctx) {
        ServerPlayer player = ctx.getSource().getPlayer();
        if (player == null) {
            ctx.getSource().sendFailure(Component.literal("/bug is for players"));
            return 0;
        }
        long now = System.currentTimeMillis();
        Long last = LAST.get(player.getUUID());
        if (last != null && now - last < COOLDOWN_MS) {
            player.sendSystemMessage(Component.literal("You just sent a report. Wait a minute before the next one.").withStyle(ChatFormatting.RED));
            return 0;
        }
        LAST.put(player.getUUID(), now);

        MinecraftServer server = player.getServer();
        String text = StringArgumentType.getString(ctx, "text").trim();
        String name = player.getGameProfile().getName();
        String stamp = DateTimeFormatter.ofPattern("yyyyMMdd-HHmmss").withZone(ZoneOffset.UTC).format(Instant.ofEpochMilli(now));
        String title = "[bug] " + name + ": " + (text.length() > 70 ? text.substring(0, 70) + "…" : text);
        String body = body(server, player, text);

        Path file = server.getServerDirectory().resolve("ttl-reports").resolve(stamp + "-" + name + ".md");
        try {
            Files.createDirectories(file.getParent());
            Files.writeString(file, "# " + title + "\n\n" + body, StandardCharsets.UTF_8);
        } catch (IOException e) {
            LOGGER.error("[ttl] bug report: could not save {}", file, e);
        }
        LOGGER.info("[ttl] bug report from {}: {} ({})", name, text, file.getFileName());

        String token = System.getenv("TTL_GITHUB_TOKEN");
        String repo = System.getenv("TTL_REPORT_REPO");
        // The bot suite runs /bug after every deploy; those reports stay on the server, not on GitHub.
        if (token == null || token.isBlank() || repo == null || repo.isBlank() || TestBots.isBot(player)) {
            player.sendSystemMessage(Component.literal("Thanks! Your report was saved (" + file.getFileName() + ").").withStyle(ChatFormatting.GREEN));
            return 1;
        }
        createIssue(server, player.getUUID(), token, repo, title, body);
        player.sendSystemMessage(Component.literal("Thanks! Sending your report…").withStyle(ChatFormatting.GREEN));
        return 1;
    }

    private static void createIssue(MinecraftServer server, UUID playerId, String token, String repo, String title, String body) {
        JsonObject issue = new JsonObject();
        issue.addProperty("title", title);
        issue.addProperty("body", body);
        JsonArray labels = new JsonArray();
        labels.add("bug");
        labels.add("from-game");
        labels.add("triage");
        issue.add("labels", labels);
        HttpRequest request = HttpRequest.newBuilder(URI.create("https://api.github.com/repos/" + repo + "/issues"))
                .header("Authorization", "Bearer " + token)
                .header("Accept", "application/vnd.github+json")
                .header("X-GitHub-Api-Version", "2022-11-28")
                .POST(HttpRequest.BodyPublishers.ofString(issue.toString(), StandardCharsets.UTF_8))
                .build();
        HTTP.sendAsync(request, HttpResponse.BodyHandlers.ofString()).whenComplete((response, error) -> server.execute(() -> {
            ServerPlayer player = server.getPlayerList().getPlayer(playerId);
            if (error != null || response.statusCode() / 100 != 2) {
                LOGGER.error("[ttl] bug report: GitHub issue failed ({})", error != null ? error.toString() : response.statusCode() + " " + response.body());
                if (player != null) player.sendSystemMessage(Component.literal("Your report was saved on the server, but GitHub did not accept it. An admin will pick it up.").withStyle(ChatFormatting.YELLOW));
                return;
            }
            JsonObject created = JsonParser.parseString(response.body()).getAsJsonObject();
            String url = created.get("html_url").getAsString();
            LOGGER.info("[ttl] bug report: created {}", url);
            if (player != null) {
                player.sendSystemMessage(Component.literal("Thanks! Reported as issue #" + created.get("number").getAsInt() + " (click to open)")
                        .withStyle(Style.EMPTY.withColor(ChatFormatting.GREEN).withUnderlined(true).withClickEvent(new ClickEvent(ClickEvent.Action.OPEN_URL, url))));
            }
        }));
    }

    private static String body(MinecraftServer server, ServerPlayer player, String text) {
        StringBuilder b = new StringBuilder();
        b.append("> ").append(text.replace("\n", "\n> ")).append("\n\n");
        b.append("| | |\n|---|---|\n");
        row(b, "Player", player.getGameProfile().getName());
        row(b, "Dimension", player.level().dimension().location().toString());
        row(b, "Position", String.format("%.1f %.1f %.1f", player.getX(), player.getY(), player.getZ()));
        row(b, "Health / food", String.format("%.1f / %d", player.getHealth(), player.getFoodData().getFoodLevel()));
        row(b, "Game mode", player.gameMode.getGameModeForPlayer().getName());
        row(b, "Main hand", BuiltInRegistries.ITEM.getKey(player.getMainHandItem().getItem()).toString());
        row(b, "MSPT / TPS", String.format("%.1f ms / %.1f", server.getAverageTickTimeNanos() / 1_000_000.0,
                Math.min(20.0, 1000.0 / Math.max(1.0, server.getAverageTickTimeNanos() / 1_000_000.0))));
        row(b, "Players online", String.valueOf(server.getPlayerCount()));
        row(b, "Pack", packHash(server));
        row(b, "Time (UTC)", Instant.now().toString());
        b.append("\n**Two Lives state** (`/ttl inspect`)\n```\n").append(inspect(server, player)).append("\n```\n");
        List<String> log = readLog(server);
        b.append("\n**Recent [ttl] log**\n```\n").append(String.join("\n", tail(log, "[ttl]", 30))).append("\n```\n");
        b.append("\n**Recent errors**\n```\n").append(String.join("\n", tail(log, "/ERROR]", 15))).append("\n```\n");
        return b.toString();
    }

    private static void row(StringBuilder b, String key, String value) {
        b.append("| ").append(key).append(" | ").append(value.replace("|", "\\|")).append(" |\n");
    }

    // Runs `/ttl inspect <player>` (KubeJS) and keeps what it prints.
    private static String inspect(MinecraftServer server, ServerPlayer player) {
        List<String> lines = new ArrayList<>();
        CommandSource capture = new CommandSource() {
            @Override
            public void sendSystemMessage(Component message) {
                lines.add(message.getString());
            }

            @Override
            public boolean acceptsSuccess() {
                return true;
            }

            @Override
            public boolean acceptsFailure() {
                return true;
            }

            @Override
            public boolean shouldInformAdmins() {
                return false;
            }
        };
        server.getCommands().performPrefixedCommand(server.createCommandSourceStack().withSource(capture),
                "ttl inspect " + player.getGameProfile().getName());
        return lines.isEmpty() ? "(no output)" : String.join("\n", lines);
    }

    private static String packHash(MinecraftServer server) {
        try {
            String json = Files.readString(server.getServerDirectory().resolve("packwiz.json"));
            String hash = JsonParser.parseString(json).getAsJsonObject().getAsJsonObject("packFileHash").get("value").getAsString();
            return hash.substring(0, 12);
        } catch (Exception e) {
            return "unknown";
        }
    }

    private static List<String> readLog(MinecraftServer server) {
        try {
            return Files.readAllLines(server.getServerDirectory().resolve("logs").resolve("latest.log"), StandardCharsets.UTF_8);
        } catch (IOException e) {
            return List.of();
        }
    }

    private static List<String> tail(List<String> log, String needle, int max) {
        List<String> hits = new ArrayList<>();
        for (String line : log) {
            if (line.contains(needle) && !line.contains("mixin")) hits.add(line.length() > 300 ? line.substring(0, 300) : line);
        }
        return hits.subList(Math.max(0, hits.size() - max), hits.size());
    }
}
