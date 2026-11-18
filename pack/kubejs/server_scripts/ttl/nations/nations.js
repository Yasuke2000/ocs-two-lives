// priority: 70
// Player nations (design/architecture/sprint3-4.md S4; numbers in design/data/nations.toml -> TtlData.nations).
//
// A NATION IS AN FTB TEAMS PARTY THAT PAID ITS CHARTER. The record is keyed by the party's team id and never holds a
// roster: members, owner and size come from FTB Teams every time (`/ftbteams party ...` is how people join, leave and are
// kicked, max_party_size = 5 is the member cap). So the same party object serves quests, the story path and boss credit
// too (design/architecture/story-characters.md §4), and a party that is disbanded takes its nation with it.
//
// Server persistentData `ttl.nations` = JSON {teamId: {name, owner, founded, home, homeRegion, rank, value, treasury,
//   owed, upkeepWeek, ally_to: [teamId], wars: [{with, declared, active_at}], renown: {uuid: n}}}
//   owner      the party owner's UUID (kept in step with FTB by the poll)
//   home       faction id of the region where the charter was signed ('' when none), homeRegion its canon letter
//   path       the party's story Oath path at founding ('light' | 'dark' | ''), read through TtlParty.partyPath (party/party.js);
//              the nation and the story party are the same FTB team, so the key is the same id in ttl.story.parties
//   rank       rank id from nations.toml, value the last computed value (the leaderboard reads it)
//   treasury   bronze coins in the nation's chest of coins; owed = unpaid upkeep (bronze)
//   ally_to    the nations THIS nation has offered an alliance; two nations are allied when both list each other
//   wars       declarations seen from this side (both nations carry one); a war counts from active_at
//   renown     last renown seen per member, so an offline member still counts
// Player facts: stages `ttl.nation.member`, `ttl.nation.owner`, `ttl.nation.rank.<id>` (exactly one rank), scoreboard
// `ttl.nation.value` (the nation's value, on every online member; for Easy NPC and FTB Quests conditions), persistentData
// `ttl.nation.extra` (claim allowance last applied, claims.js).
//
// VALUE (nations.toml [value]): sum of members' renown (TtlRep.renown) + claimed chunks + builds (Public Works chunks inside
// the claims) + treasury. Ranks come from the value and raise the land each member brings (claims.js).
//
// PUBLIC API (other packages call these; `player` is a ServerPlayer, `key` a team id string):
//   TtlNations.of(server, player)            {key, rec, team} of the player's nation, or null
//   TtlNations.isMember(server, player)      true when the player's party is a nation
//   TtlNations.all(server)                   {teamId: record}
//   TtlNations.byName(server, name)          {key, rec} (case-insensitive) or null
//   TtlNations.membersOf(key)                the party's members as Java UUIDs (offline ones too)
//   TtlNations.value(server, key)            {members, chunks, builds, treasury, total} recomputed now (also refreshes the record)
//   TtlNations.rankOf(rec)                   the rank table entry of a record
//   TtlNations.atWar(server, keyA, keyB)     true when a declared war between the two is active (S5 reads this)
//   TtlNations.warState(server, a, b)        'none' | 'pending' | 'active'
//   TtlNations.allied(server, a, b)          true when both nations offered each other an alliance
//   TtlNations.found/dissolve/deposit/withdraw/ally/unally/declareWar/endWar(server, player, ...)  the player actions
//   TtlNations.syncAll(server)               reconcile with FTB Teams now (also runs every rules.poll_ticks)
// Actions throw a plain message string on a refusal; commands.js shows it ("ttl: ...").
const TtlNations = {
  KEY: 'ttl.nations',
  api: undefined,
  warned: false,

  conf() {
    return TtlData.nations
  },

  rules() {
    return TtlData.nations.rules
  },

  ranks() {
    return TtlData.nations.rank
  },

  rankById(id) {
    var all = this.ranks()
    for (var i = 0; i < all.length; i++) {
      if (String(all[i].id) === String(id)) return all[i]
    }
    return all[0]
  },

  rankFor(value) {
    var all = this.ranks()
    var best = all[0]
    for (var i = 0; i < all.length; i++) {
      if (Number(value) >= Number(all[i].value)) best = all[i]
    }
    return best
  },

  rankOf(rec) {
    return this.rankById(rec.rank)
  },

  // ---- FTB Teams ----------------------------------------------------------------------------------------------

  // The team manager, or null while FTB Teams is absent or its world is not loaded yet.
  manager() {
    if (this.api === null) return null
    try {
      if (this.api === undefined) this.api = Java.loadClass('dev.ftb.mods.ftbteams.api.FTBTeamsAPI').api()
      return this.api.isManagerLoaded() ? this.api.getManager() : null
    } catch (e) {
      this.api = null
      console.error(`[ttl] nations: FTB Teams API not reachable, nations are off: ${e}`)
      return null
    }
  },

  // The player's current team (their own player team when they are in no party), or null.
  teamOf(player) {
    var m = this.manager()
    if (!m) return null
    var opt = m.getTeamForPlayer(player)
    return opt.isPresent() ? opt.get() : null
  },

  partyOf(player) {
    var t = this.teamOf(player)
    return t && t.isPartyTeam() ? t : null
  },

  keyOf(team) {
    return String(team.getId())
  },

  juuid(text) {
    return Java.loadClass('java.util.UUID').fromString(String(text))
  },

  // A valid party team by key, or null.
  teamByKey(key) {
    var m = this.manager()
    if (!m) return null
    var opt = m.getTeamByID(this.juuid(key))
    if (!opt.isPresent()) return null
    var t = opt.get()
    return t.isPartyTeam() && t.isValid() ? t : null
  },

  memberIdsOf(team) {
    var out = []
    var it = team.getMembers().iterator()
    while (it.hasNext()) out.push(it.next())
    return out
  },

  membersOf(key) {
    var team = this.teamByKey(key)
    return team ? this.memberIdsOf(team) : []
  },

  onlinePlayer(server, uuid) {
    try {
      return server.getPlayerList().getPlayer(uuid)
    } catch (e) {
      return null
    }
  },

  nameOfId(server, uuid) {
    var p = this.onlinePlayer(server, uuid)
    if (p) return String(p.username)
    try {
      var opt = this.manager().getPlayerTeamForPlayerID(uuid)
      if (opt.isPresent()) return String(opt.get().getShortName())
    } catch (e) {
      // fall through to the UUID
    }
    return String(uuid)
  },

  // ---- storage ------------------------------------------------------------------------------------------------

  all(server) {
    try {
      var raw = String(server.persistentData.getString(this.KEY))
      var parsed = raw ? JSON.parse(raw) : {}
      return parsed && typeof parsed === 'object' ? parsed : {}
    } catch (e) {
      console.error(`[ttl] nations: the stored nations are unreadable, treating them as empty: ${e}`)
      return {}
    }
  },

  save(server, all) {
    server.persistentData.putString(this.KEY, JSON.stringify(all))
  },

  byName(server, name) {
    var all = this.all(server)
    var want = String(name).trim().toLowerCase()
    var keys = Object.keys(all)
    for (var i = 0; i < keys.length; i++) {
      if (String(all[keys[i]].name).toLowerCase() === want) return { key: keys[i], rec: all[keys[i]] }
    }
    return null
  },

  find(server, name) {
    var n = this.byName(server, name)
    if (!n) throw `no nation called ${name}`
    return n
  },

  of(server, player) {
    var team = this.partyOf(player)
    if (!team) return null
    var key = this.keyOf(team)
    var rec = this.all(server)[key]
    return rec ? { key: key, rec: rec, team: team } : null
  },

  isMember(server, player) {
    try {
      return this.of(server, player) !== null
    } catch (e) {
      return false
    }
  },

  // The player's nation, or a refusal.
  require(server, player) {
    var n = this.of(server, player)
    if (!n) throw 'you are not in a nation (found one with /ttl nation found <name> as the owner of a party)'
    return n
  },

  requireOwner(server, player) {
    var n = this.require(server, player)
    if (String(n.team.getOwner()) !== TtlLife.uuid(player)) throw 'only the owner of the nation (the party owner) can do that'
    return n
  },

  requireLife2(player) {
    if (TtlLife.phase(player) !== 'life2') throw 'Life 2 only'
  },

  // ---- value --------------------------------------------------------------------------------------------------

  // Members' renown (live for online members, the last seen value for offline ones), claims, builds, treasury.
  // Updates rec.renown in memory; the caller saves.
  valueParts(server, rec, team) {
    var v = this.conf().value
    var renown = {}
    var members = 0
    this.memberIdsOf(team).forEach(u => {
      var id = String(u)
      var n = Number(rec.renown && rec.renown[id] ? rec.renown[id] : 0)
      var p = this.onlinePlayer(server, u)
      if (p && typeof TtlRep !== 'undefined') {
        try {
          n = Number(TtlRep.renown(server, p))
        } catch (e) {
          console.warn(`[ttl] nations: renown of ${p.username} unreadable: ${e}`)
        }
      }
      renown[id] = n
      members += n
    })
    rec.renown = renown
    var chunks = TtlNationClaims.count(team)
    var builds = TtlNationClaims.builds(server, team)
    var treasury = Math.floor(Number(rec.treasury || 0) / Number(v.coins_per_value))
    var total = members + chunks * Number(v.chunk_value) + builds * Number(v.build_value) + treasury
    return { members: members, chunks: chunks, builds: builds, treasury: treasury, total: Math.max(0, Math.round(total)) }
  },

  // Recomputes the value and rank of one nation, writes the record and the member mirrors, announces a rank-up.
  value(server, key) {
    var all = this.all(server)
    var rec = all[key]
    var team = this.teamByKey(key)
    if (!rec || !team) return null
    var parts = this.valueParts(server, rec, team)
    var before = String(rec.rank)
    var rank = this.rankFor(parts.total)
    rec.rank = String(rank.id)
    rec.value = parts.total
    all[key] = rec
    this.save(server, all)
    if (before !== rec.rank) this.rankChanged(server, key, rec, before, rank)
    this.memberIdsOf(team).forEach(u => {
      var p = this.onlinePlayer(server, u)
      if (!p) return
      try {
        this.applyMember(server, p, rec)
      } catch (e) {
        console.error(`[ttl] nations: applying ${rec.name} to ${p.username} failed: ${e}`)
      }
    })
    return parts
  },

  rankChanged(server, key, rec, before, rank) {
    var ids = this.ranks().map(r => String(r.id))
    console.info(`[ttl] nations: ${rec.name} is now a ${rank.title} (value ${rec.value}, was ${before})`)
    if (ids.indexOf(String(rank.id)) <= ids.indexOf(before)) return
    this.tell(server, key, `${rec.name} has grown into a ${rank.title}.`)
    this.post(server, `The nation ${rec.name} has grown into a ${rank.title}.`, rec)
  },

  // ---- mirrors of one player ----------------------------------------------------------------------------------

  ensureObjective(server) {
    try {
      if (!server.getScoreboard().getObjective('ttl.nation.value')) server.runCommandSilent('scoreboard objectives add ttl.nation.value dummy')
    } catch (e) {
      console.warn(`[ttl] nations: could not create the value scoreboard: ${e}`)
    }
  },

  stage(player, name, on) {
    if (on && !player.stages.has(name)) player.stages.add(name)
    else if (!on && player.stages.has(name)) player.stages.remove(name)
  },

  // Stages, scoreboard and claim allowance of a player who is in the nation `rec`.
  applyMember(server, player, rec) {
    var me = TtlLife.uuid(player)
    this.stage(player, 'ttl.nation.member', true)
    this.stage(player, 'ttl.nation.owner', String(rec.owner) === me)
    var rank = this.rankOf(rec)
    var self = this
    this.ranks().forEach(r => self.stage(player, `ttl.nation.rank.${r.id}`, String(r.id) === String(rank.id)))
    this.ensureObjective(server)
    server.runCommandSilent(`scoreboard players set ${player.username} ttl.nation.value ${Math.round(Number(rec.value || 0))}`)
    TtlNationClaims.apply(server, player, rank)
  },

  // A player who is in no nation: no stages, no extra chunks (only what we gave them, an op's own extras stay).
  clearMember(server, player) {
    var self = this
    if (player.stages.has('ttl.nation.member')) {
      this.stage(player, 'ttl.nation.member', false)
      this.stage(player, 'ttl.nation.owner', false)
      this.ranks().forEach(r => self.stage(player, `ttl.nation.rank.${r.id}`, false))
      server.runCommandSilent(`scoreboard players set ${player.username} ttl.nation.value 0`)
    }
    if (Number(player.persistentData.getInt('ttl.nation.extra')) > 0) TtlNationClaims.apply(server, player, null)
  },

  // ---- sync with FTB Teams ------------------------------------------------------------------------------------

  // Removes a nation record (without saving) and every reference other nations kept to it.
  dropRecord(server, all, key, why) {
    var rec = all[key]
    delete all[key]
    Object.keys(all).forEach(k => {
      var o = all[k]
      o.ally_to = (o.ally_to || []).filter(x => x !== key)
      o.wars = (o.wars || []).filter(w => w.with !== key)
    })
    console.info(`[ttl] nations: ${rec.name} is gone (${why})`)
    this.post(server, `The nation ${rec.name} is no more (${why}).`, rec)
  },

  // One poll: nations whose party is gone are removed, owners follow FTB, every online player gets (or loses) the nation
  // mirrors. Does nothing while FTB Teams is not ready (a missing manager must never delete nations).
  syncAll(server) {
    if (!this.manager()) return
    var all = this.all(server)
    var changed = false
    var self = this
    Object.keys(all).forEach(key => {
      var team = self.teamByKey(key)
      if (!team) {
        self.dropRecord(server, all, key, 'its party was disbanded')
        changed = true
        return
      }
      var owner = String(team.getOwner())
      if (all[key].owner !== owner) {
        all[key].owner = owner
        changed = true
      }
    })
    if (changed) {
      this.save(server, all)
      this.refreshDiscordRoles(server)
    }
    server.getPlayerList().getPlayers().forEach(p => {
      try {
        self.syncPlayer(server, p, all)
      } catch (e) {
        console.error(`[ttl] nations: sync of ${p.username} failed: ${e}`)
      }
    })
  },

  syncPlayer(server, player, all) {
    var map = all || this.all(server)
    var team = this.partyOf(player)
    var rec = team ? map[this.keyOf(team)] : null
    if (rec) this.applyMember(server, player, rec)
    else this.clearMember(server, player)
  },

  // ---- announcements ------------------------------------------------------------------------------------------

  // Chat line to every online member of the nation.
  tell(server, key, text) {
    var line = JSON.stringify([{ text: '[Nation] ', color: 'gold' }, { text: String(text), color: 'yellow' }])
    var team = this.teamByKey(key)
    if (!team) return
    var self = this
    this.memberIdsOf(team).forEach(u => {
      var p = self.onlinePlayer(server, u)
      if (p) server.runCommandSilent(`tellraw ${p.username} ${line}`)
    })
  },

  // One #story line; never for a test bot's nation (founded by a TtlBot… player, or named TtlBot…).
  post(server, text, rec) {
    try {
      if (typeof TtlDiscord === 'undefined') return
      if (rec && /^TtlBot/.test(String(rec.name))) return
      var owner = rec && rec.owner ? this.onlinePlayer(server, this.juuid(rec.owner)) : null
      if (owner && TtlDiscord.isBot(owner.username)) return
      TtlDiscord.post(server, text)
    } catch (e) {
      console.warn(`[ttl] nations: Discord post failed: ${e}`)
    }
  },

  // ---- founding and dissolving --------------------------------------------------------------------------------

  checkName(server, raw) {
    var r = this.rules()
    var name = String(raw).trim().replace(/\s+/g, ' ')
    if (name.length < Number(r.name_min) || name.length > Number(r.name_max)) throw `a nation name has ${r.name_min} to ${r.name_max} characters`
    if (!/^[A-Za-z0-9][A-Za-z0-9 '\-]*$/.test(name)) throw "a nation name uses letters, digits, spaces, ' and - only"
    if (this.byName(server, name)) throw `the name ${name} is taken`
    return name
  },

  // /ttl nation found <name>: the party owner in Life 2, in the overworld, with the boss stage and the charter fee.
  found(server, player, rawName) {
    var r = this.rules()
    this.requireLife2(player)
    if (TtlLife.dimensionOf(player) !== TtlLife.OVERWORLD) throw 'sign the charter in the Tensura overworld: where you stand is the home of your nation'
    var team = this.partyOf(player)
    if (!team) throw 'you are in no party yet: /ftbteams party create <name>, then invite your people'
    if (String(team.getOwner()) !== TtlLife.uuid(player)) throw 'only the owner of the party can found the nation'
    var key = this.keyOf(team)
    var existing = this.all(server)[key]
    if (existing) throw `your party already is the nation ${existing.name}`
    if (this.memberIdsOf(team).length < Number(r.min_members)) throw `a nation needs at least ${r.min_members} members in the party`
    if (!player.stages.has(String(r.charter_stage))) throw `the charter is not yours yet (needs the stage ${r.charter_stage})`
    var name = this.checkName(server, rawName)
    if (typeof TtlEcon === 'undefined') throw 'the economy is not loaded, the charter cannot be paid'
    if (!TtlEcon.canPay(player, r.charter_cost)) throw `the charter costs ${TtlEcon.text(r.charter_cost)}`
    var x = Math.floor(player.getX())
    var z = Math.floor(player.getZ())
    var faction = null
    var region = ''
    try {
      if (typeof TtlRep !== 'undefined') {
        faction = TtlRep.factionAt(x, z)
        region = TtlRep.regionAt(x, z) || ''
      }
    } catch (e) {
      console.warn(`[ttl] nations: home region of ${name} unreadable: ${e}`)
    }
    if (!TtlEcon.charge(server, player, r.charter_cost, `charter:${name}`)) throw `the charter costs ${TtlEcon.text(r.charter_cost)}`
    var path = ''
    try {
      if (typeof TtlParty !== 'undefined' && typeof TtlParty.info === 'function' && typeof TtlParty.partyPath === 'function') {
        var pp = TtlParty.partyPath(server, TtlParty.info(server, player), null)
        path = pp ? String(pp.path) : ''
      }
    } catch (e) {
      console.warn(`[ttl] nations: story path of ${name} unreadable: ${e}`)
    }
    var all = this.all(server)
    var rec = {
      name: name, owner: TtlLife.uuid(player), founded: Date.now(), home: faction ? String(faction.id) : '', homeRegion: String(region), path: path,
      rank: String(this.ranks()[0].id), value: 0, treasury: 0, owed: 0, upkeepWeek: '', ally_to: [], wars: [], renown: {}
    }
    all[key] = rec
    this.save(server, all)
    this.refreshDiscordRoles(server)
    console.info(`[ttl] nations: ${player.username} founded ${name} (home ${rec.home || 'none'}, ${this.memberIdsOf(team).length} members)`)
    try {
      TtlDiscordStory.post(server, 'nation', [player.username], `${TtlDiscord.name(player.username)} has founded the nation ${name}${faction ? ` in the lands of the ${faction.title}` : ''}.`, TtlDiscord.isBot(name))
    } catch (e) {
      console.warn(`[ttl] nations: founding story post failed: ${e}`)
    }
    try {
      this.seedHome(server, team, rec)
      this.value(server, key)
      this.syncAll(server)
      this.tell(server, key, `${name} is founded. Home region: ${faction ? faction.title : 'the wilds'}.`)
    } catch (e) {
      console.error(`[ttl] nations: finishing the founding of ${name} failed: ${e}`)
    }
    return rec
  },

  refreshDiscordRoles(server) {
    try {
      TtlDiscordRoles.syncNations(server)
    } catch (e) {
      TtlSdlink.warn('nation role sync', e)
    }
  },

  // Every member online at founding starts with rules.home_rep with the faction of the home region.
  seedHome(server, team, rec) {
    var n = Number(this.rules().home_rep)
    if (!n || !rec.home || typeof TtlRep === 'undefined') return
    var self = this
    this.memberIdsOf(team).forEach(u => {
      var p = self.onlinePlayer(server, u)
      if (p) TtlRep.add(server, p, rec.home, n, `nation charter ${rec.name}`)
    })
  },

  // The owner dissolves the nation; the treasury is paid back to them. The party itself stays.
  dissolve(server, player) {
    var n = this.requireOwner(server, player)
    var all = this.all(server)
    var back = Number(n.rec.treasury || 0)
    this.dropRecord(server, all, n.key, `dissolved by ${player.username}`)
    this.save(server, all)
    this.refreshDiscordRoles(server)
    if (back > 0) {
      TtlEcon.pay(server, player, back, 'treasury:refund')
      TtlEcon.note(server, 'faucet', -back, 'treasury:refund')
    }
    this.syncAll(server)
    return back
  },

  // ---- treasury -----------------------------------------------------------------------------------------------

  coinTable(coin, n) {
    var count = Number(n)
    if (!(count >= 1) || Math.floor(count) !== count) throw 'give a whole number of coins, at least 1'
    var table = {}
    table[String(coin).toLowerCase()] = count
    return table
  },

  requireTreasury() {
    if (!this.conf().treasury.enabled) throw 'the nation treasury is switched off'
  },

  // Money moving between a player and the treasury is a transfer: TtlEcon counts every charge as a sink and every pay as a
  // faucet, so the same amount is booked back (a negative note), and the 80% sink target keeps meaning real sinks.
  deposit(server, player, coin, n) {
    this.requireTreasury()
    this.requireLife2(player)
    var nat = this.require(server, player)
    var table = this.coinTable(coin, n)
    var bronze = TtlEcon.amount(table)
    if (!TtlEcon.canPay(player, bronze)) throw `you do not carry ${TtlEcon.text(table)}`
    if (!TtlEcon.charge(server, player, bronze, 'treasury:deposit')) throw `you do not carry ${TtlEcon.text(table)}`
    TtlEcon.note(server, 'sink', -bronze, 'treasury:deposit')
    var all = this.all(server)
    all[nat.key].treasury = Number(all[nat.key].treasury || 0) + bronze
    this.save(server, all)
    console.info(`[ttl] nations: ${player.username} paid ${bronze} bronze into the treasury of ${all[nat.key].name}`)
    return Number(all[nat.key].treasury)
  },

  withdraw(server, player, coin, n) {
    this.requireTreasury()
    this.requireLife2(player)
    var nat = this.requireOwner(server, player)
    var table = this.coinTable(coin, n)
    var bronze = TtlEcon.amount(table)
    var all = this.all(server)
    var have = Number(all[nat.key].treasury || 0)
    if (bronze > have) throw `the treasury holds ${TtlEcon.text(have)}`
    all[nat.key].treasury = have - bronze
    this.save(server, all)
    TtlEcon.pay(server, player, bronze, 'treasury:withdraw')
    TtlEcon.note(server, 'faucet', -bronze, 'treasury:withdraw')
    console.info(`[ttl] nations: ${player.username} took ${bronze} bronze from the treasury of ${all[nat.key].name}`)
    return Number(all[nat.key].treasury)
  },

  // Weekly upkeep: on the first check of each ISO week the nation owes the upkeep per claimed chunk and pays what the
  // treasury holds; the rest stays in `owed` (no punishment yet). The first check of a new nation only sets the week.
  upkeep(server, key) {
    if (!this.conf().treasury.upkeep || typeof TtlEcon === 'undefined') return
    var all = this.all(server)
    var rec = all[key]
    var team = this.teamByKey(key)
    if (!rec || !team) return
    var week = TtlEcon.weekKey()
    if (rec.upkeepWeek === week) return
    if (!rec.upkeepWeek) {
      rec.upkeepWeek = week
      this.save(server, all)
      return
    }
    var per
    try {
      per = TtlEcon.fee('upkeep_per_chunk_week')
    } catch (e) {
      console.warn(`[ttl] nations: no upkeep fee in the economy, skipping upkeep: ${e}`)
      return
    }
    var chunks = TtlNationClaims.count(team)
    rec.owed = Number(rec.owed || 0) + per * chunks
    var pay = Math.min(Number(rec.treasury || 0), rec.owed)
    rec.treasury = Number(rec.treasury || 0) - pay
    rec.owed -= pay
    rec.upkeepWeek = week
    this.save(server, all)
    if (pay > 0) TtlEcon.note(server, 'sink', pay, 'upkeep:nation')
    console.info(`[ttl] nations: upkeep of ${rec.name} for week ${week}: ${chunks} chunks, paid ${pay}, owes ${rec.owed}`)
    if (rec.owed > 0) this.tell(server, key, `The treasury could not cover the upkeep: ${TtlEcon.text(rec.owed)} is owed.`)
  },

  // ---- diplomacy ----------------------------------------------------------------------------------------------

  allied(server, a, b) {
    var all = this.all(server)
    return !!(all[a] && all[b] && (all[a].ally_to || []).indexOf(b) >= 0 && (all[b].ally_to || []).indexOf(a) >= 0)
  },

  warState(server, a, b) {
    var rec = this.all(server)[a]
    if (!rec) return 'none'
    var list = (rec.wars || []).filter(w => w.with === b)
    if (list.length === 0) return 'none'
    return Number(list[0].active_at) <= Date.now() ? 'active' : 'pending'
  },

  atWar(server, a, b) {
    return this.warState(server, a, b) === 'active'
  },

  ally(server, player, targetName) {
    var me = this.requireOwner(server, player)
    var other = this.find(server, targetName)
    if (other.key === me.key) throw 'that is your own nation'
    if (this.warState(server, me.key, other.key) !== 'none') throw `you are at war with ${other.rec.name}`
    var all = this.all(server)
    var mine = all[me.key].ally_to || []
    if (mine.indexOf(other.key) < 0) mine.push(other.key)
    all[me.key].ally_to = mine
    this.save(server, all)
    if (this.allied(server, me.key, other.key)) {
      this.tell(server, me.key, `${all[me.key].name} and ${other.rec.name} are now allies.`)
      this.tell(server, other.key, `${all[me.key].name} and ${other.rec.name} are now allies.`)
      this.post(server, `The nations ${all[me.key].name} and ${other.rec.name} have sworn an alliance.`, all[me.key])
      return 'allied'
    }
    this.tell(server, other.key, `${all[me.key].name} offers an alliance: the owner answers with /ttl nation ally ${all[me.key].name}.`)
    return 'offered'
  },

  unally(server, player, targetName) {
    var me = this.requireOwner(server, player)
    var other = this.find(server, targetName)
    var all = this.all(server)
    all[me.key].ally_to = (all[me.key].ally_to || []).filter(k => k !== other.key)
    this.save(server, all)
    return true
  },

  // War v1 is a flag and a Discord post (S5 reads atWar): both nations carry the declaration; it counts after the notice.
  declareWar(server, player, targetName) {
    var me = this.requireOwner(server, player)
    var other = this.find(server, targetName)
    if (other.key === me.key) throw 'that is your own nation'
    if (this.allied(server, me.key, other.key)) throw `${other.rec.name} is your ally: end the alliance first (/ttl nation ally remove ${other.rec.name})`
    if (this.warState(server, me.key, other.key) !== 'none') throw `there already is a war with ${other.rec.name}`
    var hours = Number(this.conf().diplomacy.war_notice_hours)
    var now = Date.now()
    var entry = { declared: now, active_at: now + hours * 3600000 }
    var all = this.all(server)
    all[me.key].wars = (all[me.key].wars || []).concat([{ with: other.key, declared: entry.declared, active_at: entry.active_at, by: me.key }])
    all[other.key].wars = (all[other.key].wars || []).concat([{ with: me.key, declared: entry.declared, active_at: entry.active_at, by: me.key }])
    all[me.key].ally_to = (all[me.key].ally_to || []).filter(k => k !== other.key)
    all[other.key].ally_to = (all[other.key].ally_to || []).filter(k => k !== me.key)
    this.save(server, all)
    var when = hours > 0 ? `in ${hours} hours` : 'now'
    try {
      var targetOwner = TtlRegistry.nameOf(server, other.rec.owner)
      TtlDiscordStory.post(server, 'war', [player.username, targetOwner], `The nation ${all[me.key].name} has declared war on ${other.rec.name}. It begins ${when}.`,
        TtlDiscord.isBot(all[me.key].name) || TtlDiscord.isBot(other.rec.name))
    } catch (e) {
      console.warn(`[ttl] nations: war story post failed: ${e}`)
    }
    this.tell(server, me.key, `War on ${other.rec.name} is declared; it begins ${when}.`)
    this.tell(server, other.key, `${all[me.key].name} has declared war on you; it begins ${when}.`)
    return hours
  },

  endWar(server, player, targetName) {
    var me = this.requireOwner(server, player)
    var other = this.find(server, targetName)
    if (this.warState(server, me.key, other.key) === 'none') throw `there is no war with ${other.rec.name}`
    var all = this.all(server)
    all[me.key].wars = (all[me.key].wars || []).filter(w => w.with !== other.key)
    all[other.key].wars = (all[other.key].wars || []).filter(w => w.with !== me.key)
    this.save(server, all)
    this.tell(server, me.key, `Peace with ${other.rec.name}.`)
    this.tell(server, other.key, `Peace with ${all[me.key].name}.`)
    this.post(server, `Peace between the nations ${all[me.key].name} and ${other.rec.name}.`, all[me.key])
    return true
  },

  // ---- display ------------------------------------------------------------------------------------------------

  names(server, key) {
    var self = this
    return this.membersOf(key).map(u => self.nameOfId(server, u))
  },

  nameOfKey(server, key) {
    var rec = this.all(server)[key]
    return rec ? rec.name : key
  },

  lines(server, key) {
    var all = this.all(server)
    var rec = all[key]
    var team = this.teamByKey(key)
    if (!rec || !team) return ['no such nation']
    var parts = this.value(server, key) || { members: 0, chunks: 0, builds: 0, treasury: 0, total: 0 }
    rec = this.all(server)[key]
    var rank = this.rankOf(rec)
    var next = null
    var rs = this.ranks()
    for (var i = 0; i < rs.length; i++) {
      if (Number(rs[i].value) > parts.total) {
        next = rs[i]
        break
      }
    }
    var self = this
    var out = []
    out.push(`${rec.name} · ${rank.title} · value ${parts.total}${next ? ` (${next.title} at ${next.value})` : ' (highest rank)'}`)
    out.push(`  value: members' renown ${parts.members} + chunks ${parts.chunks} + builds ${parts.builds} + treasury ${parts.treasury}`)
    var owner = this.nameOfId(server, this.juuid(rec.owner))
    out.push(`  members (${this.memberIdsOf(team).length}/${this.rules().member_cap}): ${this.names(server, key).join(', ')} · owner ${owner}`)
    var home = rec.home && typeof TtlRep !== 'undefined' ? TtlRep.title(rec.home) : 'the wilds'
    out.push(`  home: ${home}${rec.path ? ` · path ${rec.path}` : ''}`)
    var claims = TtlNationClaims.count(team)
    var max = TtlNationClaims.max(team)
    out.push(`  land: ${claims} chunks claimed${max >= 0 ? ` of ${max}` : ''} (each member brings ${TtlNationClaims.allowance(rank)})`)
    out.push(`  treasury: ${TtlEcon.text(Number(rec.treasury || 0))}${Number(rec.owed) > 0 ? ` · OWES ${TtlEcon.text(Number(rec.owed))} upkeep` : ''}`)
    var allies = Object.keys(all).filter(k => self.allied(server, key, k)).map(k => all[k].name)
    var offers = (rec.ally_to || []).filter(k => all[k] && allies.indexOf(all[k].name) < 0).map(k => all[k].name)
    out.push(`  allies: ${allies.join(', ') || 'none'}${offers.length ? ` · offered to ${offers.join(', ')}` : ''}`)
    var wars = (rec.wars || []).filter(w => all[w.with]).map(w => `${all[w.with].name} (${Number(w.active_at) <= Date.now() ? 'active' : 'begins ' + new Date(Number(w.active_at)).toISOString()})`)
    out.push(`  wars: ${wars.join(', ') || 'none'}`)
    return out
  },

  // Nations by value, best first: ["Name · Rank · value n · members"].
  top(server) {
    var all = this.all(server)
    var self = this
    return Object.keys(all).sort((a, b) => Number(all[b].value || 0) - Number(all[a].value || 0)).map((k, i) => {
      var rec = all[k]
      return `${i + 1}. ${rec.name} · ${self.rankOf(rec).title} · value ${Math.round(Number(rec.value || 0))} · ${self.membersOf(k).length} members`
    })
  }
}

// A loop that stops when a newer one (after /reload) has taken over: the token lives in server persistentData.
ServerEvents.loaded(event => {
  var server = event.server
  var token = String(Date.now())
  server.persistentData.putString('ttl.nations.loop', token)
  var alive = () => String(server.persistentData.getString('ttl.nations.loop')) === token
  var r = TtlData.nations.rules
  try {
    TtlNations.ensureObjective(server)
  } catch (e) {
    console.error(`[ttl] nations: ${e}`)
  }
  var poll = () => server.scheduleInTicks(Number(r.poll_ticks), () => {
    if (!alive()) return
    try {
      TtlNations.syncAll(server)
    } catch (e) {
      console.error(`[ttl] nations: roster sync failed: ${e}`)
    }
    poll()
  })
  var values = () => server.scheduleInTicks(Number(r.value_ticks), () => {
    if (!alive()) return
    try {
      if (TtlNations.manager()) {
        var all = TtlNations.all(server)
        Object.keys(all).forEach(key => {
          try {
            TtlNations.upkeep(server, key)
            TtlNations.value(server, key)
          } catch (e) {
            console.error(`[ttl] nations: refreshing ${all[key].name} failed: ${e}`)
          }
        })
      }
    } catch (e) {
      console.error(`[ttl] nations: value refresh failed: ${e}`)
    }
    values()
  })
  poll()
  values()
})

// FTB Teams attaches the player to their party around login, so the first look waits a moment.
PlayerEvents.loggedIn(event => {
  var { player, server } = event
  server.scheduleInTicks(60, () => {
    try {
      TtlNations.syncPlayer(server, player)
    } catch (e) {
      console.error(`[ttl] nations: login sync for ${player.username} failed: ${e}`)
    }
  })
})
