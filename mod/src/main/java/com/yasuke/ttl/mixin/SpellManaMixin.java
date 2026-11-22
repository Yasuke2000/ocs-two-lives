package com.yasuke.ttl.mixin;

import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import com.llamalad7.mixinextras.injector.wrapoperation.WrapOperation;
import com.llamalad7.mixinextras.sugar.Local;
import com.yasuke.ttl.TtlDimensions;
import io.redspace.ironsspellbooks.api.spells.AbstractSpell;
import net.minecraft.world.entity.player.Player;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;

/**
 * Iron's Spells in the Mortal dimensions spend Iron's own mana (issue #104). The Tensura bridge (tensura_iron_spells
 * 2.0.0.0, MixinAbstractSpell) wraps the same getManaCost call in canBeCastedBy and asks for
 * manaConversionMultiplier (50) x the cost in magicules, or that much Iron's mana when the body holds fewer; a Life 1
 * Human holds 50-70, so every spellbook cast there failed. Priority above the default 1000: this wrapper is applied
 * after the bridge's and so wraps it, and in the Mortal dimensions it skips the bridge and returns the plain cost.
 * Everywhere else the bridge runs as before. TensuraIronCastMixin keeps the cast itself on Iron's mana there.
 */
@Mixin(value = AbstractSpell.class, priority = 1500)
public abstract class SpellManaMixin {
    @WrapOperation(method = "canBeCastedBy", require = 0, at = @At(value = "INVOKE",
            target = "Lio/redspace/ironsspellbooks/api/spells/AbstractSpell;getManaCost(I)I"))
    private int ttl$plainManaInMortal(AbstractSpell spell, int level, Operation<Integer> original, @Local(argsOnly = true) Player player) {
        if (player != null && TtlDimensions.isMortal(player.level().dimension())) return spell.getManaCost(level);
        return original.call(spell, level);
    }
}
