package com.yasuke.ttl.bridge;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.mojang.logging.LogUtils;
import net.minecraft.commands.arguments.blocks.BlockStateParser;
import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.IntArrayTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.NbtAccounter;
import net.minecraft.nbt.NbtIo;
import net.minecraft.nbt.StringTag;
import net.minecraft.nbt.Tag;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.LevelChunk;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.storage.LevelResource;
import org.slf4j.Logger;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.Deque;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Stream;

/**
 * The write queue. A job is a box, a palette and one palette index per cell (-1 = keep). It runs in three phases
 * inside a per-tick time budget: SNAPSHOT (the cells it will change, with their block entities, saved to
 * {@code <world>/ttl-bridge/history/<id>.snapshot.nbt} so undo survives a restart), PLACE (setBlock without
 * neighbour or shape updates, drops suppressed), then block-entity NBT. Undo is a new job made from the snapshot,
 * so an undo can itself be undone.
 */
final class BridgeJobs {
    private static final Logger LOGGER = LogUtils.getLogger();
    private static final DateTimeFormatter ID = DateTimeFormatter.ofPattern("yyyyMMdd-HHmmss");
    /** Client updates only: no neighbour updates, no shape updates, no drops. */
    private static final int FLAGS_QUIET = Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE | Block.UPDATE_SUPPRESS_DROPS;
    private static final int FLAGS_FULL = Block.UPDATE_ALL;

    enum Phase { QUEUED, SNAPSHOT, PLACE, SHAPES, DONE, FAILED, CANCELLED, INTERRUPTED }

    static final class Job {
        final String id;
        final String label;
        final String dim;
        final BoundingBox box;
        final BlockState[] palette;
        final CompoundTag[] paletteNbt;
        final int[] cells;
        final Map<Integer, CompoundTag> cellNbt;
        final boolean neighborUpdates;
        final boolean fixShapes;
        final String undoOf;
        final long created = System.currentTimeMillis();
        volatile Phase phase = Phase.QUEUED;
        volatile String error;
        int cursor;
        int changed;
        int total;
        // snapshot being built
        Map<BlockState, Integer> snapIndex;
        int[] snapCells;
        Map<Integer, CompoundTag> snapNbt;

        Job(String id, String label, String dim, BoundingBox box, BlockState[] palette, CompoundTag[] paletteNbt, int[] cells,
            Map<Integer, CompoundTag> cellNbt, boolean neighborUpdates, boolean fixShapes, String undoOf) {
            this.id = id;
            this.label = label;
            this.dim = dim;
            this.box = box;
            this.palette = palette;
            this.paletteNbt = paletteNbt;
            this.cells = cells;
            this.cellNbt = cellNbt;
            this.neighborUpdates = neighborUpdates;
            this.fixShapes = fixShapes;
            this.undoOf = undoOf;
            for (int c : cells) if (c >= 0) total++;
        }

        JsonObject json() {
            JsonObject o = new JsonObject();
            o.addProperty("id", id);
            o.addProperty("label", label);
            o.addProperty("dim", dim);
            o.add("from", Bridge.arr(box.minX(), box.minY(), box.minZ()));
            o.add("to", Bridge.arr(box.maxX(), box.maxY(), box.maxZ()));
            o.addProperty("phase", phase.name().toLowerCase());
            o.addProperty("cells", total);
            o.addProperty("progress", phase == Phase.DONE ? 1.0 : progress());
            o.addProperty("changed", changed);
            o.addProperty("created", created);
            if (undoOf != null) o.addProperty("undo_of", undoOf);
            if (error != null) o.addProperty("error", error);
            return o;
        }

        private double progress() {
            if (cells.length == 0) return 1.0;
            double part = (double) cursor / cells.length;
            return switch (phase) {
                case SNAPSHOT -> part * 0.3;
                case PLACE -> 0.3 + part * 0.6;
                case SHAPES -> 0.9 + part * 0.1;
                default -> 0.0;
            };
        }
    }

    private final MinecraftServer server;
    private BridgeConfig config;
    private final Path history;
    private final Deque<Job> queue = new ArrayDeque<>();
    private final Map<String, Job> jobs = new LinkedHashMap<>();
    private int counter;

