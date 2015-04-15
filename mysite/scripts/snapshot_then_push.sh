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

## Configuration constants
HOST="linode2.openhatch.org"


## change directory into the right place
PREFIX="."
while [ ! -d "$PREFIX/mysite" ]; do
    PREFIX="../$PREFIX"
done

cd "$PREFIX"

## Create a path to store the JSON in
TEMPFILE="$(mktemp --suffix -snapshot.json.gz)"
TEMPDB="$(mktemp --suffix -snapshot.db)"
SNAPSHOT_SETTINGS_PATH="$(mktemp --suffix -snapshot_settings.py)"

## Do the slooow thing of snapshotting the database
./manage.py snapshot_public_data | gzip > "$TEMPFILE"

## Create a new settings to specify the name of the temporary snapshot db
echo "from mysite.settings import *; DATABASES = {
    'default': {
        'NAME': os.path.join(MEDIA_ROOT_BEFORE_STATIC, "$TEMPDB"),
        'ENGINE': 'django.db.backends.sqlite3',
        'CHARSET': 'utf8',
    },
}" > "$SNAPSHOT_SETTINGS_PATH"

# Load in the snapshot data, which automagically generates the temporary db in root directory
echo "TEMPFILE VARIABLE: " $TEMPFILE
./manage.py syncdb --noinput --migrate --settings="$SNAPSHOT_SETTINGS_PATH"
./manage.py migrate --settings="$SNAPSHOT_SETTINGS_PATH"
./manage.py loaddata "$TEMPFILE" --settings="$SNAPSHOT_SETTINGS_PATH"

# Set the permissions so that, after the file gets pushed to the web,
# the web server permits people to download these snapshots.
chmod 644 "$TEMPFILE"
chmod 644 "$TEMPDIR"

## push this somewhere so that we save it. Do the same thing for the db file.
rsync -q "$TEMPFILE" inside@"$HOST":/var/web/inside.openhatch.org/snapshots/$(date -I).json.gz
rsync -q "$TEMPDB" inside@"$HOST":/var/web/inside.openhatch.org/snapshots/$(date -I).db

## finally, delete the local temporary file, the local temporary db, and the local snapshot settings
rm "$TEMPFILE"
rm "$TEMPDB"
rm "$SNAPSHOT_SETTINGS_PATH"
