#!/bin/bash

## change directory into the right place
PREFIX="."
while [ ! -d "$PREFIX/mysite" ]; do
    PREFIX="../$PREFIX"
done

cd "$PREFIX"

## Create a path to store the JSON in
TEMPFILE="$(mktemp --suffix -snapshot.json.gz)"

## Do the slooow thing of snapshotting the database
./bin/production snapshot_public_data | gzip > "$TEMPFILE"

## push this somewhere so that we save it
rsync -q "$TEMPFILE" inside@inside.openhatch.org:/var/web/inside.openhatch.org/snapshots/$(date -I).json.gz

## finally, delete the local temporary file.
rm "$TEMPFILE"
