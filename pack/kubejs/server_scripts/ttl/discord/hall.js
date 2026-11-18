// Hall of Souls and the leaderboard.
// - Notes (called from discord.js, roles.js, awaken.js): Life 1 deaths with the verdict, rebirths, Legends,
//   great foes slain, Great Sage awakenings, and each player's current life. Test bots never count.
// - Weekly recap: once a week (design/data/discord.toml [timing], Sunday 20:00 Europe/Brussels) a summary of
//   the week goes to #story as an sdlink CUSTOM message. The posted week is remembered, so it never posts
//   twice; while the bot is down it retries until the evening is over, then the week rolls into the next one.
// - Leaderboard: all-time records in one #leaderboard message that the bot edits in place (its id is kept in
//   server persistentData; a deleted message is posted again). Edited every few minutes and soon after a note.
// Server persistentData: ttl.hall.week (this week, JSON), ttl.hall.records (all time, JSON),
// ttl.hall.posted (date of the last recap), ttl.hall.lbmsg (leaderboard message id).
// Commands: /ttl top (everyone) · /ttl recap preview | now (ops; preview is also a staff ?command on Discord)
const TtlHall = {
  MAX: 50,
  dirty: true,
  lastText: '',
  lastEdit: 0,
  sending: false,
  pendingId: null,
  lost: false,

  conf() {
    return TtlData.discord
  },

  read(server, key, empty) {
    try {
      var raw = String(server.persistentData.getString(key))
      return raw ? JSON.parse(raw) : empty
    } catch (e) {
      console.warn(`[ttl] hall: ${key} unreadable, starting over (${e})`)
      return empty
    }
  },

  write(server, key, value) {
    server.persistentData.putString(key, JSON.stringify(value))
  },

  week(server) {
    var w = this.read(server, 'ttl.hall.week', null)
    if (!w) w = { start: Date.now() }
    ;['deaths', 'rebirths', 'legends', 'bosses', 'awakenings'].forEach(k => { if (!w[k]) w[k] = [] })
    return w
  },

  records(server) {
    var r = this.read(server, 'ttl.hall.records', {})
    if (!r.legends) r.legends = []
    if (!r.foes) r.foes = {}
    if (!r.races) r.races = {}
    if (!r.souls) r.souls = {}
    if (!r.awakenings) r.awakenings = []
    return r
  },

  push(list, item) {
    list.push(item)
    while (list.length > this.MAX) list.shift()
  },

  // One change to this week and/or the records, then the leaderboard is refreshed soon.
  update(server, fn) {
    var w = this.week(server)
    var r = this.records(server)
    fn(w, r)
    this.write(server, 'ttl.hall.week', w)
    this.write(server, 'ttl.hall.records', r)
    this.dirty = true
  },

  noteDeath(server, player) {
    var rec = TtlKarma.record(player)
    if (!rec) return
    var name = String(player.username)
    var title = TtlKarmaView.title(rec)
    this.update(server, (w, r) => {
      this.push(w.deaths, { n: name, days: rec.days || 0, score: rec.score || 0, title: title })
      if (!r.best || (rec.score || 0) > r.best.score) r.best = { n: name, score: rec.score || 0, title: title }
      if (!r.longest || (rec.days || 0) > r.longest.days) r.longest = { n: name, days: rec.days || 0 }
      r.souls[String(player.getStringUUID())] = { n: name, phase: 'corridor' }
    })
  },

  noteRebirth(server, player, race) {
    var name = String(player.username)
    var title = TtlKarmaView.title(TtlKarma.record(player))
    this.update(server, (w, r) => {
      this.push(w.rebirths, { n: name, race: race, title: title })
      r.races[race] = (r.races[race] || 0) + 1
      r.souls[String(player.getStringUUID())] = { n: name, phase: 'life2' }
    })
  },

  noteLegend(server, name, title) {
    this.update(server, (w, r) => {
      this.push(w.legends, { n: name, title: title })
      if (r.legends.indexOf(name) < 0) r.legends.push(name)
    })
  },

  noteBoss(server, name, label) {
    this.update(server, (w, r) => {
      this.push(w.bosses, { n: name, label: label })
      r.foes[name] = (r.foes[name] || 0) + 1
    })
  },

  noteAwakening(server, name, what) {
    this.update(server, (w, r) => {
      this.push(w.awakenings, { n: name, what: what })
      this.push(r.awakenings, { n: name, what: what })
    })
  },

  // Each player's current life, for "souls now" (offline players keep their last known life).
  noteSoul(server, player) {
    var name = String(player.username)
    if (TtlDiscord.isBot(name)) return
    var phase = TtlLife.phase(player)
    if (!phase) return
    var r = this.records(server)
    var id = String(player.getStringUUID())
    var old = r.souls[id]
    if (old && old.phase === phase && old.n === name) return
    r.souls[id] = { n: name, phase: phase }
    this.write(server, 'ttl.hall.records', r)
    this.dirty = true
  },

  // Europe/Brussels wall clock without java.time: CET, CEST from the last Sunday of March to the last
  // Sunday of October (01:00 UTC both ways).
  brussels(ms) {
    var now = new Date(ms)
    var y = now.getUTCFullYear()
    var lastSunday = month => {
      var last = new Date(Date.UTC(y, month + 1, 0))
      return Date.UTC(y, month, last.getUTCDate() - last.getUTCDay(), 1)
    }
    var summer = ms >= lastSunday(2) && ms < lastSunday(9)
    var d = new Date(ms + (summer ? 2 : 1) * 3600000)
    var pad = n => (n < 10 ? '0' : '') + n
    return {
      weekday: d.getUTCDay(),
      hour: d.getUTCHours(),
      date: `${pad(d.getUTCDate())}/${pad(d.getUTCMonth() + 1)}/${d.getUTCFullYear()}`,
      short: `${pad(d.getUTCDate())}/${pad(d.getUTCMonth() + 1)}`,
      time: `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}`
    }
  },

  plural(n, one, many) {
    return `${n} ${n === 1 ? one : many}`
  },

  section(lines, title, items, fmt) {
    if (!items.length) return
    var max = this.conf().limits.recap_lines
    lines.push(`**${title}** (${items.length})`)
    items.slice(-max).forEach(i => lines.push(`- ${fmt(i)}`))
    if (items.length > max) lines.push(`- …and ${items.length - max} more`)
  },

  recapText(server) {
    var w = this.week(server)
    var n = TtlDiscord.name.bind(TtlDiscord)
    var from = this.brussels(w.start || Date.now()).short
    var to = this.brussels(Date.now()).short
    var lines = [`## Hall of Souls · ${from} – ${to}`]
    this.section(lines, 'Reborn', w.rebirths, i => `${n(i.n)} as ${/^[aeiou]/i.test(i.race) ? 'an' : 'a'} **${i.race}** (${i.title})`)
    this.section(lines, 'Fell in their first life', w.deaths, i => `${n(i.n)} after ${this.plural(i.days, 'day', 'days')}, judged ${i.title}`)
    this.section(lines, 'Legends', w.legends, i => `${n(i.n)}, judged **${i.title}**`)
    this.section(lines, 'Great foes slain', w.bosses, i => `${n(i.n)} slew the ${i.label}`)
    this.section(lines, 'Awakenings', w.awakenings, i => `${n(i.n)}: ${i.what}`)
    var best = null
    w.deaths.forEach(d => { if (!best || d.score > best.score) best = d })
    if (best) lines.push(`**Brightest soul of the week:** ${n(best.n)}, karma ${best.score} (${best.title})`)
    if (lines.length === 1) lines.push('*A quiet week. No soul fell, none was reborn.*')
    return this.clip(lines.join('\n'))
  },

  clip(text) {
    return text.length > 1900 ? text.substring(0, 1890) + '\n…' : text
  },

  // Posts this week's recap and starts a new week. False when Discord is not reachable (nothing is reset).
  postRecap(server, key) {
    if (!TtlDiscord.post(server, this.recapText(server))) return false
    this.write(server, 'ttl.hall.week', { start: Date.now() })
    server.persistentData.putString('ttl.hall.posted', key)
    console.info(`[ttl] hall: weekly recap posted (${key})`)
    return true
  },

  checkRecap(server) {
    var t = this.conf().timing
    var now = this.brussels(Date.now())
    if (now.weekday !== t.recap_weekday || now.hour < t.recap_hour) return
    if (String(server.persistentData.getString('ttl.hall.posted')) === now.date) return
    this.postRecap(server, now.date)
  },

  // Standings as [label, value] rows, shared by #leaderboard and /ttl top. `md` bolds names for Discord.
  standings(server, md) {
    var r = this.records(server)
    var max = this.conf().limits.top_lines
    var n = md ? TtlDiscord.name.bind(TtlDiscord) : x => String(x)
    var top = (obj, fmt) => Object.keys(obj).sort((a, b) => obj[b] - obj[a]).slice(0, max).map(k => fmt(k, obj[k])).join(' · ')
    var counts = { life1: 0, corridor: 0, life2: 0 }
    Object.keys(r.souls).forEach(id => { if (counts[r.souls[id].phase] !== undefined) counts[r.souls[id].phase]++ })
    var rows = [
      ['Brightest soul ever', r.best ? `${n(r.best.n)}, karma ${r.best.score} (${r.best.title})` : 'nobody yet'],
      ['Longest first life', r.longest ? `${n(r.longest.n)}, ${this.plural(r.longest.days, 'day', 'days')}` : 'nobody yet'],
      [`Legends (${r.legends.length})`, r.legends.length ? r.legends.map(x => n(x)).join(', ') : 'none yet'],
      ['Great foes slain', Object.keys(r.foes).length ? top(r.foes, (k, v) => `${n(k)} ${v}`) : 'none yet'],
      ['Most chosen races', Object.keys(r.races).length ? top(r.races, (k, v) => `${k} ${v}`) : 'none yet'],
      ['Souls now', `Life 1: ${counts.life1} · Corridor: ${counts.corridor} · Life 2: ${counts.life2}`]
    ]
    if (r.awakenings.length) rows.push(['Awakenings', r.awakenings.slice(-max).map(a => `${n(a.n)} (${a.what})`).join(', ')])
    return rows
  },

  leaderboardText(server) {
    var body = ['## Two Lives · Leaderboard'].concat(this.standings(server, true).map(row => `**${row[0]}:** ${row[1]}`)).join('\n')
    return this.clip(body)
  },

  // Runs on the server thread. JDA callbacks only set fields that the next round picks up here.
  refreshLeaderboard(server, force) {
    if (this.pendingId) {
      server.persistentData.putString('ttl.hall.lbmsg', this.pendingId)
      this.pendingId = null
    }
    if (this.lost) {
      this.lost = false
      server.persistentData.remove('ttl.hall.lbmsg')
      this.lastText = ''
    }
    if (this.sending) return
    var period = Math.max(1, this.conf().timing.leaderboard_minutes) * 60000
    if (!force && !this.dirty && Date.now() - this.lastEdit < period) return
    var channel = TtlSdlink.channel('leaderboard')
    if (!channel) return
    var body = this.leaderboardText(server)
    this.dirty = false
    this.lastEdit = Date.now()
    if (body === this.lastText && !force) return
    var text = `${body}\n-# Updated ${this.brussels(Date.now()).short} ${this.brussels(Date.now()).time} (Brussels)`
    var id = String(server.persistentData.getString('ttl.hall.lbmsg'))
    var self = this
    this.sending = true
    this.lastText = body
    try {
      if (id) {
        channel.editMessageById(id, text).queue(() => { self.sending = false }, e => {
          self.sending = false
          self.lost = true
          TtlSdlink.warn('leaderboard edit (posting a new message)', e)
        })
      } else {
        channel.sendMessage(text).queue(msg => {
          self.pendingId = String(msg.getId())
          self.sending = false
        }, e => {
          self.sending = false
          self.lastText = ''
          TtlSdlink.warn('leaderboard post', e)
        })
      }
    } catch (e) {
      this.sending = false
      this.lastText = ''
      TtlSdlink.warn('leaderboard', e)
    }
  }
}

