#!/usr/bin/env python3
"""Test committed demos independently of the generator and the repacker."""

from pathlib import Path
import os
import re
import struct
import subprocess
import sys
import tempfile


README = (
    b"IMAGEWTY synthetic demo. Not bootable; do not flash to a device.\n"
    b"Contains two editable demo.fex entries, their checksums, and an empty file.\n"
    b"All payloads were created for this project; no vendor firmware is included.\n"
)
PAYLOAD_A = b"IMAGEWTY demo payload A.\nEdit this text, then repack the dump.\n"
PAYLOAD_B = b"IMAGEWTY demo payload B.\nSame archive name, different content.\n"
NAMES = ["README.txt", "demo.fex", "Vdemo.fex", "demo.fex", "Vdemo.fex", "empty.fex"]
LOCAL_NAMES = ["README.txt", "demo.fex", "Vdemo.fex", "demo__2.fex", "Vdemo__2.fex", "empty.fex"]


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def checksum_bytes(data):
    padded = data + bytes((-len(data)) % 4)
    words = struct.unpack("<" + "I" * (len(padded) // 4), padded)
    return struct.pack("<I", sum(words) & 0xFFFFFFFF)


def run(tool, workdir, *args):
    result = subprocess.run([str(tool), *map(str, args)], cwd=workdir,
                            capture_output=True, text=True, timeout=30)
    require(result.returncode == 0,
            f"Command {args!r} failed ({result.returncode}):\n{result.stdout}\n{result.stderr}")
    return result.stdout


def snapshot(folder):
    return {path.name: path.read_bytes() for path in folder.iterdir()}


def check_archive(data, version):
    require(len(data) < 10 * 1024, "Demo must remain below 10 KiB")
    require(data[:8] == b"IMAGEWTY", "Wrong magic")
    require(struct.unpack_from("<I", data, 8)[0] == version, "Wrong header version")
    require(struct.unpack_from("<I", data, 24)[0] == len(data), "Incorrect image size")
    require(struct.unpack_from("<I", data, 32)[0] == 1024, "Incorrect entry size")
    require(struct.unpack_from("<I", data, 60)[0] == len(NAMES), "Incorrect entry count")
    expected = [README, PAYLOAD_A, checksum_bytes(PAYLOAD_A),
                PAYLOAD_B, checksum_bytes(PAYLOAD_B), b""]
    next_offset = 1024 * (len(NAMES) + 1)
    for i, (name, payload) in enumerate(zip(NAMES, expected)):
        base = 1024 * (i + 1)
        actual_name = data[base + 36:base + 292].split(b"\0", 1)[0].decode("ascii")
        require(actual_name == name, f"Entry {i}: wrong name/order")
        stored, pad1, original, pad2, offset = struct.unpack_from("<5I", data, base + 292)
        require(offset == next_offset and offset % 16 == 0, f"Entry {i}: wrong offset")
        require(stored == (len(payload) + 15) // 16 * 16 and original == len(payload),
                f"Entry {i}: wrong sizes")
        require(pad1 == pad2 == 0, f"Entry {i}: unexpected reserved fields")
        require(data[offset:offset + original] == payload, f"Entry {i}: wrong payload/checksum")
        require(data[offset + original:offset + stored] == bytes(stored - original),
                f"Entry {i}: nonzero padding")
        next_offset += stored
    require(next_offset == len(data), "Unexpected trailing data")
    return expected


def main():
    os.environ["ASAN_OPTIONS"] = os.environ.get("ASAN_OPTIONS", "") + ":exitcode=99"
    os.environ["UBSAN_OPTIONS"] = os.environ.get("UBSAN_OPTIONS", "") + ":halt_on_error=1:exitcode=98"
    tool = Path(sys.argv[1]).resolve()
    fixtures = Path(__file__).resolve().parent / "fixtures"
    for label, version in (("v3", 0x300), ("v4", 0x403)):
        image = fixtures / f"demo-{label}.img"
        original = image.read_bytes()
        expected = check_archive(original, version)
        with tempfile.TemporaryDirectory(prefix="imagewty-demo-") as temporary:
            workdir = Path(temporary)
            run(tool, workdir, "info", image)
            run(tool, workdir, "extract", image)
            dump = workdir / (image.name + ".dump")
            require(set(snapshot(dump)) == set(LOCAL_NAMES + ["image.cfg"]), "Wrong local names")
            for name, payload in zip(LOCAL_NAMES, expected):
                require((dump / name).read_bytes() == payload, f"Wrong extracted data: {name}")
            config = (dump / "image.cfg").read_text()
            require(re.findall(r'^filename="(.*)";', config, re.MULTILINE) == NAMES,
                    "Config lost original names/order")
            require(re.findall(r'^source_path="(.*)";', config, re.MULTILINE) == LOCAL_NAMES,
                    "Config lost local name mapping")
            run(tool, workdir, "config", dump / "image.cfg")
            before = snapshot(dump)
            run(tool, workdir, "repack", dump, "roundtrip.img")
            require((workdir / "roundtrip.img").read_bytes() == original, "Round-trip differs")
            require(snapshot(dump) == before, "Round-trip changed the input dump")

            edited = b"Edited demo payload for the CI round-trip.\n"
            (dump / "demo.fex").write_bytes(edited)
            before = snapshot(dump)
            run(tool, workdir, "repack", dump, "edited.img")
            require(snapshot(dump) == before, "Repack modified the edited input dump")
            run(tool, workdir, "extract", "edited.img")
            edited_dump = workdir / "edited.img.dump"
            require((edited_dump / "demo.fex").read_bytes() == edited, "Edited payload missing")
            require((edited_dump / "Vdemo.fex").read_bytes() == checksum_bytes(edited),
                    "Edited payload checksum is stale")
            for name, payload in zip(LOCAL_NAMES[3:], expected[3:]):
                require((edited_dump / name).read_bytes() == payload, f"Changed unrelated entry: {name}")
        require(image.read_bytes() == original, "Committed demo was modified")
        print(f"Demo {label}: metadata, extraction, round-trip and edited payload passed.")


if __name__ == "__main__":
    main()
