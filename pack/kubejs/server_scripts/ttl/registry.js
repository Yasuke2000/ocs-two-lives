// priority: 90
// Golden rule 1: every unique-skill grant or revoke goes through here.
// Phase 0 stub: one random innate unique at rebirth. Slots, rarities and reconcile come in Phase 1.
global.ttlRegistry = {
  // Legendary uniques are never innate (master plan §5); they are only won by absorption.
  LEGENDARY: [
    'tensura:predator', 'tensura:great_sage', 'tensura:creator',
    'tensura:envy', 'tensura:greed', 'tensura:lust', 'tensura:pride', 'tensura:sloth', 'tensura:wrath'
  ],
  // startingSkills from config/tensura/reincarnation_config.toml.
  POOL: [
    'tensura:absolute_severance', 'tensura:analyst', 'tensura:berserk', 'tensura:berserker', 'tensura:bewilder',
    'tensura:chef', 'tensura:chosen_one', 'tensura:commander', 'tensura:cook', 'tensura:creator',
    'tensura:degenerate', 'tensura:engorger', 'tensura:envy', 'tensura:falsifier', 'tensura:fighter',
    'tensura:fusionist', 'tensura:gourmand', 'tensura:gourmet', 'tensura:great_sage', 'tensura:greed',
    'tensura:guardian', 'tensura:healer', 'tensura:infinity_prison', 'tensura:lust', 'tensura:martial_master',
    'tensura:mathematician', 'tensura:merciless', 'tensura:murderer', 'tensura:musician', 'tensura:observer',
    'tensura:oppressor', 'tensura:predator', 'tensura:pride', 'tensura:reflector', 'tensura:researcher',
    'tensura:royal_beast', 'tensura:reaper', 'tensura:reverser', 'tensura:seeker', 'tensura:seer',
    'tensura:severer', 'tensura:shadow_striker', 'tensura:sloth', 'tensura:sniper', 'tensura:spearhead',
    'tensura:suppressor', 'tensura:survivor', 'tensura:traveler', 'tensura:thrower', 'tensura:tuner',
    'tensura:unyielding', 'tensura:usurper', 'tensura:villain', 'tensura:wrath'
  ],

  grantInnate(server, player) {
    const legendary = this.LEGENDARY
    const options = this.POOL.filter(id => legendary.indexOf(id) < 0)
    const skill = options[Math.floor(Math.random() * options.length)]
    server.runCommandSilent(`tensura edit ability grant ${player.username} ${skill}`)
    console.info(`[ttl] registry: innate ${skill} -> ${player.username}`)
    return skill
  },

  revokeAll(server, player) {
    server.runCommandSilent(`tensura reset ${player.username} skill`)
    console.info(`[ttl] registry: revoked all skills of ${player.username}`)
  }
}
