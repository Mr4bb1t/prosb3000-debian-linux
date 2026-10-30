#!/usr/bin/env python3
"""Generate deterministic IMAGEWTY demos without using imagewty-tool."""

import argparse
from pathlib import Path
import struct
import sys


README = (
    b"IMAGEWTY synthetic demo. Not bootable; do not flash to a device.\n"
    b"Contains two editable demo.fex entries, their checksums, and an empty file.\n"
    b"All payloads were created for this project; no vendor firmware is included.\n"
)
PAYLOAD_A = b"IMAGEWTY demo payload A.\nEdit this text, then repack the dump.\n"
PAYLOAD_B = b"IMAGEWTY demo payload B.\nSame archive name, different content.\n"


def checksum(data):
    return sum(int.from_bytes(data[i:i + 4], "little")
               for i in range(0, len(data), 4)) & 0xFFFFFFFF


def make_image(version):
    entries = [
        ("README.txt", README),
        ("demo.fex", PAYLOAD_A),
        ("Vdemo.fex", struct.pack("<I", checksum(PAYLOAD_A))),
        ("demo.fex", PAYLOAD_B),
        ("Vdemo.fex", struct.pack("<I", checksum(PAYLOAD_B))),
        ("empty.fex", b""),
    ]
    offset = 1024 * (len(entries) + 1)
    table = bytearray()
    payloads = bytearray()
    for name, data in entries:
        stored = (len(data) + 15) // 16 * 16
        entry = bytearray(1024)
        struct.pack_into("<II", entry, 0, 256, 1024)
        entry[8:16] = b"COMMON  "
        subtype = b"DEMO_CHECKSUM" if name.startswith("V") else b"DEMO_DATA"
        entry[16:32] = subtype.ljust(16, b"\0")
        encoded_name = name.encode("ascii")
        entry[36:36 + len(encoded_name)] = encoded_name
        struct.pack_into("<IIIII", entry, 0x124, stored, 0, len(data), 0, offset)
        table.extend(entry)
        payloads.extend(data)
        payloads.extend(bytes(stored - len(data)))
        offset += stored

    header = bytearray(1024)
    header[:8] = b"IMAGEWTY"
    struct.pack_into(
        "<15I", header, 8,
        version, 96, 0, 0x00100234, offset, 0, 1024,
        0x1234, 0x8743, 0x100, 0x100, 0, 1024, len(entries), 1024,
    )
    return bytes(header + table + payloads)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare without writing files")
    parser.add_argument(
        "--output-dir", type=Path,
        default=Path(__file__).resolve().parents[1] / "tests" / "fixtures",
    )
    args = parser.parse_args()
    if not args.check:
        args.output_dir.mkdir(parents=True, exist_ok=True)
    failed = False
    for name, version in (("demo-v3.img", 0x300), ("demo-v4.img", 0x403)):
        expected = make_image(version)
        path = args.output_dir / name
        if args.check:
            if not path.is_file() or path.read_bytes() != expected:
                print(f"Missing or outdated fixture: {path}", file=sys.stderr)
                failed = True
            else:
                print(f"Verified {name}: {len(expected)} bytes")
        else:
            path.write_bytes(expected)
            print(f"Generated {name}: {len(expected)} bytes")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
