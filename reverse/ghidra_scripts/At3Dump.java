// Ghidra Java script: dump analysis artifacts to JSON for AI ingestion
// Usage (headless): -postScript At3Dump.java <output_dir>
//@category Export

import java.io.File;
import java.io.FileWriter;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.data.StringDataInstance;
import ghidra.program.model.listing.Data;
import ghidra.program.model.listing.DataIterator;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.symbol.ExternalLocation;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;
import ghidra.program.model.symbol.SymbolTable;
import ghidra.program.model.symbol.SymbolType;

public class At3Dump extends GhidraScript {

	private Gson gson = new GsonBuilder().setPrettyPrinting().create();

	@Override
	public void run() throws Exception {
		String[] args = getScriptArgs();
		if (args == null || args.length < 1) {
			printerr("At3Dump.java requires output_dir argument");
			return;
		}

		File outDir = new File(args[0]);
		if (!outDir.isAbsolute()) {
			outDir = outDir.getAbsoluteFile();
		}
		if (!outDir.exists()) {
			outDir.mkdirs();
		}

		if (currentProgram == null) {
			printerr("No program loaded");
			return;
		}

		dumpOverview(outDir);
		dumpStrings(outDir);
		dumpFunctions(outDir);
		dumpImportsExports(outDir);
		dumpDecompilation(outDir);
		dumpData(outDir);
	}

	private void dumpData(File outDir) throws Exception {
		Listing listing = currentProgram.getListing();
		DataIterator it = listing.getDefinedData(true);
		List<Map<String, Object>> dataList = new ArrayList<>();
		int maxData = 10000;
		while (it.hasNext() && dataList.size() < maxData && !monitor.isCancelled()) {
			Data data = it.next();
			if (data.isPointer() || data.isString() || data.isStructure()) {
				continue;
			}
			
			String type = data.getDataType().getName().toLowerCase();
			if (type.contains("float") || type.contains("double") || type.contains("undefined4")) {
				Map<String, Object> entry = new HashMap<>();
				entry.put("address", data.getAddress().toString());
				entry.put("type", type);
				entry.put("value", data.getValue() != null ? data.getValue().toString() : "null");
				
				// If it's undefined4, try to interpret as float
				if (type.contains("undefined4")) {
					try {
						int raw = (int)data.getScalar(0).getUnsignedValue();
						float f = Float.intBitsToFloat(raw);
						entry.put("as_float", f);
					} catch (Exception e) {}
				}
				
				dataList.add(entry);
			}
		}
		writeJson(new File(outDir, "data.json"), dataList);
	}

	private void dumpOverview(File outDir) throws Exception {
		Map<String, Object> info = new HashMap<>();
		info.put("name", currentProgram.getName());
		info.put("language", currentProgram.getLanguageID().toString());
		info.put("compiler", currentProgram.getCompilerSpec().getCompilerSpecID().toString());
		info.put("image_base", currentProgram.getImageBase().toString());
		writeJson(new File(outDir, "overview.json"), info);
	}

	private void dumpStrings(File outDir) throws Exception {
		Listing listing = currentProgram.getListing();
		DataIterator it = listing.getDefinedData(true);
		List<Map<String, Object>> strings = new ArrayList<>();
		int maxStrings = 5000;
		while (it.hasNext() && strings.size() < maxStrings && !monitor.isCancelled()) {
			Data data = it.next();
			try {
				StringDataInstance sdi = StringDataInstance.getStringDataInstance(data);
				if (sdi == null) {
					continue;
				}
				String value = sdi.getStringValue();
				if (value == null) {
					continue;
				}
				Map<String, Object> entry = new HashMap<>();
				entry.put("address", data.getAddress().toString());
				entry.put("value", value);
				entry.put("length", sdi.getStringLength());
				strings.add(entry);
			}
			catch (Exception e) {
				// Not a string
			}
		}
		writeJson(new File(outDir, "strings.json"), strings);
	}

