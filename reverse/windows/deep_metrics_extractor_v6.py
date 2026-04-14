#!/usr/bin/env python3
"""
deep_metrics_extractor_v6.py

LP2 deep metrics extractor for at3tool.exe (Frida).
Focuses on robust per-call correlation so complexity/residual/actual fields are non-zero,
and captures segment energies from the LP2 path where available.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import frida

DEFAULT_AT3TOOL = Path(r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\at3tool.exe")
DEFAULT_OUT_DIR = Path(r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows")
DEFAULT_SOURCES = [
    Path(r"C:\Users\Igland\Antigravity\Ghidra\atracdenc\YOUtopia_source.wav"),
    Path(r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\quality\input\chirp_20_20k_5s.wav"),
]

RVAS = {
    "atrac3_entry": 0x4D20,
    "lp2_main": 0x3D1F0,
    "tonal_bits": 0x3CEB0,
    "gain_bits": 0x3D080,
    "extra_bits": 0x3CE80,
    "e8c0": 0x3E8C0,
    "tonal_candidate": 0x3F110,
    "energy_fn": 0x3EC60,
}

CSV_FIELDS = [
    "sample_name",
    "frame_idx",
    "channel",
    "num_bands",
    "target_bits",
    "sideinfo_bits",
    "tonal_bits",
    "gain_bits",
    "extra_bits",
    "residual_bits",
    "actual_bits_used",
    "complexity_score",
    "num_tonals",
    "tonal_candidate_count",
    "tonal_promoted_count",
    "transient_flag_raw",
    "transient_triggered",
    "attack_ratio",
    "matrix_index",
    "weight_idx",
    "gain_points_per_band",
    "energies",
]


def build_script(rvas: dict[str, int]) -> str:
    js_consts = "\n".join(f"var RVA_{k.upper()} = {hex(v)};" for k, v in rvas.items())
    return js_consts + r"""
var moduleBase = Process.mainModule.base;
var frameCounter = 0;
var lp2ChannelCounter = 0;
var callSeq = 0;

var callState = {};
var activeCallStackByTid = {};

function tidKey() {
  return Process.getCurrentThreadId().toString();
}

function getActiveCallId() {
  var tid = tidKey();
  var stack = activeCallStackByTid[tid];
  if (!stack || stack.length === 0) return null;
  return stack[stack.length - 1];
}

function readEnergies(ptrVal) {
  var out = [];
  for (var i = 0; i < 8; i++) {
    try {
      out.push(ptrVal.add(i * 4).readFloat());
    } catch (e) {
      out.push(0.0);
    }
  }
  return out;
}

function attackRatio(energies) {
  var best = 0.0;
  // Ignore S0/S1 boundary here; S0 is often a sentinel-like floor value.
  for (var i = 2; i < energies.length; i++) {
    var prev = energies[i - 1];
    var cur = energies[i];
    var ratio = cur / Math.max(Math.abs(prev), 1e-9);
    if (ratio > best) best = ratio;
  }
  return best;
}

send({type: 'log', msg: 'LP2 deep extractor v6 loaded. Base=' + moduleBase});

Interceptor.attach(moduleBase.add(RVA_ATRAC3_ENTRY), {
  onEnter: function () {
    frameCounter++;
    lp2ChannelCounter = 0;
  }
});