    BridgeJobs(MinecraftServer server, BridgeConfig config) {
        this.server = server;
        this.config = config;
        this.history = server.getWorldPath(LevelResource.ROOT).resolve("ttl-bridge").resolve("history");
    }

    // --- creating jobs (server thread) ------------------------------------------------------------------------------

    /** Validates a job request; with dry_run returns counts without queueing. */
    JsonObject submit(JsonObject req) {
        ServerLevel level = BridgeWorld.level(server, Bridge.str(req, "dim", "minecraft:overworld"));
        int[] origin = Bridge.ints(req.getAsJsonArray("origin"), 3);
        int[] size = Bridge.ints(req.getAsJsonArray("size"), 3);
        if (size[0] < 1 || size[1] < 1 || size[2] < 1) throw new Bridge.BadRequest("size must be at least 1 x 1 x 1");
        long volume = (long) size[0] * size[1] * size[2];
        if (volume > config.maxJobCells) throw new Bridge.BadRequest("box has " + volume + " cells, limit " + config.maxJobCells);
        BoundingBox box = new BoundingBox(origin[0], origin[1], origin[2], origin[0] + size[0] - 1, origin[1] + size[1] - 1, origin[2] + size[2] - 1);
        if (box.minY() < level.getMinBuildHeight() || box.maxY() >= level.getMaxBuildHeight())
            throw new Bridge.BadRequest("y " + box.minY() + ".." + box.maxY() + " outside the build height " + level.getMinBuildHeight() + ".." + (level.getMaxBuildHeight() - 1));
        String dim = level.dimension().location().toString();
        String refusal = config.writeRefusal(dim, box);
        if (refusal != null) throw new Bridge.Forbidden(refusal);

        JsonArray paletteJson = req.getAsJsonArray("palette");
        if (paletteJson == null || paletteJson.isEmpty()) throw new Bridge.BadRequest("palette missing");
        BlockState[] palette = new BlockState[paletteJson.size()];
        CompoundTag[] nbt = new CompoundTag[palette.length];
        for (int i = 0; i < palette.length; i++) {
            BlockStateParser.BlockResult r = BridgeWorld.parseState(level, paletteJson.get(i).getAsString());
            palette[i] = r.blockState();
            nbt[i] = r.nbt();
        }
        int[] cells = BridgeWorld.Rle.decode(req.getAsJsonArray("rle"), (int) volume);
        for (int c : cells) {
            if (c < -1 || c >= palette.length) throw new Bridge.BadRequest("palette index " + c + " out of range");
        }
        boolean neighbors = "neighbors".equals(Bridge.str(req, "updates", "quiet"));
        String label = Bridge.str(req, "label", "");

        if (req.has("dry_run") && req.get("dry_run").getAsBoolean()) {
            return dryRun(level, box, palette, cells, req.has("load") && req.get("load").getAsBoolean());
        }
        boolean shapes = !req.has("fix_shapes") || req.get("fix_shapes").getAsBoolean();
        Job job = new Job(newId(), label, dim, box, palette, nbt, cells, new HashMap<>(), neighbors, shapes, null);
        enqueue(job);
        return job.json();
    }

    private JsonObject dryRun(ServerLevel level, BoundingBox box, BlockState[] palette, int[] cells, boolean load) {
        int w = box.getXSpan(), l = box.getZSpan();
        int set = 0, differ = 0, unknown = 0, replacingBlockEntities = 0;
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        for (int i = 0; i < cells.length; i++) {
            if (cells[i] < 0) continue;
            set++;
            pos.set(box.minX() + i % w, box.minY() + i / (w * l), box.minZ() + (i / w) % l);
            LevelChunk c = load ? level.getChunk(pos.getX() >> 4, pos.getZ() >> 4)
                    : level.getChunkSource().getChunkNow(pos.getX() >> 4, pos.getZ() >> 4);
            if (c == null) {
                unknown++;
                continue;
            }
            BlockState now = c.getBlockState(pos);
            if (now != palette[cells[i]]) {
                differ++;
                if (now.hasBlockEntity()) replacingBlockEntities++;
            }
        }
        JsonObject o = new JsonObject();
        o.addProperty("dry_run", true);
        o.addProperty("dim", level.dimension().location().toString());
        o.add("from", Bridge.arr(box.minX(), box.minY(), box.minZ()));
        o.add("to", Bridge.arr(box.maxX(), box.maxY(), box.maxZ()));
        o.addProperty("cells_set", set);
        o.addProperty("cells_changed", differ);
        o.addProperty("cells_in_unloaded_chunks", unknown);
        o.addProperty("replaces_block_entities", replacingBlockEntities);
        o.addProperty("chunks", (box.maxX() / 16 - box.minX() / 16 + 1) * (box.maxZ() / 16 - box.minZ() / 16 + 1));
        o.addProperty("estimated_ticks", Math.max(1, (int) Math.ceil(set * 2.0 / Math.max(1, cellsPerTickEstimate()))));
        return o;
    }

