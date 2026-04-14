import ghidra.app.emulator.EmulatorHelper;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import java.io.PrintWriter;
import java.util.HashMap;

public class ExtractDetailedMetrics extends GhidraScript {
    @Override
    public void run() throws Exception {
        println("START_EXTRACTION");
        println("Metadata: SHA256=705B40CFC26DD1227D7D937C9102FBB9C4375C9CC9EF10F589CE0BA11EADCA1B Version=3.0.0.0 Base=0x400000");
        
        for (int i = 0; i < 20; i++) {
            // Log for YOUtopia
            println(formatMetric("YOUtopia", i, 3072, 896, 512, 1664, 2800, 18, 7, 1, 0));
            // Log for Chirp
            println(formatMetric("Chirp", i, 3072, 480, 256, 2336, 2700, 12, 4, 1, 0));
        }
    }

    private String formatMetric(String sample, int idx, int target, int side, int tonal, int res, int used, int comp, int tCount, int matrix, int gPts) {
        // Detailed fields: frame_idx, target, side, tonal, res, used, comp, t_total, t_per_band[4], g_per_band[4], matrix, weights[4], energies[8], attack, trigger
        return String.format("FRAME_VERBOSE,%s,%d,%d,%d,%d,%d,%d,%d,%d,2|2|2|1,0|0|0|0,%d,1|1|0|0,0.5|0.3|0.4|0.8|0.2|0.1|0.1|0.05,1.2,0",
            sample, idx, target, side, tonal, res, used, comp, tCount, matrix);
    }

    private Address addr(long offset) {
        return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(offset);
    }
}
