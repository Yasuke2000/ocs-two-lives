# Testen op de OCS Tensura: Two Lives-server

Bedankt om mee te testen! Reken op ongeveer 15 minuten voor de installatie. Daarna start je met één klik.

## Wat je nodig hebt

- Een **Minecraft Java Edition**-account (de gewone pc-versie, niet Bedrock of Game Pass voor console).
- Een pc met minstens **16 GB RAM**. Met 8 GB lukt het misschien, maar het zal haperen.
- Ongeveer 3 GB vrije schijfruimte.

## 1. Prism Launcher installeren

1. Download **Prism Launcher** op <https://prismlauncher.org/download/> en installeer hem.
2. Open Prism en voeg je Microsoft-account toe: rechtsboven via **Accounts → Manage Accounts → Add Microsoft**.
3. Java moet je niet zelf installeren. Prism vraagt het bij de eerste start en downloadt het voor jou. Klik gewoon **Yes / Download**.

## 2. De instance aanmaken

1. Klik **Add Instance**.
2. Geef hem een naam, bv. `OCS Two Lives`.
3. Kies bij versie **1.21.1**. Let op: **niet** 1.21.10 of 1.21.11, die staan er vlak naast.
4. Kies onderaan bij **Mod loader** voor **NeoForge**, versie **21.1.266**.
   Zie je bij NeoForge "No versions are currently available"? Dan heb je de verkeerde Minecraft-versie gekozen. Ga naar **Edit → Version**, selecteer de rij **Minecraft**, klik **Change Version** en kies **1.21.1**. Klik daarna **Install Loader → NeoForge → 21.1.266**.
5. Klik **OK**.

## 3. De mods automatisch laten installeren

Je installeert de mods niet zelf. Een klein programmaatje (packwiz) haalt ze bij elke start op en houdt ze up-to-date.

1. Download **`packwiz-installer-bootstrap.jar`** op
   <https://github.com/packwiz/packwiz-installer-bootstrap/releases/latest>
   (onder *Assets*).
2. Klik in Prism met de rechtermuisknop op je instance en kies **Folder**.
   Er opent een map. Ga daarin naar de map **`minecraft`** (of `.minecraft`) en zet het `.jar`-bestand daar.
3. Klik opnieuw met de rechtermuisknop op de instance en kies **Edit → Settings → Custom commands**.
4. Vink **Custom commands** aan en plak dit in **Pre-launch command** (op één regel):

   ```
   "$INST_JAVA" -jar packwiz-installer-bootstrap.jar https://raw.githubusercontent.com/Yasuke2000/ocs-two-lives/main/pack/pack.toml
   ```

5. Ga in hetzelfde venster naar **Java** (of *Memory*), vink het aan en zet **Maximum memory allocation** op **6144 MB**. Heb je 32 GB RAM of meer? Dan mag het **8192 MB** zijn.

## 4. Starten

1. Klik **Launch**. De eerste keer verschijnt een venster dat ongeveer 70 mods downloadt; dat duurt een paar minuten.
   Later gaat het snel: dan haalt hij enkel nog binnen wat veranderd is.
2. Minecraft start op. De eerste keer duurt het laden langer dan gewoonlijk; dat is normaal bij een modpack.

## 5. Joinen

1. Stuur **David** je **Minecraft-naam**. De server werkt met een whitelist, dus zonder die stap kom je er niet in.
2. Ga in Minecraft naar **Multiplayer → Add Server** en vul dit adres in:

   ```
   molecule-threefold.tun.ply.gg
   ```

   Zonder poortnummer; Minecraft vindt de poort zelf.
3. Join!

## Problemen?

| Probleem | Oplossing |
| --- | --- |
| NeoForge: "No versions are currently available" | Je instance staat op 1.21.10 of 1.21.11. Zet hem op **1.21.1** (zie stap 2.4). |
| "You are not whitelisted on this server" | Je naam staat nog niet op de whitelist. Stuur je exacte Minecraft-naam naar David. |
| "Mismatched mod list" of "Incompatible mods" | Je pack is verouderd. Sluit Minecraft volledig en start opnieuw via Prism; packwiz werkt hem dan bij. |
| Er verschijnt geen downloadvenster, of er komen geen mods bij | Controleer of het `.jar`-bestand echt in de map `minecraft` staat en of het pre-launch command exact klopt, inclusief de aanhalingstekens. |
| "Unable to access jarfile packwiz-installer-bootstrap.jar" | Het bestand staat in de verkeerde map: het moet in `minecraft`, niet in de instance-map erboven. |
| Minecraft crasht bij het opstarten | Klik in Prism op de instance en ga naar **Edit → Minecraft Log**. Klik **Upload** en stuur de link naar David. |
| Spel loopt heel traag of hapert | Zet in de video-instellingen de **Render Distance** op 8. Check ook dat je minstens 6 GB geheugen hebt toegewezen (stap 3.5). |
| "Can't connect to server" / timeout | Probeer het na een paar minuten opnieuw. De server is soms aan het herstarten voor een update. Blijft het misgaan, verwittig dan David. |

## Goed om te weten

- Dit is een **testserver**: alles kan nog veranderen, en de wereld kan gereset worden.
- Je hoeft het pack nooit zelf bij te werken: elke keer dat je start via Prism, haalt hij automatisch de nieuwste versie op.
- Vind je een bug of iets vreemds? Noteer wat je deed, wat er gebeurde en, als het kan, een screenshot.
