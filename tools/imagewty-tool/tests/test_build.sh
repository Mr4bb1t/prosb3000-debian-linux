#!/bin/sh
set -eu
repo=${1:?Repository path required}
build_root=$(mktemp -d /tmp/imagewty-build-tests.XXXXXX)
trap 'rm -rf "$build_root"' EXIT HUP INT TERM
mkdir "$build_root/src" "$build_root/include"
cp "$repo/Makefile" "$build_root/"
cp "$repo"/src/*.c "$build_root/src/"
cp "$repo"/include/*.h "$build_root/include/"
cd "$build_root"

make -s -j4 all debug
test -x imagewty-tool
test -x build/debug/imagewty-tool
cp imagewty-tool release.before
make -s -j4 debug
cmp release.before imagewty-tool
make -q all debug

# -W models a header edit without relying on filesystem timestamp resolution.
make -n -W include/img_header.h all debug >header-build.log
grep -q 'src/img_header.c' header-build.log
grep -q 'src/img_repack.c' header-build.log
grep -q 'build/debug/img_header.o' header-build.log
make -s -W include/img_header.h all debug
make -q all debug
make -n -W include/img_repack.h all debug >alignment-build.log
grep -q 'src/img_repack.c' alignment-build.log
if grep -q 'src/checksum.c' alignment-build.log; then
    echo 'Unrelated checksum object would be rebuilt for img_repack.h.' >&2
    exit 1
fi

make -s clean
test ! -e imagewty-tool
test ! -e build/debug/imagewty-tool
make -s -j4 debug
test -x build/debug/imagewty-tool
make -s -j4 all
test -x imagewty-tool
echo 'Build dependency and parallel debug tests passed.'
