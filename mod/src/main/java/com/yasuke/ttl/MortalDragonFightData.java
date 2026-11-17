package com.yasuke.ttl;

import com.mojang.logging.LogUtils;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.NbtOps;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.dimension.end.EndDragonFight;
import net.minecraft.world.level.saveddata.SavedData;
import org.slf4j.Logger;

/**
 * Dragon fight state of the Mortal End. Vanilla keeps one dragon fight in level.dat, shared by
 * whichever End saves last, so the Mortal End keeps its own copy in its dimension data folder.
 */
public final class MortalDragonFightData extends SavedData {
    private static final Logger LOGGER = LogUtils.getLogger();
    private static final String ID = "ttl_mortal_dragon_fight";
    private static final String KEY = "DragonFight";

    private EndDragonFight.Data data;

    private MortalDragonFightData(EndDragonFight.Data data) {
        this.data = data;
    }

    public EndDragonFight.Data data() {
        return data;
    }

    public void update(EndDragonFight.Data data) {
        this.data = data;
        setDirty();
    }

    @Override
    public CompoundTag save(CompoundTag tag, HolderLookup.Provider registries) {
        EndDragonFight.Data.CODEC.encodeStart(NbtOps.INSTANCE, data)
                .resultOrPartial(LOGGER::error)
                .ifPresent(encoded -> tag.put(KEY, encoded));
        return tag;
    }

    private static MortalDragonFightData load(CompoundTag tag, HolderLookup.Provider registries) {
        EndDragonFight.Data data = EndDragonFight.Data.DEFAULT;
        if (tag.contains(KEY)) {
            data = EndDragonFight.Data.CODEC.parse(NbtOps.INSTANCE, tag.get(KEY))
                    .resultOrPartial(LOGGER::error)
                    .orElse(EndDragonFight.Data.DEFAULT);
        }
        return new MortalDragonFightData(data);
    }

    public static MortalDragonFightData get(ServerLevel level) {
        return level.getDataStorage().computeIfAbsent(
                new SavedData.Factory<>(() -> new MortalDragonFightData(EndDragonFight.Data.DEFAULT), MortalDragonFightData::load, null),
                ID);
    }
}