Interceptor.attach(moduleBase.add(RVA_LP2_MAIN), {
  onEnter: function (args) {
    var callId = 'c' + (++callSeq);
    this.callId = callId;
    this.ctx = args[2];
    this.frame = frameCounter;
    this.channel = lp2ChannelCounter % 2;
    lp2ChannelCounter++;

    callState[callId] = {
      tonal_bits: 0,
      gain_bits: 0,
      extra_bits: 0,
      costs: [],
      tonal_candidates: [],
      energies: [0, 0, 0, 0, 0, 0, 0, 0],
    };

    var tid = tidKey();
    if (!activeCallStackByTid[tid]) activeCallStackByTid[tid] = [];
    activeCallStackByTid[tid].push(callId);
  },

  onLeave: function (retval) {
    var tid = tidKey();
    var stack = activeCallStackByTid[tid];
    if (stack && stack.length > 0) stack.pop();

    if (retval.toInt32() === -0x8000) {
      delete callState[this.callId];
      return;
    }

    var st = callState[this.callId];
    if (!st) return;

    try {
      var ctx = this.ctx;
      var numBands = ctx.readS32();
      var matrixIdx = ctx.add(4).readS32();
      var targetBits = ctx.add(0x1872 * 4).readS32();
      var transientFlag = ctx.add(0x1860 * 4).readS32();
      var numTonals = ctx.add(0x110 * 4).readS32();

      var weights = [];
      var gainPoints = [];
      for (var i = 0; i < 4; i++) {
        weights.push(ctx.add((0x143f + i) * 4).readS32());
        gainPoints.push(ctx.add((0x141f + i) * 4).readS32());
      }

      var residualBits = st.costs.length > 0 ? st.costs[0] : 0;
      var actualBits = st.costs.length > 0 ? st.costs[st.costs.length - 1] : 0;
      var complexity = actualBits - residualBits;
      var candMax = 0;
      for (var j = 0; j < st.tonal_candidates.length; j++) {
        if (st.tonal_candidates[j] > candMax) candMax = st.tonal_candidates[j];
      }
      var atk = attackRatio(st.energies);

      var row = {
        frame_idx: this.frame,
        channel: this.channel,
        num_bands: numBands,
        target_bits: targetBits,
        sideinfo_bits: st.tonal_bits + st.gain_bits + st.extra_bits,
        tonal_bits: st.tonal_bits,
        gain_bits: st.gain_bits,
        extra_bits: st.extra_bits,
        residual_bits: residualBits,
        actual_bits_used: actualBits,
        complexity_score: complexity,
        num_tonals: numTonals,
        tonal_candidate_count: candMax,
        tonal_promoted_count: numTonals,
        transient_flag_raw: transientFlag,
        transient_triggered: (atk > 2.0) ? 1 : 0,
        attack_ratio: atk,
        matrix_index: matrixIdx,
        weight_idx: weights.join(';'),
        gain_points_per_band: gainPoints.join(';'),
        energies: st.energies.join(';'),
      };
      send({type: 'row', data: row});
    } catch (e) {
      send({type: 'log', msg: 'LP2 onLeave read error: ' + e});
    } finally {
      delete callState[this.callId];
    }
  }
});

Interceptor.attach(moduleBase.add(RVA_TONAL_BITS), {
  onLeave: function (retval) {
    var callId = getActiveCallId();
    if (!callId || !callState[callId]) return;
    callState[callId].tonal_bits = retval.toInt32();
  }
});

Interceptor.attach(moduleBase.add(RVA_GAIN_BITS), {
  onLeave: function (retval) {
    var callId = getActiveCallId();
    if (!callId || !callState[callId]) return;
    callState[callId].gain_bits = retval.toInt32();
  }
});

Interceptor.attach(moduleBase.add(RVA_EXTRA_BITS), {
  onLeave: function (retval) {
    var callId = getActiveCallId();
    if (!callId || !callState[callId]) return;
    callState[callId].extra_bits = retval.toInt32();
  }
});

Interceptor.attach(moduleBase.add(RVA_E8C0), {
  onEnter: function (args) {
    this.costPtr = args[5];
    this.callId = getActiveCallId();
  },
  onLeave: function () {
    if (!this.callId || !callState[this.callId]) return;
    try {
      callState[this.callId].costs.push(this.costPtr.readS32());
    } catch (e) {
    }
  }
});

Interceptor.attach(moduleBase.add(RVA_TONAL_CANDIDATE), {
  onLeave: function (retval) {
    var callId = getActiveCallId();
    if (!callId || !callState[callId]) return;
    callState[callId].tonal_candidates.push(retval.toInt32());
  }
});

