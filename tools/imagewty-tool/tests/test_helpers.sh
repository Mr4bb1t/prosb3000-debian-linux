#!/bin/sh

# Keep sanitizer failures distinct from the CLI's expected error status (1).
ASAN_OPTIONS="${ASAN_OPTIONS:-}:exitcode=99"
UBSAN_OPTIONS="${UBSAN_OPTIONS:-}:halt_on_error=1:exitcode=98"
export ASAN_OPTIONS UBSAN_OPTIONS

expect_failure()
{
    expected_message=$1
    shift
    if "$@" >"$test_root/expected-error.log" 2>&1; then
        command_status=0
    else
        command_status=$?
    fi
    if [ "$command_status" -ne 1 ] ||
        grep -Eq 'AddressSanitizer|UndefinedBehaviorSanitizer|LeakSanitizer|runtime error:' "$test_root/expected-error.log" ||
        ! grep -Fq "$expected_message" "$test_root/expected-error.log"; then
        echo "Expected exit 1 and diagnostic '$expected_message'; got exit $command_status: $*" >&2
        cat "$test_root/expected-error.log" >&2
        exit 1
    fi
}
