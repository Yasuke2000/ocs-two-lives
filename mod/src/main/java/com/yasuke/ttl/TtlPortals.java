package com.yasuke.ttl;

import com.yasuke.ttl.bot.TestBots;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.common.NeoForge;

@Mod(TtlPortals.MOD_ID)
public final class TtlPortals {
    public static final String MOD_ID = "ttl";

    public TtlPortals() {
        NeoForge.EVENT_BUS.addListener(TestBots::registerCommands);
        NeoForge.EVENT_BUS.addListener(TestBots::onChangedDimension);
        NeoForge.EVENT_BUS.addListener(TestBots::onServerTick);
    }
}
