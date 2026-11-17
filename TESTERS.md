# Testen op de OCS Tensura: Two Lives-server

Bedankt om mee te testen! De installatie duurt ongeveer 5 minuten. Daarna start je met één klik.

## Wat je nodig hebt

- Een **Minecraft Java Edition**-account (de gewone pc-versie, niet Bedrock of Game Pass voor console).
- Een pc met minstens **16 GB RAM**. Met 8 GB lukt het misschien, maar het zal haperen.
- Ongeveer 3 GB vrije schijfruimte.

## 1. Prism Launcher installeren

1. Download **Prism Launcher** op <https://prismlauncher.org/download/> en installeer hem.
2. Open Prism en voeg je Microsoft-account toe: rechtsboven via **Accounts → Manage Accounts → Add Microsoft**.
3. Java moet je niet zelf installeren. Prism vraagt het bij de eerste start en downloadt het voor jou. Klik gewoon **Yes / Download**.

## 2. Het pack importeren

1. Klik linksboven op **Add Instance**.
2. Kies links **Import**.
3. Plak deze link in het vak **Local file or link to a direct download**:

   ```
   https://github.com/Yasuke2000/ocs-two-lives/releases/download/prism-instance/OCS-Two-Lives.zip
   ```

4. Klik **OK**. Er verschijnt een nieuwe instance **OCS Two Lives**.

Alles staat dan al juist: de Minecraft-versie, NeoForge, het geheugen, de mod-installer en de server in je lijst.

## 3. Starten

1. Selecteer **OCS Two Lives** en klik **Launch**. De eerste keer verschijnt een venster dat ongeveer 70 mods downloadt; dat duurt een paar minuten.
   Later gaat het snel: dan haalt hij enkel nog binnen wat veranderd is.
2. Minecraft start op. De eerste keer duurt het laden langer dan gewoonlijk; dat is normaal bij een modpack.

## 4. Joinen

1. Stuur **David** je **Minecraft-naam**. De server werkt met een whitelist, dus zonder die stap kom je er niet in.
2. Ga naar **Multiplayer**. De server **OCS Tensura: Two Lives** staat er al. Dubbelklik erop.

Staat hij er niet? Klik **Add Server** en vul als adres `molecule-threefold.tun.ply.gg` in, zonder poortnummer.

## Problemen?

| Probleem | Oplossing |
| --- | --- |
| "You are not whitelisted on this server" | Je naam staat nog niet op de whitelist. Stuur je exacte Minecraft-naam naar David. |
| "Mismatched mod list" of "Incompatible mods" | Je pack is verouderd. Sluit Minecraft volledig en start opnieuw via Prism; packwiz werkt hem dan bij. |
| Het importeren lukt niet | Controleer of je de link volledig hebt geplakt. Lukt het nog steeds niet, volg dan de handmatige installatie hieronder. |
| Er verschijnt geen downloadvenster, of er komen geen mods bij | Verwijder de instance en importeer opnieuw (stap 2). |
| Minecraft crasht bij het opstarten | Klik in Prism op de instance en ga naar **Edit → Minecraft Log**. Klik **Upload** en stuur de link naar David. |
| Spel loopt heel traag of hapert | Zet in de video-instellingen de **Render Distance** op 8. Heb je 32 GB RAM of meer? Zet dan via **Edit → Settings → Java** het geheugen op 8192 MB. |
| "Can't connect to server" / timeout | Probeer het na een paar minuten opnieuw. De server is soms aan het herstarten voor een update. Blijft het misgaan, verwittig dan David. |

## Goed om te weten

- Dit is een **testserver**: alles kan nog veranderen, en de wereld kan gereset worden.
- Je hoeft het pack nooit zelf bij te werken: elke keer dat je start via Prism, haalt hij automatisch de nieuwste versie op.
- Vind je een bug of iets vreemds? Noteer wat je deed, wat er gebeurde en, als het kan, een screenshot.

## Handmatige installatie (alleen als importeren niet lukt)

1. **Add Instance → Custom**. Naam `OCS Two Lives`, versie **1.21.1** (niet 1.21.10 of 1.21.11), **Mod loader** NeoForge **21.1.266**, **OK**.
   Zie je bij NeoForge "No versions are currently available"? Dan staat de versie verkeerd: **Edit → Version → Minecraft → Change Version → 1.21.1**, daarna **Install Loader → NeoForge → 21.1.266**.
2. Download `packwiz-installer-bootstrap.jar` op <https://github.com/packwiz/packwiz-installer-bootstrap/releases/latest> (onder *Assets*). Open de instance via **Edit → Version → Open .minecraft** en zet het bestand daar.
3. **Edit → Settings → Custom commands**: vink **Custom commands** aan en plak in **Pre-launch command** (op één regel):

   ```
   "$INST_JAVA" -jar packwiz-installer-bootstrap.jar https://raw.githubusercontent.com/Yasuke2000/ocs-two-lives/main/pack/pack.toml
   ```

4. **Edit → Settings → Java**: vink geheugen aan en zet **Maximum memory allocation** op **6144 MB**.
5. Ga verder bij stap 3 hierboven.
