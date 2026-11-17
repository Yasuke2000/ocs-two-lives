package com.yasuke.ttl.ui;

import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.neoforged.neoforge.event.RegisterCommandsEvent;

/**
 * {@code /quietly <command>} runs a command without any chat message reaching players. Scripts use it
 * for Tensura/vanilla commands that announce themselves to the target ("X has been granted",
 * "Your game mode has been updated"); ServerPlayerMixin drops system messages while ACTIVE is set.
 */
public final class Quiet {
    static boolean active;

    private Quiet() {}

    public static boolean isActive() {
        return active;
    }

    public static void registerCommands(RegisterCommandsEvent event) {
        event.getDispatcher().register(Commands.literal("quietly")
                .requires(source -> source.hasPermission(2))
                .then(Commands.argument("command", StringArgumentType.greedyString()).executes(Quiet::run)));
    }

    private static int run(CommandContext<CommandSourceStack> ctx) {
        CommandSourceStack source = ctx.getSource();
        boolean outer = active;
        active = true;
        try {
            source.getServer().getCommands().performPrefixedCommand(source.withSuppressedOutput(), StringArgumentType.getString(ctx, "command"));
        } finally {
            active = outer;
        }
        return 1;
    }
}
