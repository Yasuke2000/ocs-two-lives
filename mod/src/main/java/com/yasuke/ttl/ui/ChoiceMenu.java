package com.yasuke.ttl.ui;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import com.mojang.logging.LogUtils;
import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.Style;
import net.minecraft.network.chat.TextColor;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.inventory.ClickType;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.ItemLore;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import org.slf4j.Logger;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * {@code /ttlmenu <player> <json>} opens an on-screen choice menu: a chest screen whose items are buttons.
 * Works with an unmodded client (it is a vanilla chest screen). Clicking an item closes the menu and runs
 * its command as the player; items can never be taken out.
 * JSON: {"title": "...", "rows": 3, "items": [{"slot": 10, "item": "minecraft:book", "name": "Knowledge",
 * "color": "#55FFFF", "lore": ["line", ...], "command": "ttl wish knowledge"}]}
 */
public final class ChoiceMenu extends ChestMenu {
    private static final Logger LOGGER = LogUtils.getLogger();
    private static final MenuType<?>[] TYPES = {MenuType.GENERIC_9x1, MenuType.GENERIC_9x2, MenuType.GENERIC_9x3,
            MenuType.GENERIC_9x4, MenuType.GENERIC_9x5, MenuType.GENERIC_9x6};

    private final Map<Integer, String> commands;
    private final int size;

    private ChoiceMenu(int id, Inventory inventory, SimpleContainer container, int rows, Map<Integer, String> commands) {
        super(TYPES[rows - 1], id, inventory, container, rows);
        this.commands = commands;
        this.size = rows * 9;
    }

    public static void registerCommands(RegisterCommandsEvent event) {
        event.getDispatcher().register(Commands.literal("ttlmenu")
                .requires(source -> source.hasPermission(2))
                .then(Commands.argument("player", EntityArgument.player())
                        .then(Commands.argument("json", StringArgumentType.greedyString()).executes(ChoiceMenu::open))));
    }

    private static int open(CommandContext<CommandSourceStack> ctx) throws CommandSyntaxException {
        ServerPlayer player = EntityArgument.getPlayer(ctx, "player");
        JsonObject spec;
        try {
            spec = JsonParser.parseString(StringArgumentType.getString(ctx, "json")).getAsJsonObject();
        } catch (RuntimeException e) {
            ctx.getSource().sendFailure(Component.literal("ttlmenu: bad JSON: " + e.getMessage()));
            return 0;
        }
        int rows = Math.max(1, Math.min(6, spec.has("rows") ? spec.get("rows").getAsInt() : 3));
        SimpleContainer container = new SimpleContainer(rows * 9);
        Map<Integer, String> commands = new HashMap<>();
        JsonArray items = spec.has("items") ? spec.getAsJsonArray("items") : new JsonArray();
        for (JsonElement element : items) {
            JsonObject entry = element.getAsJsonObject();
            int slot = entry.get("slot").getAsInt();
            if (slot < 0 || slot >= rows * 9) continue;
            container.setItem(slot, icon(entry));
            if (entry.has("command")) commands.put(slot, entry.get("command").getAsString());
        }
        Component title = Component.literal(spec.has("title") ? spec.get("title").getAsString() : "Choose");
        player.openMenu(new SimpleMenuProvider((id, inventory, p) -> new ChoiceMenu(id, inventory, container, rows, commands), title));
        return 1;
    }

    private static ItemStack icon(JsonObject entry) {
        ItemStack stack = new ItemStack(BuiltInRegistries.ITEM.get(ResourceLocation.parse(entry.get("item").getAsString())));
        Style style = Style.EMPTY.withItalic(false);
        if (entry.has("color")) {
            TextColor color = TextColor.parseColor(entry.get("color").getAsString()).result().orElse(null);
            if (color != null) style = style.withColor(color);
        }
        if (entry.has("name")) stack.set(DataComponents.CUSTOM_NAME, Component.literal(entry.get("name").getAsString()).withStyle(style));
        if (entry.has("lore")) {
            List<Component> lines = new ArrayList<>();
            for (JsonElement line : entry.getAsJsonArray("lore")) {
                lines.add(Component.literal(line.getAsString()).withStyle(Style.EMPTY.withItalic(false).withColor(ChatFormatting.GRAY)));
            }
            stack.set(DataComponents.LORE, new ItemLore(lines));
        }
        if (entry.has("count")) stack.setCount(Math.max(1, Math.min(64, entry.get("count").getAsInt())));
        return stack;
    }

    @Override
    public void clicked(int slotId, int button, ClickType clickType, Player player) {
        // Never let the vanilla logic move items: the screen is a set of buttons, not storage.
        String command = slotId >= 0 && slotId < size ? commands.get(slotId) : null;
        if (command == null || !(player instanceof ServerPlayer serverPlayer)) {
            sendAllDataToRemote();
            return;
        }
        serverPlayer.closeContainer();
        LOGGER.info("[ttl] menu: {} chose /{}", serverPlayer.getGameProfile().getName(), command);
        serverPlayer.getServer().getCommands().performPrefixedCommand(serverPlayer.createCommandSourceStack(), command);
    }

    @Override
    public ItemStack quickMoveStack(Player player, int index) {
        return ItemStack.EMPTY;
    }

    @Override
    public boolean stillValid(Player player) {
        return true;
    }
}
