#!/bin/bash

# In case anything returns non-zero, just fail immediately.
set -e

BUG_TRACKER_LIST="$(mktemp --suffix=.yaml /tmp/bug-trackers.$(date -I).XXXX)"
SCRAPY_RESULT_FILE="$(mktemp --suffix=.jsonlines /tmp/scrapy-results.XXXX)"
SCRAPY_LOG="$(mktemp --suffix=.log /tmp/scrapy.XXXX)"
MAX_TRACKERS="500"
if [ ! -z "$1" ] ; then
    MAX_TRACKERS="$1"
fi

if [ ! -z "2" ] ; then
    TRACKER_ID="$2"
fi

wget https://openhatch.org/+api/v1/customs/tracker_model/\?just_stale\=yes\&format\=yaml\&limit\="$MAX_TRACKERS"\&tracker_id="$TRACKER_ID" -O "$BUG_TRACKER_LIST"

pushd ../oh-bugimporters
bin/python bugimporters/main.py -i "$BUG_TRACKER_LIST" -o "$SCRAPY_RESULT_FILE"
popd

python manage.py import_bugimporter_data "$SCRAPY_RESULT_FILE"
