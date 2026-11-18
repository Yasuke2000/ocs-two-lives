# De ringen van Jura

**Trek voor je eerste reis in noordoostelijke richting naar Dwargon.** Je verschijnt aan de buitenrand van het Grote Jurawoud in `minecraft:overworld`, bij **X 271, Z -624**. Je kijkt dan al ongeveer naar de poort op **X 435, Z -1000**. De server zoekt binnen 40 blokken van het aankomstpunt naar een open plek. Tempest ligt de andere kant op, op **X 0, Z 0**. Op weg naar die stad kom je door een gebied met veel meer magicules. [Wereldkaart](world-map.md) · [English](../en/jura-rings.md)

De zonebreedtes, magiculewaarden en aankomstbescherming kunnen veranderen.

## Zo lees je het landschap

Door de magicules die uit Veldora zijn gelekt, kent het bos drie zones. De buitenste zone volgt de *buitengrens van Jura*. Alleen de kern wordt vanaf Tempest gemeten. Wie langs de grens reist, kan lang aan de bosrand blijven. Snijd je een bocht af, dan kun je in de middenzone belanden. Rond het Meer van Siss, het moeras en de rivieren binnen Jura ontstaat geen nieuwe veilige rand.

| Zone | Waar je die tegenkomt | Waaraan je die herkent |
| --- | --- | --- |
| Bosrand | Ongeveer de eerste 280 blokken binnen de buitengrens | Eiken- en berkenbos, oud berkenbos, bloemenbos, vlaktes of moeras. Deze gewone biomen hebben een nominale omgevingswaarde van 500 magicules. |
| Middenzone | Tussen de bosrand en de kern | Vooral donker bos, met normaal 2.000 magicules in de omgeving. Ertussen liggen stukken oerbos met 20.000. De overgang naar een ander bioom kan al gevaarlijk zijn voordat je de kern bereikt. |
| Kern | Een straal van ongeveer 200 blokken rond Tempest | Overwegend oerbos (`tensura:ancient_forest`), afgewisseld met donker bos. In het oerbos kan een pas herboren ziel binnen enkele seconden een magiculevergiftiging oplopen. |

De grenzen verschuiven van plek tot plek met ongeveer 50 blokken. Ook hoogte en water beïnvloeden welk bioom je aantreft. De cijfers geven de huidige nominale hoeveelheid magicules in de **omgeving** aan. Je eigen EP telt je magicules en aura samen. Daaruit kun je geen vaste toegangsdrempel afleiden. Terrein dat onder een oudere packversie is gegenereerd kan zijn oorspronkelijke bioom behouden. [Regio- en bioominstellingen](../../../pack/config/ttl/canon_regions.json) · [Geografie van Jura](../../../design/lore/world.md)

## Onderweg

- **Bij aankomst** heb je momenteel 20 seconden bescherming. Gebruik die tijd om je coördinaten te bekijken en de weg te vinden. Blade Tigers en Barghests kunnen je aan de bosrand al achtervolgen en wegduwen. Schade door de leegte en het kill-commando omzeilen die bescherming. Na de beschermingsperiode loop je weer gewone schade op.
- **Tijdens je reis** kun je de open plek en de poort van Dwargon als waypoints opslaan. Loop je het oerbos in of krijg je schade door magicules, keer dan langs dezelfde weg terug naar het lichtere bos aan de buitengrens. Een rivieroever kan juist dieper Jura in leiden.
- **In Tempest** beschermt het plein binnen 56 blokken van **(0, 0)** spelers in Leven 2 tegen magiculevergiftiging. Vijandige wezens verschijnen daar niet via een natuurlijke spawn, maar ze kunnen wel van buiten naar binnen lopen. De aanlooproute buiten die kleine cirkel loopt nog steeds door de kern. Gevechten en vervloekingen blijven ook op het plein gevaarlijk.

Afstanden en timers kunnen bij een packupdate veranderen. Gedraagt het bos of je aankomstpunt zich anders, vermeld dan de dimensie, je X/Z en het bioom uit het debugscherm bij je melding. Een beheerder kan met `/ttl arrival` het opgeslagen aankomstpunt opvragen en met `/ttlmap <x> <z>` het verwachte bioom controleren. [Aankomstinstellingen](../../../design/data/arrival.toml) · [Bescherming in Leven 2](../../../pack/kubejs/server_scripts/ttl/life/mortal_immunity.js) · [Een fout melden](report-bugs.md)
