package com.yasuke.ttl.world;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.EOFException;
import java.io.IOException;
import java.io.InputStream;
import java.io.RandomAccessFile;
import java.nio.charset.StandardCharsets;
import java.nio.file.AtomicMoveNotSupportedException;
import java.nio.file.DirectoryStream;
import java.nio.file.FileVisitResult;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.SimpleFileVisitor;
import java.nio.file.StandardCopyOption;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.function.Predicate;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.zip.GZIPInputStream;
import java.util.zip.InflaterInputStream;

/**
 * Puts a prepared world (Lerfing's map, {@code tools/lerfing_import.py}) in place of a dimension's terrain:
 * {@code <world>/ttl-import.txt} holds one line {@code <dimension id> <folder> [<region file count>]}. Pure Java
 * (no Minecraft types) so {@link #main} can test it on synthetic region files; {@link WorldReset} wires it in.
 *
 * <p>Order, all before the levels load: check the source ({@code <folder>/region}: region file names and headers,
 * the expected count, and per file the first and last chunk decompressed: its {@code Status} must be one this
 * Minecraft knows, since an unknown status loads as EMPTY and the chunk would be regenerated over the import; its
 * {@code DataVersion} not newer than the game's; its {@code xPos}/{@code zPos} inside the file's region). Nothing is
 * moved unless every check passes. Then a journal file is written, the old terrain moves to the backup folder (as a
 * world reset does), and the source's {@code region}, {@code entities} and {@code poi} move into the dimension (a
 * rename on the same volume; a verified copy that keeps the source otherwise). If any step fails, every step done so
 * far is undone in reverse order. The journal is deleted only when the swap or the undo completed; a journal left
 * behind (the JVM died mid-swap, or the undo failed) stops the next start until an operator has checked the folders.
 */
public final class WorldImport {
    public static final String MARKER = "ttl-import.txt", JOURNAL = "ttl-import.journal";
    static final Pattern REGION_FILE = Pattern.compile("r\\.(-?\\d+)\\.(-?\\d+)\\.mca");
    static final String[] PARTS = {"region", "entities", "poi"};

    private WorldImport() {}

    /** Where log lines go (the mod passes the slf4j logger, the self-check stdout). */
    public interface Log {
        void info(String msg);

        void warn(String msg);
    }

    /** The import is refused; nothing was moved. */
    public static final class Refused extends Exception {
        Refused(String msg) {
            super(msg);
        }
    }

    /** The marker: which dimension, from which folder, and optionally how many region files must be there. */
    public record Request(String dimension, String folder, Integer expectedFiles) {}

    /** One non-comment line {@code <dimension id> <folder> [<count>]}; throws Refused when it is not that. */
    public static Request parse(List<String> lines) throws Refused {
        Request found = null;
        for (String raw : lines) {
            String line = raw.strip();
            if (line.isEmpty() || line.startsWith("#")) continue;
            if (found != null) throw new Refused("the marker must hold one import line, found a second: '" + line + "'");
            String[] parts = line.split("\\s+");
            if (parts.length < 2 || parts.length > 3) throw new Refused("expected '<dimension id> <folder> [<region file count>]', got '" + line + "'");
            if (!parts[0].matches("[a-z0-9_.-]+:[a-z0-9_./-]+")) throw new Refused("not a dimension id: '" + parts[0] + "'");
            Integer count = null;
            if (parts.length == 3) {
                try {
                    count = Integer.parseInt(parts[2]);
                } catch (NumberFormatException e) {
                    throw new Refused("region file count is not a number: '" + parts[2] + "'");
                }
                if (count <= 0) throw new Refused("region file count must be > 0: " + count);
            }
            found = new Request(parts[0], parts[1], count);
        }
        if (found == null) throw new Refused("the marker has no import line");
        return found;
    }

