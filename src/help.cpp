#include "help.h"
#include <string>

const std::string& GetHelp() {
    const static std::string txt = R"(
atracdenc is a tool to encode in to ATRAC1 or ATRAC3, ATRAC3PLUS, decode from ATRAC1 formats

Usage:
atracdenc {-e <codec> | --encode=<codec> | -d | --decode} -i <in> -o <out>

-e or --encode		encode file using one of codecs
	{atrac1 | atrac3 | atrac3_lp | atrac3plus}
-d or --decode		decode file (only ATRAC1 supported for decoding)
-i			path to input file
-o			path to output file
-h			print help and exit

--bitrate		allow to specify bitrate (for ATRAC3 + RealMedia container only)
--notonal		disable tonal component coding (ATRAC3)
--nogaincontrol		disable gain control side info (ATRAC3)
--ml-hints		enable ML-style hint policy (ATRAC3, syntax-compatible)
--parity		enable experimental parity analysis path (ATRAC3, currently not quality-recommended)
--parity-search	enable risky-frame local candidate search (ATRAC3, experimental/off by default)
--quality-v10		force legacy v10-style allocation/stereo policy (ATRAC3, quality baseline mode)
--quality-v10-stable	enable continuity clamps on top of legacy v10 policy (ATRAC3, tuning mode)
--stereo-exp		enable LP2 joint-stereo experiment lane (ATRAC3, testing mode)
--stereo-balance-exp	enable LP2 non-JS stereo bit-balance experiment lane (ATRAC3, testing mode)
--gain-exp		enable very narrow gain-control experiments (ATRAC3, testing mode)
--gain-exp2		enable high-band-only gain experiment lane (ATRAC3, testing mode)
--decision-log <file>	write frame decision log for parity analysis (ATRAC3)
--start-frame <n>	start parity/log analysis window at frame n (ATRAC3)
--max-frames <n>	limit parity/log analysis window to n frames; 0 means full file (ATRAC3)

Advanced options:
--bfuidxconst		Set constant amount of used BFU (ATRAC1, ATRAC3).
--notransient[=mask]	Disable transient detection and use optional mask
			to set bands with forced short MDCT window (ATRAC1)

Examples:
Encode in to ATRAC1 (SP)
	atracdenc -e atrac1 -i my_file.wav -o my_file.aea
Encode in to ATRAC3 (LP2)
	atracdenc -e atrac3 -i my_file.wav -o my_file.oma
Encode in to ATRAC3PLUS
	atracdenc -e atrac3plus -i my_file.wav -o my_file.oma

)";

    return txt;
}
