// priority: 70
// Story core (design/architecture/story-characters.md §2, §3; numbers and words: design/data/story.toml → TtlData.story).
// One main line in seven acts with one explicit choice, the Oath (light or dark), and one reversible twist per soul
// (Atonement / Corruption). Everything is a Life 2 thing: Life 1 souls and corridor souls have no story state.
//
// State (R3: truth in persistentData, mirrors for quests and Easy NPC conditions, always rewritten together by syncScoreboard):
//   player persistentData  ttl.story.path (light|dark), .oath (epoch ms), .flips (int), .acts (JSON {act: epoch}),
//                          .flags (JSON {flag: epoch}), .pending (path to apply at login; the party layer may write it)
//   stages                 ttl.path.light | ttl.path.dark (exactly one after the Oath), ttl.story.act<N>, ttl.story.<flag>
//   scoreboard ttl.path    0 none, 1 light, 2 dark
//   server persistentData  ttl.story.parties {teamId: {path, oathBy, at}}, ttl.story.log (ring), ttl.story.unlocked [boss ids]
//
// PUBLIC API (other packages call these; `player` is a ServerPlayer; errors are returned as a string, success as null):
//   TtlStory.path(player)                      'light' | 'dark' | ''
//   TtlStory.oath(server, player, choice, opts) swear the Oath: choice light | dark | unaligned (see story.toml [oath]); applies to
//                                              the online party when the party layer is present; also completes Act I
//   TtlStory.oathMenu(server, player)          opens the on-screen choice (chat buttons as a fallback)
//   TtlStory.flip(server, player)              Atonement (dark to light) or Corruption (light to dark), once per soul
//   TtlStory.act(server, player, n, opts)      complete act n: lane reputation, renown, stage, unlocked bosses, #story line
//   TtlStory.flag(server, player, id)          set a story flag (idempotent); TtlStory.unflag(...) removes it
//   TtlStory.hasFlag(player, id), TtlStory.actsDone(player) (highest completed act), TtlStory.currentAct(player)
//   TtlStory.talk(server, player, npcId)       prints what that NPC says to this soul now (the entry rules are in story.toml)
//   TtlStory.fight(server, player, bossId)     start a boss fight from the story: near the arena, through TtlBoss.summon
//   TtlStory.onBossKill(server, player, id)    the reputation / flag cost of killing that boss (kill_rep in bosses.toml); boss.js
//                                              `reward` (called by `finish` for every winner) calls it, guarded (WP-S3)
//   TtlStory.syncScoreboard(server, player)    rewrite scoreboard and stages from the stored truth (login, reset)
//   TtlStory.clear(server, player)             forget all story state (`/ttl reset`, `/ttl story reset`)
//   TtlStory.unlocked(server)                  boss ids unlocked by completed acts (server-wide)
// Optional party layer (WP-S2), every call guarded with typeof; without it a soul is a party of one:
//   TtlParty.membersOf(server, player)         array of the ONLINE ServerPlayers of the player's party, the player included
//   TtlParty.isOwner(server, player)           true when the player leads that party
//   TtlParty.teamId(server, player)            the FTB team id as a string
const TtlStory = {
  K_PATH: 'ttl.story.path',
  K_OATH: 'ttl.story.oath',
  K_FLIPS: 'ttl.story.flips',
  K_ACTS: 'ttl.story.acts',
  K_FLAGS: 'ttl.story.flags',
  K_PENDING: 'ttl.story.pending',
  PARTIES: 'ttl.story.parties',
  LOG: 'ttl.story.log',
  UNLOCKED: 'ttl.story.unlocked',
  BOARD: 'ttl.path',
  LANES: ['light', 'dark'],

  // ---- data ------------------------------------------------------------------------------------------------

  conf() {
    return TtlData.story
  },

  rules() {
    return TtlData.story.rules
  },

  acts() {
    return TtlData.story.act
  },

  actDef(n) {
    var all = this.acts()
    for (var i = 0; i < all.length; i++) {
      if (all[i].id === Number(n)) return all[i]
    }
    return null
  },

  flagDef(id) {
    return TtlData.story.flag[id] || null
  },

  npcDef(id) {
    var all = TtlData.story.npc
    for (var i = 0; i < all.length; i++) {
      if (all[i].id === id) return all[i]
    }
    return null
  },

  isLife2(player) {
    return TtlLife.phase(player) === 'life2'
  },

  // ---- storage ---------------------------------------------------------------------------------------------

  readJson(holder, key, fallback) {
    try {
      var raw = String(holder.getString(key))
      if (!raw) return fallback
      var parsed = JSON.parse(raw)
      return parsed && typeof parsed === 'object' ? parsed : fallback
    } catch (e) {
      console.error(`[ttl] story: ${key} is unreadable, treating it as empty: ${e}`)
      return fallback
    }
  },

  path(player) {
    var p = String(player.persistentData.getString(this.K_PATH))
    return this.LANES.indexOf(p) >= 0 ? p : ''
  },

  actsOf(player) {
    return this.readJson(player.persistentData, this.K_ACTS, {})
  },

  flagsOf(player) {
    return this.readJson(player.persistentData, this.K_FLAGS, {})
  },

  hasFlag(player, id) {
    return this.flagsOf(player)[id] !== undefined
  },

  hasAct(player, n) {
    return this.actsOf(player)[String(n)] !== undefined
  },

  // The highest completed act (0 when none); acts are sequential unless rules.sequential_acts is off.
  actsDone(player) {
    var acts = this.actsOf(player)
    var best = 0
    Object.keys(acts).forEach(k => {
      if (Number(k) > best) best = Number(k)
    })
    return best
  },

  // The act the soul is in: completed acts + 1, at most the last act.
  currentAct(player) {
    var last = this.acts().length
    var n = this.actsDone(player) + 1
    return n > last ? last : n
  },

  flips(player) {
    return Number(player.persistentData.getInt(this.K_FLIPS))
  },

  serverJson(server, key, fallback) {
    return this.readJson(server.persistentData, key, fallback)
  },

  unlocked(server) {
    var list = this.serverJson(server, this.UNLOCKED, [])
    return Array.isArray(list) ? list : []
  },

  // ---- log and announcements -------------------------------------------------------------------------------

  note(server, player, what) {
    try {
      var list = this.serverJson(server, this.LOG, [])
      if (!Array.isArray(list)) list = []
      list.push({ t: Date.now(), p: String(player.username), e: String(what) })
      var max = Number(this.rules().log_size)
      while (list.length > max) list.shift()
      var text = JSON.stringify(list)
      while (text.length > 60000 && list.length > 1) {
        list.shift()
        text = JSON.stringify(list)
      }
      server.persistentData.putString(this.LOG, text)
    } catch (e) {
      console.warn(`[ttl] story: could not write the log: ${e}`)
    }
    console.info(`[ttl] story: ${player.username} ${what}`)
  },

  // One #story line per story event (Discord); never for test bots.
  post(server, player, text) {
    try {
      if (!text || typeof TtlDiscord === 'undefined' || TtlDiscord.isBot(player.username)) return
      TtlDiscord.post(server, `${TtlDiscord.name(player.username)} ${text}`)
    } catch (e) {
      console.warn(`[ttl] story: #story post failed: ${e}`)
    }
  },

  voice(server, player, text) {
    try {
      TtlCorridor.voice(server, player.username, text)
    } catch (e) {
      player.tell(Text.gold(text))
    }
  },

  // ---- mirrors ---------------------------------------------------------------------------------------------

  ensure(server) {
    if (!server.getScoreboard().getObjective(this.BOARD)) server.runCommandSilent(`scoreboard objectives add ${this.BOARD} dummy`)
  },

  // Rewrites the scoreboard and every story stage from the stored truth.
  syncScoreboard(server, player) {
    var name = String(player.username)
    var path = this.path(player)
    this.LANES.forEach(l => {
      var stage = `ttl.path.${l}`
      if (l === path) {
        if (!player.stages.has(stage)) player.stages.add(stage)
      } else if (player.stages.has(stage)) {
        player.stages.remove(stage)
      }
    })
    this.ensure(server)
    server.runCommandSilent(`scoreboard players set ${name} ${this.BOARD} ${path === 'light' ? 1 : path === 'dark' ? 2 : 0}`)
    var acts = this.actsOf(player)
    this.acts().forEach(a => this.setStage(player, `ttl.story.act${a.id}`, acts[String(a.id)] !== undefined))
    var flags = this.flagsOf(player)
    Object.keys(TtlData.story.flag).forEach(id => this.setStage(player, `ttl.story.${id}`, flags[id] !== undefined))
  },

  setStage(player, stage, on) {
    var has = player.stages.has(stage)
    if (on && !has) player.stages.add(stage)
    if (!on && has) player.stages.remove(stage)
  },

  // ---- reputation, titles ----------------------------------------------------------------------------------

  rep(server, player, table, why) {
    if (typeof TtlRep === 'undefined') return
    Object.keys(table || {}).forEach(f => TtlRep.add(server, player, f, table[f], why))
  },

  repSet(server, player, table, why) {
    if (typeof TtlRep === 'undefined') return
    Object.keys(table || {}).forEach(f => TtlRep.set(server, player, f, table[f], why))
  },

  // Same comma-separated list as the Builder title (economy/merit.js).
  addTitle(player, title) {
    if (!title) return
    var raw = String(player.persistentData.getString('ttl.titles') || '')
    var list = raw ? raw.split(',') : []
    if (list.indexOf(title) >= 0) return
    list.push(title)
    player.persistentData.putString('ttl.titles', list.join(','))
  },

  renown(server, player, n, why) {
    if (n > 0 && typeof TtlRep !== 'undefined') TtlRep.addRenown(server, player, n, why)
  },

  // ---- party layer (optional) ------------------------------------------------------------------------------

  party(server, player) {
    try {
      if (typeof TtlParty === 'undefined' || typeof TtlParty.membersOf !== 'function') return null
      var raw = TtlParty.membersOf(server, player)
      var members = []
      if (raw) raw.forEach(m => members.push(m))
      if (members.length === 0) return null
      return {
        members: members,
        owner: typeof TtlParty.isOwner === 'function' ? !!TtlParty.isOwner(server, player) : true,
        id: typeof TtlParty.teamId === 'function' ? String(TtlParty.teamId(server, player)) : ''
      }
    } catch (e) {
      console.warn(`[ttl] story: the party layer failed, treating ${player.username} as alone: ${e}`)
      return null
    }
  },

  // ---- the Oath --------------------------------------------------------------------------------------------

  // On-screen choice. A Fallen soul (ttl.tier.dark) sees the dark choice first; a Legend-tier soul may get a third one.
  oathMenu(server, player) {
    var name = String(player.username)
    var err = this.oathGate(player)
    if (err) return err
    var oath = this.conf().oath
    var fallen = player.stages.has('ttl.tier.dark')
    var unaligned = oath.unaligned_for_legend && player.stages.has('ttl.tier.legendary')
    var lane = id => {
      var cfg = oath[id]
      var lore = TtlCorridor.wrap(cfg.lore, 34)
      if (id === 'dark' && fallen) lore = [cfg.remembers, ''].concat(lore)
      return { item: cfg.item, name: cfg.label, color: id === 'dark' ? '#B14DFF' : '#FFD966', lore: lore, command: `ttl story oath ${id}` }
    }
    var picks = fallen ? ['dark', 'light'] : ['light', 'dark']
    var items = picks.map(id => lane(id))
    if (unaligned) items.push({ item: 'minecraft:feather', name: 'Walk alone', color: '#CCCCCC', lore: TtlCorridor.wrap(`You answer to no side. For every gate you count as light, and the title ${oath.unaligned_title} is yours.`, 34), command: 'ttl story oath unaligned' })
    var slots = items.length === 2 ? [11, 15] : [10, 13, 16]
    items.forEach((it, i) => { it.slot = slots[i] })
    try {
      TtlCorridor.menu(server, player, oath.menu_title, 3, items, null)
      TtlCorridor.buttons(server, name, 'The crossroads waits. Choose your Oath.', [{ label: 'Open', command: '/ttl story oath', hover: 'Reopen the choice' }])
    } catch (e) {
      console.warn(`[ttl] story: Oath menu for ${name} failed, chat fallback: ${e}`)
      var buttons = picks.map(id => ({ label: oath[id].label, command: `/ttl story oath ${id}`, hover: oath[id].lore }))
      TtlCorridor.buttons(server, name, 'Choose your Oath.', buttons)
    }
    return null
  },

  // Why this soul cannot swear (null when it may).
  oathGate(player) {
    if (!this.isLife2(player)) return 'The Oath is sworn in the world of Tensura. Finish your rebirth first.'
    var have = this.path(player)
    if (have) return `You already swore the Oath of the ${have === 'dark' ? 'Dark' : 'Light'}. Only Atonement or Corruption can turn you.`
    var need = String(this.conf().oath.require_stage || '')
    if (need && !player.stages.has(need)) return 'You are not ready for the Oath yet.'
    return null
  },

  // choice: light | dark | unaligned. opts: {force: true} (ops: skips the leader and Legend checks), {by: name}.
  oath(server, player, choice, opts) {
    opts = opts || {}
    var oath = this.conf().oath
    choice = String(choice)
    if (choice !== 'light' && choice !== 'dark' && choice !== 'unaligned') return `unknown Oath ${choice} (light, dark${oath.unaligned_for_legend ? ' or unaligned' : ''})`
    if (choice === 'unaligned' && !opts.force && !(oath.unaligned_for_legend && player.stages.has('ttl.tier.legendary'))) return 'That Oath is not open to you.'
    var err = this.oathGate(player)
    if (err) return err
    var info = this.rules().party_oath ? this.party(server, player) : null
    if (info && !info.owner && !opts.force) return 'The Oath binds the whole party: ask your party leader to swear it.'
    var lane = choice === 'dark' ? 'dark' : 'light'
    var swearer = String(player.username)
    var members = [player]
    if (info) {
      members = []
      var seen = {}
      info.members.concat([player]).forEach(m => {
        var u = TtlLife.uuid(m)
        if (!seen[u]) {
          seen[u] = true
          members.push(m)
        }
      })
    }
    var sworn = 0
    members.forEach(m => {
      if (this.oathGate(m)) {
        this.note(server, m, `skipped the party Oath (${lane}): ${this.oathGate(m)}`)
        return
      }
      this.applyOath(server, m, choice, m === player ? 'oath' : `party oath of ${swearer}`)
      sworn++
    })
    if (info && info.id) {
      var parties = this.serverJson(server, this.PARTIES, {})
      parties[info.id] = { path: lane, oathBy: swearer, at: Date.now() }
      server.persistentData.putString(this.PARTIES, JSON.stringify(parties))
    }
    var cfg = oath[lane]
    this.post(server, player, `${cfg.line}${sworn > 1 ? ` (${sworn - 1} party member${sworn > 2 ? 's' : ''} swore with them.)` : ''}`)
    return null
  },

  // The Oath for one soul: path, mirrors, the lane's deltas, title, Act I.
  applyOath(server, player, choice, why) {
    var oath = this.conf().oath
    var lane = choice === 'dark' ? 'dark' : 'light'
    var cfg = oath[lane]
    var d = player.persistentData
    d.putString(this.K_PATH, lane)
    d.putString(this.K_OATH, String(Date.now()))
    d.remove(this.K_PENDING)
    this.syncScoreboard(server, player)
    this.rep(server, player, cfg.rep, `story oath ${lane}`)
    var title = cfg.title
    if (lane === 'light' && player.stages.has('ttl.tier.dark') && cfg.fallen_title) title = cfg.fallen_title
    if (choice === 'unaligned') {
      this.flag(server, player, 'unaligned', { quiet: true, anyPath: true })
      title = oath.unaligned_title
    }
    this.addTitle(player, title)
    this.voice(server, player, cfg.say)
    this.note(server, player, `swore the ${choice} Oath (${why})`)
    var first = this.act(server, player, 1, { quiet: true })
    if (first) console.warn(`[ttl] story: Act I for ${player.username} after the Oath: ${first}`)
  },

  // ---- flip ------------------------------------------------------------------------------------------------

  flip(server, player) {
    var flip = this.conf().flip
    if (!this.isLife2(player)) return 'Only a soul of the Tensura world can turn.'
    var have = this.path(player)
    if (!have) return 'You have not sworn the Oath yet.'
    if (this.flips(player) >= Number(flip.max)) return 'You have already turned once. A soul turns only once.'
    var cfg = have === 'dark' ? flip.atonement : flip.corruption
    var open = false
    cfg.requires_any.forEach(f => {
      if (this.hasFlag(player, f)) open = true
    })
    if (!open) return have === 'dark' ? 'Atonement is not open to you: finish the hand-ins first.' : 'Corruption is not open to you: no deed has made it yours.'
    var to = have === 'dark' ? 'light' : 'dark'
    player.persistentData.putString(this.K_PATH, to)
    player.persistentData.putInt(this.K_FLIPS, this.flips(player) + 1)
    this.syncScoreboard(server, player)
    this.repSet(server, player, cfg.set, `story ${have === 'dark' ? 'atonement' : 'corruption'}`)
    this.rep(server, player, cfg.rep, `story ${have === 'dark' ? 'atonement' : 'corruption'}`)
    this.addTitle(player, cfg.title)
    this.voice(server, player, cfg.say)
    this.note(server, player, `turned from ${have} to ${to}`)
    this.post(server, player, cfg.line)
    return null
  },

  // ---- acts, flags -----------------------------------------------------------------------------------------

  // opts: {force: true} (skip the sequence rule), {quiet: true} (no chat line, no #story line: the Oath says it).
  act(server, player, n, opts) {
    opts = opts || {}
    var def = this.actDef(n)
    if (!def) return `unknown act ${n} (1 to ${this.acts().length})`
    if (!this.isLife2(player)) return 'The story is told in the world of Tensura.'
    var path = this.path(player)
    if (!path) return 'Swear the Oath first.'
    if (this.hasAct(player, n)) return `act ${n} is already done`
    if (this.rules().sequential_acts && n > 1 && !opts.force && !this.hasAct(player, n - 1)) return `finish act ${n - 1} first`
    var acts = this.actsOf(player)
    acts[String(n)] = Date.now()
    player.persistentData.putString(this.K_ACTS, JSON.stringify(acts))
    this.syncScoreboard(server, player)
    this.rep(server, player, path === 'dark' ? def.dark_rep : def.light_rep, `story act ${n} ${path}`)
    this.renown(server, player, def.renown, `story act ${n}`)
    var list = this.unlocked(server)
    var added = []
    def.unlock_bosses.forEach(b => {
      if (list.indexOf(b) < 0) {
        list.push(b)
        added.push(b)
      }
    })
    if (added.length) server.persistentData.putString(this.UNLOCKED, JSON.stringify(list))
    this.note(server, player, `completed act ${n} (${def.key}, ${path})${added.length ? `, unlocked ${added.join(',')}` : ''}`)
    if (!opts.quiet) {
      player.tell(Text.gold(`Act ${n} complete: ${def.title}.`))
      this.post(server, player, def.story_line)
    }
    return null
  },

  // opts: {quiet: true} (no chat line), {anyPath: true} (skip the flag's `path` restriction: internal use).
  flag(server, player, id, opts) {
    opts = opts || {}
    var def = this.flagDef(id)
    if (!def) return `unknown flag ${id} (one of ${Object.keys(TtlData.story.flag).join(', ')})`
    if (!this.isLife2(player)) return 'The story is told in the world of Tensura.'
    if (def.path && !opts.anyPath && this.path(player) !== def.path) return `the flag ${id} belongs to the ${def.path} path`
    if (this.hasFlag(player, id)) return null
    var flags = this.flagsOf(player)
    flags[id] = Date.now()
    player.persistentData.putString(this.K_FLAGS, JSON.stringify(flags))
    this.syncScoreboard(server, player)
    this.rep(server, player, def.rep, `story flag ${id}`)
    this.renown(server, player, Number(def.renown || 0), `story flag ${id}`)
    this.addTitle(player, def.title)
    this.note(server, player, `flag ${id}`)
    if (!opts.quiet && def.title) player.tell(Text.gold(`You are now known as ${def.title}.`))
    this.post(server, player, def.line)
    return null
  },

  unflag(server, player, id) {
    if (!this.flagDef(id)) return `unknown flag ${id}`
    var flags = this.flagsOf(player)
    if (flags[id] === undefined) return null
    delete flags[id]
    player.persistentData.putString(this.K_FLAGS, JSON.stringify(flags))
    this.syncScoreboard(server, player)
    this.note(server, player, `flag ${id} removed`)
    return null
  },

  // ---- bosses ----------------------------------------------------------------------------------------------

  // The cost of one kill: the boss's `kill_rep` in bosses.toml (the only source; boss.js `reward` calls this for every
  // credited winner and applies nothing itself while the story core is loaded). Returns a short text of what changed
  // (empty: nothing).
  onBossKill(server, player, bossId) {
    var def = typeof TtlBoss !== 'undefined' && typeof TtlBoss.def === 'function' ? TtlBoss.def(bossId) : null
    var kill = def && def.kill_rep
    if (!kill) return ''
    if (kill.unless_flag && this.hasFlag(player, kill.unless_flag)) {
      this.unflag(server, player, kill.unless_flag)
      this.note(server, player, `killed ${bossId} under ${kill.unless_flag}: no cost`)
      return `no cost (${kill.unless_flag})`
    }
    var rep = {}
    Object.keys(kill).forEach(f => {
      if (f !== 'flag' && f !== 'unless_flag') rep[f] = kill[f]
    })
    this.rep(server, player, rep, `story kill ${bossId}`)
    if (kill.flag) {
      var err = this.flag(server, player, kill.flag, { anyPath: true })
      if (err) console.warn(`[ttl] story: kill flag ${kill.flag} for ${player.username} (${bossId}): ${err}`)
    }
    this.note(server, player, `killed ${bossId}: ${JSON.stringify(rep)}${kill.flag ? ` flag ${kill.flag}` : ''}`)
    return JSON.stringify(rep)
  },

  // `/ttl story fight <id>`: a soul in Life 2 standing near the boss's arena starts the fight (cooldown and `requires` are
  // TtlBoss.summon's own rules; opts.force, ops only, skips the distance and arena check). Fights are path-free.
  fight(server, player, bossId, opts) {
    opts = opts || {}
    if (typeof TtlBoss === 'undefined' || typeof TtlBoss.summon !== 'function') return 'The boss framework is not loaded.'
    if (!this.isLife2(player)) return 'Bosses wait in the world of Tensura.'
    var def = TtlBoss.def(bossId)
    if (!def) return `unknown boss ${bossId}`
    var dim = String(player.level.dimension)
    var here = { dim: dim, x: player.getX(), y: player.getY(), z: player.getZ() }
    var near = Number(this.rules().fight_near)
    var spot = TtlBoss.arenaOf(server, def, {})
    if (typeof spot === 'string' && !opts.force) return `${def.title} has no place to be fought from a command: ${spot}`
    if (typeof spot !== 'string' && !opts.force) {
      var dx = here.x - spot.x
      var dz = here.z - spot.z
      if (here.dim !== spot.dim || Math.sqrt(dx * dx + dz * dz) > near) return `${def.title} waits near ${spot.x} ${spot.z}. Go there first.`
    }
    var error = TtlBoss.summon(server, bossId, { summoner: player, by: String(player.username), at: here })
    if (error) return error
    this.note(server, player, `starts the fight ${bossId}`)
    return null
  },

  // ---- talk ------------------------------------------------------------------------------------------------

  // The entry that answers this soul now (see the rules at the top of the [[npc]] section in story.toml), or null.
  pick(player, npc) {
    var path = this.path(player)
    var current = this.currentAct(player)
    var best = null
    var bestRank = null
    npc.talk.forEach((t, i) => {
      var tp = t.path || 'any'
      if (tp !== 'any' && tp !== path) return
      var from = t.act === undefined ? 1 : t.act
      if (current < from) return
      if (t.until_act !== undefined && current > t.until_act) return
      if (t.faction) {
        if (typeof TtlRep === 'undefined') return
        var band = TtlRep.band(player, t.faction)
        if (t.at_most && TtlRep.rank(band) > TtlRep.rank(t.at_most)) return
        if (t.at_least && TtlRep.rank(band) < TtlRep.rank(t.at_least)) return
      }
      var rank = [tp === 'any' ? 0 : 1, from, t.faction ? 1 : 0, i]
      if (bestRank === null || this.later(rank, bestRank)) {
        best = t
        bestRank = rank
      }
    })
    return best
  },

  later(a, b) {
    for (var i = 0; i < a.length; i++) {
      if (a[i] !== b[i]) return a[i] > b[i]
    }
    return false
  },

  talk(server, player, npcId) {
    var npc = this.npcDef(npcId)
    if (!npc) return `nobody called ${npcId} has anything to say (${TtlData.story.npc.map(n => n.id).join(', ')})`
    if (!this.isLife2(player)) return 'Nobody answers.'
    var entry = this.pick(player, npc)
    var name = String(player.username)
    if (!entry) {
      player.tell(Text.gray(`${npc.name} has nothing to say to you.`))
      return null
    }
    server.runCommandSilent(`tellraw ${name} ${JSON.stringify([{ text: `<${npc.name}> `, color: npc.color || 'gold' }, { text: entry.text, color: 'white' }])}`)
    if (entry.buttons && entry.buttons.length) {
      var line = []
      entry.buttons.forEach(b => line.push({
        text: `[${b.label}]`, color: 'aqua',
        clickEvent: { action: 'run_command', value: `/${b.command}` },
        hoverEvent: { action: 'show_text', contents: b.label }
      }, ' '))
      server.runCommandSilent(`tellraw ${name} ${JSON.stringify(line)}`)
    }
    return null
  },

  // ---- login, reset, status --------------------------------------------------------------------------------

  // A soul without a path takes the one waiting for it: ttl.story.pending (the party layer), else its party's recorded path.
  onLogin(server, player) {
    if (!this.isLife2(player)) return
    if (!this.path(player)) {
      var want = String(player.persistentData.getString(this.K_PENDING))
      var why = 'pending at login'
      if (!want && this.rules().party_oath) {
        var info = this.party(server, player)
        var rec = info && info.id ? this.serverJson(server, this.PARTIES, {})[info.id] : null
        if (rec && this.LANES.indexOf(rec.path) >= 0) {
          want = rec.path
          why = `party path of ${rec.oathBy}`
        }
      }
      if (this.LANES.indexOf(want) >= 0) this.applyOath(server, player, want, why)
    }
    this.syncScoreboard(server, player)
  },

  clear(server, player) {
    var d = player.persistentData
    ;[this.K_PATH, this.K_OATH, this.K_FLIPS, this.K_ACTS, this.K_FLAGS, this.K_PENDING].forEach(k => d.remove(k))
    this.syncScoreboard(server, player)
    // The titles this system gave belong to the story that is being erased.
    var mine = ['Marked', 'Repentant', 'True Hero', 'Demon Lord', String(this.conf().oath.unaligned_title)]
    var raw = String(d.getString('ttl.titles') || '')
    if (raw) {
      var keep = raw.split(',').filter(t => mine.indexOf(t) < 0)
      if (keep.length) d.putString('ttl.titles', keep.join(','))
      else d.remove('ttl.titles')
    }
  },

  lines(player) {
    var path = this.path(player)
    var done = Object.keys(this.actsOf(player)).map(Number).sort((a, b) => a - b)
    var flags = Object.keys(this.flagsOf(player)).sort()
    var out = [`Path: ${path || 'none yet (the Oath is sworn at Tempest)'}${this.flips(player) ? ' (turned once)' : ''}`]
    out.push(`Acts done: ${done.length ? done.join(', ') : 'none'} · now in act ${this.currentAct(player)}: ${this.actDef(this.currentAct(player)).title}`)
    if (flags.length) out.push(`Marks: ${flags.join(', ')}`)
    return out
  }
}

ServerEvents.loaded(event => {
  try {
    TtlStory.ensure(event.server)
  } catch (e) {
    console.error(`[ttl] story: creating the scoreboard failed: ${e}`)
  }
})

// The story mirrors are rewritten at login here (the doc reserved a line in karma.js, which has no login hook).
PlayerEvents.loggedIn(event => {
  var { player, server } = event
  try {
    TtlStory.onLogin(server, player)
  } catch (e) {
    console.error(`[ttl] story: login sync for ${player.username} failed: ${e}`)
  }
})