    private int cellsPerTickEstimate() {
        return (int) (config.budgetMs * 4000); // ~4 cells per microsecond with quiet flags; measured per server it varies
    }

    private String newId() {
        String id;
        do {  // the counter restarts with the server: never reuse an id whose snapshot is in the history folder
            id = "j" + LocalDateTime.now().format(ID) + "-" + (++counter);
        } while (jobs.containsKey(id) || Files.exists(history.resolve(id + ".json")));
        return id;
    }

    private void enqueue(Job job) {
        jobs.put(job.id, job);
        queue.add(job);
        writeMeta(job);
        LOGGER.info("[ttl] bridge: queued job {} ({} cells in {} {}) {}", job.id, job.total, job.dim, job.box, job.label);
    }

    JsonObject undo(String id) {
        Path file = history.resolve(id + ".snapshot.nbt");
        if (!Files.exists(file)) throw new Bridge.NotFound("no snapshot for job " + id);
        Job running = jobs.get(id);
        if (running != null && (running.phase == Phase.QUEUED || running.phase == Phase.SNAPSHOT))
            throw new Bridge.BadRequest("job " + id + " has not started placing yet; cancel it instead");
        try {
            CompoundTag tag = NbtIo.readCompressed(file, NbtAccounter.unlimitedHeap());
            ServerLevel level = BridgeWorld.level(server, tag.getString("dim"));
            int[] o = tag.getIntArray("origin"), s = tag.getIntArray("size");
            BoundingBox box = new BoundingBox(o[0], o[1], o[2], o[0] + s[0] - 1, o[1] + s[1] - 1, o[2] + s[2] - 1);
            String refusal = config.writeRefusal(level.dimension().location().toString(), box);
            if (refusal != null) throw new Bridge.Forbidden("undo refused: " + refusal);
            ListTag paletteTag = tag.getList("palette", Tag.TAG_STRING);
            BlockState[] palette = new BlockState[paletteTag.size()];
            for (int i = 0; i < palette.length; i++) palette[i] = BridgeWorld.parseState(level, paletteTag.getString(i)).blockState();
            Map<Integer, CompoundTag> nbt = new HashMap<>();
            for (Tag t : tag.getList("block_entities", Tag.TAG_COMPOUND)) {
                CompoundTag e = (CompoundTag) t;
                nbt.put(e.getInt("cell"), e.getCompound("nbt"));
            }
            Job job = new Job(newId(), "undo " + id, level.dimension().location().toString(), box, palette,
                    new CompoundTag[palette.length], tag.getIntArray("cells"), nbt, false, false, id);
            enqueue(job);
            return job.json();
        } catch (IOException e) {
            throw new IllegalStateException("snapshot " + file + " unreadable: " + e);
        }
    }

    JsonObject cancel(String id) {
        Job job = jobs.get(id);
        if (job == null) throw new Bridge.NotFound("no running job " + id);
        if (job.phase == Phase.QUEUED || job.phase == Phase.SNAPSHOT || job.phase == Phase.PLACE || job.phase == Phase.SHAPES) {
            boolean placing = job.phase == Phase.PLACE || job.phase == Phase.SHAPES;
            job.phase = Phase.CANCELLED;
            job.error = placing ? "cancelled while placing; undo " + id + " restores the box" : "cancelled before any block changed";
            queue.remove(job);
            writeMeta(job);
        }
        return job.json();
    }

