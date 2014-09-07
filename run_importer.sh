#!/bin/bash

# In case anything returns non-zero, just fail immediately.
set -e

BASE_DIR="/var/web/inside.openhatch.org/crawl-logs"
if [ ! -z "$1" ] ; then
    BASE_DIR="$1"
fi
BUG_TRACKER_LIST="$(mktemp --suffix=.yaml /tmp/bug-trackers.$(date -I).XXXX)"
SCRAPY_RESULT_FILE="$(mktemp --suffix=.jsonlines /tmp/scrapy-results.$(date -I).XXXX)"
SCRAPY_LOG="$(mktemp --suffix=.log $BASE_DIR/scrapy.$(date -I).XXXX)"

# Set our own output to go there.
exec >>"$SCRAPY_LOG" 2>&1

chmod 644 "$SCRAPY_LOG"

MAX_TRACKERS="500"
if [ ! -z "$2" ] ; then
    MAX_TRACKERS="$2"
fi

if [ ! -z "$3" ] ; then
    TRACKER_ID="$3"
fi

URL=https://openhatch.org/+api/v1/customs/tracker_model/\?just_stale\=yes\&format\=yaml\&limit\="$MAX_TRACKERS"\&tracker_id="$TRACKER_ID"

function grab_bug_tracker_list() {
    # Try to download $URL. If curl bails on us, then
    # we exit 1.
    curl "$URL" > "$BUG_TRACKER_LIST" || return 1

    # Sanity-check the document -- is it actually YAML, or
    # is it a "helpful" CloudFlare error message? To do this
    # check, we ask Python to parse this document, and if it
    # bails out, then we also return 1.
    DJANGO_SETTINGS_MODULE='mysite.settings' python -c "import vendor; vendor.vendorify(); import tastypie.serializers; import yaml; yaml.load(open('$BUG_TRACKER_LIST'), Loader=tastypie.serializers.TastypieLoader)" || return 1

    # Amazing. It is valid YAML. Exit succesfully.
    return 0
}

# It's OK if curl has to try 4 times.
grab_bug_tracker_list || grab_bug_tracker_list || grab_bug_tracker_list || grab_bug_tracker_list || exit 1

pushd ../oh-bugimporters
env/bin/python bugimporters/main.py -i "$BUG_TRACKER_LIST" -o "$SCRAPY_RESULT_FILE"
popd

python manage.py import_bugimporter_data "$SCRAPY_RESULT_FILE"

# Remove old log files.
find "$BASE_DIR" -name 'scrapy.*.log' -mtime +14 -print0 | xargs -0 rm
