package com.yasuke.ttl.mixin;

import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import com.llamalad7.mixinextras.injector.wrapoperation.WrapOperation;
import com.yasuke.ttl.world.DesignWorld;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.structure.StructureStart;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;

/**
 * The own world's structure exclusion mask (design/architecture/own-world.md, owner answer Q4: every vanilla and
 * Tensura structure may generate on the continent, except where it would collide with the design): a structure start
 * whose bounding box touches a site box (plus margin), a road corridor or the Dwargon cavity is dropped as if it were
 * invalid, so the next entry of its structure set may try. Only in the Tensura world's generator and only with design
 * rasters ({@link DesignWorld#excludesStart}); everywhere else the vanilla answer stands.
 */
@Mixin(ChunkGenerator.class)
public abstract class ChunkGeneratorMixin {
    @WrapOperation(method = "tryGenerateStructure",
            at = @At(value = "INVOKE", target = "Lnet/minecraft/world/level/levelgen/structure/StructureStart;isValid()Z"))
    private boolean ttl$excludeDesignedAreas(StructureStart start, Operation<Boolean> original) {
        boolean valid = original.call(start);
        return valid && !DesignWorld.excludesStart((ChunkGenerator) (Object) this, start);
    }
}
