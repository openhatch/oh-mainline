#!/bin/bash

CLONE_AND_TEST_LOCK="/tmp/clone-and-test-$USER"
mkdir $CLONE_AND_TEST_LOCK || die "Could not lock clone-and-test."

notify_send() {
    notify-send -u critical -t 10000 "$1"
}

find_or_die() {
    which $1 2>&1 > /dev/null || die Could not find $1
}

die() {
    echo $1 >&2
    exit 1
}

REPO="$1"

## Check for dependencies
find_or_die notify-send
find_or_die git

## Create a clone of the git repository
MYTEMP="$(mktemp -d /tmp/$(date -I)-testing-git-clone.XXXX)"
cd "$MYTEMP"
nohup git clone "$REPO"

# Find test.sh
cd "$(dirname */*/test.sh)"
nohup ./test.sh

result=$?

if [ $result -eq 0 ]; then
    notify_send "Tests aced! Deleting temporary clone."
    sleep 5
    rm -rf "$MYTEMP"
else
    notify_send "Tests failboated. Temporary clone in $MYTEMP"
    # Do not delete the directory
fi

rmdir "$CLONE_AND_TEST_LOCK"
