package com.yasuke.ttl;

import com.yasuke.ttl.bot.TestBots;
import com.yasuke.ttl.build.Capture;
import com.yasuke.ttl.rebirth.Rebirth;
import com.yasuke.ttl.rebirth.RebirthOffersPayload;
import com.yasuke.ttl.report.BugReports;
import com.yasuke.ttl.ui.ChoiceMenu;
import com.yasuke.ttl.ui.Quiet;
import com.yasuke.ttl.world.CanonMap;
import com.yasuke.ttl.world.CanonMapCommand;
import com.yasuke.ttl.world.DesignFeatures;
import com.yasuke.ttl.world.DesignWorld;
import com.yasuke.ttl.world.SiteCheckCommand;
import com.yasuke.ttl.world.MortalWorldgen;
import com.yasuke.ttl.world.WorldReset;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.common.NeoForge;

@Mod(TtlPortals.MOD_ID)
public final class TtlPortals {
    public static final String MOD_ID = "ttl";

    public TtlPortals(IEventBus modBus) {
        modBus.addListener(RebirthOffersPayload::register);
        CanonMap.TYPES.register(modBus);
        DesignFeatures.FEATURES.register(modBus);
        MortalWorldgen.BIOME_SOURCES.register(modBus);
        NeoForge.EVENT_BUS.addListener(Rebirth::registerCommands);
        NeoForge.EVENT_BUS.addListener(BugReports::registerCommands);
        NeoForge.EVENT_BUS.addListener(Capture::registerCommands);
        NeoForge.EVENT_BUS.addListener(TestBots::registerCommands);
        NeoForge.EVENT_BUS.addListener(TestBots::onChangedDimension);
        NeoForge.EVENT_BUS.addListener(TestBots::onServerTick);
        NeoForge.EVENT_BUS.addListener(Quiet::registerCommands);
        NeoForge.EVENT_BUS.addListener(ChoiceMenu::registerCommands);
        NeoForge.EVENT_BUS.addListener(WorldReset::onServerAboutToStart);
        NeoForge.EVENT_BUS.addListener(WorldReset::onServerStarted);
        NeoForge.EVENT_BUS.addListener(EventPriority.HIGH, DesignWorld::onServerAboutToStart); // before CanonMap reloads its grid
        NeoForge.EVENT_BUS.addListener(CanonMap::onServerAboutToStart);
        NeoForge.EVENT_BUS.addListener(SiteCheckCommand::registerCommands);
        NeoForge.EVENT_BUS.addListener(CanonMapCommand::registerCommands);
    }
}
