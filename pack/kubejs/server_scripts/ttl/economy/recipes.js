// priority: 70
// Lightman's Currency's bank machine, made magical (owner decision 18/11/2026: "banks, but the ATMs must look magical,
// not high-tech"). Names and textures live in pack/kubejs/assets/lightmanscurrency/ (lang/en_us.json: Mana Ledger,
// Guild Coffer, Merchant's Scrying Glass; the ATM block, Pocket Ledger and Ledger Seal textures are recolours).
// Here the Mana Ledger's recipe swaps iron and redstone for Tensura magic ore and a magic crystal, with amethyst for
// the glass: nothing in it exists in Life 1 (Tensura items are banned in the Mortal dimensions), so the bank is
// a Life 2 machine like the coins it handles. The recipe id `lightmanscurrency:atm` is removed by id, NOT by output:
// the Pocket Mana Ledger swap recipes also output the ATM.
ServerEvents.recipes(event => {
  var needs = ['tensura:magic_ore_shard', 'tensura:low_quality_magic_crystal', 'minecraft:amethyst_shard']
  var missing = needs.filter(id => !Item.exists(id))
  if (missing.length > 0) {
    console.error(`[ttl] economy: Mana Ledger recipe not changed, unknown items: ${missing.join(', ')}`)
    return
  }
  event.remove({ id: 'lightmanscurrency:atm' })
  event.shaped('lightmanscurrency:atm', ['SAS', 'SAS', 'SCS'], {
    S: 'tensura:magic_ore_shard',
    A: 'minecraft:amethyst_shard',
    C: 'tensura:low_quality_magic_crystal'
  }).id('ttl:mana_ledger')
})

// The two mithrils (design/architecture/paths-necro-artificer.md §3.4; WP-A1): tensura:mithril_ingot and Iron's
// irons_spellbooks:mithril_ingot are different items. Tensura's kiln reconciles them both ways at 1:1 so neither mod's
// content is orphaned: Iron's ingot melts into the same molten magisteel + silver as Tensura's (tensura:kiln_melting,
// the numbers of data/tensura/recipe/melting/mithril_ingot.json), and that melt can be mixed into Iron's ingot as well as
// Tensura's (tensura:kiln_mixing; the kiln's mixing screen pages between recipes with the same inputs). JEI shows both.
ServerEvents.recipes(event => {
  var ids = ['tensura:mithril_ingot', 'irons_spellbooks:mithril_ingot']
  var missing = ids.filter(id => !Item.exists(id))
  if (missing.length > 0) {
    console.error(`[ttl] economy: mithril bridge skipped, unknown items: ${missing.join(', ')}`)
    return
  }
  event.custom({
    type: 'tensura:kiln_melting',
    input: { item: 'irons_spellbooks:mithril_ingot' },
    primary: 'tensura:magisteel',
    primary_count: 20,
    secondary: 'tensura:silver',
    secondary_count: 4,
    smeltTick: 300
  }).id('ttl:irons_mithril_melting')
  event.custom({
    type: 'tensura:kiln_mixing',
    left: 'tensura:silver',
    left_count: 4,
    right: 'tensura:magisteel',
    right_count: 20,
    output: { count: 1, id: 'irons_spellbooks:mithril_ingot' }
  }).id('ttl:irons_mithril_mixing')
})
