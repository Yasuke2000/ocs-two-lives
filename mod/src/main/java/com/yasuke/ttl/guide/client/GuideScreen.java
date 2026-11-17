package com.yasuke.ttl.guide.client;

import com.yasuke.ttl.guide.GuidePayload;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.network.chat.Style;
import net.minecraft.network.chat.TextColor;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.util.Mth;

import java.util.ArrayList;
import java.util.List;

/**
 * The guide pop-up, in the look of the Great Sage addon's windows (its Voice of the World colours): a dark
 * translucent navy panel with a thin cyan border, a soft glow and bright corner marks, the page title in gold,
 * light body text. Pages turn with Previous/Next (or the arrow keys); long pages scroll with the mouse wheel.
 * Body lines, as written in design/data/guide.toml:
 * "# text" a cyan heading · "- text" a bullet · "" a gap · `text` a command (mint) · *text* emphasis (gold).
 * Everything is laid out in GUI pixels, so it follows the GUI scale.
 */
public final class GuideScreen extends Screen {
    static final int CYAN = 0xFF6FD6FF;
    static final int ICE = 0xFFBFEFFF;
    static final int TEXT = 0xFFEAF6FF;
    static final int GOLD = 0xFFFFD27A;
    static final int MINT = 0xFF8FE9C0;
    static final int MUTED = 0xFF9FC2B2;
    private static final int LINE = 10;
    private static final int GAP = 5;

    private final GuidePayload guide;
    private int page;
    private int left;
    private int top;
    private int panelW;
    private int panelH;
    private int scroll;
    private int contentH;
    private final List<Row> rows = new ArrayList<>();
    private Button prev;
    private Button next;

    private record Row(FormattedCharSequence text, int indent, boolean bullet, int height) {}

    public GuideScreen(GuidePayload guide) {
        super(Component.literal(guide.pages().isEmpty() ? "Guide" : guide.pages().get(0).title()));
        this.guide = guide;
    }

    @Override
    protected void init() {
        panelW = Math.min(340, width - 24);
        panelH = Math.min(236, height - 24);
        left = (width - panelW) / 2;
        top = (height - panelH) / 2;
        int y = top + panelH - 26;
        int side = Math.min(84, (panelW - 40) / 3);
        prev = addRenderableWidget(new GuideButton(left + 10, y, side, 18, Component.literal("< Previous"), b -> turn(-1)));
        addRenderableWidget(new GuideButton(left + (panelW - side) / 2, y, side, 18, Component.literal("Close"), b -> onClose()));
        next = addRenderableWidget(new GuideButton(left + panelW - 10 - side, y, side, 18, Component.literal("Next >"), b -> turn(1)));
        layout();
    }

    private void turn(int delta) {
        int target = Mth.clamp(page + delta, 0, guide.pages().size() - 1);
        if (target == page) return;
        page = target;
        scroll = 0;
        layout();
    }

    private int bodyTop() {
        return top + 42;
    }

    private int bodyBottom() {
        return top + panelH - (guide.pages().size() > 1 ? 44 : 36);
    }

    private int bodyWidth() {
        return panelW - 30;
    }

    private void layout() {
        rows.clear();
        prev.active = page > 0;
        next.active = page < guide.pages().size() - 1;
        if (guide.pages().isEmpty()) return;
        int width = bodyWidth();
        for (String raw : guide.pages().get(page).lines()) {
            String line = raw.stripTrailing();
            if (line.isBlank()) {
                rows.add(new Row(FormattedCharSequence.EMPTY, 0, false, GAP));
            } else if (line.startsWith("# ")) {
                Component heading = Component.literal(line.substring(2).trim()).withStyle(Style.EMPTY.withColor(TextColor.fromRgb(CYAN)).withBold(true));
                for (FormattedCharSequence seq : font.split(heading, width)) rows.add(new Row(seq, 0, false, LINE + 1));
            } else if (line.startsWith("- ")) {
                List<FormattedCharSequence> wrapped = font.split(styled(line.substring(2).trim()), width - 10);
                for (int i = 0; i < wrapped.size(); i++) rows.add(new Row(wrapped.get(i), 10, i == 0, LINE));
            } else {
                for (FormattedCharSequence seq : font.split(styled(line.trim()), width)) rows.add(new Row(seq, 0, false, LINE));
            }
        }
        contentH = rows.stream().mapToInt(Row::height).sum();
        scroll = Mth.clamp(scroll, 0, maxScroll());
    }

    private int maxScroll() {
        return Math.max(0, contentH - (bodyBottom() - bodyTop()));
    }

