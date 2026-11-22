package com.yasuke.ttl.bridge;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.mojang.datafixers.util.Either;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import net.minecraft.SharedConstants;
import net.minecraft.commands.arguments.blocks.BlockStateParser;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.commands.FillBiomeCommand;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.Property;
import net.minecraft.world.level.chunk.LevelChunk;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.neoforged.fml.ModList;

import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Optional;

/** World reads and biome writes for the bridge. Every method here runs on the server thread. */
final class BridgeWorld {
    private BridgeWorld() {}

    static ServerLevel level(MinecraftServer server, String dim) {
        ResourceLocation id = ResourceLocation.tryParse(dim == null ? "minecraft:overworld" : dim);
        if (id == null) throw new Bridge.BadRequest("bad dimension id: " + dim);
        ServerLevel level = server.getLevel(ResourceKey.create(Registries.DIMENSION, id));
        if (level == null) throw new Bridge.BadRequest("unknown dimension: " + dim);
        return level;
    }

    /** Blocks with their properties, biomes, dimensions and mods: what every build is validated against. */
    static JsonObject registry(MinecraftServer server) {
        JsonObject out = new JsonObject();
        out.addProperty("data_version", SharedConstants.getCurrentVersion().getDataVersion().getVersion());
        out.addProperty("minecraft", SharedConstants.getCurrentVersion().getName());
        JsonObject mods = new JsonObject();
        ModList.get().getMods().forEach(m -> mods.addProperty(m.getModId(), m.getVersion().toString()));
        out.add("mods", mods);
        JsonObject blocks = new JsonObject();
        for (Block block : BuiltInRegistries.BLOCK) {
            JsonObject b = new JsonObject();
            JsonObject props = new JsonObject();
            for (Property<?> p : block.getStateDefinition().getProperties()) {
                JsonArray values = new JsonArray();
                for (Object v : p.getPossibleValues()) values.add(name(p, v));
                props.add(p.getName(), values);
            }
            if (!props.isEmpty()) b.add("props", props);
            b.addProperty("default", BlockStateParser.serialize(block.defaultBlockState()));
            if (block.defaultBlockState().hasBlockEntity()) b.addProperty("block_entity", true);
            if (block.defaultBlockState().isAir()) b.addProperty("air", true);
            blocks.add(BuiltInRegistries.BLOCK.getKey(block).toString(), b);
        }
        out.add("blocks", blocks);
        JsonArray biomes = new JsonArray();
        server.registryAccess().registryOrThrow(Registries.BIOME).keySet().stream().map(ResourceLocation::toString).sorted()
                .forEach(biomes::add);
        out.add("biomes", biomes);
        JsonObject dims = new JsonObject();
        for (ServerLevel l : server.getAllLevels()) {
            JsonObject d = new JsonObject();
            d.addProperty("min_y", l.getMinBuildHeight());
            d.addProperty("height", l.getHeight());
            d.addProperty("sea_level", l.getSeaLevel());
            dims.add(l.dimension().location().toString(), d);
        }
        out.add("dimensions", dims);
        return out;
    }

    @SuppressWarnings({"unchecked", "rawtypes"})
    private static String name(Property p, Object v) {
        return p.getName((Comparable) v);
    }

    private static LevelChunk chunk(ServerLevel level, int cx, int cz, boolean load) {
        if (load) return level.getChunk(cx, cz);
        return level.getChunkSource().getChunkNow(cx, cz);
    }

