package com.yasuke.ttl;

import com.yasuke.ttl.bot.TestBots;
import com.yasuke.ttl.rebirth.Rebirth;
import com.yasuke.ttl.rebirth.RebirthOffersPayload;
import com.yasuke.ttl.report.BugReports;
import com.yasuke.ttl.ui.ChoiceMenu;
import com.yasuke.ttl.ui.Quiet;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.common.NeoForge;

@Mod(TtlPortals.MOD_ID)
public final class TtlPortals {
    public static final String MOD_ID = "ttl";

    public TtlPortals(IEventBus modBus) {
        modBus.addListener(RebirthOffersPayload::register);
        NeoForge.EVENT_BUS.addListener(Rebirth::registerCommands);
        NeoForge.EVENT_BUS.addListener(BugReports::registerCommands);
        NeoForge.EVENT_BUS.addListener(TestBots::registerCommands);
        NeoForge.EVENT_BUS.addListener(TestBots::onChangedDimension);
        NeoForge.EVENT_BUS.addListener(TestBots::onServerTick);
        NeoForge.EVENT_BUS.addListener(Quiet::registerCommands);
        NeoForge.EVENT_BUS.addListener(ChoiceMenu::registerCommands);
    }
}
