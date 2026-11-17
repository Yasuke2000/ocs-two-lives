// The Voice of the World in the Spirit Corridor hall: a floating, glowing allay just south of the arrival point
// (souls arrive at 0.5 65 0.5 facing south, so it is the first thing they see; the pedestals stand at radius 11.5).
// Right-click → ttl-portals (guide/VoiceNpc.java) runs `/ttl talk` as the player (guide.js): the current Corridor
// step, or the guide outside the Corridor. The mod also cancels its own allay interaction and all damage except
// /kill and the void. NoAI, Silent, persistent; team ttl.voice gives the aqua glow and keeps it from being pushed.
// L2 Hostility only levels hostile mobs (and the allay is on its blacklist tag too).
// Checked every 30 s and on start: summoned again when missing. Bump TTL_VOICE_NPC_VERSION after changing
// POS or the NBT to replace it on the next start.
const TTL_VOICE_NPC_VERSION = 1

const TtlVoiceNpc = {
  TAG: 'ttl.voice_npc',
  TEAM: 'ttl.voice',
  POS: '0.5 65.6 6.5',
  // Facing north, towards the arrival point.
  NBT: '{NoAI:1b,NoGravity:1b,Invulnerable:1b,Silent:1b,PersistenceRequired:1b,Glowing:1b,CanPickUpLoot:0b,' +
    'CustomNameVisible:1b,CustomName:\'{"text":"Voice of the World","color":"aqua"}\',Tags:["ttl.voice_npc"],' +
    'Rotation:[180f,0f],attributes:[{id:"minecraft:generic.scale",base:1.8d}]}',

  find(server) {
    var found = []
    var tag = this.TAG
    server.getLevel(TtlLife.CORRIDOR).getEntities().forEach(e => {
      if (e.isAlive() && e.getTags().contains(tag)) found.push(e)
    })
    return found
  },

  team(server) {
    server.runCommandSilent(`team add ${this.TEAM}`)
    server.runCommandSilent(`team modify ${this.TEAM} color aqua`)
    server.runCommandSilent(`team modify ${this.TEAM} collisionRule never`)
  },

  summon(server) {
    server.runCommandSilent(`execute in ${TtlLife.CORRIDOR} run summon minecraft:allay ${this.POS} ${this.NBT}`)
    server.runCommandSilent(`team join ${this.TEAM} @e[tag=${this.TAG}]`)
  },

  // Exactly one NPC: summons it when missing, removes duplicates.
  ensure(server) {
    var found = this.find(server)
    found.slice(1).forEach(e => e.discard())
    if (found.length > 0) return
    this.summon(server)
    console.info('[ttl] voice of the world npc placed in the spirit corridor')
  },

  replace(server) {
    this.find(server).forEach(e => e.discard())
    this.team(server)
    this.summon(server)
    server.persistentData.putInt('ttl.voice.version', TTL_VOICE_NPC_VERSION)
    console.info(`[ttl] voice of the world npc replaced (version ${TTL_VOICE_NPC_VERSION})`)
  }
}

ServerEvents.loaded(event => {
  var server = event.server
  var check = () => {
    try {
      TtlVoiceNpc.ensure(server)
    } catch (e) {
      console.error(`[ttl] voice npc check failed: ${e}`)
    }
    server.scheduleInTicks(600, check)
  }
  // After corridor.js: its forceload takes a tick and the hall goes in at tick 40.
  server.scheduleInTicks(80, () => {
    try {
      TtlVoiceNpc.team(server)
      if (server.persistentData.getInt('ttl.voice.version') !== TTL_VOICE_NPC_VERSION) TtlVoiceNpc.replace(server)
    } catch (e) {
      console.error(`[ttl] voice npc setup failed: ${e}`)
    }
    check()
  })
})