Interceptor.attach(moduleBase.add(RVA_ENERGY_FN), {
  onEnter: function (args) {
    this.energyPtr = args[1];
    this.callId = getActiveCallId();
  },
  onLeave: function () {
    if (!this.callId || !callState[this.callId]) return;
    try {
      callState[this.callId].energies = readEnergies(this.energyPtr);
    } catch (e) {
    }
  }
});
"""


def run_one(
    at3tool: Path,
    bitrate: int,
    sample_path: Path,
    output_dir: Path,
    *,
    max_runtime_s: int,
    stall_timeout_s: int,
    heartbeat_s: int,
) -> tuple[Path, Path, int]:
    sample_name = sample_path.stem
    csv_path = output_dir / f"deep_metrics_{sample_name}.csv"
    jsonl_path = output_dir / f"deep_metrics_{sample_name}.jsonl"

    row_count = 0
    max_frame_idx = -1
    start_ts = time.time()
    last_progress_ts = start_ts
    last_heartbeat_ts = start_ts
    output_dir.mkdir(parents=True, exist_ok=True)

    with csv_path.open("w", newline="", encoding="utf-8") as f_csv, jsonl_path.open(
        "w", encoding="utf-8"
    ) as f_jsonl:
        writer = csv.DictWriter(f_csv, fieldnames=CSV_FIELDS)
        writer.writeheader()

        def on_message(message, data):
            nonlocal row_count, max_frame_idx, last_progress_ts
            if message["type"] == "send":
                payload = message["payload"]
                ptype = payload.get("type")
                if ptype == "row":
                    rec = payload["data"]
                    try:
                        max_frame_idx = max(max_frame_idx, int(rec.get("frame_idx", -1)))
                    except (TypeError, ValueError):
                        pass
                    rec["sample_name"] = sample_name
                    writer.writerow(rec)
                    f_jsonl.write(json.dumps(rec) + "\n")
                    row_count += 1
                    last_progress_ts = time.time()
                    if row_count % 500 == 0:
                        sys.stdout.write(f"\r  streamed {row_count} rows")
                        sys.stdout.flush()
                elif ptype == "log":
                    print(f"\n  [JS] {payload.get('msg', '')}")
            elif message["type"] == "error":
                print(f"\n  [FRIDA ERROR] {message.get('description', 'unknown')}")

        temp_out = str(output_dir / "temp_lp2_v6.at3")
        pid = frida.spawn([str(at3tool), "-e", "-br", str(bitrate), str(sample_path), temp_out])
        session = frida.attach(pid)
        script = session.create_script(build_script(RVAS))
        script.on("message", on_message)
        script.load()
        frida.resume(pid)

        while True:
            now = time.time()
            elapsed = now - start_ts
            no_progress_for = now - last_progress_ts
            if now - last_heartbeat_ts >= heartbeat_s:
                print(
                    f"\n  [hb] rows={row_count} max_frame={max_frame_idx} "
                    f"elapsed={int(elapsed)}s idle={int(no_progress_for)}s"
                )
                last_heartbeat_ts = now

            alive = True
            try:
                os.kill(pid, 0)
            except OSError:
                alive = False

            if not alive:
                break
            if elapsed > max_runtime_s:
                print(f"\n  [guard] max runtime reached ({max_runtime_s}s), terminating PID {pid}")
                frida.kill(pid)
                break
            if no_progress_for > stall_timeout_s:
                print(
                    f"\n  [guard] no progress for {stall_timeout_s}s "
                    f"(rows={row_count}, max_frame={max_frame_idx}), terminating PID {pid}"
                )
                frida.kill(pid)
                break
            time.sleep(1.0)

        time.sleep(2.0)
        session.detach()

    return csv_path, jsonl_path, row_count


def main() -> None:
    ap = argparse.ArgumentParser(description="Extract LP2 deep metrics from at3tool.exe")
    ap.add_argument("--at3tool", type=Path, default=DEFAULT_AT3TOOL)
    ap.add_argument("--bitrate", type=int, default=132)
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUT_DIR)
    ap.add_argument("--max-runtime-s", type=int, default=1800)
    ap.add_argument("--stall-timeout-s", type=int, default=180)
    ap.add_argument("--heartbeat-s", type=int, default=30)
    ap.add_argument("--kill-stale-at3tool", action="store_true")
    ap.add_argument("sources", nargs="*", type=Path)
    args = ap.parse_args()

    sources = args.sources if args.sources else DEFAULT_SOURCES

    if not args.at3tool.exists():
        raise SystemExit(f"at3tool not found: {args.at3tool}")

    if args.kill_stale_at3tool:
        subprocess.run(
            ["taskkill", "/F", "/IM", "at3tool.exe"],
            capture_output=True,
            text=True,
            check=False,
        )

    ran = 0
    for src in sources:
        if not src.exists():
            print(f"[skip] missing source: {src}")
            continue
        print(f"\n[*] extracting {src.name}")
        csv_path, jsonl_path, count = run_one(
            args.at3tool,
            args.bitrate,
            src,
            args.output_dir,
            max_runtime_s=args.max_runtime_s,
            stall_timeout_s=args.stall_timeout_s,
            heartbeat_s=args.heartbeat_s,
        )
        print(f"\n[ok] rows={count} csv={csv_path} jsonl={jsonl_path}")
        ran += 1

    if ran == 0:
        raise SystemExit("no sources extracted")


if __name__ == "__main__":
    main()
