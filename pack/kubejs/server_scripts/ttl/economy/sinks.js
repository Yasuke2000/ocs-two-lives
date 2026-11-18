// priority: 70
// Coins and sinks (design/architecture/sprint3-4.md S7; numbers in design/data/economy.toml -> TtlData.economy).
// Money is Tensura's four coins (bronze < silver < gold < stellar), and since the owner decision of 18/11/2026 also
// Lightman's Currency's main chain (pack/config/lightmanscurrency/MasterCoinList.json) so that player shops and the
// Mana Ledger (ATM) count the same coins. The unit everywhere is the BRONZE COIN ("bronze"): 1 silver = 10, 1 gold = 100,
// 1 stellar = 1,000 with the default rates. A "coin table" is { silver = 3, bronze = 5 }.
//
// PUBLIC API (other packages call these; `player` is a ServerPlayer, `x` is a bronze number, a coin table or the name
// of a fee in [sinks], so `TtlEcon.charge(server, p, 'charter', 'nation charter')` works):
//   TtlEcon.amount(x)                 bronze worth of x
//   TtlEcon.text(x)                   "1 gold, 2 silver" for x
//   TtlEcon.balance(player)           bronze the player carries (inventory + equipped wallet through Lightman's Currency;
//                                     inventory only when its API is unreachable). NOT the bank account.
//   TtlEcon.canPay(player, x)         true when the player can pay x
//   TtlEcon.charge(server, p, x, why) takes x (change is returned); false and nothing taken when they cannot pay. A SINK.
//   TtlEcon.pay(server, p, x, why)    gives x. A FAUCET.
//   TtlEcon.fee(name)                 bronze worth of [sinks].<name>
//   TtlEcon.report(server)            this week's faucet/sink counters as text (for the staff channel)
// The weekly counters live in server persistentData `ttl.econ.mint` (JSON {week, faucet, sink, by, hist}); a new ISO
// week (Monday, UTC) archives the old one into `hist` (8 weeks) and logs one `[ttl] econ week ...` line.
const TtlEcon = {
  KEY: 'ttl.econ.mint',
  CHAIN: 'main',
  lc: undefined,
  warned: false,

  conf() {
    return TtlData.economy
  },

  chain() {
    return this.conf().coins.chain.map(c => String(c))
  },

  item(coin) {
    return String(this.conf().coins.item[coin])
  },

  // Worth of one coin in bronze: the product of the exchange rates up to it.
  worthOf(coin) {
    var chain = this.chain()
    var rates = this.conf().coins.rate
    var w = 1
    for (var i = 1; i <= chain.indexOf(coin); i++) w *= Number(rates[chain[i]])
    return w
  },

  amount(x) {
    if (typeof x === 'number') return Math.max(0, Math.floor(x))
    if (typeof x === 'string') return this.fee(x)
    var self = this
    var total = 0
    Object.keys(x).forEach(coin => {
      if (self.chain().indexOf(coin) < 0) throw `unknown coin ${coin}`
      total += self.worthOf(coin) * Number(x[coin])
    })
    return total
  },

  fee(name) {
    var table = this.conf().sinks[name]
    if (!table) throw `unknown fee ${name} (one of ${Object.keys(this.conf().sinks).join(', ')})`
    return this.amount(table)
  },

  // Highest coin first: 125 bronze -> { gold: 1, silver: 2, bronze: 5 }.
  split(n) {
    var out = {}
    var left = Math.max(0, Math.floor(n))
    var chain = this.chain().slice().reverse()
    for (var i = 0; i < chain.length; i++) {
      var w = this.worthOf(chain[i])
      var k = Math.floor(left / w)
      if (k > 0) out[chain[i]] = k
      left -= k * w
    }
    return out
  },

  // A coin table prints as written ("50 gold", not "5 stellar"); a number or fee name as the fewest coins.
  text(x) {
    var parts = typeof x === 'object' ? x : this.split(this.amount(x))
    var list = this.chain().slice().reverse().filter(c => parts[c]).map(c => `${parts[c]} ${c}`)
    return list.length > 0 ? list.join(', ') : '0'
  },

  // ---- Lightman's Currency bridge (verify in game: class and method names read from its 1.21-2.3.0.6 source) ----

  api() {
    if (this.lc !== undefined) return this.lc
    try {
      this.lc = {
        money: Java.loadClass('io.github.lightman314.lightmanscurrency.api.money.MoneyAPI'),
        coin: Java.loadClass('io.github.lightman314.lightmanscurrency.api.money.value.builtin.CoinValue')
      }
    } catch (e) {
      this.lc = null
      console.info(`[ttl] econ: Lightman's Currency API not reachable, counting coins in the inventory only (${e})`)
    }
    return this.lc
  },

  handler(player) {
    var api = this.api()
    if (!api) return null
    try {
      return api.money.getApi().GetPlayersMoneyHandler(player)
    } catch (e) {
      this.warnOnce(`money handler unavailable (${e})`)
      return null
    }
  },

  warnOnce(text) {
    if (this.warned) return
    this.warned = true
    console.warn(`[ttl] econ: ${text}; falling back to inventory coins`)
  },

  inventoryBalance(player) {
    var self = this
    var total = 0
    this.chain().forEach(coin => {
      total += Number(player.inventory.count(self.item(coin))) * self.worthOf(coin)
    })
    return total
  },

  balance(player) {
    var h = this.handler(player)
    if (h) {
      try {
        var all = h.getStoredMoney().allValues()
        var total = 0
        for (var i = 0; i < all.size(); i++) total += Number(all.get(i).getCoreValue())
        return total
      } catch (e) {
        this.warnOnce(`reading the stored money failed (${e})`)
      }
    }
    return this.inventoryBalance(player)
  },

  canPay(player, x) {
    var n = this.amount(x)
    if (n <= 0) return true
    var h = this.handler(player)
    if (h) {
      try {
        return h.extractMoney(this.api().coin.fromNumber(this.CHAIN, n), true).isEmpty()
      } catch (e) {
        this.warnOnce(`simulated extract failed (${e})`)
      }
    }
    return this.inventoryBalance(player) >= n
  },

  give(server, player, n) {
    var self = this
    var parts = this.split(n)
    Object.keys(parts).forEach(coin => {
      server.runCommandSilent(`give ${player.username} ${self.item(coin)} ${parts[coin]}`)
    })
  },

  charge(server, player, x, why) {
    var n = this.amount(x)
    if (n <= 0) return true
    if (!this.canPay(player, n)) return false
    var done = false
    var h = this.handler(player)
    if (h) {
      try {
        var left = h.extractMoney(this.api().coin.fromNumber(this.CHAIN, n), false)
        done = left.isEmpty()
        if (!done) console.error(`[ttl] econ: ${player.username} paid only part of ${n} (${left}) for ${why}`)
      } catch (e) {
        this.warnOnce(`extract failed (${e})`)
      }
    }
    if (!done) {
      // Inventory fallback: take every coin, hand back the change.
      var have = this.inventoryBalance(player)
      var self = this
      this.chain().forEach(coin => server.runCommandSilent(`clear ${player.username} ${self.item(coin)}`))
      this.give(server, player, have - n)
    }
    this.note(server, 'sink', n, why)
    return true
  },

  pay(server, player, x, why) {
    var n = this.amount(x)
    if (n <= 0) return 0
    var done = false
    var h = this.handler(player)
    if (h) {
      try {
        var left = h.insertMoney(this.api().coin.fromNumber(this.CHAIN, n), false)
        done = left.isEmpty()
        if (!done) this.give(server, player, Number(left.getCoreValue()))
        done = true
      } catch (e) {
        this.warnOnce(`insert failed (${e})`)
      }
    }
    if (!done) this.give(server, player, n)
    this.note(server, 'faucet', n, why)
    return n
  },

  // ---- weekly faucet / sink counters ----

  weekKey(date) {
    var d = date || new Date()
    var back = (d.getUTCDay() + 6) % 7
    return new Date(d.getTime() - back * 86400000).toISOString().slice(0, 10)
  },

  dayKey(date) {
    return (date || new Date()).toISOString().slice(0, 10)
  },

  load(server) {
    var raw = String(server.persistentData.getString(this.KEY) || '')
    var data = raw ? JSON.parse(raw) : { week: this.weekKey(), faucet: 0, sink: 0, by: {}, hist: [] }
    var week = this.weekKey()
    if (data.week !== week) {
      console.info(`[ttl] econ week ${data.week}: ${this.line(data)}`)
      data.hist.push({ week: data.week, faucet: data.faucet, sink: data.sink })
      data.hist = data.hist.slice(-8)
      data.week = week
      data.faucet = 0
      data.sink = 0
      data.by = {}
    }
    return data
  },

  save(server, data) {
    server.persistentData.putString(this.KEY, JSON.stringify(data))
  },

  note(server, kind, n, why) {
    try {
      var data = this.load(server)
      data[kind] += n
      var tag = `${kind}:${String(why || 'other').split(':')[0]}`
      data.by[tag] = (data.by[tag] || 0) + n
      this.save(server, data)
    } catch (e) {
      console.error(`[ttl] econ: counting ${kind} ${n} failed: ${e}`)
    }
  },

  line(data) {
    var pct = data.faucet > 0 ? Math.round((100 * data.sink) / data.faucet) : 100
    return `faucet ${data.faucet} bronze, sink ${data.sink} bronze, sinks are ${pct}% of faucets (target at least 80%)`
  },

  report(server) {
    var data = this.load(server)
    this.save(server, data)
    var by = Object.keys(data.by).sort().map(k => `${k}=${data.by[k]}`).join(' ') || 'nothing yet'
    var out = [`week ${data.week}: ${this.line(data)}`, `by reason: ${by}`]
    data.hist.slice().reverse().forEach(h => out.push(`week ${h.week}: faucet ${h.faucet}, sink ${h.sink}`))
    return out
  }
}