    /**
     * The source folder: an absolute path, or relative to the world folder, else to the server folder (the world's
     * parent, e.g. /data/import next to /data/world-ttl). Refused when it is missing, ambiguous or overlaps what the
     * swap moves.
     */
    public static Path resolveSource(Path world, Path dimension, String folder) throws Refused {
        Path given = Path.of(folder);
        Path source;
        if (given.isAbsolute()) {
            source = given.normalize();
        } else {
            Path inWorld = world.resolve(given).normalize(), inServer = world.getParent() == null ? null : world.getParent().resolve(given).normalize();
            boolean a = Files.isDirectory(inWorld.resolve("region")), b = inServer != null && !inServer.equals(inWorld) && Files.isDirectory(inServer.resolve("region"));
            if (a && b) throw new Refused("'" + folder + "' is ambiguous: both " + inWorld + " and " + inServer + " hold a region folder; give an absolute path");
            source = a ? inWorld : b ? inServer : inWorld;
        }
        if (!Files.isDirectory(source)) throw new Refused("source folder " + source + " does not exist");
        if (!Files.isDirectory(source.resolve("region"))) throw new Refused("source folder " + source + " has no region folder");
        if (source.equals(world) || source.equals(dimension) || world.startsWith(source))
            throw new Refused("source folder " + source + " is the world or contains it");
        if (source.startsWith(world.resolve("ttl-backup"))) throw new Refused("source folder " + source + " lies inside ttl-backup");
        if (dimension.equals(world)) {
            for (String part : List.of("region", "entities", "poi", "data"))
                if (source.startsWith(world.resolve(part))) throw new Refused("source folder " + source + " lies inside the overworld's " + part + " folder");
        } else if (source.startsWith(dimension)) {
            throw new Refused("source folder " + source + " lies inside the dimension folder that is backed up");
        }
        return source;
    }

    /** What the check found. */
    public record Report(int files, long bytes, long chunks, int sampled, Map<String, Integer> statuses, int minVersion, int maxVersion,
                         List<String> notes) {
        public String describe() {
            return String.format(java.util.Locale.ROOT, "%d region files (%.2f GB), %d chunks; %d sampled: statuses %s, DataVersion %d..%d%s", files, bytes / 1e9, chunks,
                    sampled, statuses, minVersion, maxVersion, notes.isEmpty() ? "" : "; " + String.join("; ", notes));
        }
    }

    /**
     * Checks {@code region} (see the class comment). {@code knownStatus} answers whether this Minecraft knows a raw
     * Status string; {@code maxDataVersion} is the game's data version.
     */
    public static Report validate(Path region, Integer expectedFiles, Predicate<String> knownStatus, int maxDataVersion) throws Refused, IOException {
        List<Path> files = new ArrayList<>();
        List<String> notes = new ArrayList<>();
        int others = 0;
        try (DirectoryStream<Path> dir = Files.newDirectoryStream(region)) {
            for (Path p : dir) {
                if (Files.isRegularFile(p) && REGION_FILE.matcher(p.getFileName().toString()).matches()) files.add(p);
                else others++;
            }
        }
        files.sort(null);
        if (files.isEmpty()) throw new Refused(region + " holds no region files (r.<x>.<z>.mca)");
        if (expectedFiles != null && files.size() != expectedFiles)
            throw new Refused(region + " holds " + files.size() + " region files, the marker expects " + expectedFiles + " (upload incomplete?)");
        if (others > 0) notes.add(others + " other entries in the region folder (moved along, ignored by the game)");
        long bytes = 0, chunks = 0;
        int sampled = 0, minV = Integer.MAX_VALUE, maxV = Integer.MIN_VALUE, empty = 0;
        Map<String, Integer> statuses = new TreeMap<>();
        for (Path file : files) {
            Matcher m = REGION_FILE.matcher(file.getFileName().toString());
            if (!m.matches()) continue;
            int rx = Integer.parseInt(m.group(1)), rz = Integer.parseInt(m.group(2));
            long size = Files.size(file);
            bytes += size;
            if (size < 8192) throw new Refused(file.getFileName() + " is " + size + " bytes, shorter than a region header (8192): truncated upload?");
            try (RandomAccessFile raf = new RandomAccessFile(file.toFile(), "r")) {
                byte[] header = new byte[4096];
                raf.readFully(header);
                int first = -1, last = -1, n = 0;
                for (int i = 0; i < 1024; i++) {
                    int entry = ((header[i * 4] & 0xFF) << 24) | ((header[i * 4 + 1] & 0xFF) << 16) | ((header[i * 4 + 2] & 0xFF) << 8) | (header[i * 4 + 3] & 0xFF);
                    if (entry == 0) continue;
                    long offset = (entry >>> 8) & 0xFFFFFFL, sectors = entry & 0xFF;
                    if (offset < 2 || sectors == 0 || offset * 4096 + 5 > size)
                        throw new Refused(file.getFileName() + ": chunk entry " + i + " points outside the file (sector " + offset + ", " + sectors + " sectors, file " + size + " bytes)");
                    if (first < 0) first = i;
                    last = i;
                    n++;
                }
                chunks += n;
                if (n == 0) {
                    empty++;
                    continue;
                }
                for (int i : first == last ? new int[] {first} : new int[] {first, last}) {
                    int entry = ((header[i * 4] & 0xFF) << 24) | ((header[i * 4 + 1] & 0xFF) << 16) | ((header[i * 4 + 2] & 0xFF) << 8) | (header[i * 4 + 3] & 0xFF);
                    Chunk c = readChunk(raf, (entry >>> 8) & 0xFFFFFFL, size, file.getFileName() + " entry " + i);
                    if (c == null) continue; // external (.mcc) or LZ4: not sampled
                    String where = file.getFileName() + " chunk " + (i & 31) + "," + (i >> 5);
                    if (c.status == null) throw new Refused(where + " has no Status");
                    if (!knownStatus.test(c.status))
                        throw new Refused(where + " has status '" + c.status + "', which this Minecraft does not know: it would load as EMPTY and be"
                                + " regenerated over the import (tools/lerfing_import.py renames it)");
                    if (c.dataVersion == null) throw new Refused(where + " has no DataVersion");
                    if (c.dataVersion > maxDataVersion) throw new Refused(where + " has DataVersion " + c.dataVersion + ", newer than this game's " + maxDataVersion);
                    if (c.x != null && c.z != null && (Math.floorDiv(c.x, 32) != rx || Math.floorDiv(c.z, 32) != rz || Math.floorMod(c.x, 32) != (i & 31) || Math.floorMod(c.z, 32) != (i >> 5)))
                        throw new Refused(where + " claims to be chunk " + c.x + "," + c.z + ": the file is misnamed or damaged");
                    statuses.merge(c.status, 1, Integer::sum);
                    minV = Math.min(minV, c.dataVersion);
                    maxV = Math.max(maxV, c.dataVersion);
                    sampled++;
                }
            }
        }
        if (chunks == 0) throw new Refused(region + ": every region file is empty");
        if (sampled == 0) throw new Refused(region + ": no chunk could be sampled (all external or LZ4); check the export");
        if (empty > 0) notes.add(empty + " region files without chunks");
        return new Report(files.size(), bytes, chunks, sampled, statuses, minV, maxV, notes);
    }

