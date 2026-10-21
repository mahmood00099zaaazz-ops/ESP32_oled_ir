"""Cut long block recordings into one WAV per sentence.

Record each block of 50 sentences as one file, pausing 2 seconds between
sentences (the studio page does the timing). Name the file as the studio
page shows at the end of the block:

    b03.m4a              block 3 (sentences 101-150), no mistakes
    b03_r112_131.m4a     block 3, sentences 112 and 131 were read twice

For a sentence read more than once, the last take is kept.

Usage:
    python3 split_blocks.py RECORDINGS_DIR OUTPUT_DIR
Writes OUTPUT_DIR/badini_0101.wav ... (22050 Hz, mono, 16-bit), ready for Piper.
"""

import os
import re
import subprocess
import sys

BLOCK_SIZE = 50
TOTAL = 1000
SAMPLE_RATE = 22050
SILENCE_DB = -35   # quieter than this counts as silence
MIN_PAUSE = 1.0    # seconds of silence between two sentences
PAD = 0.2          # seconds of silence kept before and after each sentence

NAME_RE = re.compile(r"^b(\d{1,2})((?:_r\d{1,4})*)$", re.IGNORECASE)


def parse_name(stem):
    m = NAME_RE.match(stem)
    if not m:
        return None
    block = int(m.group(1))
    repeats = [int(n) for n in re.findall(r"\d+", m.group(2))]
    return block, repeats


def expected_order(block, repeats):
    """Sentence numbers in the order they were spoken."""
    first = (block - 1) * BLOCK_SIZE + 1
    last = min(block * BLOCK_SIZE, TOTAL)
    order = []
    for n in range(first, last + 1):
        order.extend([n] * (1 + repeats.count(n)))
    return order


def duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", path],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout)


def find_speech(path):
    """Return [(start, end)] of the parts between long silences."""
    out = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af",
         f"silencedetect=noise={SILENCE_DB}dB:d={MIN_PAUSE}", "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", out)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out)]
    total = duration(path)

    segments, pos = [], 0.0
    for s, e in zip(starts, ends + [total] * (len(starts) - len(ends))):
        if s - pos > 0.3:
            segments.append((pos, s))
        pos = e
    if total - pos > 0.3:
        segments.append((pos, total))
    return segments, total


def cut(src, start, end, dst):
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
         "-ss", f"{start:.3f}", "-to", f"{end:.3f}", "-i", src,
         "-ac", "1", "-ar", str(SAMPLE_RATE), "-sample_fmt", "s16", dst],
        check=True,
    )


def split_file(path, out_dir):
    stem = os.path.splitext(os.path.basename(path))[0]
    parsed = parse_name(stem)
    if not parsed:
        print(f"  ? {os.path.basename(path)}: name should look like b03 or b03_r112_131, skipped")
        return False
    order = expected_order(*parsed)
    segments, total = find_speech(path)

    if len(segments) != len(order):
        print(f"  ✗ {os.path.basename(path)}: found {len(segments)} sentences, expected {len(order)}.")
        print("    Check that you paused 2 seconds between sentences and that the room was quiet.")
        print("    Lengths found (s): " + ", ".join(f"{e - s:.1f}" for s, e in segments))
        return False

    takes = {}
    for n, seg in zip(order, segments):
        takes[n] = seg  # a later take replaces an earlier one
    for n, (s, e) in takes.items():
        cut(path, max(0.0, s - PAD), min(total, e + PAD),
            os.path.join(out_dir, f"badini_{n:04d}.wav"))
    print(f"  ✓ {os.path.basename(path)}: sentences {min(takes)}–{max(takes)} saved")
    return True


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    rec_dir, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    files = sorted(f for f in os.listdir(rec_dir) if not f.startswith("."))
    ok = sum(split_file(os.path.join(rec_dir, f), out_dir) for f in files)
    done = len([f for f in os.listdir(out_dir) if f.endswith(".wav")])
    print(f"\n{ok}/{len(files)} files split. {done} of {TOTAL} sentences ready.")


if __name__ == "__main__":
    main()
