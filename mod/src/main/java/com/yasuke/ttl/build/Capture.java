package com.yasuke.ttl.build;

import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import com.mojang.logging.LogUtils;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.arguments.coordinates.BlockPosArgument;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Vec3i;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.NbtIo;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import org.slf4j.Logger;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

/**
 * {@code /ttlcapture <name> <from> <to>}: save any region of the world (built by hand, with WorldEdit or
 * placed from a blueprint) as a vanilla structure file in {@code ttl-captures/<name>.nbt}, without a player
 * and without the 48-block structure-block limit. tools/capture.py pulls it into blueprints/ so the build
 * becomes code again. Use with `execute in <dimension>` for other dimensions.
 */
public final class Capture {
    private static final Logger LOGGER = LogUtils.getLogger();
    private static final int MAX_SIDE = 256;

    private Capture() {}

    public static void registerCommands(RegisterCommandsEvent event) {
        event.getDispatcher().register(Commands.literal("ttlcapture")
                .requires(source -> source.hasPermission(2))
                .then(Commands.argument("name", StringArgumentType.word())
                        .then(Commands.argument("from", BlockPosArgument.blockPos())
                                .then(Commands.argument("to", BlockPosArgument.blockPos()).executes(Capture::capture)))));
    }

    private static int capture(CommandContext<CommandSourceStack> ctx) throws CommandSyntaxException {
        CommandSourceStack source = ctx.getSource();
        ServerLevel level = source.getLevel();
        String name = StringArgumentType.getString(ctx, "name");
        BlockPos a = BlockPosArgument.getLoadedBlockPos(ctx, "from");
        BlockPos b = BlockPosArgument.getLoadedBlockPos(ctx, "to");
        BlockPos min = new BlockPos(Math.min(a.getX(), b.getX()), Math.min(a.getY(), b.getY()), Math.min(a.getZ(), b.getZ()));
        Vec3i size = new Vec3i(Math.abs(a.getX() - b.getX()) + 1, Math.abs(a.getY() - b.getY()) + 1, Math.abs(a.getZ() - b.getZ()) + 1);
        if (size.getX() > MAX_SIDE || size.getY() > MAX_SIDE || size.getZ() > MAX_SIDE) {
            source.sendFailure(Component.literal("ttlcapture: region larger than " + MAX_SIDE + " blocks on a side"));
            return 0;
        }
        StructureTemplate template = new StructureTemplate();
        // Air is kept (only structure voids are skipped), so placing the capture reproduces the region exactly.
        template.fillFromWorld(level, min, size, false, Blocks.STRUCTURE_VOID);
        CompoundTag tag = template.save(new CompoundTag());
        Path file = source.getServer().getServerDirectory().resolve("ttl-captures").resolve(name + ".nbt");
        try {
            Files.createDirectories(file.getParent());
            NbtIo.writeCompressed(tag, file);
        } catch (IOException e) {
            LOGGER.error("[ttl] capture {} failed", name, e);
            source.sendFailure(Component.literal("ttlcapture: could not write " + file.getFileName()));
            return 0;
        }
        LOGGER.info("[ttl] captured {} {}x{}x{} at {} in {}", name, size.getX(), size.getY(), size.getZ(), min.toShortString(), level.dimension().location());
        source.sendSuccess(() -> Component.literal("Captured " + name + " (" + size.getX() + "x" + size.getY() + "x" + size.getZ() + ")"), true);
        return 1;
    }
}