    record Chunk(String status, Integer dataVersion, Integer x, Integer z) {}

    private static Chunk readChunk(RandomAccessFile raf, long sector, long size, String where) throws IOException, Refused {
        raf.seek(sector * 4096);
        int length = raf.readInt();
        int type = raf.readUnsignedByte();
        if ((type & 0x80) != 0) return null; // the chunk lives in an external c.<x>.<z>.mcc file
        if (length < 1 || sector * 4096 + 4 + length > size) throw new Refused(where + ": chunk length " + length + " runs past the end of the file");
        byte[] data = new byte[length - 1];
        raf.readFully(data);
        InputStream in;
        switch (type) {
            case 1 -> in = new GZIPInputStream(new ByteArrayInputStream(data));
            case 2 -> in = new InflaterInputStream(new ByteArrayInputStream(data));
            case 3 -> in = new ByteArrayInputStream(data);
            case 4 -> {
                return null; // LZ4: the game reads it, this check does not
            }
            default -> throw new Refused(where + ": unknown compression type " + type);
        }
        try (DataInputStream nbt = new DataInputStream(in)) {
            if (nbt.readUnsignedByte() != 10) throw new Refused(where + ": chunk data is not an NBT compound");
            nbt.skipNBytes(nbt.readUnsignedShort());
            Chunk[] out = {new Chunk(null, null, null, null)};
            readCompound(nbt, out, 0);
            return out[0];
        } catch (EOFException | java.util.zip.ZipException e) {
            throw new Refused(where + ": chunk data is damaged (" + e + ")");
        }
    }

    /** Reads a compound, keeping Status / DataVersion / xPos / zPos of the root and of a legacy {@code Level}. */
    private static void readCompound(DataInputStream in, Chunk[] out, int depth) throws IOException {
        while (true) {
            int type = in.readUnsignedByte();
            if (type == 0) return;
            String name = in.readUTF();
            Chunk c = out[0];
            if (depth <= 1 && type == 8 && name.equals("Status")) {
                out[0] = new Chunk(in.readUTF(), c.dataVersion, c.x, c.z);
            } else if (depth <= 1 && type == 3 && (name.equals("DataVersion") || name.equals("xPos") || name.equals("zPos"))) {
                int v = in.readInt();
                out[0] = name.equals("DataVersion") ? new Chunk(c.status, depth == 0 ? Integer.valueOf(v) : c.dataVersion, c.x, c.z)
                        : name.equals("xPos") ? new Chunk(c.status, c.dataVersion, v, c.z) : new Chunk(c.status, c.dataVersion, c.x, v);
            } else if (depth == 0 && type == 10 && name.equals("Level")) {
                readCompound(in, out, 1);
            } else {
                skip(in, type);
            }
        }
    }

