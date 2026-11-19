package com.yasuke.ttl.world;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;
import org.jetbrains.annotations.Nullable;

/**
 * Reads the {@code regions} of canon_regions.json into {@link CanonGrid.Region}s and its {@code sites} into
 * {@link CanonSites}. Only Gson, no Minecraft types, so
 * {@link CanonGrid#main} can check the real file. Malformed pieces are skipped through {@code warn}; a region with
 * broken {@code zones} simply has none (its plain {@code biomes} palette applies).
 */
public final class CanonConfig {
    private CanonConfig() {}

    public static Map<Character, CanonGrid.Region> regions(JsonObject json, Consumer<String> warn) {
        Map<Character, CanonGrid.Region> regions = new HashMap<>();
        JsonObject regionsJson = json.getAsJsonObject("regions");
        if (regionsJson == null) return regions;
        for (Map.Entry<String, JsonElement> e : regionsJson.entrySet()) {
            if (e.getKey().length() != 1 || !e.getValue().isJsonObject()) continue;
            JsonObject r = e.getValue().getAsJsonObject();
            String name = r.has("name") ? r.get("name").getAsString() : e.getKey();
            regions.put(e.getKey().charAt(0), new CanonGrid.Region(name,
                    knob(r, "erosion"), knob(r, "temperature"), knob(r, "vegetation"),
                    r.has("strength") ? Math.max(0, Math.min(1, r.get("strength").getAsDouble())) : 1,
                    palette(r, "biomes", name, warn), r.has("replace_peaks") && r.get("replace_peaks").getAsBoolean(),
                    palette(r, "peaks", name, warn), text(r, "banner_title"), text(r, "banner_subtitle"),
                    zones(r, name, warn)));
        }
        return regions;
    }

    /** {@code [[id, weight], ...]}; malformed entries are skipped with a warning, null when none is usable. */
    @Nullable
    static CanonPalette palette(JsonObject r, String key, String region, Consumer<String> warn) {
        JsonElement v = r.get(key);
        if (v == null || v.isJsonNull()) return null;
        if (!v.isJsonArray()) {
            warn.accept("canon region " + region + ": '" + key + "' is not a list of [id, weight]");
            return null;
        }
        return list(v.getAsJsonArray(), key, region, warn);
    }

    @Nullable
    private static CanonPalette list(JsonArray entries, String key, String region, Consumer<String> warn) {
        List<String> ids = new ArrayList<>();
        List<Integer> weights = new ArrayList<>();
        for (JsonElement entry : entries) {
            try {
                JsonArray pair = entry.getAsJsonArray();
                String id = pair.get(0).getAsString();
                int weight = pair.size() > 1 ? pair.get(1).getAsInt() : 1;
                if (weight <= 0 || id.isBlank()) throw new IllegalArgumentException("weight " + weight);
                ids.add(id);
                weights.add(weight);
            } catch (RuntimeException ex) {
                warn.accept("canon region " + region + ": skipping " + key + " entry " + entry + " (" + ex + ")");
            }
        }
        return ids.isEmpty() ? null : new CanonPalette(ids.toArray(String[]::new), weights.stream().mapToInt(Integer::intValue).toArray());
    }

    /**
     * {@code "zones": {"centre": [x, z], "fade": blocks, "interior": "~W", "rings": [{"name", "radius" | "depth",
     * "biomes"}, ...]}}: see {@link CanonZones}. Null when absent or unusable (a warning says why).
     */
    @Nullable
    static CanonZones zones(JsonObject r, String region, Consumer<String> warn) {
        JsonElement v = r.get("zones");
        if (v == null || v.isJsonNull()) return null;
        try {
            JsonObject z = v.getAsJsonObject();
            JsonArray centre = z.has("centre") ? z.getAsJsonArray("centre") : null;
            double cx = centre == null ? 0 : centre.get(0).getAsDouble(), cz = centre == null ? 0 : centre.get(1).getAsDouble();
            double fade = z.has("fade") ? z.get("fade").getAsDouble() : 0;
            String interior = z.has("interior") ? z.get("interior").getAsString() : "~";
            List<CanonZones.Ring> rings = new ArrayList<>();
            for (JsonElement e : z.getAsJsonArray("rings")) {
                JsonObject ring = e.getAsJsonObject();
                String name = ring.has("name") ? ring.get("name").getAsString() : "ring " + (rings.size() + 1);
                CanonPalette biomes = list(ring.getAsJsonArray("biomes"), "zones." + name, region, warn);
                if (biomes == null) throw new IllegalArgumentException("ring " + name + " has no usable biomes");
                rings.add(new CanonZones.Ring(name, ring.has("radius") ? ring.get("radius").getAsDouble() : 0,
                        ring.has("depth") ? ring.get("depth").getAsDouble() : 0, biomes));
            }
            return new CanonZones(cx, cz, fade, interior, rings.toArray(CanonZones.Ring[]::new));
        } catch (RuntimeException ex) {
            warn.accept("canon region " + region + ": zones ignored, the plain 'biomes' palette applies (" + ex + ")");
            return null;
        }
    }

    /**
     * {@code "sites": [{"name", "centre": [x, z], "radius", "fade", "terrain": keep|flat|lowland|hills|mountain,
     * "ground" (flat), "biomes": [[id, weight], ...] (optional), "erosion"/"continents"/"ridges" (optional)}, ...]}:
     * see {@link CanonSites}. Other keys (notes) are ignored; a malformed site is skipped with a warning.
     */
    public static CanonSites sites(JsonObject json, Consumer<String> warn) {
        JsonElement v = json.get("sites");
        if (v == null || v.isJsonNull()) return CanonSites.NONE;
        if (!v.isJsonArray()) {
            warn.accept("canon sites: 'sites' is not a list; no sites");
            return CanonSites.NONE;
        }
        List<CanonSites.Site> sites = new ArrayList<>();
        java.util.Set<String> names = new java.util.HashSet<>();
        for (JsonElement e : v.getAsJsonArray()) {
            String name = "?";
            try {
                JsonObject s = e.getAsJsonObject();
                name = s.get("name").getAsString();
                if (!names.add(name)) throw new IllegalArgumentException("duplicate name");
                JsonArray centre = s.getAsJsonArray("centre");
                CanonPalette biomes = s.has("biomes") ? palette(s, "biomes", "site " + name, warn) : null;
                if (s.has("biomes") && biomes == null) throw new IllegalArgumentException("biomes has no usable entry");
                CanonSites.Terrain terrain = CanonSites.Terrain.of(s.has("terrain") ? s.get("terrain").getAsString() : "keep");
                sites.add(CanonSites.Site.of(name, centre.get(0).getAsDouble(), centre.get(1).getAsDouble(),
                        s.get("radius").getAsDouble(), s.has("fade") ? s.get("fade").getAsDouble() : 0, biomes, terrain,
                        s.has("ground") ? s.get("ground").getAsInt() : null, knob(s, "continents"), knob(s, "erosion"), knob(s, "ridges")));
            } catch (RuntimeException ex) {
                warn.accept("canon site " + name + " skipped: " + ex);
            }
        }
        return sites.isEmpty() ? CanonSites.NONE : new CanonSites(sites.toArray(CanonSites.Site[]::new));
    }

    @Nullable
    private static String text(JsonObject r, String key) {
        JsonElement v = r.get(key);
        return v == null || v.isJsonNull() || !v.isJsonPrimitive() ? null : v.getAsString();
    }

    @Nullable
    private static Double knob(JsonObject r, String key) {
        JsonElement v = r.get(key);
        return v == null || v.isJsonNull() ? null : v.getAsDouble();
    }
}
