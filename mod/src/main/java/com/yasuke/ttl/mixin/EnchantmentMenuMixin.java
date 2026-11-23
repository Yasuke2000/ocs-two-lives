package com.yasuke.ttl.mixin;

import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import com.llamalad7.mixinextras.injector.wrapoperation.WrapOperation;
import com.yasuke.ttl.TtlDimensions;
import net.minecraft.core.Holder;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.RandomSource;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.inventory.EnchantmentMenu;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.enchantment.Enchantment;
import net.minecraft.world.item.enchantment.EnchantmentHelper;
import net.minecraft.world.item.enchantment.EnchantmentInstance;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;

import java.util.List;
import java.util.stream.Stream;

/**
 * An enchanting table in the Mortal dimensions never offers Tombstone's Soulbound (issue #70, owner 22/11/2026). The Life 1
 * death is cancelled, so Tombstone never keeps anything there; only ttl:soulbound items (the Soul Gem) cross to Life 2.
 * The enchantment is taken out of the candidates before the roll (EnchantmentMenu.getEnchantmentList), so the slot offers
 * another enchantment instead, and the clue and the real result stay the same roll. Elsewhere the table is untouched.
 */
@Mixin(EnchantmentMenu.class)
public abstract class EnchantmentMenuMixin {
    private static final ResourceLocation TTL_SOULBOUND = ResourceLocation.fromNamespaceAndPath("tombstone", "soulbound");

    @Shadow
    @Final
    private ContainerLevelAccess access;

    @WrapOperation(method = "getEnchantmentList", at = @At(value = "INVOKE",
            target = "Lnet/minecraft/world/item/enchantment/EnchantmentHelper;selectEnchantment(Lnet/minecraft/util/RandomSource;Lnet/minecraft/world/item/ItemStack;ILjava/util/stream/Stream;)Ljava/util/List;"))
    private List<EnchantmentInstance> ttl$noSoulboundInMortal(RandomSource random, ItemStack stack, int cost, Stream<Holder<Enchantment>> candidates,
                                                             Operation<List<EnchantmentInstance>> original) {
        boolean mortal = this.access.evaluate((level, pos) -> TtlDimensions.isMortal(level.dimension()), false);
        if (mortal) candidates = candidates.filter(holder -> !holder.is(TTL_SOULBOUND));
        return original.call(random, stack, cost, candidates);
    }
}
