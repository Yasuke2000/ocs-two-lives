package com.yasuke.ttl.world;

import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.context.CommandContext;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.Holder;
import net.minecraft.core.QuartPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.chunk.LevelChunk;
import net.minecraft.world.level.levelgen.DensityFunction;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.NoiseRouter;
import net.minecraft.world.level.levelgen.RandomState;
import net.neoforged.neoforge.event.RegisterCommandsEvent;

/**
 * {@code /ttlmap <x> <z>}: what the canon map says about an overworld block column, for checks over RCON. Inside
 * Lerfing's imported area the chunks come from his map, so it reports the stored biome of the loaded chunk (and the
 * grid letter, which the continent rule reads) instead of what the generator would make.
 */
public final class CanonMapCommand {
    private CanonMapCommand() {}

    public static void registerCommands(RegisterCommandsEvent event) {
        event.getDispatcher().register(Commands.literal("ttlmap")
                .requires(source -> source.hasPermission(2))
                .then(Commands.argument("x", IntegerArgumentType.integer())
                        .then(Commands.argument("z", IntegerArgumentType.integer()).executes(CanonMapCommand::run))));
    }

    private static int run(CommandContext<CommandSourceStack> ctx) {
        int x = IntegerArgumentType.getInteger(ctx, "x"), z = IntegerArgumentType.getInteger(ctx, "z");
        ServerLevel level = ctx.getSource().getServer().overworld();
        RandomState random = level.getChunkSource().randomState();
        NoiseRouter router = random.router();
        CanonGrid grid = CanonMap.grid();
        StringBuilder out = new StringBuilder("[ttl] canon map at ").append(x).append(' ').append(z).append(": ");
        CanonRasters design = DesignWorld.rasters();
        String designLine = design == null ? "" : "\n  " + design.describe(x, z);
        if (grid != null && grid.imported(x, z)) {
            char c = grid.charAt(x, z), owner = grid.ownerCell(x, z);
            out.append('\'').append(c).append("' ").append(grid.regionName(c))
                    .append(owner != 0 && owner != c ? " (owner " + grid.regionName(owner) + ")" : owner == 0 ? " (not on the continent)" : "");
            LevelChunk chunk = level.getChunkSource().getChunkNow(x >> 4, z >> 4);
            if (chunk == null) {
                out.append("\n  imported, not loaded: Lerfing's stored chunk (the generator is never asked here); load it to read its biome");
            } else {
                int surface = chunk.getHeight(Heightmap.Types.WORLD_SURFACE, x & 15, z & 15) + 1;
                String biome = chunk.getNoiseBiome(QuartPos.fromBlock(x), QuartPos.fromBlock(surface), QuartPos.fromBlock(z)).unwrapKey()
                        .map(key -> key.location().toString()).orElse("?");
                out.append("\n  imported chunk: stored biome ").append(biome).append(" at surface y").append(surface);
            }
            out.append(designLine);
            String text = out.toString();
            ctx.getSource().sendSuccess(() -> Component.literal(text), false);
            return 1;
        }
        if (grid == null) {
            out.append("NOT LOADED (see the server log), vanilla terrain");
        } else {
            char c = grid.charAt(x, z);
            out.append('\'').append(c).append("' ").append(grid.regionName(c))
                    .append(String.format(", canon weight %.2f", grid.canonWeight(x, z)));
            String sites = grid.sites().describe(x, z);
            if (sites != null) out.append("\n  ").append(sites);
        }
        out.append(designLine);
        DensityFunction.SinglePointContext point = new DensityFunction.SinglePointContext(x, 0, z);
        out.append(channel("continents", router.continents(), point))
                .append(channel("erosion", router.erosion(), point))
                .append(channel("temperature", router.temperature(), point))
                .append(channel("vegetation", router.vegetation(), point))
                .append(channel("ridges", router.ridges(), point));
        double cont = router.continents().compute(point);
        out.append("\n  band: ").append(cont < -1.05 ? "mushroom" : cont < -0.455 ? "deep ocean" : cont < -0.19 ? "ocean" : cont < -0.11 ? "coast" : "inland");
        ChunkGenerator generator = level.getChunkSource().getGenerator();
        int surface = generator.getBaseHeight(x, z, Heightmap.Types.WORLD_SURFACE_WG, level, random);
        int qx = QuartPos.fromBlock(x), qy = QuartPos.fromBlock(surface), qz = QuartPos.fromBlock(z);
        if (generator.getBiomeSource() instanceof CanonBiomes canon) {
            StringBuilder why = new StringBuilder();
            Holder<Biome> biome = canon.select(qx, qy, qz, random.sampler(), why);
            out.append("\n  canon biome at surface y").append(surface).append(": ")
                    .append(biome.unwrapKey().map(key -> key.location().toString()).orElse("?")).append(" (").append(why).append(')');
        } else {
            generator.getBiomeSource().getNoiseBiome(qx, qy, qz, random.sampler()).unwrapKey()
                    .ifPresent(key -> out.append(", biome at surface y").append(surface).append(": ").append(key.location())
                            .append(" (biome source is not ttl:canon_biomes)"));
        }
        String text = out.toString();
        ctx.getSource().sendSuccess(() -> Component.literal(text), false);
        return 1;
    }

    private static String channel(String name, DensityFunction function, DensityFunction.SinglePointContext point) {
        List<CanonMap> found = new ArrayList<>();
        function.mapAll(f -> {
            if (f instanceof CanonMap map) found.add(map);
            return f;
        });
        String value = String.format("\n  %s %.3f", name, function.compute(point));
        return found.isEmpty() ? value + " (no ttl:canon_map in the router!)" : value + String.format(" (vanilla %.3f)", found.get(0).outside().compute(point));
    }
}
