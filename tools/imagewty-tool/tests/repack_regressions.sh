#!/bin/sh
# Sourced by run_tests.sh; all changes below are confined to test_root.

# An edited component changes only the generated firmware, never the dump.
# ABCDE sums to 0x44434286 (little endian), including the final partial word.
for payload_size in small buffered; do
    edited_dump="edited-$payload_size.dump"
    cp -R input.dump "$edited_dump"
    if [ "$payload_size" = buffered ]; then
        dd if=/dev/zero of="$edited_dump/payload.fex" bs=65536 count=1 status=none
        printf 'ABCDE' >>"$edited_dump/payload.fex"
    else
        printf 'ABCDE' >"$edited_dump/payload.fex"
    fi
    : >"$edited_dump/payload__2.fex"
    printf 'TAIL' >>"$edited_dump/Vpayload.fex"
    cp -RP "$edited_dump" "$edited_dump.before"
    "$tool" repack "$edited_dump" "edited-$payload_size.img" >/dev/null
    diff -r "$edited_dump.before" "$edited_dump"
    "$tool" extract "edited-$payload_size.img" >/dev/null
    cmp "$edited_dump/payload.fex" "edited-$payload_size.img.dump/payload.fex"
    cmp "$edited_dump/payload__2.fex" "edited-$payload_size.img.dump/payload__2.fex"
    printf '\206BCDTAIL' >expected-vfile
    cmp expected-vfile "edited-$payload_size.img.dump/Vpayload.fex"
    printf '\000\000\000\000' >expected-vfile
    cmp expected-vfile "edited-$payload_size.img.dump/Vpayload__2.fex"
done

# Each failure phase must preserve both the source dump and existing output.
expect_failure 'Cannot create temporary output' "$tool" repack edited-small.dump missing-parent/out.img
diff -r edited-small.dump.before edited-small.dump
mkdir publish-target.img
printf 'keep directory contents' >publish-target.img/keep
expect_failure 'Cannot finalize' "$tool" repack edited-small.dump publish-target.img
test "$(cat publish-target.img/keep)" = 'keep directory contents'
diff -r edited-small.dump.before edited-small.dump

limited_repack()
(
    # Ignore SIGXFSZ so stdio reports EFBIG and the tool exercises its cleanup.
    trap '' XFSZ
    ulimit -f 1
    "$tool" repack edited-small.dump write-failure.img
)
printf 'previous image' >write-failure.img
cp write-failure.img write-failure.before
expect_failure 'Error writing image headers' limited_repack
cmp write-failure.before write-failure.img
diff -r edited-small.dump.before edited-small.dump
for temporary_output in ./*.tmp.*; do
    test ! -e "$temporary_output"
done

cp -R input.dump short-checksum.dump
printf 'BAD' >short-checksum.dump/Vpayload.fex
cp -RP short-checksum.dump short-checksum.before
expect_failure 'must contain at least four bytes' "$tool" repack short-checksum.dump short-checksum.img
diff -r short-checksum.before short-checksum.dump
test ! -e short-checksum.img

cp -R input.dump short-name.dump
sed -i 's/filename_length=0x100;/filename_length=1;/' short-name.dump/image.cfg
expect_failure 'Filename exceeds filename_length' "$tool" repack short-name.dump short-name.img
test ! -e short-name.img

for numeric_case in 010:0000000A 08:00000008 0x10:00000010 0X10:00000010; do
    number=${numeric_case%:*}
    expected=${numeric_case#*:}
    sed "s/usb_product_id=0x00001234;/usb_product_id=$number;/" input.dump/image.cfg >number.cfg
    "$tool" config number.cfg >number.log
    grep -Eq "USB Product ID[[:space:]]*: 0x$expected$" number.log
done
for number in -1 4294967296 0x100000000 12x 0x ''; do
    sed "s/usb_product_id=0x00001234;/usb_product_id=$number;/" input.dump/image.cfg >number.cfg
    expect_failure 'contains invalid fields' "$tool" config number.cfg
done

# Use short source paths to pack long archive names, including 256-byte fields.
stem251=$(printf '%0251d' 0 | tr 0 x)
stem248=$(printf '%0248d' 0 | tr 0 x)
long_name="$stem251.fex"
collision_name="${stem248}__2.fex"
name256="${stem251}x.fex"
cp -R input.dump long-names.dump
sed -i \
    -e "s/^filename=\"payload.fex\";/filename=\"$long_name\";/" \
    -e "0,/^filename=\"Vpayload.fex\";/s//filename=\"$collision_name\";/" \
    -e "s/^filename=\"Vpayload.fex\";/filename=\"$name256\";/" \
    long-names.dump/image.cfg
"$tool" repack long-names.dump long-names.img >/dev/null
"$tool" extract long-names.img >/dev/null
cmp input.dump/payload.fex "long-names.img.dump/$long_name"
cmp input.dump/Vpayload.fex "long-names.img.dump/$collision_name"
cmp input.dump/payload__2.fex "long-names.img.dump/${stem248}__3.fex"
cmp input.dump/Vpayload__2.fex "long-names.img.dump/${stem248}__1.fex"
"$tool" repack long-names.img.dump long-names-roundtrip.img >/dev/null
cmp long-names.img long-names-roundtrip.img

# An extension too long to preserve must also permit a unique local name.
extension=$(printf '%0253d' 0 | tr 0 e)
cp -R input.dump long-extension.dump
sed -i \
    -e "s/^filename=\"payload.fex\";/filename=\"x.$extension\";/" \
    -e 's/^filename="Vpayload.fex";/filename="companion.bin";/' \
    long-extension.dump/image.cfg
"$tool" repack long-extension.dump long-extension.img >/dev/null
"$tool" extract long-extension.img >/dev/null
"$tool" repack long-extension.img.dump long-extension-roundtrip.img >/dev/null
cmp long-extension.img long-extension-roundtrip.img
