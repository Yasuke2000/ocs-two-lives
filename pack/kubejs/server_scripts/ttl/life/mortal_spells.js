// Iron's Spells in Life 1 (issue #104). The Tensura bridge (tensura_iron_spells, config/tensura/iron_spell_config.toml
// manaConversionMultiplier = 50) pays every spell from Tensura magicules: a cast is allowed only when the body holds
// 50 x the mana cost in magicules, else it asks for 50 x the cost in Iron's mana. A Life 1 Human holds 50-70 magicules
// (config/tensura/race/human_config.toml), so every spellbook cast in the Mortal Realm failed with "not enough mana"
// while scrolls (they spend no mana) still worked. ttl-portals (SpellManaMixin, TensuraIronCastMixin) turns the bridge off
// in the three Mortal dimensions: there Iron's spends its own mana, as in a world without Tensura (master plan §4: Iron's
// is a Life 1 thing and what a soul learns there carries over). The blood/eldritch veto (mortal_banned.toml
// spell_schools, life/mortal_banned.js) is a separate rule and stays. Life 2 keeps the bridge.
//
// Ops / tests: /ttl spells <player>                               magicules, Iron's mana and max mana
//              /ttl spells <player> mana <n>                      set Iron's mana (test setup)
//              /ttl spells <player> cancast <spell> <yes|no>      test assertion: a spellbook cast of that spell (its minimum
//                                                                 level) passes Iron's own checks (mana, cooldown, learning)
//                                                                 where the player stands; prints "ttl: ..." when it does not
//              /ttl spells <player> cost <spell> <n|plain>        test assertion: the Iron's mana that cast asks for (plain =
//                                                                 the spell's own cost, no magicule conversion)
//              /ttl spells <player> cast <spell> <yes|no>         a real spellbook cast (Iron's attemptInitiateCast, with its
//                                                                 pre-cast event); yes = it started. Use an instant spell: Iron's
//                                                                 casts it on the next tick (SpellOnCastEvent, mana spent)
//              /ttl spells <player> summons <n>                   test assertion: at least n spell summons (Iron's IMagicSummon)
//                                                                 of this player stand within 16 blocks (summons near Wayfarer's
//                                                                 Rest used to be removed as natural spawns, life/mortal_spawns.js)
//              /ttl spells <player> spent                         test assertion, a tick or more after `cast ... yes`: the cast
//                                                                 took its plain mana (minus at most 5 regenerated meanwhile)
//                                                                 and not a single magicule
const TtlMortalSpells = {
  classes: null,

  api() {
    if (this.classes) return this.classes
    this.classes = {
      registry: Java.loadClass('io.redspace.ironsspellbooks.api.registry.SpellRegistry'),
      magic: Java.loadClass('io.redspace.ironsspellbooks.api.magic.MagicData'),
      source: Java.loadClass('io.redspace.ironsspellbooks.api.spells.CastSource')
    }
    return this.classes
  },

  spell(id) {
    var spell = this.api().registry.getSpell(String(id))
    if (!spell || String(spell.getSpellId()) !== String(id)) throw `unknown Iron's spell ${id}`
    return spell
  },

  magicule(player) {
    try {
      var storages = Java.loadClass('io.github.manasmods.tensura.storage.TensuraStorages')
      return Math.round(Number(storages.getExistenceFrom(player).getMagicule()))
    } catch (e) {
      return -1
    }
  },

  data(player) {
    return this.api().magic.getPlayerMagicData(player)
  },

  maxMana(player) {
    try {
      var attrs = Java.loadClass('io.redspace.ironsspellbooks.api.registry.AttributeRegistry')
      return Math.round(Number(player.getAttributeValue(attrs.MAX_MANA)))
    } catch (e) {
      return -1
    }
  },

  // {ok, why}: Iron's own canBeCastedBy for a spellbook cast at the spell's minimum level, the check a real cast makes
  // first (attemptInitiateCast), with the bridge's mana conversion applied or not by ttl-portals.
  check(player, id) {
    var spell = this.spell(id)
    var result = spell.canBeCastedBy(spell.getMinLevel(), this.api().source.SPELLBOOK, this.data(player), player)
    var why = ''
    try {
      if (result.message) why = String(result.message.getString())
    } catch (e) {
      why = ''
    }
    return { ok: !!result.isSuccess(), why: why }
  },

  // The last `cast` per player name: {id, mana, magicule} before it, for `spent`.
  before: {},

  // A real spellbook cast, as a key press on a held spellbook starts it. True when Iron's started it; the mana and
  // magicules before it are kept for `spent`.
  cast(player, id) {
    var spell = this.spell(id)
    var name = String(player.username)
    this.before[name] = { id: String(id), mana: Number(this.data(player).getMana()), magicule: this.magicule(player) }
    return !!spell.attemptInitiateCast(player.getMainHandItem(), spell.getMinLevel(), player.level, player, this.api().source.SPELLBOOK, true, 'mainhand')
  },

  // Spell summons of this player within `radius` blocks.
  summons(player, radius) {
    var type = Java.loadClass('io.redspace.ironsspellbooks.entity.mobs.IMagicSummon')
    var AABB = Java.loadClass('net.minecraft.world.phys.AABB')
    var box = new AABB(player.getX() - radius, player.getY() - radius, player.getZ() - radius, player.getX() + radius, player.getY() + radius, player.getZ() + radius)
    var n = 0
    var me = TtlLife.uuid(player)
    player.level.getEntitiesWithin(box).forEach(e => {
      try {
        if (!(e instanceof type) || !e.isAlive()) return
        var by = e.getSummoner()
        if (by && TtlLife.uuid(by) === me) n++
      } catch (err) {
        // not a summon of this player
      }
    })
    return n
  },

  // The mana the spellbook cast asks for, as canBeCastedBy sees it: mana is enough exactly when mana >= this. Found by
  // probing the check with full and empty mana around the plain cost (the bridge asks for 0 or 50 x the cost).
  askedMana(player, id) {
    var spell = this.spell(id)
    var data = this.data(player)
    var before = Number(data.getMana())
    var plain = Number(spell.getManaCost(spell.getMinLevel()))
    try {
      data.setMana(0)
      if (this.check(player, id).ok) return 0
      data.setMana(plain)
      if (this.check(player, id).ok) return plain
      return -1
    } finally {
      data.setMana(before)
    }
  }
}