ServerEvents.loaded(event => {
  var server = event.server
  var loop = () => server.scheduleInTicks(600, () => {
    try {
      TtlHall.refreshLeaderboard(server, false)
    } catch (e) {
      console.error(`[ttl] hall: leaderboard failed: ${e}`)
    }
    try {
      TtlHall.checkRecap(server)
    } catch (e) {
      console.error(`[ttl] hall: recap check failed: ${e}`)
    }
    loop()
  })
  loop()
})

ServerEvents.commandRegistry(event => {
  var { commands: Commands } = event
  var logged = fn => ctx => {
    try {
      return fn(ctx)
    } catch (e) {
      console.error(`[ttl] hall command failed: ${e}`)
      ctx.source.sendSystemMessage(Text.red(`ttl: ${e}`))
      return 0
    }
  }
  // One message (Discord ?commands only relay the first message of a command).
  var top = ctx => {
    var text = Text.gold('Two Lives · standings')
    TtlHall.standings(ctx.source.getServer(), false).forEach(row => {
      text = text.append('\n').append(Text.yellow(`${row[0]}: `)).append(Text.white(row[1]))
    })
    ctx.source.sendSystemMessage(text)
    return 1
  }
  event.register(Commands.literal('ttl')
    .then(Commands.literal('top').executes(logged(top)))
    .then(Commands.literal('recap')
      .requires(src => src.hasPermission(2))
      .then(Commands.literal('preview').executes(logged(ctx => {
        var text = TtlHall.recapText(ctx.source.getServer())
        console.info(`[ttl] hall: recap preview\n${text}`)
        ctx.source.sendSystemMessage(Text.of(text))
        return 1
      })))
      .then(Commands.literal('now').executes(logged(ctx => {
        var server = ctx.source.getServer()
        var ok = TtlHall.postRecap(server, TtlHall.brussels(Date.now()).date)
        TtlHall.refreshLeaderboard(server, true)
        ctx.source.sendSystemMessage(ok ? Text.of('Recap posted to #story; a new week starts.') : Text.red('ttl: recap not posted, the Discord bot is not connected'))
        return ok ? 1 : 0
      })))))
})