    JsonObject get(String id) {
        Job job = jobs.get(id);
        if (job != null) return job.json();
        Path meta = history.resolve(id + ".json");
        if (Files.exists(meta)) {
            try {
                return BridgeConfig.GSON.fromJson(Files.readString(meta, StandardCharsets.UTF_8), JsonObject.class);
            } catch (IOException e) {
                throw new IllegalStateException(e);
            }
        }
        throw new Bridge.NotFound("no job " + id);
    }

    /** This run's jobs and, after a restart, the ones in the history folder (newest first). */
    JsonArray list(int limit) {
        JsonArray out = new JsonArray();
        List<JsonObject> all = new ArrayList<>();
        jobs.values().forEach(j -> all.add(j.json()));
        if (Files.isDirectory(history)) {
            try (Stream<Path> files = Files.list(history)) {
                files.filter(p -> p.getFileName().toString().endsWith(".json")).forEach(p -> {
                    String id = p.getFileName().toString().replace(".json", "");
                    if (jobs.containsKey(id)) return;
                    try {
                        all.add(BridgeConfig.GSON.fromJson(Files.readString(p, StandardCharsets.UTF_8), JsonObject.class));
                    } catch (Exception ignored) {
                        // a half-written meta file: skip it
                    }
                });
            } catch (IOException e) {
                LOGGER.warn("[ttl] bridge: cannot list {}: {}", history, e.toString());
            }
        }
        all.sort(Comparator.comparingLong((JsonObject o) -> o.has("created") ? o.get("created").getAsLong() : 0L).reversed());
        all.stream().limit(limit).forEach(out::add);
        return out;
    }

    void config(BridgeConfig config) {
        this.config = config;
    }

    int queued() {
        return queue.size();
    }

    // --- running jobs (server tick) ---------------------------------------------------------------------------------

    void tick() {
        if (queue.isEmpty()) return;
        double mspt = server.getAverageTickTimeNanos() / 1_000_000.0;
        if (mspt > config.pauseMspt) return; // the server is already behind: players first
        long deadline = System.nanoTime() + (long) (config.budgetMs * 1_000_000);
        while (!queue.isEmpty() && System.nanoTime() < deadline) {
            Job job = queue.peek();
            try {
                if (!step(job, deadline)) continue; // budget used up inside the job
                queue.poll();
            } catch (Exception e) {
                job.phase = Phase.FAILED;
                job.error = e.toString();
                queue.poll();
                writeMeta(job);
                LOGGER.error("[ttl] bridge: job {} failed: {}", job.id, e.toString());
            }
        }
    }

