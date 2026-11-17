package com.yasuke.ttl.world;

import com.mojang.logging.LogUtils;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.dimension.DimensionType;
import net.minecraft.world.level.storage.LevelResource;
import net.neoforged.neoforge.event.server.ServerAboutToStartEvent;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import org.slf4j.Logger;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

/**
 * Regenerates dimensions after a worldgen change. List them (one id per line, e.g. {@code minecraft:overworld},
 * {@code ttl:mortal_realm}) in {@code <world>/ttl-reset.txt} and restart: before the levels load, their terrain
 * is moved to {@code <world>/ttl-backup/<time>/} (nothing is deleted) and the marker removed. Once the server has
 * started, {@code /ttl worldreset <ids>} tells the scripts, which re-place spawns and move players on login.
 * Player data, the Spirit Corridor and every dimension not listed stay as they are.
 */
public final class WorldReset {
    private static final Logger LOGGER = LogUtils.getLogger();
    private static final List<String> RESET = new ArrayList<>();

    private WorldReset() {}

    public static void onServerAboutToStart(ServerAboutToStartEvent event) {
        RESET.clear();
        Path world = event.getServer().getWorldPath(LevelResource.ROOT);
        Path marker = world.resolve("ttl-reset.txt");
        if (!Files.isRegularFile(marker)) return;
        Path backup = world.resolve("ttl-backup").resolve(LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd-HHmmss")));
        try {
            for (String line : Files.readAllLines(marker, StandardCharsets.UTF_8)) {
                String id = line.strip();
                if (id.isEmpty() || id.startsWith("#")) continue;
                ResourceLocation location = ResourceLocation.tryParse(id);
                if (location == null) {
                    LOGGER.warn("[ttl] world reset: not a dimension id: {}", id);
                    continue;
                }
                move(world, backup, ResourceKey.create(Registries.DIMENSION, location));
                RESET.add(location.toString());
            }
            Files.delete(marker);
        } catch (IOException e) {
            LOGGER.error("[ttl] world reset failed; the marker stays for the next start", e);
            return;
        }
        LOGGER.info("[ttl] world reset: {} regenerate; old terrain in {}", RESET, world.relativize(backup));
    }

    public static void onServerStarted(ServerStartedEvent event) {
        if (RESET.isEmpty()) return;
        MinecraftServer server = event.getServer();
        server.getCommands().performPrefixedCommand(server.createCommandSourceStack().withSuppressedOutput(),
                "ttl worldreset " + String.join(",", RESET));
        RESET.clear();
    }

    private static void move(Path world, Path backup, ResourceKey<Level> key) throws IOException {
        Path folder = DimensionType.getStorageFolder(key, world);
        Path target = backup.resolve(key.location().getNamespace()).resolve(key.location().getPath());
        Files.createDirectories(target);
        if (!folder.equals(world)) {
            if (Files.exists(folder)) Files.move(folder, target.resolve("dimension"));
            return;
        }
        // The overworld lives in the world folder itself: only its terrain and its Distant Horizons LODs move.
        for (String name : List.of("region", "entities", "poi")) {
            if (Files.exists(world.resolve(name))) Files.move(world.resolve(name), target.resolve(name));
        }
        Path data = world.resolve("data");
        if (!Files.isDirectory(data)) return;
        try (DirectoryStream<Path> files = Files.newDirectoryStream(data, "DistantHorizons*")) {
            for (Path file : files) Files.move(file, target.resolve(file.getFileName()));
        }
    }
}
