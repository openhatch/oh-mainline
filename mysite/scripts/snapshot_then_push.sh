#!/bin/bash

# This file is part of OpenHatch.
# Copyright (C) 2010 OpenHatch, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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

# Set the permissions so that, after the file gets pushed to the web,
# the web server permits people to download these snapshots.
chmod 644 "$TEMPFILE"

## push this somewhere so that we save it
rsync -q "$TEMPFILE" inside@inside.openhatch.org:/var/web/inside.openhatch.org/snapshots/$(date -I).json.gz

## finally, delete the local temporary file.
rm "$TEMPFILE"
