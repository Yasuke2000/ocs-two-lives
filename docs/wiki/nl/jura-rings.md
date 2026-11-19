# De ringen van Jura

**Trek voor je eerste reis naar het noorden, richting Dwargon.** Je verschijnt aan de noordrand van het Grote Jurawoud in `minecraft:overworld`, bij **X 1780, Z -150**. Je kijkt dan al naar de poort op **X 1900, Z -500**, ongeveer 370 blokken verderop. De server zoekt binnen 40 blokken van het aankomstpunt naar een open plek. Tempest ligt de andere kant op, ongeveer 1.050 blokken naar het zuiden, op **X 1720, Z 900**. Op weg naar die stad kom je door een gebied met veel meer magicules. [Wereldkaart](world-map.md) · [English](../en/jura-rings.md)

De zonebreedtes, magiculewaarden en aankomstbescherming kunnen veranderen.

## Zo lees je het landschap

Door de magicules die uit Veldora zijn gelekt, kent het bos drie zones. Alle drie worden in ringen vanaf Tempest gemeten: naar het noorden, zuiden, westen of oosten leg je dezelfde afstanden af. Lerfings kaart is open land met bosjes, dus de zones volgen de afstand tot Tempest en niet hoe dicht de bomen staan. Meren, stranden en rivieren worden nooit herschilderd: ook de grond ernaast heeft het gevaar van de zone.

| Zone | Waar je die tegenkomt | Waaraan je die herkent |
| --- | --- | --- |
| Bosrand | Meer dan ongeveer 600 blokken van Tempest, dus ook je aankomstpunt | Wat Lerfings kaart daar laat groeien: vlaktes, eiken- en berkenbos, bloemenbos of moeras. Deze gewone biomen hebben een nominale omgevingswaarde van 500 magicules. |
| Middenzone | Ongeveer 200 tot 600 blokken van Tempest | Donker bos, met normaal 2.000 magicules in de omgeving. Het oude goblindorp, de Verzegelde Grot en de Geestenpoort liggen in deze zone. De overgang naar een ander bioom kan al gevaarlijk zijn voordat je de kern bereikt. |
| Kern | Een straal van ongeveer 200 blokken rond Tempest | Oerbos (`tensura:ancient_forest`), met normaal 20.000 magicules in de omgeving. In het oerbos kan een pas herboren ziel binnen enkele seconden een magiculevergiftiging oplopen. |

De grenzen golven met ongeveer 50 blokken. De ringen zijn één keer op Lerfings kaart geschilderd, bij de import van de wereld, en verschuiven dus niet. De cijfers geven de huidige nominale hoeveelheid magicules in de **omgeving** aan. Je eigen EP telt je magicules en aura samen. Daaruit kun je geen vaste toegangsdrempel afleiden. [Regio- en bioominstellingen](../../../pack/config/ttl/canon_regions.json) · [Geografie van Jura](../../../design/lore/world.md)

## Onderweg

- **Bij aankomst** heb je momenteel 20 seconden bescherming. Gebruik die tijd om je coördinaten te bekijken en de weg te vinden. Blade Tigers en Barghests kunnen je aan de bosrand al achtervolgen en wegduwen. Schade door de leegte en het kill-commando omzeilen die bescherming. Na de beschermingsperiode loop je weer gewone schade op.
- **Tijdens je reis** kun je de open plek en de poort van Dwargon als waypoints opslaan. Loop je het oerbos in of krijg je schade door magicules, keer dan langs dezelfde weg terug, weg van Tempest, naar het lichtere land buiten de donkere zone. Een rivieroever kan juist dieper Jura in leiden.
- **In Tempest** beschermt het plein binnen 56 blokken van **(1720, 900)** spelers in Leven 2 tegen magiculevergiftiging. Vijandige wezens verschijnen daar niet via een natuurlijke spawn, maar ze kunnen wel van buiten naar binnen lopen. De aanlooproute buiten die kleine cirkel loopt nog steeds door de kern. Gevechten en vervloekingen blijven ook op het plein gevaarlijk.

Afstanden en timers kunnen bij een packupdate veranderen. Gedraagt het bos of je aankomstpunt zich anders, vermeld dan de dimensie, je X/Z en het bioom uit het debugscherm bij je melding. Een beheerder kan met `/ttl arrival` het opgeslagen aankomstpunt opvragen en met `/ttlmap <x> <z>` het verwachte bioom controleren. [Aankomstinstellingen](../../../design/data/arrival.toml) · [Bescherming in Leven 2](../../../pack/kubejs/server_scripts/ttl/life/mortal_immunity.js) · [Een fout melden](report-bugs.md)
