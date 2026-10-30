#!/bin/sh
set -eu

. "$(dirname "$0")/test_helpers.sh"

tool=${1:-./imagewty-tool}
case "$tool" in
    /*) ;;
    *) tool=$(pwd)/$tool ;;
esac
image=${H713_IMAGE:?Set H713_IMAGE to the local H713 firmware path; use make test for portable demo tests}
case "$image" in
    /*) ;;
    *) image=$(pwd)/$image ;;
esac
test -f "$image" || { echo "H713 image not found: $image" >&2; exit 1; }

test_root=$(mktemp -d /tmp/imagewty-h713.XXXXXX)
trap 'rm -rf "$test_root"' EXIT HUP INT TERM
cd "$test_root"

# ASan requires a large virtual address space; use unlimited for sanitized runs.
if [ "${H713_MEMORY_LIMIT_KB:-262144}" != unlimited ]; then
    ulimit -v "${H713_MEMORY_LIMIT_KB:-262144}"
fi
"$tool" extract "$image" >/dev/null
dump="$(basename "$image").dump"
test -f "$dump/boot-resource.fex"
test -f "$dump/boot-resource__2.fex"
"$tool" repack "$dump" repacked.img >/dev/null
cmp "$image" repacked.img
echo "H713 integration test passed."