    private static void skip(DataInputStream in, int type) throws IOException {
        switch (type) {
            case 1 -> in.skipNBytes(1);
            case 2 -> in.skipNBytes(2);
            case 3, 5 -> in.skipNBytes(4);
            case 4, 6 -> in.skipNBytes(8);
            case 7 -> in.skipNBytes(in.readInt());
            case 8 -> in.skipNBytes(in.readUnsignedShort());
            case 9 -> {
                int element = in.readUnsignedByte(), n = in.readInt();
                for (int i = 0; i < n; i++) skip(in, element);
            }
            case 10 -> {
                int t;
                while ((t = in.readUnsignedByte()) != 0) {
                    in.skipNBytes(in.readUnsignedShort());
                    skip(in, t);
                }
            }
            case 11 -> in.skipNBytes(4L * in.readInt());
            case 12 -> in.skipNBytes(8L * in.readInt());
            default -> throw new IOException("unknown NBT tag type " + type);
        }
    }

    // ---- the swap ----

    /** File operations, replaceable by the self-check to inject failures. */
    interface Ops {
        /** Moves a file or a whole folder; a rename where the volume allows it. */
        default void move(Path from, Path to) throws IOException {
            Files.move(from, to, StandardCopyOption.ATOMIC_MOVE);
        }

        default void copyTree(Path from, Path to) throws IOException {
            WorldImport.copyTree(from, to);
        }
    }

    static final Ops FILES = new Ops() {};

    /** A step done, so it can be undone: a move (move back), a copy or a created folder (delete it). */
    private record Step(Path from, Path to, boolean delete) {
        String undoText() {
            return delete ? "delete " + to : "move " + to + " back to " + from;
        }
    }

    /**
     * Backs up the dimension's terrain into {@code backupDim} and puts the source's parts in place; undoes everything
     * on failure. {@code dimension} is the dimension's storage folder (the world folder for the overworld).
     * Returns a log line about how the parts got there. Throws IOException after a successful undo, and
     * IllegalStateException (journal kept) when the undo failed too.
     */
    static String swap(Path world, Path dimension, Path source, Path backupDim, Ops ops, Log log) throws IOException {
        Path journal = world.resolve(JOURNAL);
        Files.writeString(journal, "# ttl world import in progress; if the server found this file at start, the swap did not finish.\n"
                + "# Check the folders below by hand, put the old terrain back if needed, then delete this file.\n"
                + "source " + source + "\nbackup " + backupDim + "\ndimension " + dimension + "\n", StandardCharsets.UTF_8);
        List<Step> done = new ArrayList<>();
        boolean keptSource = false;
        try {
            Files.createDirectories(backupDim);
            if (!dimension.equals(world)) {
                if (Files.exists(dimension)) step(ops, done, dimension, backupDim.resolve("dimension"));
                Files.createDirectories(dimension);
                done.add(new Step(null, dimension, true));
            } else {
                for (String part : PARTS)
                    if (Files.exists(world.resolve(part))) step(ops, done, world.resolve(part), backupDim.resolve(part));
                Path data = world.resolve("data");
                if (Files.isDirectory(data)) {
                    List<Path> lods = new ArrayList<>();
                    try (DirectoryStream<Path> files = Files.newDirectoryStream(data, "DistantHorizons*")) {
                        files.forEach(lods::add);
                    }
                    for (Path file : lods) step(ops, done, file, backupDim.resolve(file.getFileName()));
                }
            }
            for (String part : PARTS)
                if (Files.exists(dimension.resolve(part))) throw new IOException(dimension.resolve(part) + " is still there after the backup");
            for (String part : PARTS) {
                Path from = source.resolve(part), to = dimension.resolve(part);
                if (!Files.exists(from)) continue;
                try {
                    step(ops, done, from, to);
                } catch (AtomicMoveNotSupportedException e) {
                    // Another volume: copy, verify, keep the source (the operator deletes it once the world is checked).
                    log.warn("[ttl] world import: " + from + " is on another volume; copying (the source is kept)");
                    long need = treeSize(from), free = Files.getFileStore(dimension).getUsableSpace();
                    if (free < need + (1L << 30)) throw new IOException("not enough space to copy " + need + " bytes (" + free + " free, 1 GiB margin)");
                    done.add(new Step(from, to, true));
                    ops.copyTree(from, to);
                    verifyCopy(from, to);
                    keptSource = true;
                }
            }
            if (!Files.isDirectory(dimension.resolve("region"))) throw new IOException("no region folder in " + dimension + " after the swap");
        } catch (IOException | RuntimeException e) {
            log.warn("[ttl] world import failed (" + e + "); undoing " + done.size() + " steps");
            List<String> stuck = undo(done, ops, log);
            if (!stuck.isEmpty()) {
                throw new IllegalStateException("[ttl] world import failed AND could not be undone; the server must not start on a half-swapped world."
                        + " Undo by hand: " + String.join("; ", stuck) + ". Then delete " + journal, e);
            }
            Files.deleteIfExists(journal);
            throw new IOException("world import failed and was undone, the old terrain is back: " + e.getMessage(), e);
        }
        Files.deleteIfExists(journal);
        return keptSource ? "copied (the source in " + source + " is kept; delete it once the world is checked)" : "moved";
    }

