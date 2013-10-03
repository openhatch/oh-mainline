#!/bin/bash

# In case anything returns non-zero, just fail immediately.
set -e

BASE_DIR="/var/web/inside.openhatch.org/crawl-logs"
BUG_TRACKER_LIST="$(mktemp --suffix=.yaml /tmp/bug-trackers.$(date -I).XXXX)"
SCRAPY_RESULT_FILE="$(mktemp --suffix=.jsonlines /tmp/scrapy-results.$(date -I).XXXX)"
SCRAPY_LOG="$(mktemp --suffix=.log $BASE_DIR/scrapy.$(date -I).XXXX)"

# Set our own output to go there.
exec >>"$SCRAPY_LOG" 2>&1

chmod 644 "$SCRAPY_LOG"

MAX_TRACKERS="500"
if [ ! -z "$1" ] ; then
    MAX_TRACKERS="$1"
fi

if [ ! -z "2" ] ; then
    TRACKER_ID="$2"
fi

URL=https://openhatch.org/+api/v1/customs/tracker_model/\?just_stale\=yes\&format\=yaml\&limit\="$MAX_TRACKERS"\&tracker_id="$TRACKER_ID"

# It's OK if wget has to try 4 times.
(wget "$URL" -O- || wget "$URL" -O- || wget "$URL" -O- || wget "$URL" -O-) > "$BUG_TRACKER_LIST"

pushd ../oh-bugimporters
env/bin/python bugimporters/main.py -i "$BUG_TRACKER_LIST" -o "$SCRAPY_RESULT_FILE"
popd

python manage.py import_bugimporter_data "$SCRAPY_RESULT_FILE"
