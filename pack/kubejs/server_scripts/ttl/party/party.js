// priority: 70
// Party layer (design/architecture/story-characters.md §4, WP-S2). A party is an FTB Teams party team (FTB Teams 2101.1.12);
// this file is the ONE place that reads it for the rest of the pack (story.js for the Oath, boss.js for shared boss credit).
// Creating, inviting, joining and leaving stay FTB's own (`/ftbteams party ...` or the sidebar button of the quest book).
//
// PUBLIC API (`player` is a ServerPlayer; a soul that is in no party is a party of one):
//   TtlParty.membersOf(server, player)   array of the ONLINE ServerPlayers of the player's party, the player included
//   TtlParty.isOwner(server, player)     true when the player leads the party (also true when alone)
//   TtlParty.teamId(server, player)      the FTB team id as a string, '' when the player is in no party (a solo soul has
//                                        only a personal team, and story.js keeps party records per party id)
//   TtlParty.partyOf(server, player)     {id, owner, members: [lowercase uuids, offline ones too]} or null (what boss.js snapshots)
//   TtlParty.partyPath(server, info, except)   {path, by} the party's Oath path or null while undecided
//   TtlParty.cap()                       the party size cap FTB enforces (`max_party_size` in config/ftbteams-server.snbt), 0 = none
//   TtlParty.enforce(server)             one pass of the join lock (the poll runs it; `/ttl party poll` for ops)
//
// Path lock (§4.2, owner decision O2 = per party). A member the pass has not seen in that party yet is "joining":
//   - the party has an Oath path (recorded by TtlStory.oath in ttl.story.parties, else the owner's, else the first sworn
//     member's) and the joiner swore the OTHER one: the joiner is removed again with a Voice line (Atonement / Corruption
//     are the only way a soul turns, and a turned soul stays in the party it is already in: only NEW members are checked);
//   - the joiner has no path: they take the party's (ttl.story.pending + TtlStory.onLogin, the story core's own login route);
//   - the party has no path yet and the joiner has one: it becomes the party's (the record is written; the first Oath wins).
// A soul that is not in Life 2 yet is not checked until it is (a Life 1 soul has no story state). Test bots count like players.
//
// Why a poll and not PlayerJoinedPartyTeamEvent: FTB's events are Architectury `Event<Consumer<...>>` whose register(T) erases
// to Object, which Rhino cannot fill with a script function, and a listener cannot be unregistered by a script reload. The
// poll (every POLL_TICKS) reads the same API, is idempotent and survives /reload (stamped loop at the bottom).
// Roster memory: server persistentData ttl.party.roster = {teamId: [uuids the lock has already accepted]}.
const TtlParty = {
  K_ROSTER: 'ttl.party.roster',
  POLL_TICKS: 60,
  LANES: ['light', 'dark'],

  // ---- FTB Teams ---------------------------------------------------------------------------------------------

  ftb() {
    if (this.teamApi === undefined) {
      try {
        this.teamApi = Java.loadClass('dev.ftb.mods.ftbteams.api.FTBTeamsAPI')
      } catch (e) {
        this.teamApi = null
        console.warn(`[ttl] party: FTB Teams API not available, every soul is a party of one: ${e}`)
      }
    }
    return this.teamApi
  },

  manager() {
    var cls = this.ftb()
    if (!cls) return null
    try {
      var api = cls.api()
      return api.isManagerLoaded() ? api.getManager() : null
    } catch (e) {
      console.warn(`[ttl] party: FTB team manager unavailable: ${e}`)
      return null
    }
  },

  uid(player) {
    return TtlLife.uuid(player).toLowerCase()
  },

  // The party team a player is in, or null (a player alone stands in a personal team, which is not a party).
  teamOf(server, player) {
    var mgr = this.manager()
    if (!mgr) return null
    try {
      var opt = mgr.getTeamForPlayer(player)
      if (!opt.isPresent()) return null
      var team = opt.get()
      return team.isPartyTeam() ? team : null
    } catch (e) {
      console.warn(`[ttl] party: reading the FTB party of ${player.username} failed: ${e}`)
      return null
    }
  },

  // {team, id, owner, members} for a player in a party, else null. members = every member's lowercase uuid, offline too.
  info(server, player) {
    var team = this.teamOf(server, player)
    if (!team) return null
    try {
      var members = []
      var arr = team.getMembers().toArray()
      for (var i = 0; i < arr.length; i++) members.push(String(arr[i]).toLowerCase())
      return { team: team, id: String(team.getId()), owner: String(team.getOwner()).toLowerCase(), members: members }
    } catch (e) {
      console.warn(`[ttl] party: reading the members of ${player.username}'s party failed: ${e}`)
      return null
    }
  },

  partyOf(server, player) {
    var info = this.info(server, player)
    return info ? { id: info.id, owner: info.owner, members: info.members } : null
  },

  online(server) {
    var out = []
    var arr = server.getPlayerList().getPlayers().toArray()
    for (var i = 0; i < arr.length; i++) out.push(arr[i])
    return out
  },

  membersOf(server, player) {
    var self = this.uid(player)
    var out = []
    var info = this.info(server, player)
    if (info) {
      var all = this.online(server)
      for (var i = 0; i < all.length; i++) {
        if (info.members.indexOf(this.uid(all[i])) >= 0) out.push(all[i])
      }
    }
    var has = false
    for (var j = 0; j < out.length; j++) {
      if (this.uid(out[j]) === self) has = true
    }
    if (!has) out.unshift(player)
    return out
  },

  isOwner(server, player) {
    var info = this.info(server, player)
    return info ? info.owner === this.uid(player) : true
  },

  teamId(server, player) {
    var info = this.info(server, player)
    return info ? info.id : ''
  },

  // FTB's own `max_party_size` (0 = unlimited); -1 when the config cannot be read.
  cap() {
    try {
      var cfg = Java.loadClass('dev.ftb.mods.ftbteams.config.ServerConfig')
      return Number(cfg.MAX_TEAM_SIZE.get())
    } catch (e) {
      console.warn(`[ttl] party: could not read FTB's max_party_size: ${e}`)
      return -1
    }
  },

  // ---- the party's Oath path ---------------------------------------------------------------------------------

  story() {
    return typeof TtlStory !== 'undefined' && typeof TtlStory.path === 'function'
  },

  records(server) {
    return TtlStory.serverJson(server, TtlStory.PARTIES, {})
  },

  // {path, by, recorded} or null. Order: the record TtlStory.oath wrote, else the owner's path, else the first sworn online
  // member (the one named `except` is the soul being checked and never decides for the party).
  partyPath(server, info, except) {
    if (!this.story() || !info) return null
    var rec = this.records(server)[info.id]
    if (rec && this.LANES.indexOf(rec.path) >= 0) return { path: rec.path, by: String(rec.oathBy || ''), recorded: true }
    var skip = except ? this.uid(except) : ''
    var all = this.online(server)
    var order = []
    for (var i = 0; i < all.length; i++) {
      var u = this.uid(all[i])
      if (u === skip || info.members.indexOf(u) < 0 || TtlLife.phase(all[i]) !== 'life2') continue
      if (u === info.owner) order.unshift(all[i])
      else order.push(all[i])
    }
    for (var k = 0; k < order.length; k++) {
      var path = TtlStory.path(order[k])
      if (path) return { path: path, by: String(order[k].username), recorded: false }
    }
    return null
  },

  writeRecord(server, info, path, by) {
    var parties = this.records(server)
    parties[info.id] = { path: path, oathBy: by, at: Date.now() }
    server.persistentData.putString(TtlStory.PARTIES, JSON.stringify(parties))
  },

  // ---- removing a member -------------------------------------------------------------------------------------

  // Takes `player` out of their party. Three routes, each verified by looking at the party again: FTB's own forced kick
  // (what limited lives use; no command source needed), the member leaving, the owner kicking by command (owner online only).
  remove(server, player, info) {
    var gone = () => {
      var now = this.info(server, player)
      return !now || now.id !== info.id
    }
    try {
      info.team.kickPlayerForcibly(player)
      if (gone()) return true
    } catch (e) {
      console.warn(`[ttl] party: forced kick of ${player.username} failed: ${e}`)
    }
    try {
      info.team.leave(Java.loadClass('java.util.UUID').fromString(TtlLife.uuid(player)))
      if (gone()) return true
    } catch (e) {
      console.warn(`[ttl] party: leave for ${player.username} failed: ${e}`)
    }
    var owner = null
    var all = this.online(server)
    for (var i = 0; i < all.length; i++) {
      if (this.uid(all[i]) === info.owner) owner = all[i]
    }
    if (owner) TtlCmd.runAs(owner, `ftbteams party kick ${player.username}`)
    return gone()
  },

  tellParty(server, info, text, except) {
    var skip = except ? this.uid(except) : ''
    var all = this.online(server)
    for (var i = 0; i < all.length; i++) {
      var u = this.uid(all[i])
      if (u !== skip && info.members.indexOf(u) >= 0) all[i].tell(Text.gold(text))
    }
  },

  laneName(path) {
    return path === 'dark' ? 'Dark' : 'Light'
  },

  // ---- the join lock -----------------------------------------------------------------------------------------

  // Checks one soul that the pass has not accepted in its party yet. Returns 'ok' | 'inherited' | 'recorded' | 'kicked' |
  // 'failed' | 'gone' (no longer in a party). The party is read again each time, so a kick earlier in the pass is seen.
  admit(server, player) {
    var info = this.info(server, player)
    if (!info) return 'gone'
    var name = String(player.username)
    var mine = TtlStory.path(player)
    var party = this.partyPath(server, info, player)
    if (mine && party && mine !== party.path) {
      if (!this.remove(server, player, info)) {
        console.error(`[ttl] party: ${name} (${mine}) does not match their party (${party.path}) but could not be removed`)
        return 'failed'
      }
      TtlStory.voice(server, player, `You swore the Oath of the ${this.laneName(mine)}, and that party walks the ${this.laneName(party.path)} road. One party, one Oath: you were turned away. Only Atonement or Corruption can turn a soul.`)
      this.tellParty(server, info, `${name} was turned away: their Oath does not match your party's (${party.path}).`, player)
      TtlStory.note(server, player, `turned away from the party of ${party.by || 'its leader'} (${mine} against ${party.path})`)
      return 'kicked'
    }
    if (!mine && party) {
      player.persistentData.putString(TtlStory.K_PENDING, party.path)
      TtlStory.onLogin(server, player)
      if (TtlStory.path(player) !== party.path) {
        console.warn(`[ttl] party: ${name} could not take the party's ${party.path} Oath`)
        return 'failed'
      }
      TtlStory.note(server, player, `joined the party of ${party.by || 'its leader'} and took the ${party.path} Oath`)
      return 'inherited'
    }
    if (mine && !party) {
      this.writeRecord(server, info, mine, name)
      TtlStory.note(server, player, `the ${mine} Oath became their party's (first Oath in it)`)
      return 'recorded'
    }
    return 'ok'
  },

  loadRoster(server) {
    try {
      var raw = String(server.persistentData.getString(this.K_ROSTER) || '')
      var r = raw ? JSON.parse(raw) : {}
      return r && typeof r === 'object' && !Array.isArray(r) ? r : {}
    } catch (e) {
      console.error(`[ttl] party: ${this.K_ROSTER} is unreadable, starting empty: ${e}`)
      return {}
    }
  },

  // One pass over every online soul that is in a party. Returns {checked, kicked, inherited, recorded}.
  enforce(server) {
    var out = { checked: 0, kicked: 0, inherited: 0, recorded: 0 }
    if (!this.story()) return out
    var roster = this.loadRoster(server)
    var teams = {}
    var all = this.online(server)
    for (var i = 0; i < all.length; i++) {
      var info = this.info(server, all[i])
      if (!info) continue
      if (!teams[info.id]) teams[info.id] = { info: info, online: [] }
      teams[info.id].online.push(all[i])
    }
    var before = JSON.stringify(roster)
    var ids = Object.keys(teams)
    for (var t = 0; t < ids.length; t++) {
      var id = ids[t]
      var entry = teams[id]
      // Members who left are forgotten, so a soul that comes back is checked again.
      var known = (roster[id] || []).filter(u => entry.info.members.indexOf(u) >= 0)
      var fresh = entry.online.filter(p => known.indexOf(this.uid(p)) < 0)
      fresh.sort((a, b) => (this.uid(b) === entry.info.owner ? 1 : 0) - (this.uid(a) === entry.info.owner ? 1 : 0))
      for (var f = 0; f < fresh.length; f++) {
        var p = fresh[f]
        // A Life 1 or corridor soul has no story state: checked once it reaches Life 2.
        if (TtlLife.phase(p) !== 'life2') continue
        var result = 'failed'
        try {
          result = this.admit(server, p)
        } catch (e) {
          console.error(`[ttl] party: checking ${p.username} failed: ${e}`)
        }
        out.checked++
        if (result === 'kicked') out.kicked++
        else if (result === 'inherited') out.inherited++
        else if (result === 'recorded') out.recorded++
        if (result === 'failed') {
          // Three tries (a pass every POLL_TICKS), then the soul is left alone instead of spamming the log forever.
          this.tries = this.tries || {}
          var tk = id + ':' + this.uid(p)
          this.tries[tk] = (this.tries[tk] || 0) + 1
          if (this.tries[tk] >= 3) {
            console.error(`[ttl] party: giving up on ${p.username} in party ${id} after ${this.tries[tk]} tries (an operator must fix it)`)
            delete this.tries[tk]
            known.push(this.uid(p))
          }
        } else if (result === 'ok' || result === 'inherited' || result === 'recorded') {
          known.push(this.uid(p))
        }
      }
      roster[id] = known
    }
    // Parties nobody is online in stay as they were while they exist; deleted teams and teams that stopped being parties go.
    var mgr = this.manager()
    Object.keys(roster).forEach(id => {
      if (teams[id] || !mgr) return
      try {
        var opt = mgr.getTeamByID(Java.loadClass('java.util.UUID').fromString(id))
        if (!opt.isPresent() || !opt.get().isPartyTeam()) delete roster[id]
      } catch (e) {
        delete roster[id]
      }
    })
    var text = JSON.stringify(roster)
    if (text !== before) server.persistentData.putString(this.K_ROSTER, text)
    if (out.kicked || out.inherited || out.recorded) console.info(`[ttl] party: pass checked ${out.checked}, turned away ${out.kicked}, took the party's Oath ${out.inherited}, set the party's Oath ${out.recorded}`)
    return out
  },

  // ---- what /ttl party prints -------------------------------------------------------------------------------

  lines(server, player) {
    var info = this.info(server, player)
    var cap = this.cap()
    if (!info) {
      return ['Party: none. You adventure alone (a party of one).', 'Make one with the FTB Teams button of the quest book or /ftbteams party create <name>.', `Party size cap: ${cap > 0 ? cap : 'none'}`]
    }
    var online = this.membersOf(server, player)
    var names = online.map(m => String(m.username))
    var offline = info.members.length - online.length
    var teamName = info.id
    try {
      teamName = String(info.team.getName().getString())
    } catch (e) {
      // the id is a fine name
    }
    var out = [`Party: ${teamName}`]
    var leader = info.owner === this.uid(player) ? 'you' : null
    for (var i = 0; i < online.length; i++) {
      if (this.uid(online[i]) === info.owner) leader = String(online[i].username)
    }
    out.push(`Leader: ${leader || 'offline'}`)
    out.push(`Members: ${info.members.length}${cap > 0 ? '/' + cap : ''} (online: ${names.join(', ')}${offline > 0 ? '; offline: ' + offline : ''})`)
    var party = this.partyPath(server, info, null)
    out.push(party ? `Oath: ${party.path}${party.by ? ' (sworn by ' + party.by + ')' : ''}. A soul with the other path is turned away.` : 'Oath: not sworn yet. The leader swears it for the whole party (/ttl story oath).')
    try {
      if (typeof TtlBoss !== 'undefined') {
        var c = TtlBoss.conf()
        out.push(`Boss credit: online party members within ${c.partyRange} x the boss's range share the kill; at most ${c.corePerParty} of them also get the Skill Core.`)
      }
    } catch (e) {
      // the boss framework is optional here
    }
    return out
  }
}

ServerEvents.loaded(event => {
  var server = event.server
  // A script reload runs this again; the stamp makes the older loop stop instead of doubling up.
  var stamp = String(Date.now())
  server.persistentData.putString('ttl.party.loop', stamp)
  var poll = () => server.scheduleInTicks(TtlParty.POLL_TICKS, () => {
    if (String(server.persistentData.getString('ttl.party.loop')) !== stamp) return
    try {
      TtlParty.enforce(server)
    } catch (e) {
      console.error(`[ttl] party: pass failed: ${e}`)
    }
    poll()
  })
  poll()
})