    /** `command` in mint, *emphasis* in gold, the rest in the light body colour. */
    private static Component styled(String text) {
        MutableComponent out = Component.empty();
        StringBuilder part = new StringBuilder();
        int color = TEXT;
        for (int i = 0; i < text.length(); i++) {
            char c = text.charAt(i);
            int toggled = c == '`' ? MINT : c == '*' ? GOLD : 0;
            if (toggled != 0 && (color == TEXT || color == toggled)) {
                if (!part.isEmpty()) out.append(Component.literal(part.toString()).withColor(color));
                part.setLength(0);
                color = color == TEXT ? toggled : TEXT;
            } else {
                part.append(c);
            }
        }
        if (!part.isEmpty()) out.append(Component.literal(part.toString()).withColor(color));
        return out;
    }

    @Override
    public void renderBackground(GuiGraphics g, int mouseX, int mouseY, float partialTick) {
        super.renderBackground(g, mouseX, mouseY, partialTick);
        int x1 = left;
        int y1 = top;
        int x2 = left + panelW;
        int y2 = top + panelH;
        int[] glow = {0x34, 0x22, 0x14, 0x0A, 0x05};
        for (int i = 0; i < glow.length; i++) frame(g, x1 - 1 - i, y1 - 1 - i, x2 + 1 + i, y2 + 1 + i, glow[i] << 24 | 0x6FD6FF);
        g.fillGradient(x1, y1, x2, y2, 0xEE0C1B2E, 0xEE050B16);
        g.fillGradient(x1 + 1, y1 + 1, x2 - 1, y1 + 36, 0x2E6FD6FF, 0x006FD6FF);
        frame(g, x1, y1, x2, y2, 0xC06FD6FF);
        corners(g, x1, y1, x2, y2);
        divider(g, x1 + 12, x2 - 12, y1 + 34, true);
        divider(g, x1 + 12, x2 - 12, y2 - 33, false);
    }

    @Override
    public void render(GuiGraphics g, int mouseX, int mouseY, float partialTick) {
        super.render(g, mouseX, mouseY, partialTick);
        int pages = guide.pages().size();
        g.drawString(font, "GUIDE", left + 10, top + 7, CYAN, false);
        if (pages > 1) {
            String counter = (page + 1) + " / " + pages;
            g.drawString(font, counter, left + panelW - 10 - font.width(counter), top + 7, ICE, false);
        }
        String title = pages == 0 ? "" : guide.pages().get(page).title();
        title = font.plainSubstrByWidth(title, panelW - 24);
        g.drawCenteredString(font, Component.literal(title), left + panelW / 2, top + 20, GOLD);

        int bodyX = left + 14;
        int bodyTop = bodyTop();
        int bodyBottom = bodyBottom();
        g.enableScissor(left + 2, bodyTop, left + panelW - 2, bodyBottom);
        int y = bodyTop - scroll;
        for (Row row : rows) {
            if (y + row.height() > bodyTop - LINE && y < bodyBottom) {
                if (row.bullet()) g.fill(bodyX + 2, y + 3, bodyX + 5, y + 6, CYAN);
                g.drawString(font, row.text(), bodyX + row.indent(), y, TEXT, true);
            }
            y += row.height();
        }
        g.disableScissor();

        int max = maxScroll();
        if (max > 0) {
            if (scroll > 0) g.fillGradient(left + 2, bodyTop, left + panelW - 2, bodyTop + 8, 0xC0091424, 0x00091424);
            if (scroll < max) g.fillGradient(left + 2, bodyBottom - 8, left + panelW - 2, bodyBottom, 0x00070F1C, 0xC0070F1C);
            int trackX = left + panelW - 7;
            int trackH = bodyBottom - bodyTop;
            g.fill(trackX, bodyTop, trackX + 1, bodyBottom, 0x406FD6FF);
            int thumbH = Math.max(12, trackH * trackH / (trackH + max));
            int thumbY = bodyTop + (trackH - thumbH) * scroll / max;
            g.fill(trackX - 1, thumbY, trackX + 2, thumbY + thumbH, CYAN);
        }

        if (pages > 1 && pages <= 24) {
            int dotY = top + panelH - 39;
            int start = left + panelW / 2 - (pages * 8 - 4) / 2;
            for (int i = 0; i < pages; i++) {
                int x = start + i * 8;
                if (i == page) g.fill(x - 1, dotY - 1, x + 5, dotY + 5, 0x606FD6FF);
                g.fill(x, dotY, x + 4, dotY + 4, i == page ? CYAN : 0x705A8CA0);
            }
        }
    }

