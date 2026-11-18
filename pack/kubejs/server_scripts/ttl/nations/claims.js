// priority: 70
// Land of the nations (design/architecture/sprint3-4.md S4; numbers in design/data/nations.toml -> TtlData.nations).
// FTB Chunks does the claiming; this file reads it and sets the allowance:
//   - Claims exist only in minecraft:overworld (ftbchunks-world.snbt claim_dimension_whitelist), i.e. Life 2 only.
//   - party_limit_mode = "sum": the limit of a party is the sum of its members' limits, and a member's limit is
//     max_claimed_chunks (rules.base_chunks) + the member's personal "extra claim chunks". A nation member gets the extra
//     that brings them to rules.chunks_per_member + the rank's bonus; a player outside every nation gets 0 extra.
//     The extra is written with `ftbchunks admin extra_claim_chunks <player> set <n>` (it persists and recomputes the
//     party limit; it needs the player online, so a player who was offline when the rank changed is topped up at their
//     next poll). The value applied last is kept in player persistentData `ttl.nation.extra`.
//
// PUBLIC API (`team` is an FTB Teams Team, `player` a ServerPlayer):
//   TtlNationClaims.data(team)               FTB Chunks ChunkTeamData of the team, or null when FTB Chunks is unreachable
//   TtlNationClaims.count(team)              chunks the team has claimed (0 when unreachable)
//   TtlNationClaims.max(team)                the team's claim limit as FTB Chunks computes it, or -1
//   TtlNationClaims.keys(team)               ["<dimension>|<chunkX>,<chunkZ>"] of every claimed chunk (the merit.js key form)
//   TtlNationClaims.builds(server, team)     Public Works chunks (/ttl merit works mark) that lie inside the team's claims
//   TtlNationClaims.allowance(rank)          chunks one member brings at that rank: chunks_per_member + rank bonus
//   TtlNationClaims.apply(server, player, rank)   give the player the extra their nation rank calls for (null rank = none)
//   TtlNationClaims.extraOf(player)          the extra FTB Chunks reports for the player (-1 when unreachable)
//   TtlNationClaims.teamAt(server, dim, x, z)  the FTB team id that claimed the chunk at block x/z, or '' (absorb/liability.js,
//                                            nations/upkeep_debuff.js)
const TtlNationClaims = {
  mgr: undefined,
  warned: false,
  dimPos: undefined,

  conf() {
    return TtlData.nations
  },

  manager() {
    if (this.mgr !== undefined) return this.mgr
    try {
      var api = Java.loadClass('dev.ftb.mods.ftbchunks.api.FTBChunksAPI').api()
      this.mgr = api.isManagerLoaded() ? api.getManager() : undefined
    } catch (e) {
      this.mgr = null
      console.warn(`[ttl] nations: FTB Chunks API not reachable, claim counts read 0 (${e})`)
    }
    // The manager exists once a world is loaded; try again later instead of caching "not yet".
    return this.mgr === undefined ? null : this.mgr
  },

  data(team) {
    var m = this.manager()
    if (!m || !team) return null
    try {
      return m.getOrCreateData(team)
    } catch (e) {
      if (!this.warned) console.warn(`[ttl] nations: reading the claims of a team failed (${e})`)
      this.warned = true
      return null
    }
  },

  list(team) {
    var d = this.data(team)
    if (!d) return []
    var out = []
    var it = d.getClaimedChunks().iterator()
    while (it.hasNext()) out.push(it.next())
    return out
  },

  count(team) {
    var d = this.data(team)
    return d ? Number(d.getClaimedChunks().size()) : 0
  },

  max(team) {
    var d = this.data(team)
    return d ? Number(d.getMaxClaimChunks()) : -1
  },

  keys(team) {
    return this.list(team).map(c => {
      var pos = c.getPos()
      return `${String(pos.dimension().location())}|${Number(pos.x())},${Number(pos.z())}`
    })
  },

  builds(server, team) {
    try {
      if (typeof TtlMerit === 'undefined') return 0
      var works = TtlMerit.works(server)
      var mine = {}
      this.keys(team).forEach(k => { mine[k] = true })
      return Object.keys(works).filter(k => mine[k]).length
    } catch (e) {
      console.warn(`[ttl] nations: counting builds failed: ${e}`)
      return 0
    }
  },

  // A hash lookup in FTB Chunks' own map (ClaimedChunkManager.getChunk, verified with javap on 2101.1.24); cheap enough for
  // block events. ChunkDimPos(ResourceKey, int, int) is the only 3-argument constructor, so Rhino picks it unambiguously.
  teamAt(server, dim, x, z) {
    if (this.dimPos === null) return ''
    try {
      var m = this.manager()
      if (!m) return ''
      if (this.dimPos === undefined) {
        this.dimPos = Java.loadClass('dev.ftb.mods.ftblibrary.math.ChunkDimPos')
        this.resKey = Java.loadClass('net.minecraft.resources.ResourceKey')
        this.dimReg = Java.loadClass('net.minecraft.core.registries.Registries').DIMENSION
        this.resLoc = Java.loadClass('net.minecraft.resources.ResourceLocation')
        this.dimKeys = {}
      }
      // KubeJS shadows ServerLevel.dimension() with its `dimension` property (a ResourceLocation), so the key is built here.
      var d = String(dim)
      var key = this.dimKeys[d]
      if (!key) key = this.dimKeys[d] = this.resKey.create(this.dimReg, this.resLoc.parse(d))
      var c = m.getChunk(new this.dimPos(key, Math.floor(Number(x)) >> 4, Math.floor(Number(z)) >> 4))
      return c ? String(c.getTeamData().getTeam().getId()) : ''
    } catch (e) {
      if (!this.warned) console.warn(`[ttl] nations: reading the claim at ${dim} ${x} ${z} failed (${e})`)
      this.warned = true
      return ''
    }
  },

  allowance(rank) {
    var c = this.conf()
    return Number(c.rules.chunks_per_member) + (rank ? Number(rank.chunks) : 0)
  },

  extraOf(player) {
    var m = this.manager()
    if (!m) return -1
    try {
      var d = m.getPersonalData(Java.loadClass('java.util.UUID').fromString(TtlLife.uuid(player)))
      return d ? Number(d.getExtraClaimChunks()) : -1
    } catch (e) {
      return -1
    }
  },

  // Sets the player's personal extra to the nation allowance minus the base every soul has (0 outside a nation).
  // Only runs the FTB command when the value differs from what FTB Chunks reports, so the poll costs nothing.
  apply(server, player, rank) {
    var want = rank ? Math.max(0, this.allowance(rank) - Number(this.conf().rules.base_chunks)) : 0
    var have = this.extraOf(player)
    if (have < 0 || have === want) {
      player.persistentData.putInt('ttl.nation.extra', want)
      return want
    }
    // Through the dispatcher (TtlCmd.run), not runCommandSilent: reading FTB right after a runCommandSilent still saw the
    // old value, so `ttl.nation.extra` kept 0 while FTB had 8 and leaving the nation never took the 8 back (in game 18/11/2026).
    TtlCmd.run(server, `ftbchunks admin extra_claim_chunks ${player.username} set ${want}`)
    var now = this.extraOf(player)
    if (now !== want) {
      console.warn(`[ttl] nations: extra claim chunks of ${player.username} should be ${want} but FTB Chunks says ${now}`)
    } else {
      console.info(`[ttl] nations: ${player.username} extra claim chunks ${have} -> ${want}`)
    }
    // What we asked for, so clearMember takes it back later even when FTB had not caught up yet.
    player.persistentData.putInt('ttl.nation.extra', Math.max(want, now))
    return want
  }
}
