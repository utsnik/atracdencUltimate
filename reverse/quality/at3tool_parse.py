import struct


def _read_u16le(b, off):
    return struct.unpack_from("<H", b, off)[0]


def _read_u32le(b, off):
    return struct.unpack_from("<I", b, off)[0]


class BitReader:
    def __init__(self, data):
        self.data = data
        self.pos = 0  # bit position

    def read(self, n):
        val = 0
        for _ in range(n):
            byte_idx = self.pos // 8
            bit_idx = self.pos % 8
            if byte_idx >= len(self.data):
                raise EOFError("bitstream overrun")
            bit = (self.data[byte_idx] >> (7 - bit_idx)) & 1
            val = (val << 1) | bit
            self.pos += 1
        return val


def _make_signed(val, bits):
    sign = 1 << (bits - 1)
    mask = (1 << bits) - 1
    val &= mask
    return (val ^ sign) - sign


def _gen_huff_tables_wl():
    # Parse tables from atrac3plus_data.h by hardcoding the arrays here.
    # Keep in sync with ff/atrac3plus_data.h in atracdenc.
    atrac3p_wl_cbs = [
        [1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [1, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [1, 0, 2, 3, 2, 0, 0, 0, 0, 0, 0, 0],
        [1, 0, 2, 3, 2, 0, 0, 0, 0, 0, 0, 0],
    ]
    atrac3p_wl_ct_xlats = [
        0, 1, 7,
        0, 1, 2, 3,
        0, 1, 2, 6, 7,
        0, 1, 2, 3, 4, 5, 6, 7,
        0, 1, 7, 2, 5, 6, 3, 4,
        0, 1, 2, 3, 6, 7, 4, 5,
        0, 1, 7, 2, 3, 6, 4, 5,
        0, 1, 2, 3, 4, 5, 6, 7,
    ]

    def gen_table(cb, xlat, out_len):
        code = 0
        idx = 0
        table = [(0, 0)] * out_len
        for b in range(1, 13):
            count = cb[b - 1]
            for _ in range(count):
                sym = xlat[idx]
                table[sym] = (code, b)
                idx += 1
                code += 1
            code <<= 1
        return table, idx

    wl_tabs = []
    x = 0
    for i in range(4):
        wl_tab, used = gen_table(atrac3p_wl_cbs[i], atrac3p_wl_ct_xlats[x:], 8)
        x += used
        # skip code table for this i
        ct_tab, used2 = gen_table(atrac3p_ct_cbs[i], atrac3p_wl_ct_xlats[x:], 8)
        x += used2
        wl_tabs.append(wl_tab)
    # Build decoding maps
    dec = []
    for tab in wl_tabs:
        m = {}
        for sym, (code, length) in enumerate(tab):
            if length > 0:
                m[(code, length)] = sym
        dec.append(m)
    return dec


atrac3p_ct_cbs = [
    [1, 1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 1, 5, 2, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 1, 5, 2, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 0, 1, 6, 0, 0, 0, 0, 0, 0, 0, 0],
]


_WL_DEC = _gen_huff_tables_wl()


def _decode_vlc(br, table):
    code = 0
    for length in range(1, 13):
        code = (code << 1) | br.read(1)
        key = (code, length)
        if key in table:
            return table[key]
    raise ValueError("VLC decode failed")


def parse_at3_frames(data, frame_size):
    frames = []
    num_frames = len(data) // frame_size
    for fi in range(num_frames):
        frame = data[fi * frame_size:(fi + 1) * frame_size]
        br = BitReader(frame)
        br.read(1)  # start bit
        ch_mode = br.read(2)
        channels = ch_mode + 1
        num_qu = br.read(5) + 1
        br.read(1)  # mute flag

        # Wordlen (mono only for now)
        wl = []
        mode = br.read(2)
        if mode == 0:
            br.read(2)  # weight idx
            br.read(2)  # num_coded_vals
            for _ in range(num_qu):
                wl.append(br.read(3))
        else:
            br.read(2)  # weight idx
            br.read(2)  # num_coded_vals
            idx = br.read(2)
            first = br.read(3)
            wl.append(first)
            dec_tab = _WL_DEC[idx]
            for _ in range(1, num_qu):
                delta = _decode_vlc(br, dec_tab)
                delta = _make_signed(delta, 3)
                wl.append((wl[-1] + delta) & 7)

        # SF idx
        sf = []
        br.read(2)  # const bits
        for _ in range(num_qu):
            sf.append(br.read(6))

        # Spec tab idx (mono)
        spec_tab = []
        use_full = br.read(1)
        br.read(1)  # table type
        br.read(2)  # const bits
        br.read(1)  # num_coded_vals
        bits = 2 + use_full
        for _ in range(num_qu):
            spec_tab.append(br.read(bits))

        frames.append({
            "channels": channels,
            "num_qu": num_qu,
            "wordlen": wl,
            "sf_idx": sf,
            "spec_tab": spec_tab,
        })
    return frames


def parse_at3_file(path):
    with open(path, "rb") as f:
        data = f.read()
    if data.startswith(b"RIFF"):
        # Parse RIFF/WAVE
        off = 12
        fmt = None
        payload = None
        while off + 8 <= len(data):
            chunk_id = data[off:off + 4]
            size = _read_u32le(data, off + 4)
            off += 8
            if chunk_id == b"fmt ":
                fmt = data[off:off + size]
            elif chunk_id == b"data":
                payload = data[off:off + size]
            off += size + (size & 1)
        if fmt is None or payload is None:
            raise ValueError("Invalid RIFF/WAVE")
        block_align = _read_u16le(fmt, 12)
        return parse_at3_frames(payload, block_align)
    if data.startswith(b"EA3"):
        # OMA/EA3
        if len(data) < 96:
            raise ValueError("Invalid EA3 header")
        params = int.from_bytes(data[32:36], "big", signed=False)
        frame_size = ((params & 0x3FF) * 8) + 8
        payload = data[96:]
        return parse_at3_frames(payload, frame_size)
    raise ValueError("Unknown file format")
