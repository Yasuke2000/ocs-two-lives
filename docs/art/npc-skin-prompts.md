# Hand-made NPC skins: ChatGPT image prompts

The generic NPCs (Free Guild adventurers, merchants, dwarves, goblins, the Church, knights) wear skins that
`tools/gen_npc_looks.py` composes from parts. The catalogue is `tools/npc_looks.py`, and the contact sheet is
[`docs/previews/npc_skins.png`](../previews/npc_skins.png). These prompts are for hand-made replacements if Yasuke wants
nicer art later. The costumes are our interpretation of the Western Nations in *That Time I Got Reincarnated as a Slime*.
The palettes follow the pack's heraldry (`design/lore/heraldry.md`).

## How to use them

1. Paste the **shared preamble** and then one **archetype block** into ChatGPT (image generation).
2. Image models rarely get the 64 × 64 UV layout right. A reliable route is to ask for the **front and back turnaround**
   first. Paint the skin in a skin editor such as Blockbench or NovaSkin over the existing `look_<look>_<n>.png` as a
   template, using the turnaround as reference. If the model does return a skin sheet, check it in a skin viewer before
   using it.
3. Save it as `pack/kubejs/assets/ttl/textures/entity/npc/hand_<look>_<n>.png`. It must be 64 × 64 with an opaque
   base layer and the classic (4 px) or slim (3 px) arms the variant uses.
4. In `tools/npc_looks.py`, replace that variant's spec with `dict(slim=..., texture="ttl:textures/entity/npc/hand_<look>_<n>.png")`.
   Keep its place in the list so the NPCs that wear it keep it. Then run `python tools/gen_npc_looks.py`,
   `python -I tools/gen_npcs.py` and `packwiz refresh` in `pack/`. Bump `[ambient] rev` in `design/data/sidequests.toml`.
5. Keep the result original. Do not trace official art or paste in skins from skin sites without a clear licence.
   Add the source to `CREDITS.md`.

## Shared preamble

> Design an original Minecraft Java Edition player skin, 64 × 64 pixels, standard modern skin layout (head, hat
> overlay, body, jacket overlay, arms and legs with their sleeve and pants overlays). Clean low-detail pixel art in
> the vanilla Minecraft style: flat colours, 2–3 shades per material, a readable face with an 8 × 8 front (eyes on
> row 4). Setting: the medieval-fantasy Western Nations of the light novel *That Time I Got Reincarnated as a Slime*
> (guild adventurers, small kingdoms, dwarven forges, monster peoples of the Jura forest). No modern clothing, no
> logos, no text, no Steve or Alex look. Show the skin sheet and a front and back render of it on a player model.

## Archetype blocks

| Look (`npc_looks.py`) | Arms | Prompt |
| --- | --- | --- |
| `guild_rookie` | classic | A Free Guild rookie of rank F to E: a young human in a plain wool tunic (olive, rust or brown) over a cream shirt, a leather belt and a small bronze or copper guild plate pinned on the left chest. Dark trousers, worn boots and a short travelling cloak on the back. Hopeful and slightly scruffy. |
| `guild_veteran` | classic | A Free Guild veteran of rank D to C: a weathered human in a chainmail shirt over a padded gambeson. Add leather bracers, a dark travelling cloak, a shoulder strap and a silver guild plate on the chest. One variant wears a forest-green tabard. Short beard or moustache, scars allowed. |
| `guild_elite` | classic | A Free Guild elite of rank B to A: polished steel breastplate and faulds with gold edging, armoured boots and a long cape in deep blue or crimson. Add a gold or pale-blue mithril guild plate. Confident, white or red hair. |
| `guild_scout` | classic + slim | A Free Guild scout or ranger: a deep green or brown hooded cloak, a laced leather jerkin, wrapped forearms and a quiver strap across the chest. Soft boots. The face is partly shaded by the hood. |
| `guild_mage` | slim + classic | A Free Guild mage: a long robe in violet, midnight blue or wine red with a gold trim running down the front opening. Wide sleeves, a sash belt and an optional deep hood. Long hair or an old mage's grey goatee. |
| `bard` | classic | A wandering bard: a bright tunic (rose or teal) with gold trim and a feathered cap. Add a cloak in a contrasting colour and a lute strap across the chest. |
| `otherworlder` | classic | An otherworlder (a reincarnated or summoned Japanese person) now dressed as a guild adventurer. Black hair, a dark high-collared travelling coat over a cream shirt and a low-rank guild plate. Any modern hint should stay small, such as a neat school-style haircut. |
| `merchant` | classic | A travelling merchant. Use one of three styles: a Blumund pedlar in a red coat, cream vest and flat cap with a big backpack and bedroll; a southern trader in an ochre hooded robe with a red sash; or an Englassian factor in a navy coat with red trim and a neat grey moustache. |
| `dwarf_trader` | classic | A dwarf trader or caravan master of the Armed Nation of Dwargon: broad face, ruddy skin and a long braided beard falling onto the chest. Add a mustard-yellow or brown coat with red trim and a heavy pack or red cloak. |
| `dwarf_warrior` | classic | A dwarf warrior or guard of Dwargon: a steel nasal helm, chainmail and a red tabard with a yellow anvil emblem. Add iron boots, leather gloves and a thick beard over the chest. |
| `dwarf_smith` | classic | A dwarf smith: rolled-up sleeves, muscular forearms, a scorched leather apron over a work shirt, a red bandana or bald head with a grey beard, and heavy gloves. |
| `luminist_cleric` | slim + classic | A priest or cleric of Luminism, the Western Holy Church: an ivory robe with gold trim and a blue sash, a gold cross on a narrow tabard and an optional white hood. Calm and pious. |
| `holy_knight` | classic | A Holy Knight of Lubelius: white plate armour with gold edging, an ivory tabard with a gold cross, a blue or ivory cape and an optional chainmail coif. Stern. |
| `englassia_knight` | classic | A knight of the Kingdom of Englassia: steel plate or chainmail, a navy tabard with a crimson emblem, a navy cape, gold trim and an optional nasal helm. |
| `goblin` | classic | A wild goblin of the Jura forest: small and wiry with green skin, yellow or red eyes without whites, two fangs, long pointed ears and a ragged hide vest. Add a loincloth, forearm wraps and bare feet. Still cute rather than gory. |
| `hobgoblin` | classic + slim | A named hobgoblin of Tempest: human-sized, olive-green skin, small pointed ears, one fang and dark hair. The clothes are neat and simple, made by Shuna: a work vest with iron shoulder plates, or a blue kimono-style top with a gold obi. |
| `kijin` | classic + slim | A kijin (ogre-folk) of Tempest: pale skin, two small horns (ivory or black) above the fringe and red or violet eyes. Use a dark or white wrapped kimono with a red obi and hakama trousers. |
| `lizardman` | classic | A lizardman of Lake Siss: green or teal scales, a pale belly and jaw, yellow slit eyes, a dark crest down the head and spear-fighter gear. Choose a chainmail shirt with a blue reed-emblem tabard or a leather harness and loincloth. |
| `tempest_citizen` | classic + slim | A citizen of Tempest: a human or monster townsperson in Tempest's Japanese-influenced clothes. Use a blue or sage-green wrapped top, a gold or blue obi and simple sandals. |
| `outcast` | classic | The Outcast Society's contact: a deep purple hooded cloak over a dark coat with a broken pale-star clasp. Add dark gloves and a mostly shadowed face. Mysterious, not evil-looking. |
| `falmuth_knight` | classic | Not needed: it uses Tensura's own `falmuth_knight` texture at runtime. |