	private void dumpFunctions(File outDir) throws Exception {
		FunctionManager fm = currentProgram.getFunctionManager();
		FunctionIterator it = fm.getFunctions(true);
		List<Map<String, Object>> funcs = new ArrayList<>();
		while (it.hasNext() && !monitor.isCancelled()) {
			Function f = it.next();
			Map<String, Object> entry = new HashMap<>();
			entry.put("name", f.getName());
			entry.put("entry", f.getEntryPoint().toString());
			entry.put("signature", f.getSignature().toString());
			entry.put("param_count", f.getParameterCount());
			entry.put("return_type", f.getReturnType().toString());
			entry.put("is_external", f.isExternal());
			entry.put("is_thunk", f.isThunk());
			int size = f.getBody() != null ? (int) f.getBody().getNumAddresses() : 0;
			entry.put("size", size);
			funcs.add(entry);
		}
		writeJson(new File(outDir, "functions.json"), funcs);
	}

	private void dumpImportsExports(File outDir) throws Exception {
		SymbolTable symtab = currentProgram.getSymbolTable();
		List<Map<String, Object>> imports = new ArrayList<>();
		List<Map<String, Object>> exports = new ArrayList<>();

		SymbolIterator extIt = symtab.getExternalSymbols();
		while (extIt.hasNext() && !monitor.isCancelled()) {
			Symbol sym = extIt.next();
			Map<String, Object> entry = new HashMap<>();
			entry.put("name", sym.getName());
			entry.put("address", sym.getAddress().toString());
			entry.put("source", sym.getSource().toString());
			String library = null;
			Object obj = sym.getObject();
			if (obj instanceof ExternalLocation) {
				library = ((ExternalLocation) obj).getLibraryName();
			}
			entry.put("library", library);
			imports.add(entry);
		}

		SymbolIterator symIt = symtab.getAllSymbols(true);
		while (symIt.hasNext() && !monitor.isCancelled()) {
			Symbol sym = symIt.next();
			if (sym.getSymbolType() != SymbolType.FUNCTION) {
				continue;
			}
			if (sym.isExternal()) {
				continue;
			}
			if (!sym.isPrimary()) {
				continue;
			}
			Map<String, Object> entry = new HashMap<>();
			entry.put("name", sym.getName());
			entry.put("address", sym.getAddress().toString());
			entry.put("source", sym.getSource().toString());
			exports.add(entry);
		}

		writeJson(new File(outDir, "imports.json"), imports);
		writeJson(new File(outDir, "exports.json"), exports);
	}

	private void dumpDecompilation(File outDir) throws Exception {
		FunctionManager fm = currentProgram.getFunctionManager();
		FunctionIterator it = fm.getFunctions(true);
		List<Function> funcs = new ArrayList<>();
		while (it.hasNext() && !monitor.isCancelled()) {
			Function f = it.next();
			if (!f.isExternal()) {
				funcs.add(f);
			}
		}

		Collections.sort(funcs, new Comparator<Function>() {
			@Override
			public int compare(Function a, Function b) {
				int sizeA = a.getBody() != null ? (int) a.getBody().getNumAddresses() : 0;
				int sizeB = b.getBody() != null ? (int) b.getBody().getNumAddresses() : 0;
				return Integer.compare(sizeB, sizeA);
			}
		});

		int topN = Math.min(30, funcs.size());
		List<Map<String, Object>> out = new ArrayList<>();
		if (topN == 0) {
			writeJson(new File(outDir, "decompilation.json"), out);
			return;
		}

		DecompInterface iface = new DecompInterface();
		iface.openProgram(currentProgram);

		for (int i = 0; i < topN && !monitor.isCancelled(); i++) {
			Function f = funcs.get(i);
			DecompileResults res = iface.decompileFunction(f, 30, monitor);
			String code = null;
			if (res != null && res.decompileCompleted()) {
				code = res.getDecompiledFunction().getC();
			}

			Map<String, Object> entry = new HashMap<>();
			entry.put("name", f.getName());
			entry.put("entry", f.getEntryPoint().toString());
			int size = f.getBody() != null ? (int) f.getBody().getNumAddresses() : 0;
			entry.put("size", size);
			entry.put("c", code);
			out.add(entry);
		}

		writeJson(new File(outDir, "decompilation.json"), out);
	}

	private void writeJson(File file, Object obj) throws Exception {
		try (FileWriter writer = new FileWriter(file)) {
			gson.toJson(obj, writer);
		}
	}
}
