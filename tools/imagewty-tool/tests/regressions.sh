#!/bin/sh
# Sourced by run_tests.sh, using its isolated fixtures and error assertions.

# Conflicts must fail before any checksum or existing output is modified.
for alias_kind in same hard symbolic payload_before payload_after cfg_same cfg_hard cfg_symbolic; do
    alias_dump="alias-$alias_kind.dump"
    cp -R input.dump "$alias_dump"
    case "$alias_kind" in
        same)
            sed -i 's/source_path="Vpayload__2.fex";/source_path="Vpayload.fex";/' "$alias_dump/image.cfg"
            ;;
        hard|symbolic)
            rm "$alias_dump/Vpayload__2.fex"
            if [ "$alias_kind" = hard ]; then
                ln "$alias_dump/Vpayload.fex" "$alias_dump/Vpayload__2.fex"
            else
                ln -s Vpayload.fex "$alias_dump/Vpayload__2.fex"
            fi
            ;;
        payload_before)
            sed -i 's/source_path="Vpayload__2.fex";/source_path="payload.fex";/' "$alias_dump/image.cfg"
            ;;
        payload_after)
            sed -i 's/source_path="Vpayload.fex";/source_path="payload__2.fex";/' "$alias_dump/image.cfg"
            ;;
        cfg_same)
            sed -i 's/source_path="Vpayload__2.fex";/source_path="image.cfg";/' "$alias_dump/image.cfg"
            ;;
        cfg_hard|cfg_symbolic)
            rm "$alias_dump/Vpayload__2.fex"
            if [ "$alias_kind" = cfg_hard ]; then
                ln "$alias_dump/image.cfg" "$alias_dump/Vpayload__2.fex"
            else
                ln -s image.cfg "$alias_dump/Vpayload__2.fex"
            fi
            ;;
    esac
    # A pending correction on the first pair exposes premature checksum writes.
    printf '\000\000\000\000' >"$alias_dump/Vpayload.fex"
    cp -RP "$alias_dump" "$alias_dump.before"
    case "$alias_kind" in
        cfg_*) alias_message='must not alias image.cfg' ;;
        *) alias_message='Conflicting checksum source aliases' ;;
    esac
    expect_failure "$alias_message" "$tool" repack "$alias_dump" "$alias_kind.img"
    test ! -e "$alias_kind.img"
    printf 'existing output' >"$alias_kind.img"
    expect_failure "$alias_message" "$tool" repack "$alias_dump" "$alias_kind.img"
    test "$(cat "$alias_kind.img")" = 'existing output'
    diff -r "$alias_dump.before" "$alias_dump"
done

# Read-only payload sharing remains valid, including filesystem aliases.
for alias_kind in same hard symbolic; do
    alias_dump="readonly-$alias_kind.dump"
    cp -R input.dump "$alias_dump"
    case "$alias_kind" in
        same)
            sed -i 's/source_path="payload__2.fex";/source_path="payload.fex";/' "$alias_dump/image.cfg"
            ;;
        hard|symbolic)
            rm "$alias_dump/payload__2.fex"
            if [ "$alias_kind" = hard ]; then
                ln "$alias_dump/payload.fex" "$alias_dump/payload__2.fex"
            else
                ln -s payload.fex "$alias_dump/payload__2.fex"
            fi
            ;;
    esac
    "$tool" repack "$alias_dump" "readonly-$alias_kind.img" >/dev/null
    "$tool" extract "readonly-$alias_kind.img" >/dev/null
    cmp input.dump/payload.fex "$alias_dump/payload.fex"
    cmp input.dump/payload.fex "readonly-$alias_kind.img.dump/payload__2.fex"
done

# Reserve metadata names even when archive entries already use suffixes.
cp -R input.dump reserved.dump
sed -i \
    -e 's/^filename="payload.fex";/filename="image.cfg";/' \
    -e '0,/^filename="Vpayload.fex";/s//filename="image__2.cfg";/' \
    -e 's/^filename="Vpayload.fex";/filename="image__3.cfg";/' \
    reserved.dump/image.cfg
"$tool" repack reserved.dump reserved.img >/dev/null
"$tool" extract reserved.img >/dev/null
"$tool" config reserved.img.dump/image.cfg >/dev/null
cmp input.dump/payload.fex reserved.img.dump/image__2.cfg
cmp input.dump/Vpayload.fex reserved.img.dump/image__2__2.cfg
cmp input.dump/payload__2.fex reserved.img.dump/image__3.cfg
cmp input.dump/Vpayload__2.fex reserved.img.dump/image__3__2.cfg
"$tool" repack reserved.img.dump reserved-roundtrip.img >/dev/null
cmp reserved.img reserved-roundtrip.img

# Braces inside quoted values are data; a standalone brace closes a block.
cp -R input.dump braces.dump
sed -i \
    -e 's/^filename="payload.fex";/filename="a}b.fex";/' \
    -e 's/^filename="Vpayload.fex";/filename="Va}b.fex";/' \
    -e 's/^maintype="RFSFAT16";/maintype="RFS}AT16";/' \
    -e 's/^subtype="PAYLOAD_FEX00000";/subtype="PAY}OAD_FEX00000";/' \
    braces.dump/image.cfg
"$tool" repack braces.dump braces.img >/dev/null
"$tool" extract braces.img >/dev/null
"$tool" config braces.img.dump/image.cfg >/dev/null
cmp input.dump/payload.fex 'braces.img.dump/a}b.fex'
cmp input.dump/payload__2.fex 'braces.img.dump/a}b__2.fex'
"$tool" repack braces.img.dump braces-roundtrip.img >/dev/null
cmp braces.img braces-roundtrip.img
sed '$d' braces.img.dump/image.cfg >unclosed.cfg
expect_failure 'contains invalid fields' "$tool" config unclosed.cfg

# Verify the assertion itself: neither crashes nor sanitizer output may pass.
ulimit -c 0
if (expect_failure 'invalid header' sh -c 'echo "invalid header" >&2; kill -SEGV $$') >crash-check.log 2>&1; then
    echo 'The error assertion accepted SIGSEGV.' >&2
    exit 1
fi
for sanitizer in AddressSanitizer UndefinedBehaviorSanitizer LeakSanitizer 'runtime error:'; do
    if (expect_failure 'invalid header' sh -c 'echo "invalid header: $1" >&2; exit 1' sh "$sanitizer") >sanitizer-check.log 2>&1; then
        echo "The error assertion accepted $sanitizer." >&2
        exit 1
    fi
done
if (expect_failure 'invalid header' sh -c 'echo "unrelated failure" >&2; exit 1') >diagnostic-check.log 2>&1; then
    echo 'The error assertion accepted an unrelated diagnostic.' >&2
    exit 1
fi
