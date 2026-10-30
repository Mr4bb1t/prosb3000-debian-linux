#!/bin/sh
set -eu

tests_dir=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
. "$tests_dir/test_helpers.sh"

tool=${1:-./imagewty-tool}
test_root=$(mktemp -d /tmp/imagewty-tests.XXXXXX)
trap 'rm -rf "$test_root"' EXIT HUP INT TERM

mkdir "$test_root/input.dump"
printf 'ABCD' >"$test_root/input.dump/payload.fex"
printf 'WXYZ' >"$test_root/input.dump/payload__2.fex"
printf 'ABCD' >"$test_root/input.dump/Vpayload.fex"
printf 'WXYZ' >"$test_root/input.dump/Vpayload__2.fex"

cat >"$test_root/input.dump/image.cfg" <<'EOF'
[IMAGE_CFG]
magic="IMAGEWTY";
header_version=0x00000300;
header_size=0x00000060;
base_ram=0x04D00000;
format_version=0x00100234;
total_image_size=0x00000000;
header_size_including_alignment=0;
file_header_length=0x00000400;
usb_product_id=0x00001234;
usb_vendor_id=0x00008743;
hardware_id=0x00000100;
firmware_id=0x00000100;
unknown_field_1=0;
unknown_field_2=0x400;
unknown_field_3=0x400;
number_of_files=4;

[FILELIST]
file_1 {
filename_length=0x100;
file_header_size=0x400;
maintype="RFSFAT16";
subtype="PAYLOAD_FEX00000";
unknown0=0;
filename="payload.fex";
source_path="payload.fex";
stored_length=16;
pad1=0;
original_length=4;
pad2=0;
offset=0;
}
file_2 {
filename_length=0x100;
file_header_size=0x400;
maintype="RFSFAT16";
subtype="VPAYLOAD_FEX0000";
unknown0=0;
filename="Vpayload.fex";
source_path="Vpayload.fex";
stored_length=16;
pad1=0;
original_length=4;
pad2=0;
offset=0;
}
file_3 {
filename_length=0x100;
file_header_size=0x400;
maintype="RFSFAT16";
subtype="PAYLOAD_FEX00000";
unknown0=0;
filename="payload.fex";
source_path="payload__2.fex";
stored_length=16;
pad1=0;
original_length=4;
pad2=0;
offset=0;
}
file_4 {
filename_length=0x100;
file_header_size=0x400;
maintype="RFSFAT16";
subtype="VPAYLOAD_FEX0000";
unknown0=0;
filename="Vpayload.fex";
source_path="Vpayload__2.fex";
stored_length=16;
pad1=0;
original_length=4;
pad2=0;
offset=0;
}
EOF

cd "$test_root"
"$tool" repack input.dump fixture.img >/dev/null
"$tool" info fixture.img >/dev/null
"$tool" extract fixture.img >/dev/null
cmp input.dump/payload.fex fixture.img.dump/payload.fex
cmp input.dump/payload__2.fex fixture.img.dump/payload__2.fex
expect_failure 'Refusing to overwrite existing dump' "$tool" extract fixture.img
"$tool" repack fixture.img.dump roundtrip.img >/dev/null
cmp fixture.img roundtrip.img

cp -R input.dump v4.dump
sed -i 's/header_version=0x00000300;/header_version=0x00000403;/' v4.dump/image.cfg
"$tool" repack v4.dump v4.img >/dev/null
"$tool" info v4.img >/dev/null
"$tool" extract v4.img >/dev/null

cp -R input.dump invalid-config.dump
sed -i 's/number_of_files=4;/number_of_files=5;/' invalid-config.dump/image.cfg
expect_failure 'Invalid image.cfg' "$tool" repack invalid-config.dump invalid-config.img
test ! -e invalid-config.img

cp input.dump/payload.fex original-payload
expect_failure 'Output file must not replace input' "$tool" repack input.dump input.dump/payload.fex
cmp original-payload input.dump/payload.fex

cp -R input.dump missing-file.dump
rm missing-file.dump/Vpayload.fex
expect_failure 'Cannot access input file' "$tool" repack missing-file.dump missing-file.img
test ! -e missing-file.img

cp fixture.img bad-checksum.img
printf '\000\000\000\000' | dd of=bad-checksum.img bs=1 seek=$((0x1410)) conv=notrunc status=none
expect_failure '[FAIL]' "$tool" extract bad-checksum.img
test -d bad-checksum.img.dump

cp fixture.img bad-header.img
printf '\000\001\000\000' | dd of=bad-header.img bs=1 seek=$((0x20)) conv=notrunc status=none
expect_failure 'invalid header table dimensions' "$tool" info bad-header.img

cp fixture.img bad-offset.img
printf '\377\377\377\377' | dd of=bad-offset.img bs=1 seek=$((0x534)) conv=notrunc status=none
expect_failure 'invalid file entry' "$tool" info bad-offset.img

cp fixture.img unsafe-name.img
printf '../evil\000' | dd of=unsafe-name.img bs=1 seek=$((0x424)) conv=notrunc status=none
expect_failure 'invalid file entry' "$tool" extract unsafe-name.img
test ! -e evil

. "$tests_dir/regressions.sh"
. "$tests_dir/repack_regressions.sh"

echo "All synthetic tests passed."