    private static void step(Ops ops, List<Step> done, Path from, Path to) throws IOException {
        if (Files.exists(to)) throw new IOException(to + " already exists");
        ops.move(from, to);
        done.add(new Step(from, to, false));
    }

    /** Undoes the steps in reverse order; returns what could not be undone (empty = all undone). */
    private static List<String> undo(List<Step> done, Ops ops, Log log) {
        List<String> stuck = new ArrayList<>();
        for (int i = done.size() - 1; i >= 0; i--) {
            Step s = done.get(i);
            try {
                if (s.delete()) deleteTree(s.to());
                else ops.move(s.to(), s.from());
            } catch (IOException | RuntimeException e) {
                log.warn("[ttl] world import undo failed: " + s.undoText() + " (" + e + ")");
                stuck.add(s.undoText());
            }
        }
        return stuck;
    }

    static void copyTree(Path from, Path to) throws IOException {
        Files.walkFileTree(from, new SimpleFileVisitor<>() {
            @Override
            public FileVisitResult preVisitDirectory(Path dir, BasicFileAttributes attrs) throws IOException {
                Files.createDirectories(to.resolve(from.relativize(dir).toString()));
                return FileVisitResult.CONTINUE;
            }

            @Override
            public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) throws IOException {
                Files.copy(file, to.resolve(from.relativize(file).toString()), StandardCopyOption.COPY_ATTRIBUTES);
                return FileVisitResult.CONTINUE;
            }
        });
    }

    /** Same files with the same sizes on both sides, or IOException. */
    static void verifyCopy(Path from, Path to) throws IOException {
        Map<String, Long> a = sizes(from), b = sizes(to);
        if (!a.equals(b)) throw new IOException("copy of " + from + " does not match: " + a.size() + " files there, " + b.size() + " here or sizes differ");
    }

    private static Map<String, Long> sizes(Path root) throws IOException {
        Map<String, Long> out = new TreeMap<>();
        try (var walk = Files.walk(root)) {
            for (Path p : (Iterable<Path>) walk::iterator)
                if (Files.isRegularFile(p)) out.put(root.relativize(p).toString(), Files.size(p));
        }
        return out;
    }

    private static long treeSize(Path root) throws IOException {
        return sizes(root).values().stream().mapToLong(Long::longValue).sum();
    }

    static void deleteTree(Path root) throws IOException {
        if (!Files.exists(root)) return;
        Files.walkFileTree(root, new SimpleFileVisitor<>() {
            @Override
            public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) throws IOException {
                Files.delete(file);
                return FileVisitResult.CONTINUE;
            }

            @Override
            public FileVisitResult postVisitDirectory(Path dir, IOException e) throws IOException {
                if (e != null) throw e;
                Files.delete(dir);
                return FileVisitResult.CONTINUE;
            }
        });
    }

    // ---- self-check: java -cp build/classes/java/main com.yasuke.ttl.world.WorldImport ----

    public static void main(String[] args) throws Exception {
        Path tmp = Files.createTempDirectory("ttl-import-check");
        Log log = new Log() {
            public void info(String msg) {
                System.out.println("  " + msg);
            }

            public void warn(String msg) {
                System.out.println("  WARN " + msg);
            }
        };
        Predicate<String> known = s -> List.of("minecraft:carvers", "minecraft:full", "carvers", "full", "minecraft:features").contains(s);
        try {
            // Marker parsing.
            check(parse(List.of("# comment", "minecraft:overworld import 800", "")).equals(new Request("minecraft:overworld", "import", 800)), "marker with count");
            check(parse(List.of("minecraft:overworld /data/import")).expectedFiles() == null, "marker without count");
            for (List<String> bad : List.<List<String>>of(List.of(), List.of("# only a comment"), List.of("minecraft:overworld"), List.of("Overworld import"),
                    List.of("minecraft:overworld import x"), List.of("minecraft:overworld import 0"), List.of("minecraft:overworld a", "minecraft:overworld b")))
                refused(() -> parse(bad), "bad marker " + bad);

            // A valid import of the overworld from <server>/import.
            Path server = Files.createDirectories(tmp.resolve("ok")), world = Files.createDirectories(server.resolve("world-ttl"));
            oldWorld(world);
            Path source = Files.createDirectories(server.resolve("import"));
            writeRegion(source.resolve("region"), 0, 0, "minecraft:carvers", 2860, false);
            writeRegion(source.resolve("region"), -1, 0, "full", 2860, false);
            writeRegion(source.resolve("region"), 0, -1, "minecraft:carvers", 2860, true);
            Files.writeString(source.resolve("region").resolve("manifest.sha256"), "x");
            Path resolved = resolveSource(world, world, "import");
            check(resolved.equals(source.normalize()), "relative folder resolves next to the world: " + resolved);
            Report report = validate(resolved.resolve("region"), 3, known, 3955);
            check(report.files() == 3 && report.sampled() == 6 && report.chunks() == 6 && report.statuses().get("minecraft:carvers") == 4, "report: " + report.describe());
            System.out.println("valid source: " + report.describe());
            refused(() -> validate(resolved.resolve("region"), 800, known, 3955), "count mismatch");
            Path backup = world.resolve("ttl-backup").resolve("t1").resolve("minecraft").resolve("overworld");
            String how = swap(world, world, resolved, backup, FILES, log);
            check(how.equals("moved") && Files.exists(world.resolve("region").resolve("r.0.0.mca")) && !Files.exists(world.resolve("region").resolve("r.5.5.mca")),
                    "import in place");
            check(Files.exists(backup.resolve("region").resolve("r.5.5.mca")) && Files.exists(backup.resolve("entities")) && Files.exists(backup.resolve("poi"))
                    && Files.exists(backup.resolve("DistantHorizons.sqlite")) && !Files.exists(world.resolve("data").resolve("DistantHorizons.sqlite")), "old terrain backed up");
            check(Files.exists(world.resolve("data").resolve("other.dat")) && Files.exists(world.resolve("level.dat")), "the rest of the world stays");
            check(!Files.exists(world.resolve(JOURNAL)) && !Files.exists(world.resolve("entities")), "journal gone, no stale entities");

            // Refusals before anything moves.
            Path w2 = Files.createDirectories(tmp.resolve("bad").resolve("world-ttl"));
            oldWorld(w2);
            refused(() -> resolveSource(w2, w2, "missing"), "missing source");
            Files.createDirectories(w2.getParent().resolve("empty").resolve("region"));
            refused(() -> validate(resolveSource(w2, w2, "empty").resolve("region"), null, known, 3955), "no region files");
            refused(() -> resolveSource(w2, w2, "region"), "the world's own region folder");
            refused(() -> resolveSource(w2, w2, "."), "the world itself");
            Path legacy = w2.getParent().resolve("legacy").resolve("region");
            writeRegion(legacy, 0, 0, "liquid_carvers", 2860, false);
            refused(() -> validate(legacy, null, known, 3955), "unknown status liquid_carvers");
            Path future = w2.getParent().resolve("future").resolve("region");
            writeRegion(future, 0, 0, "minecraft:full", 9999, false);
            refused(() -> validate(future, null, known, 3955), "newer DataVersion");
            Path misnamed = w2.getParent().resolve("misnamed").resolve("region");
            writeRegion(misnamed, 0, 0, "minecraft:full", 2860, false);
            Files.move(misnamed.resolve("r.0.0.mca"), misnamed.resolve("r.3.0.mca"));
            refused(() -> validate(misnamed, null, known, 3955), "chunk coordinates do not match the file name");
            Path truncated = w2.getParent().resolve("truncated").resolve("region");
            Files.createDirectories(truncated);
            Files.write(truncated.resolve("r.0.0.mca"), new byte[5000]);
            refused(() -> validate(truncated, null, known, 3955), "truncated region file");
            check(Files.exists(w2.resolve("region").resolve("r.5.5.mca")), "refusals moved nothing");

            // A failure while placing the import: everything is undone.
            Path w3 = Files.createDirectories(tmp.resolve("undo").resolve("world-ttl"));
            oldWorld(w3);
            Path s3 = w3.getParent().resolve("import");
            writeRegion(s3.resolve("region"), 0, 0, "minecraft:carvers", 2860, false);
            Files.createDirectories(s3.resolve("poi"));
            Path b3 = w3.resolve("ttl-backup").resolve("t3").resolve("minecraft").resolve("overworld");
            Ops failOnPoi = new Ops() {
                public void move(Path from, Path to) throws IOException {
                    if (from.equals(s3.resolve("poi"))) throw new IOException("injected failure");
                    FILES.move(from, to);
                }
            };
            try {
                swap(w3, w3, s3, b3, failOnPoi, log);
                check(false, "the injected failure must surface");
            } catch (IOException expected) {
                System.out.println("undo: " + expected.getMessage());
            }
            check(Files.exists(w3.resolve("region").resolve("r.5.5.mca")) && Files.exists(w3.resolve("entities")) && Files.exists(w3.resolve("poi"))
                    && Files.exists(w3.resolve("data").resolve("DistantHorizons.sqlite")), "old terrain back in place");
            check(Files.exists(s3.resolve("region").resolve("r.0.0.mca")) && Files.exists(s3.resolve("poi")) && !Files.exists(w3.resolve(JOURNAL))
                    && !Files.exists(b3.resolve("region")) && !Files.exists(b3.resolve("DistantHorizons.sqlite")), "source back, backup empty, journal gone");

            // The undo fails too: the journal stays and the start is stopped.
            Path w4 = Files.createDirectories(tmp.resolve("stuck").resolve("world-ttl"));
            oldWorld(w4);
            Path s4 = w4.getParent().resolve("import");
            writeRegion(s4.resolve("region"), 0, 0, "minecraft:carvers", 2860, false);
            Path b4 = w4.resolve("ttl-backup").resolve("t4").resolve("minecraft").resolve("overworld");
            Ops failBack = new Ops() {
                public void move(Path from, Path to) throws IOException {
                    if (from.equals(s4.resolve("region")) || from.startsWith(b4)) throw new IOException("injected failure");
                    FILES.move(from, to);
                }
            };
            try {
                swap(w4, w4, s4, b4, failBack, log);
                check(false, "a failed undo must stop the start");
            } catch (IllegalStateException expected) {
                check(expected.getMessage().contains("could not be undone") && Files.exists(w4.resolve(JOURNAL)), "journal kept: " + expected.getMessage());
            }

            // Another volume: a verified copy, the source is kept.
            Path w5 = Files.createDirectories(tmp.resolve("copy").resolve("world-ttl"));
            oldWorld(w5);
            Path s5 = w5.getParent().resolve("import");
            writeRegion(s5.resolve("region"), 0, 0, "minecraft:carvers", 2860, false);
            Ops otherVolume = new Ops() {
                public void move(Path from, Path to) throws IOException {
                    if (from.startsWith(s5)) throw new AtomicMoveNotSupportedException(from.toString(), to.toString(), "injected: other volume");
                    FILES.move(from, to);
                }
            };
            String copied = swap(w5, w5, s5, w5.resolve("ttl-backup").resolve("t5"), otherVolume, log);
            check(copied.startsWith("copied") && Files.size(w5.resolve("region").resolve("r.0.0.mca")) == Files.size(s5.resolve("region").resolve("r.0.0.mca"))
                    && Files.exists(s5.resolve("region")), "copy in place, source kept");

            // A non-overworld dimension: its whole folder is backed up and the import goes into a fresh one.
            Path w6 = Files.createDirectories(tmp.resolve("dim").resolve("world-ttl"));
            Path dim = Files.createDirectories(w6.resolve("dimensions").resolve("ttl").resolve("test").resolve("region"));
            Files.writeString(dim.resolve("r.9.9.mca"), "old");
            Path s6 = w6.getParent().resolve("import");
            writeRegion(s6.resolve("region"), 0, 0, "minecraft:full", 2860, false);
            Path d6 = w6.resolve("dimensions").resolve("ttl").resolve("test");
            swap(w6, d6, resolveSource(w6, d6, "import"), w6.resolve("ttl-backup").resolve("t6").resolve("ttl").resolve("test"), FILES, log);
            check(Files.exists(d6.resolve("region").resolve("r.0.0.mca")) && !Files.exists(d6.resolve("region").resolve("r.9.9.mca"))
                    && Files.exists(w6.resolve("ttl-backup").resolve("t6").resolve("ttl").resolve("test").resolve("dimension").resolve("region").resolve("r.9.9.mca")), "dimension import");
            System.out.println("world import self-check passed");
        } finally {
            deleteTree(tmp);
        }
    }

    private static void oldWorld(Path world) throws IOException {
        Files.createDirectories(world.resolve("region"));
        Files.writeString(world.resolve("region").resolve("r.5.5.mca"), "old terrain");
        Files.createDirectories(world.resolve("entities"));
        Files.createDirectories(world.resolve("poi"));
        Files.createDirectories(world.resolve("data"));
        Files.writeString(world.resolve("data").resolve("DistantHorizons.sqlite"), "lods");
        Files.writeString(world.resolve("data").resolve("other.dat"), "keep");
        Files.writeString(world.resolve("level.dat"), "keep");
    }

    /** A region file with two zlib (or gzip) chunks, at local 0,0 and 31,31, carrying the given Status and DataVersion. */
    private static void writeRegion(Path dir, int rx, int rz, String status, int version, boolean gzip) throws IOException {
        Files.createDirectories(dir);
        ByteArrayOutputStream file = new ByteArrayOutputStream();
        byte[] header = new byte[8192];
        List<byte[]> bodies = new ArrayList<>();
        int sector = 2;
        for (int local : new int[] {0, 1023}) {
            ByteArrayOutputStream raw = new ByteArrayOutputStream();
            try (DataOutputStream nbt = new DataOutputStream(gzip ? new java.util.zip.GZIPOutputStream(raw) : new java.util.zip.DeflaterOutputStream(raw))) {
                nbt.writeByte(10);
                nbt.writeUTF("");
                nbt.writeByte(3);
                nbt.writeUTF("DataVersion");
                nbt.writeInt(version);
                nbt.writeByte(9); // sections: a list of compounds, skipped
                nbt.writeUTF("sections");
                nbt.writeByte(10);
                nbt.writeInt(1);
                nbt.writeByte(12);
                nbt.writeUTF("data");
                nbt.writeInt(2);
                nbt.writeLong(1);
                nbt.writeLong(2);
                nbt.writeByte(0);
                nbt.writeByte(3);
                nbt.writeUTF("xPos");
                nbt.writeInt(rx * 32 + (local & 31));
                nbt.writeByte(3);
                nbt.writeUTF("zPos");
                nbt.writeInt(rz * 32 + (local >> 5));
                nbt.writeByte(8);
                nbt.writeUTF("Status");
                nbt.writeUTF(status);
                nbt.writeByte(0);
            }
            byte[] data = raw.toByteArray();
            ByteArrayOutputStream body = new ByteArrayOutputStream();
            DataOutputStream b = new DataOutputStream(body);
            b.writeInt(data.length + 1);
            b.writeByte(gzip ? 1 : 2);
            b.write(data);
            int sectors = (body.size() + 4095) / 4096;
            byte[] padded = java.util.Arrays.copyOf(body.toByteArray(), sectors * 4096);
            int entry = (sector << 8) | sectors;
            header[local * 4] = (byte) (entry >>> 24);
            header[local * 4 + 1] = (byte) (entry >>> 16);
            header[local * 4 + 2] = (byte) (entry >>> 8);
            header[local * 4 + 3] = (byte) entry;
            bodies.add(padded);
            sector += sectors;
        }
        file.write(header);
        for (byte[] body : bodies) file.write(body);
        Files.write(dir.resolve("r." + rx + "." + rz + ".mca"), file.toByteArray());
    }

    private interface Action {
        void run() throws Exception;
    }

    private static void refused(Action action, String what) throws Exception {
        try {
            action.run();
        } catch (Refused expected) {
            System.out.println("refused (" + what + "): " + expected.getMessage());
            return;
        }
        throw new AssertionError("world import self-check failed: not refused: " + what);
    }

    private static void check(boolean ok, String what) {
        if (!ok) throw new AssertionError("world import self-check failed: " + what);
    }
}