    /** Blocks of a box as palette + run-length data (x fastest, then z, then y), the job format. */
    static JsonObject readBlocks(ServerLevel level, BoundingBox box, boolean load, boolean withNbt) {
        int w = box.getXSpan(), h = box.getYSpan(), l = box.getZSpan();
        Map<BlockState, Integer> index = new LinkedHashMap<>();
        JsonArray palette = new JsonArray();
        Rle rle = new Rle();
        JsonArray entities = new JsonArray();
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        int unloaded = 0;
        for (int y = 0; y < h; y++) {
            for (int z = 0; z < l; z++) {
                for (int x = 0; x < w; x++) {
                    pos.set(box.minX() + x, box.minY() + y, box.minZ() + z);
                    LevelChunk c = chunk(level, pos.getX() >> 4, pos.getZ() >> 4, load);
                    if (c == null) {
                        rle.add(-1);
                        unloaded++;
                        continue;
                    }
                    BlockState state = c.getBlockState(pos);
                    Integer i = index.get(state);
                    if (i == null) {
                        i = index.size();
                        index.put(state, i);
                        palette.add(BlockStateParser.serialize(state));
                    }
                    rle.add(i);
                    if (state.hasBlockEntity()) {
                        BlockEntity be = c.getBlockEntity(pos);
                        if (be != null) {
                            JsonObject e = new JsonObject();
                            e.add("pos", Bridge.arr(x, y, z));
                            e.addProperty("id", String.valueOf(BuiltInRegistries.BLOCK_ENTITY_TYPE.getKey(be.getType())));
                            if (withNbt) e.addProperty("snbt", be.saveWithFullMetadata(level.registryAccess()).toString());
                            entities.add(e);
                        }
                    }
                }
            }
        }
        JsonObject out = new JsonObject();
        out.addProperty("dim", level.dimension().location().toString());
        out.add("origin", Bridge.arr(box.minX(), box.minY(), box.minZ()));
        out.add("size", Bridge.arr(w, h, l));
        out.add("palette", palette);
        out.add("rle", rle.json());
        out.add("block_entities", entities);
        if (unloaded > 0) out.addProperty("unloaded_cells", unloaded);
        return out;
    }

    /** Surface heights (WORLD_SURFACE: y of the highest non-air block), surface blocks and surface biomes per column. */
    static JsonObject heightmap(ServerLevel level, int x1, int z1, int x2, int z2, boolean load) {
        int w = x2 - x1 + 1, l = z2 - z1 + 1;
        JsonArray heights = new JsonArray();
        Map<String, Integer> blockIdx = new LinkedHashMap<>();
        Map<String, Integer> biomeIdx = new LinkedHashMap<>();
        Rle blocks = new Rle();
        Rle biomes = new Rle();
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        for (int z = 0; z < l; z++) {
            for (int x = 0; x < w; x++) {
                int wx = x1 + x, wz = z1 + z;
                LevelChunk c = chunk(level, wx >> 4, wz >> 4, load);
                if (c == null) {
                    heights.add((Number) null);
                    blocks.add(-1);
                    biomes.add(-1);
                    continue;
                }
                int y = c.getHeight(Heightmap.Types.WORLD_SURFACE, wx & 15, wz & 15);
                heights.add(y);
                pos.set(wx, y, wz);
                String block = BuiltInRegistries.BLOCK.getKey(c.getBlockState(pos).getBlock()).toString();
                blocks.add(blockIdx.computeIfAbsent(block, k -> blockIdx.size()));
                String biome = biomeName(level.getBiome(pos));
                biomes.add(biomeIdx.computeIfAbsent(biome, k -> biomeIdx.size()));
            }
        }
        JsonObject out = new JsonObject();
        out.addProperty("dim", level.dimension().location().toString());
        out.add("from", Bridge.arr(x1, z1));
        out.add("size", Bridge.arr(w, l));
        out.addProperty("order", "x fastest, then z");
        out.add("heights", heights);
        out.add("block_palette", Bridge.strings(blockIdx.keySet()));
        out.add("blocks_rle", blocks.json());
        out.add("biome_palette", Bridge.strings(biomeIdx.keySet()));
        out.add("biomes_rle", biomes.json());
        return out;
    }

    /** Counts of blocks and biomes in a box, for context that fits in a few hundred tokens. */
    static JsonObject summary(ServerLevel level, BoundingBox box, boolean load) {
        Map<String, Integer> blocks = new HashMap<>();
        Map<String, Integer> biomes = new HashMap<>();
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        int unloaded = 0, air = 0;
        for (int x = box.minX(); x <= box.maxX(); x++) {
            for (int z = box.minZ(); z <= box.maxZ(); z++) {
                LevelChunk c = chunk(level, x >> 4, z >> 4, load);
                if (c == null) {
                    unloaded += box.getYSpan();
                    continue;
                }
                for (int y = box.minY(); y <= box.maxY(); y++) {
                    pos.set(x, y, z);
                    BlockState s = c.getBlockState(pos);
                    if (s.isAir()) air++;
                    else blocks.merge(BuiltInRegistries.BLOCK.getKey(s.getBlock()).toString(), 1, Integer::sum);
                    if ((x & 3) == 0 && (y & 3) == 0 && (z & 3) == 0) biomes.merge(biomeName(level.getBiome(pos)), 1, Integer::sum);
                }
            }
        }
        JsonObject out = new JsonObject();
        out.addProperty("dim", level.dimension().location().toString());
        out.add("from", Bridge.arr(box.minX(), box.minY(), box.minZ()));
        out.add("to", Bridge.arr(box.maxX(), box.maxY(), box.maxZ()));
        out.addProperty("air", air);
        if (unloaded > 0) out.addProperty("unloaded_cells", unloaded);
        out.add("blocks", top(blocks, 64));
        out.add("biomes_sampled_4x4x4", top(biomes, 64));
        return out;
    }

