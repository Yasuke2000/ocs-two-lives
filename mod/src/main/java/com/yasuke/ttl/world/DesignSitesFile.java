package com.yasuke.ttl.world;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.function.Consumer;
import org.jetbrains.annotations.Nullable;

/**
 * {@code pack/config/ttl/world/sites.json} (WP-W1's converter writes it next to the rasters): one entry per anchor site
 * in the schema {@link CanonSites} reads ({@code name, centre | x z, radius, fade, terrain, ground, biomes}) plus the
 * own-world keys {@code kind} (clearing, plateau, carve, lakeside, coast, village), {@code min_cover} and {@code roof}
 * (carve sites). Accepts a top-level list or {@code {"sites": [...]}}, {@code id}/{@code r}/{@code site} as aliases.
 * A site without {@code terrain} is {@code flat} when it has a {@code ground} and is not a carve site ({@code keep}
 * otherwise). Pure Java.
 */
public final class DesignSitesFile {
    private DesignSitesFile() {}

    /** One site as /ttlsite reports it. */
    public record Info(String id, double x, double z, double r, double fade, @Nullable Integer ground, String kind,
                       @Nullable Integer minCover, @Nullable Integer roof) {}

    /** The entries normalised to CanonConfig's schema, as {@code {"sites": [...]}}. */
    public static JsonObject normalise(JsonElement root, Consumer<String> warn) {
        JsonArray in = root.isJsonArray() ? root.getAsJsonArray()
                : root.isJsonObject() && root.getAsJsonObject().has("sites") && root.getAsJsonObject().get("sites").isJsonArray()
                ? root.getAsJsonObject().getAsJsonArray("sites") : new JsonArray();
        if (in.isEmpty() && !(root.isJsonArray())) warn.accept("design sites: sites.json has no 'sites' list");
        JsonArray out = new JsonArray();
        for (JsonElement e : in) {
            if (!e.isJsonObject()) continue;
            JsonObject s = e.getAsJsonObject().deepCopy();
            alias(s, "name", "id");
            alias(s, "radius", "r");
            alias(s, "kind", "site");
            if (!s.has("centre")) {
                if (s.has("center")) s.add("centre", s.get("center"));
                else if (s.has("x") && s.has("z")) {
                    JsonArray c = new JsonArray();
                    c.add(s.get("x"));
                    c.add(s.get("z"));
                    s.add("centre", c);
                }
            }
            String kind = s.has("kind") ? s.get("kind").getAsString().toLowerCase(Locale.ROOT) : "clearing";
            if (!s.has("terrain")) s.addProperty("terrain", s.has("ground") && !kind.equals("carve") ? "flat" : "keep");
            if (s.has("terrain") && s.get("terrain").getAsString().equals("fixed")) s.addProperty("terrain", "flat");
            out.add(s);
        }
        JsonObject o = new JsonObject();
        o.add("sites", out);
        return o;
    }

    /**
     * The entries {@link CanonSites} should get: those that shape terrain or biomes (a carve site keeps the designed
     * massif and only names its place, so it is left out instead of being skipped with a warning).
     */
    public static JsonObject forCanonSites(JsonObject normalised) {
        JsonArray out = new JsonArray();
        for (JsonElement e : normalised.getAsJsonArray("sites")) {
            JsonObject s = e.getAsJsonObject();
            boolean keep = !s.has("terrain") || s.get("terrain").getAsString().equals("keep");
            boolean shapes = s.has("biomes") || s.has("erosion") || s.has("continents") || s.has("ridges");
            if (!keep || shapes) out.add(s);
        }
        JsonObject o = new JsonObject();
        o.add("sites", out);
        return o;
    }

    public static List<Info> infos(JsonObject normalised, Consumer<String> warn) {
        List<Info> out = new ArrayList<>();
        for (JsonElement e : normalised.getAsJsonArray("sites")) {
            JsonObject s = e.getAsJsonObject();
            try {
                String id = s.get("name").getAsString();
                JsonArray c = s.getAsJsonArray("centre");
                out.add(new Info(id, c.get(0).getAsDouble(), c.get(1).getAsDouble(), s.get("radius").getAsDouble(),
                        s.has("fade") ? s.get("fade").getAsDouble() : 0, s.has("ground") ? s.get("ground").getAsInt() : null,
                        s.has("kind") ? s.get("kind").getAsString() : "clearing",
                        s.has("min_cover") ? s.get("min_cover").getAsInt() : null, s.has("roof") ? s.get("roof").getAsInt() : null));
            } catch (RuntimeException ex) {
                warn.accept("design sites: entry skipped (" + ex + "): " + s);
            }
        }
        return out;
    }

    /** Sites of {@code a} followed by those of {@code b} whose names {@code a} does not have. */
    public static CanonSites merge(CanonSites a, CanonSites b) {
        if (b.isEmpty()) return a;
        if (a.isEmpty()) return b;
        List<CanonSites.Site> all = new ArrayList<>();
        java.util.Set<String> names = new java.util.HashSet<>();
        for (int i = 0; i < a.size(); i++) {
            all.add(a.site(i));
            names.add(a.site(i).name());
        }
        for (int i = 0; i < b.size(); i++) if (names.add(b.site(i).name())) all.add(b.site(i));
        return new CanonSites(all.toArray(CanonSites.Site[]::new));
    }

    private static void alias(JsonObject s, String key, String alias) {
        if (!s.has(key) && s.has(alias)) s.add(key, s.get(alias));
    }
}
