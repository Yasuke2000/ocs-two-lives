# Nations, claims and war

Stand where you want your home to be before signing the charter. The faction associated with that region becomes your home faction. You can inspect another nation's rank, land, treasury and diplomatic standing with `/ttl nation info <name>`.

## Found and claim

The party owner must be in Life 2 in the Tensura overworld, have earned the first boss-tier stage (for example by defeating the Orc Lord) and carry the charter fee. You currently need at least two party members including the owner and **50 gold**. The party can have up to five members. These requirements may change. Use `/ttl nation found Dawn` to sign for a nation named Dawn. Members already in the party become its members. Online members receive a founding reputation bonus where the home region has a faction.

Use the FTB Chunks map or `/ftbchunks claim` in the chunk you want. Use `/ftbchunks unclaim` to release it. Land claims work in the Tensura overworld. Current allowances (may change) are four chunks per Life 2 soul before a charter, then ten per nation member at Hamlet. Each higher rank adds two more per member, up to eighteen at Kingdom. Two members in a Hamlet therefore contribute twenty chunks together.

## Pay upkeep and grow

Use `/ttl nation info` to check land, funds and debt. Any member can pay in, for example `/ttl nation deposit silver 10`. Only the owner can withdraw with `/ttl nation withdraw silver 10`. Budget **one silver per claimed chunk per week** (may change). The first upkeep check of the new UTC week bills the treasury. Deposits pay outstanding debt immediately.

Two consecutive unpaid weekly bills currently trigger **Neglect**. The following unpaid week can bring **Unrest**. Your claims remain yours, but affected crops grow more slowly and ores and other covered resources yield less inside them. Clearing the debt lifts the penalty.

Member renown, claimed chunks, marked Public Works chunks inside the claims and treasury holdings contribute to value. Use `/ttl nation value` for your figures and `/ttl nation top` for the rankings. The owner can use `/ttl nation dissolve` to end the nation and receive its remaining treasury. The party survives dissolution.

## Diplomacy and reparations

Both owners enter `/ttl nation ally <other nation>` for an alliance. Use `/ttl nation unally <name>` before declaring war on a former ally. An owner's `/ttl nation war <name>` starts a notice period, currently **24 hours** (may change). Check `/ttl nation info` before fighting. Once the war is active, killing an enemy nation's Legendary holder can transfer their Legendary through the war rules. Either owner can end the war with `/ttl nation peace <name>`.

A consensual duel or awakening challenge can make its **initiator** responsible for public damage if either participant is in a public place when it starts. Towns, placed canon builds and landmarks, and a third party's claimed chunks qualify. Each recorded public block both players place, break or destroy in an attributable explosion counts toward the initiator's bill. The current rate is five bronze per block, capped at five gold and limited by what the initiator can pay (may change). A nation's treasury receives the share from its affected claims. The server attempts to restore eligible blocks. Wilderness damage is outside this reparation rule.

[Parties](parties.md) · [Reputation](reputation.md) · [Economy](economy.md) · [Nederlands](../nl/nations.md)