    private static JsonObject top(Map<String, Integer> counts, int n) {
        JsonObject o = new JsonObject();
        counts.entrySet().stream().sorted(Map.Entry.<String, Integer>comparingByValue().reversed()).limit(n)
                .forEach(e -> o.addProperty(e.getKey(), e.getValue()));
        return o;
    }

    private static String biomeName(Holder<Biome> holder) {
        return holder.unwrapKey().map(k -> k.location().toString()).orElse("?");
    }

    /** Sets the biome of a box through vanilla's fillbiome logic, chunk column by column (under its volume limit). */
    static JsonObject fillBiome(ServerLevel level, BoundingBox box, String biomeId, boolean dryRun) {
        ResourceLocation id = ResourceLocation.tryParse(biomeId);
        Optional<Holder.Reference<Biome>> biome = id == null ? Optional.empty()
                : level.registryAccess().registryOrThrow(Registries.BIOME).getHolder(ResourceKey.create(Registries.BIOME, id));
        if (biome.isEmpty()) throw new Bridge.BadRequest("unknown biome: " + biomeId);
        JsonObject out = new JsonObject();
        out.addProperty("biome", biomeId);
        int chunks = 0;
        long cells = 0;
        for (int cx = box.minX() >> 4; cx <= box.maxX() >> 4; cx++) {
            for (int cz = box.minZ() >> 4; cz <= box.maxZ() >> 4; cz++) {
                chunks++;
                if (dryRun) continue;
                level.getChunk(cx, cz); // fillbiome needs the chunk loaded
                int ax = Math.max(box.minX(), cx << 4), bx = Math.min(box.maxX(), (cx << 4) + 15);
                int az = Math.max(box.minZ(), cz << 4), bz = Math.min(box.maxZ(), (cz << 4) + 15);
                for (int y = box.minY(); y <= box.maxY(); y += 128) {
                    int by = Math.min(box.maxY(), y + 127);
                    Either<Integer, CommandSyntaxException> r = FillBiomeCommand.fill(level, new BlockPos(ax, y, az),
                            new BlockPos(bx, by, bz), biome.get());
                    if (r.right().isPresent()) throw new Bridge.BadRequest("fillbiome: " + r.right().get().getMessage());
                    cells += r.left().orElse(0);
                }
            }
        }
        out.addProperty("chunks", chunks);
        out.addProperty("biome_cells_changed", cells);
        out.addProperty("dry_run", dryRun);
        return out;
    }

    /** Parses a block state in command syntax ("ns:block[prop=v]{nbt}"); a bad id or property is a 400. */
    static BlockStateParser.BlockResult parseState(Level level, String state) {
        try {
            return BlockStateParser.parseForBlock(level.holderLookup(Registries.BLOCK), state, true);
        } catch (CommandSyntaxException e) {
            throw new Bridge.BadRequest("bad block state '" + state + "': " + e.getMessage());
        }
    }

    /** Run-length list of palette indexes: [[count, index], ...]. */
    static final class Rle {
        private final JsonArray runs = new JsonArray();
        private int current = Integer.MIN_VALUE;
        private int count = 0;

        void add(int value) {
            if (value == current) {
                count++;
                return;
            }
            flush();
            current = value;
            count = 1;
        }

        private void flush() {
            if (count > 0) runs.add(Bridge.arr(count, current));
        }

        JsonArray json() {
            flush();
            count = 0;
            current = Integer.MIN_VALUE;
            return runs;
        }

        static int[] decode(JsonArray runs, int cells) {
            int[] out = new int[cells];
            int at = 0;
            for (var e : runs) {
                JsonArray r = e.getAsJsonArray();
                int n = r.get(0).getAsInt(), v = r.get(1).getAsInt();
                if (n < 0 || at + n > cells) throw new Bridge.BadRequest("rle covers more cells than size (" + cells + ")");
                java.util.Arrays.fill(out, at, at + n, v);
                at += n;
            }
            if (at != cells) throw new Bridge.BadRequest("rle covers " + at + " cells, size has " + cells);
            return out;
        }
    }
}
