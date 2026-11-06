import java.io.File; // Input is a separately supplied level.dat, not a running world.
import com.mojang.serialization.*; // Mojang's codec result and lifecycle types.

/**
 * Check world settings using the official Java 1.16.5 server JAR's parser.
 * Obfuscated names below are specific to that version's official mappings.
 * This initializes registries only: it does not start a server or accept an EULA.
 * Compile with: javac -cp /path/to/server-1.16.5.jar CheckWorldSettings.java
 * Run with both that JAR and this class's directory on the Java classpath.
 */
public class CheckWorldSettings {
    public static void main(String[] args) throws Exception {
        vm.a(); // Bootstrap vanilla block, biome and world-generation registrations.
        gn.b registry = gn.b(); // Create a holder containing the built-in registries.
        vh<mt> ops = vh.a(mo.a, new vh.b.a(), registry); // Decode NBT with registry lookups.
        md data = mn.a(new File(args[0])).p("Data").p("WorldGenSettings"); // Read compressed NBT and select the settings compound.
        DataResult<chw> result = chw.a.parse(ops, data); // Parse WorldGenSettings with Minecraft's own codec.
        System.out.println("RESULT=" + result); // Print decoding errors or the successful result.
        System.out.println("LIFECYCLE=" + result.lifecycle()); // Stable/experimental is independent of visual correctness.
        if (!result.result().isPresent()) System.exit(2); // Missing complete result means decoding failed.
        if (result.lifecycle() != Lifecycle.stable()) System.exit(3); // Reject experimental settings even if parsing succeeded.
    }
}