    /** Advances a job until the deadline; true when it has finished. */
    private boolean step(Job job, long deadline) throws IOException {
        ServerLevel level = BridgeWorld.level(server, job.dim);
        int w = job.box.getXSpan(), l = job.box.getZSpan();
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        if (job.phase == Phase.QUEUED) {
            job.phase = Phase.SNAPSHOT;
            job.cursor = 0;
            job.snapIndex = new LinkedHashMap<>();
            job.snapCells = new int[job.cells.length];
            job.snapNbt = new HashMap<>();
        }
        if (job.phase == Phase.SNAPSHOT) {
            while (job.cursor < job.cells.length) {
                int i = job.cursor++;
                if (job.cells[i] < 0) {
                    job.snapCells[i] = -1;
                    continue;
                }
                pos.set(job.box.minX() + i % w, job.box.minY() + i / (w * l), job.box.minZ() + (i / w) % l);
                LevelChunk chunk = level.getChunk(pos.getX() >> 4, pos.getZ() >> 4);
                BlockState now = chunk.getBlockState(pos);
                job.snapCells[i] = job.snapIndex.computeIfAbsent(now, k -> job.snapIndex.size());
                if (now.hasBlockEntity()) {
                    BlockEntity be = chunk.getBlockEntity(pos);
                    if (be != null) job.snapNbt.put(i, be.saveWithFullMetadata(level.registryAccess()));
                }
                if ((i & 255) == 0 && System.nanoTime() > deadline) return false;
            }
            writeSnapshot(job);
            job.snapIndex = null;
            job.snapCells = null;
            job.snapNbt = null;
            job.phase = Phase.PLACE;
            job.cursor = 0;
            writeMeta(job);
        }
        if (job.phase == Phase.PLACE) {
            int flags = job.neighborUpdates ? FLAGS_FULL : FLAGS_QUIET;
            while (job.cursor < job.cells.length) {
                int i = job.cursor++;
                int c = job.cells[i];
                if (c < 0) continue;
                pos.set(job.box.minX() + i % w, job.box.minY() + i / (w * l), job.box.minZ() + (i / w) % l);
                BlockState state = job.palette[c];
                LevelChunk chunk = level.getChunk(pos.getX() >> 4, pos.getZ() >> 4);
                if (chunk.getBlockState(pos) != state) {
                    level.setBlock(pos, state, flags);
                    job.changed++;
                }
                CompoundTag nbt = job.cellNbt.containsKey(i) ? job.cellNbt.get(i) : job.paletteNbt[c];
                if (nbt != null) {
                    BlockEntity be = level.getBlockEntity(pos);
                    if (be != null) {
                        be.loadWithComponents(nbt, level.registryAccess());
                        be.setChanged();
                        level.sendBlockUpdated(pos, state, state, Block.UPDATE_CLIENTS);
                    }
                }
                if ((i & 255) == 0 && System.nanoTime() > deadline) return false;
            }
            job.phase = job.fixShapes ? Phase.SHAPES : Phase.DONE;
            job.cursor = 0;
        }
        if (job.phase == Phase.SHAPES) {
            // Quiet placement skips shape updates, so fences, panes, walls and stairs do not connect yet: let every
            // placed block recompute its shape once, now that all
            // its neighbours are there.
            while (job.cursor < job.cells.length) {
                int i = job.cursor++;
                if (job.cells[i] < 0) continue;
                pos.set(job.box.minX() + i % w, job.box.minY() + i / (w * l), job.box.minZ() + (i / w) % l);
                BlockState now = level.getBlockState(pos);
                BlockState shaped = Block.updateFromNeighbourShapes(now, level, pos);
                if (shaped != now && !shaped.isAir()) level.setBlock(pos, shaped, FLAGS_QUIET);
                if ((i & 255) == 0 && System.nanoTime() > deadline) return false;
            }
            job.phase = Phase.DONE;
            writeMeta(job);
            LOGGER.info("[ttl] bridge: job {} done, {} of {} cells changed", job.id, job.changed, job.total);
        }
        return true;
    }

    private void writeSnapshot(Job job) throws IOException {
        CompoundTag tag = new CompoundTag();
        tag.putString("id", job.id);
        tag.putString("dim", job.dim);
        tag.put("origin", new IntArrayTag(new int[]{job.box.minX(), job.box.minY(), job.box.minZ()}));
        tag.put("size", new IntArrayTag(new int[]{job.box.getXSpan(), job.box.getYSpan(), job.box.getZSpan()}));
        ListTag palette = new ListTag();
        for (BlockState s : job.snapIndex.keySet()) palette.add(StringTag.valueOf(BlockStateParser.serialize(s)));
        tag.put("palette", palette);
        tag.putIntArray("cells", job.snapCells);
        ListTag bes = new ListTag();
        job.snapNbt.forEach((cell, nbt) -> {
            CompoundTag e = new CompoundTag();
            e.putInt("cell", cell);
            e.put("nbt", nbt);
            bes.add(e);
        });
        tag.put("block_entities", bes);
        Files.createDirectories(history);
        NbtIo.writeCompressed(tag, history.resolve(job.id + ".snapshot.nbt"));
    }

    private void writeMeta(Job job) {
        try {
            Files.createDirectories(history);
            Files.writeString(history.resolve(job.id + ".json"), BridgeConfig.GSON.toJson(job.json()), StandardCharsets.UTF_8);
        } catch (IOException e) {
            LOGGER.warn("[ttl] bridge: cannot write job meta {}: {}", job.id, e.toString());
        }
    }

    /** Server stopping: running jobs are marked interrupted (undo works once their snapshot was written). */
    void shutdown() {
        for (Job job : queue) {
            job.phase = Phase.INTERRUPTED;
            job.error = "server stopped";
            writeMeta(job);
        }
        queue.clear();
    }

}