ServerEvents.commandRegistry(event => {
  var { commands: Commands, arguments: Arguments } = event

  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] spells command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  var say = (ctx, line) => ctx.source.sendSystemMessage(Text.of(line))
  var target = ctx => Arguments.PLAYER.getResult(ctx, 'target')
  var spellArg = ctx => String(Arguments.RESOURCE_LOCATION.getResult(ctx, 'spell'))

  var describe = p => `magicule=${TtlMortalSpells.magicule(p)} mana=${Math.round(Number(TtlMortalSpells.data(p).getMana()))} max_mana=${TtlMortalSpells.maxMana(p)} in ${TtlLife.dimensionOf(p)}`

  var show = ctx => {
    var p = target(ctx)
    say(ctx, `spells ${p.username}: ${describe(p)}`)
    return 1
  }

  var mana = ctx => {
    var p = target(ctx)
    TtlMortalSpells.data(p).setMana(Number(Arguments.INTEGER.getResult(ctx, 'n')))
    say(ctx, `spells ${p.username}: ${describe(p)}`)
    return 1
  }

  var cancast = ctx => {
    var p = target(ctx)
    var id = spellArg(ctx)
    var want = String(Arguments.STRING.getResult(ctx, 'want')) === 'yes'
    var got = TtlMortalSpells.check(p, id)
    if (got.ok !== want) throw `${p.username}: a spellbook cast of ${id} is ${got.ok ? 'allowed' : `refused (${got.why || 'no message'})`}, expected ${want ? 'allowed' : 'refused'} (${describe(p)})`
    say(ctx, `spells ${p.username}: ${id} ${got.ok ? 'allowed' : 'refused'} as expected`)
    return 1
  }

  var plain = (p, id) => {
    var spell = TtlMortalSpells.spell(id)
    return Number(spell.getManaCost(spell.getMinLevel()))
  }

  var cost = ctx => {
    var p = target(ctx)
    var id = spellArg(ctx)
    var raw = String(Arguments.STRING.getResult(ctx, 'n'))
    var want = raw === 'plain' ? plain(p, id) : Number(raw)
    var got = TtlMortalSpells.askedMana(p, id)
    if (got !== want) throw `${p.username}: a spellbook cast of ${id} asks for ${got < 0 ? 'more than its plain cost in' : got} mana, expected ${want} (${describe(p)})`
    say(ctx, `spells ${p.username}: ${id} asks for ${got} mana as expected`)
    return 1
  }

  var cast = ctx => {
    var p = target(ctx)
    var id = spellArg(ctx)
    var want = String(Arguments.STRING.getResult(ctx, 'want')) === 'yes'
    var got = TtlMortalSpells.cast(p, id)
    if (got !== want) throw `${p.username}: the cast of ${id} ${got ? 'started' : 'did not start'}, expected it to ${want ? '' : 'not '}start (${describe(p)})`
    say(ctx, `spells ${p.username}: the cast of ${id} ${got ? 'started' : 'did not start'} as expected`)
    return 1
  }

  var spent = ctx => {
    var p = target(ctx)
    var before = TtlMortalSpells.before[String(p.username)]
    if (!before) throw `${p.username}: no cast to check (run ttl spells ${p.username} cast <spell> yes first)`
    var cost = plain(p, before.id)
    var mana = before.mana - Number(TtlMortalSpells.data(p).getMana())
    var magicule = before.magicule - TtlMortalSpells.magicule(p)
    var line = `the cast of ${before.id} took ${Math.round(mana)} mana and ${magicule} magicules`
    if (mana > cost || mana < cost - 5 || magicule !== 0) throw `${p.username}: ${line}, expected ${cost} mana and 0 magicules (${describe(p)})`
    say(ctx, `spells ${p.username}: ${line} as expected`)
    return 1
  }

  var summons = ctx => {
    var p = target(ctx)
    var want = Number(Arguments.INTEGER.getResult(ctx, 'n'))
    var got = TtlMortalSpells.summons(p, 16)
    if (got < want) throw `${p.username}: ${got} spell summons within 16 blocks, expected at least ${want} (${describe(p)})`
    say(ctx, `spells ${p.username}: ${got} spell summons within 16 blocks as expected`)
    return 1
  }

  event.register(Commands.literal('ttl')
    .then(Commands.literal('spells')
      .requires(src => src.hasPermission(2))
      .then(Commands.argument('target', Arguments.PLAYER.create(event))
        .executes(logged(show))
        .then(Commands.literal('mana')
          .then(Commands.argument('n', Arguments.INTEGER.create(event)).executes(logged(mana))))
        .then(Commands.literal('cancast')
          .then(Commands.argument('spell', Arguments.RESOURCE_LOCATION.create(event))
            .then(Commands.argument('want', Arguments.STRING.create(event)).executes(logged(cancast)))))
        .then(Commands.literal('spent').executes(logged(spent)))
        .then(Commands.literal('summons')
          .then(Commands.argument('n', Arguments.INTEGER.create(event)).executes(logged(summons))))
        .then(Commands.literal('cast')
          .then(Commands.argument('spell', Arguments.RESOURCE_LOCATION.create(event))
            .then(Commands.argument('want', Arguments.STRING.create(event)).executes(logged(cast)))))
        .then(Commands.literal('cost')
          .then(Commands.argument('spell', Arguments.RESOURCE_LOCATION.create(event))
            .then(Commands.argument('n', Arguments.STRING.create(event)).executes(logged(cost))))))))
})
