package com.yasuke.ttl.world;

import com.mojang.logging.LogUtils;
import net.minecraft.SharedConstants;
import net.minecraft.core.registries.BuiltInRegistries;
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
 *
 * <p>{@code <world>/ttl-import.txt} ({@link WorldImport}) does the same for one dimension but then puts a prepared
 * world's region files in its place (Lerfing's map as the overworld) instead of leaving it to regenerate. It runs
 * first, and a reset marker never resets the dimension an import marker names.
 */
public final class WorldReset {
    private static final Logger LOGGER = LogUtils.getLogger();
    private static final List<String> RESET = new ArrayList<>();

    private WorldReset() {}

    public static void onServerAboutToStart(ServerAboutToStartEvent event) {
        RESET.clear();
        Path world = event.getServer().getWorldPath(LevelResource.ROOT).toAbsolutePath().normalize();
        Path backup = world.resolve("ttl-backup").resolve(LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd-HHmmss")));
        String imported = importWorld(world, backup);
        Path marker = world.resolve("ttl-reset.txt");
        if (!Files.isRegularFile(marker)) return;
        List<String> reset = new ArrayList<>();
        try {
            for (String line : Files.readAllLines(marker, StandardCharsets.UTF_8)) {
                String id = line.strip();
                if (id.isEmpty() || id.startsWith("#")) continue;
                ResourceLocation location = ResourceLocation.tryParse(id);
                if (location == null) {
                    LOGGER.warn("[ttl] world reset: not a dimension id: {}", id);
                    continue;
                }
                if (location.toString().equals(imported)) {
                    LOGGER.warn("[ttl] world reset: skipping {}: ttl-import.txt names it, and an import is never reset in the same start", id);
                    continue;
                }
                move(world, backup, ResourceKey.create(Registries.DIMENSION, location));
                reset.add(location.toString());
            }
            Files.delete(marker);
        } catch (IOException e) {
            LOGGER.error("[ttl] world reset failed; the marker stays for the next start", e);
            RESET.addAll(reset);
            return;
        }
        RESET.addAll(reset);
        LOGGER.info("[ttl] world reset: {} regenerate; old terrain in {}", reset, world.relativize(backup));
    }

    /**
     * Handles {@code ttl-import.txt}; returns the dimension id it names (also when refused, so the reset marker leaves
     * that dimension alone), or null without a marker. Throws, so the server does not start, while the journal of an
     * unfinished swap is there or when a failed swap could not be undone.
     */
    private static String importWorld(Path world, Path backup) {
        Path journal = world.resolve(WorldImport.JOURNAL);
        if (Files.exists(journal)) {
            throw new IllegalStateException("[ttl] " + journal + " exists: a world import did not finish (the server died mid-swap or the undo failed)."
                    + " The server does not start on a half-swapped world. Read the file, check region/entities/poi and ttl-backup by hand, then delete it.");
        }
        Path marker = world.resolve(WorldImport.MARKER);
        if (!Files.isRegularFile(marker)) return null;
        WorldImport.Log log = new WorldImport.Log() {
            public void info(String msg) {
                LOGGER.info(msg);
            }

            public void warn(String msg) {
                LOGGER.warn(msg);
            }
        };
        String id = null;
        WorldImport.Request request;
        ResourceLocation location;
        String how;
        try {
            request = WorldImport.parse(Files.readAllLines(marker, StandardCharsets.UTF_8));
            id = request.dimension();
            location = ResourceLocation.tryParse(id);
            if (location == null) throw new WorldImport.Refused("not a dimension id: " + id);
            id = location.toString();
            Path dimension = DimensionType.getStorageFolder(ResourceKey.create(Registries.DIMENSION, location), world).toAbsolutePath().normalize();
            Path source = WorldImport.resolveSource(world, dimension, request.folder());
            LOGGER.info("[ttl] world import: checking {} for {}", source, id);
            WorldImport.Report report = WorldImport.validate(source.resolve("region"), request.expectedFiles(), WorldReset::knownStatus,
                    SharedConstants.getCurrentVersion().getDataVersion().getVersion());
            LOGGER.info("[ttl] world import: source OK: {}", report.describe());
            how = WorldImport.swap(world, dimension, source, backup.resolve(location.getNamespace()).resolve(location.getPath()), WorldImport.FILES, log);
        } catch (WorldImport.Refused e) {
            LOGGER.error("[ttl] world import REFUSED, nothing was moved and the old world starts; the marker stays for the next start: {}", e.getMessage());
            return id;
        } catch (IOException e) {
            LOGGER.error("[ttl] world import FAILED and was undone, the old world starts; the marker stays for the next start: {}", e.getMessage(), e);
            return id;
        }
        // The swap is done: the marker must go, or the next start would import again over the new world.
        try {
            Files.move(marker, backup.resolve(WorldImport.MARKER));
        } catch (IOException e) {
            try {
                Files.delete(marker);
            } catch (IOException again) {
                throw new IllegalStateException("[ttl] world import done but " + marker + " cannot be removed; delete it by hand before the next start", again);
            }
        }
        RESET.add(id);
        LOGGER.info("[ttl] world import: {} from {}; old terrain in {} ({}); /ttl worldreset {} follows once the server has started",
                id, request.folder(), world.relativize(backup), how, id);
        return id;
    }

    /** True when this game knows a chunk's raw Status string (an unknown one loads as EMPTY and regenerates). */
    static boolean knownStatus(String status) {
        ResourceLocation id = ResourceLocation.tryParse(status);
        return id != null && BuiltInRegistries.CHUNK_STATUS.containsKey(id);
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
