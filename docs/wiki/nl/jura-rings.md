# De ringen van Jura

**Trek voor je eerste reis naar het noorden, naar Dwargon.** Je verschijnt aan de noordrand van Jura in `minecraft:overworld`, bij **X 1780, Z −150**, op de weg tussen het dwergenrijk en Tempest. De witte poort van Dwargon staat ongeveer 370 blokken noordwaarts op **X 1900, Z −500**. Tempest ligt de andere kant op, op **X 1720, Z 900**. Op weg naar die stad kom je door een gebied met veel meer magicules. [Wereldkaart](world-map.md) · [English](../en/jura-rings.md)

De zonebreedtes, magiculewaarden en aankomstbescherming kunnen veranderen.

## Zo lees je het landschap

Door de magicules die uit Veldora zijn gelekt, kent Jura drie ringen. De ringen worden **vanaf Tempest** gemeten en volgen het bioom. Het bioom onder je voeten (druk op F3) zegt dus meer over het gevaar dan de afstand.

| Ring | Waar je die tegenkomt | Waaraan je die herkent |
| --- | --- | --- |
| Rand | Meer dan ongeveer 650 blokken van Tempest: de open vlaktes en bossen van Jura | Gewone biomen zoals vlaktes en bos, met een nominale omgevingswaarde van 500 magicules. Je aankomst ligt hier. |
| Band | Ruwweg 200 tot 600 blokken van Tempest | Donker bos, nominaal 2.000 magicules in de omgeving. Het oude goblindorp, de Verzegelde Grot en de Geestenpoort liggen erin. |
| Kern | Ruwweg 200 blokken rond Tempest | Oerbos (`tensura:ancient_forest`), nominaal 20.000 magicules in de omgeving. Een pas herboren ziel kan er binnen enkele seconden een magiculevergiftiging oplopen. |

Elke grens verschuift met ongeveer 50 blokken. Rivieren, meren en hun zandoevers houden hun gewone bioom, ook binnen de ringen. Het gevaar volgt dus het bioom waarin je staat. Ook hoogte en water beïnvloeden wat je ziet. De cijfers geven de huidige nominale hoeveelheid magicules in de **omgeving** aan. Je eigen EP telt je magicules en aura samen. Daaruit kun je geen vaste toegangsdrempel afleiden. [Ringinstellingen](../../../design/data/lerfing/repaint.json) · [Geografie van Jura](../../../design/lore/world.md)

## Onderweg

- **Bij aankomst** heb je momenteel 20 seconden bescherming. Gebruik die tijd om je coördinaten te bekijken en de weg te vinden. Blade Tigers en Barghests kunnen je aan de rand al achtervolgen en wegduwen, en de rotsige voet van het Canaatgebergte vlak ten oosten van je aankomstpunt heeft eigen berggedierte. Schade door de leegte en het kill-commando omzeilen die bescherming. Na de beschermingsperiode loop je weer gewone schade op.
- **Tijdens je reis** kun je de poort van Dwargon als waypoint opslaan. Loop je het donkere bos in en voel je de lucht dikker worden, of krijg je schade door magicules in het oerbos, keer dan langs dezelfde weg terug naar de vlaktes. Een rivieroever kan juist dieper Jura in leiden.
- **In Tempest** beschermt het plein binnen 56 blokken van **(1720, 900)** spelers in Leven 2 tegen magiculevergiftiging. Vijandige wezens verschijnen daar niet via een natuurlijke spawn, maar ze kunnen wel van buiten naar binnen lopen. De aanlooproute buiten die kleine cirkel loopt nog steeds door de kern. Gevechten en vervloekingen blijven ook op het plein gevaarlijk.

Afstanden en timers kunnen bij een packupdate veranderen. Gedraagt het bos of je aankomstpunt zich anders, vermeld dan de dimensie, je X/Z en het bioom uit het debugscherm bij je melding. Een beheerder kan met `/ttl arrival` het opgeslagen aankomstpunt opvragen en met `/ttlmap <x> <z>` het verwachte bioom controleren. [Aankomstinstellingen](../../../design/data/arrival.toml) · [Bescherming in Leven 2](../../../pack/kubejs/server_scripts/ttl/life/mortal_immunity.js) · [Een fout melden](report-bugs.md)