    private static void frame(GuiGraphics g, int x1, int y1, int x2, int y2, int color) {
        g.fill(x1, y1, x2, y1 + 1, color);
        g.fill(x1, y2 - 1, x2, y2, color);
        g.fill(x1, y1 + 1, x1 + 1, y2 - 1, color);
        g.fill(x2 - 1, y1 + 1, x2, y2 - 1, color);
    }

    // Bright L-shaped marks on the corners, like the Sage's status window.
    private static void corners(GuiGraphics g, int x1, int y1, int x2, int y2) {
        int c = ICE;
        int l = 9;
        g.fill(x1 - 1, y1 - 1, x1 + l, y1 + 1, c);
        g.fill(x1 - 1, y1 - 1, x1 + 1, y1 + l, c);
        g.fill(x2 - l, y1 - 1, x2 + 1, y1 + 1, c);
        g.fill(x2 - 1, y1 - 1, x2 + 1, y1 + l, c);
        g.fill(x1 - 1, y2 - 1, x1 + l, y2 + 1, c);
        g.fill(x1 - 1, y2 - l, x1 + 1, y2 + 1, c);
        g.fill(x2 - l, y2 - 1, x2 + 1, y2 + 1, c);
        g.fill(x2 - 1, y2 - l, x2 + 1, y2 + 1, c);
    }

    // A thin line, brighter towards the middle; the title divider carries a small gold diamond.
    private static void divider(GuiGraphics g, int x1, int x2, int y, boolean jewel) {
        int w = x2 - x1;
        g.fill(x1, y, x2, y + 1, 0x406FD6FF);
        g.fill(x1 + w / 6, y, x2 - w / 6, y + 1, 0x806FD6FF);
        g.fill(x1 + w / 3, y, x2 - w / 3, y + 1, 0xD06FD6FF);
        if (jewel) {
            int cx = (x1 + x2) / 2;
            g.fill(cx - 1, y - 2, cx + 2, y + 3, GOLD);
            g.fill(cx - 2, y - 1, cx + 3, y + 2, GOLD);
        }
    }

    @Override
    public boolean mouseScrolled(double mouseX, double mouseY, double scrollX, double scrollY) {
        if (maxScroll() > 0) {
            scroll = Mth.clamp(scroll - (int) Math.round(scrollY * LINE * 2), 0, maxScroll());
            return true;
        }
        return super.mouseScrolled(mouseX, mouseY, scrollX, scrollY);
    }

    @Override
    public boolean keyPressed(int keyCode, int scanCode, int modifiers) {
        // GLFW: 262 right, 263 left, 264 down, 265 up, 266 page up, 267 page down.
        switch (keyCode) {
            case 262 -> { turn(1); return true; }
            case 263 -> { turn(-1); return true; }
            case 264, 267 -> { scroll = Mth.clamp(scroll + (keyCode == 264 ? LINE : bodyBottom() - bodyTop() - LINE), 0, maxScroll()); return true; }
            case 265, 266 -> { scroll = Mth.clamp(scroll - (keyCode == 265 ? LINE : bodyBottom() - bodyTop() - LINE), 0, maxScroll()); return true; }
            default -> { return super.keyPressed(keyCode, scanCode, modifiers); }
        }
    }

    @Override
    public void onClose() {
        String then = guide.then();
        super.onClose();
        Minecraft mc = Minecraft.getInstance();
        if (!then.isBlank() && mc.player != null) mc.player.connection.sendCommand(then);
    }

    @Override
    public boolean isPauseScreen() {
        return false;
    }

    private static final class GuideButton extends Button {
        GuideButton(int x, int y, int w, int h, Component message, OnPress onPress) {
            super(x, y, w, h, message, onPress, DEFAULT_NARRATION);
        }

        @Override
        protected void renderWidget(GuiGraphics g, int mouseX, int mouseY, float partialTick) {
            boolean hot = active && isHoveredOrFocused();
            int x1 = getX();
            int y1 = getY();
            int x2 = x1 + width;
            int y2 = y1 + height;
            if (hot) frame(g, x1 - 1, y1 - 1, x2 + 1, y2 + 1, 0x406FD6FF);
            g.fillGradient(x1, y1, x2, y2, !active ? 0x80101A24 : hot ? 0xE0164A62 : 0xD0102A3C, !active ? 0x80080E16 : hot ? 0xE00C2A3C : 0xD0081622);
            frame(g, x1, y1, x2, y2, !active ? 0x50406070 : hot ? ICE : 0xC04FA8C8);
            Font font = Minecraft.getInstance().font;
            g.drawCenteredString(font, getMessage(), x1 + width / 2, y1 + (height - 8) / 2, !active ? 0xFF56697A : hot ? 0xFFFFFFFF : 0xFFD8F0FF);
        }
    }
}
