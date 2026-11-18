// priority: 95
// Last Wish: in the lore a reincarnator's unique is born from their strongest wish at death (Rimuru's
// dying thoughts gave him Great Sage and Predator). The wish picked in the Corridor sets the pool the
// unique is drawn from. Skill IDs come from config/tensura/reincarnation_config.toml (startingSkills).
// `echo` is the Legendary that answers this wish for a Legend soul: corridor_flow.js offers it next to the unique
// options while the registry has room (skills.toml [legend_pick]); this file never grants it.
const TtlWishes = {
  LIST: [
    { id: 'strength', label: 'Strength', wish: 'Never to be powerless again.',
      pool: ['tensura:berserker', 'tensura:berserk', 'tensura:fighter', 'tensura:martial_master', 'tensura:unyielding', 'tensura:spearhead'],
      echo: 'tensura:wrath' },
    { id: 'knowledge', label: 'Knowledge', wish: 'To understand everything.',
      pool: ['tensura:analyst', 'tensura:researcher', 'tensura:mathematician', 'tensura:observer', 'tensura:seer', 'tensura:seeker'],
      echo: 'tensura:great_sage' },
    { id: 'protection', label: 'Protection', wish: 'To keep the ones I love safe.',
      pool: ['tensura:guardian', 'tensura:healer', 'tensura:reflector', 'tensura:chosen_one', 'tensura:survivor'],
      echo: 'tensura:creator' },
    { id: 'hunger', label: 'Hunger', wish: 'Never to go hungry again.',
      pool: ['tensura:gourmand', 'tensura:gourmet', 'tensura:engorger', 'tensura:chef', 'tensura:cook'],
      echo: 'tensura:predator' },
    { id: 'freedom', label: 'Freedom', wish: 'To go anywhere, and never be caught.',
      pool: ['tensura:traveler', 'tensura:shadow_striker', 'tensura:thrower', 'tensura:sniper'],
      echo: 'tensura:sloth' },
    { id: 'creation', label: 'Creation', wish: 'To make something that outlasts me.',
      pool: ['tensura:fusionist', 'tensura:tuner', 'tensura:musician', 'tensura:chef'],
      echo: 'tensura:creator' },
    { id: 'vengeance', label: 'Vengeance', wish: 'To make them pay.',
      pool: ['tensura:murderer', 'tensura:merciless', 'tensura:reaper', 'tensura:villain', 'tensura:severer', 'tensura:absolute_severance'],
      echo: 'tensura:wrath' },
    { id: 'deceit', label: 'Deceit', wish: 'Never to be seen through.',
      pool: ['tensura:falsifier', 'tensura:bewilder', 'tensura:degenerate', 'tensura:reverser', 'tensura:infinity_prison'],
      echo: 'tensura:envy' },
    { id: 'dominion', label: 'Dominion', wish: 'To stand above everyone.',
      pool: ['tensura:commander', 'tensura:oppressor', 'tensura:royal_beast', 'tensura:suppressor', 'tensura:usurper'],
      echo: 'tensura:pride' },
    { id: 'survival', label: 'Survival', wish: 'To live, whatever it takes.',
      pool: ['tensura:survivor', 'tensura:unyielding', 'tensura:healer', 'tensura:degenerate'],
      echo: 'tensura:greed' }
  ],

  get(id) {
    for (var i = 0; i < this.LIST.length; i++) {
      if (this.LIST[i].id === id) return this.LIST[i]
    }
    return null
  },

  // The Legendary that answers this wish for a Legend soul (corridor_flow.js legendEcho); null when the wish has none
  // or the registry does not rate it Legendary any more (skills.toml). Whether there is room for it is the registry's call.
  echo(id) {
    var wish = this.get(id)
    if (!wish || !wish.echo) return null
    return TtlRegistry.rarityOf(wish.echo) === 'legendary' ? wish.echo : null
  }
}
