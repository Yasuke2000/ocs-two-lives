# Arenas and duels

In Life 2 you can fight on the **Banquet Floor at Walpurgis** or in the **round hall of Ramiris’s Labyrinth**. Use `/ttl arena list` to see which venue is free.

## Start a match

1. For example, enter `/ttl arena join labyrinth challenge` to travel to the hall. Friends can join that lobby with `/ttl arena join labyrinth`.
2. Pick `duel` for one against one, `party` for two teams of currently two to five fighters each, or `challenge` for one to five players fighting waves together. In a party match, `/ttl arena join walpurgis party b` selects side B.
3. Whoever opened the lobby enters `/ttl arena start`. A normally fatal blow eliminates a fighter. Logging out, remaining outside the arena too long or using `/ttl arena leave` also takes you out. After the match you return to where you joined.

The **Elemental Colossus** follows the Labyrinth waves. **Clayman** is the last opponent on the Walpurgis floor. Match type and result determine the arena payout. For example, a full Labyrinth clear awards gold, magic crystals, experience levels and a loot-table roll. Current loot cooldowns per player and venue are one hour for a duel, two hours for a party battle and twelve hours for a challenge. Duels and party battles under 30 seconds pay no loot. [Bosses](bosses.md)

## Arrange a skill duel

Booking an arena and agreeing to fight for skills are separate choices. In a Labyrinth arena duel, defeat can settle an accepted skill pact. You can also arrange a skill duel elsewhere in Life 2.

1. Pick open ground away from settlements and other teams’ claims. If Sam wants to challenge Alex, Sam enters `/ttl absorb duel Alex`.
2. Alex can select **Accept** or **Decline** in chat, or type `/ttl absorb accept Sam` or `/ttl absorb decline Sam`. Both players must be in Life 2. With the current settings the invitation lasts five minutes and an accepted duel lasts up to fifteen.
3. A blow from your opponent that would kill you settles the duel as a defeat. Logging out within 30 seconds of a hit can also count as a defeat. Check your pact with `/ttl absorb status`.

A nonlethal duel can still cost a skill. A qualifying absorber can take a Legendary unique or copy an eligible lower-rarity unique under the skill-transfer rules. The winner’s skills, both players’ EP and the transfer cooldown affect the outcome. Agree on those stakes before accepting. Life 1 dimensions and the Spirit Corridor are excluded.

## Who pays for damaged blocks?

If either player is in a public area when the duel opens, the **challenger** pays for recorded public damage caused by either participant. This covers breaking and placing blocks and player-caused explosions. Public areas include Tempest, Dwargon, placed canon builds and landmarks, and third-party claims. The current fee is five bronze per recorded change, up to five gold per pact, limited by what the challenger can pay. The server attempts to restore the recorded blocks afterward. Choosing clear ground outside public areas before accepting avoids that disruption.

Damage **inside either arena’s defined bounds** is exempt from those fees. Outside the match floor, ordinary public-place rules can apply again.

## Visit the Walpurgis council

Step onto the dais of Clayman’s throne in his castle in Jistav. The gate leads to the separate Walpurgis Hall. Frey, Guy, Leon and Dagruel stand beside its round table. The Banquet Floor lies east of the council. Use the return gate in the hall to go back after visiting.

Check access with `/ttl walpurgis status`. Legendary unique holders, souls with the Demon Lord or Hero story stage, invited guests and fighters booked for Walpurgis may enter. A Legendary holder can invite an online player with `/ttl walpurgis invite <player>`. Invitations last 24 hours by default. Joining a match takes you directly to its floor.

The personal Spirit Corridor trials belong to the transition between your two lives. There, `/ttl menu` reopens the current step. [Player commands](player-commands.md)

[Nederlands](../nl/arenas.md)
