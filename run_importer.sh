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

wget https://openhatch.org/+api/v1/customs/tracker_model/\?format\=yaml\&limit\="$MAX_TRACKERS" -O "$BUG_TRACKER_LIST"

pushd ../oh-bugimporters
env/bin/scrapy runspider bugimporters/main.py  -a input_filename="$BUG_TRACKER_LIST" -s TELNETCONSOLE_ENABLED=0 -s WEBSERVICE_ENABLED=0 -s FEED_FORMAT=jsonlines -s FEED_URI="$SCRAPY_RESULT_FILE"  -s LOG_FILE="$SCRAPY_LOG" -s CONCURRENT_REQUESTS_PER_DOMAIN=1 -s CONCURRENT_REQUESTS=200 -s DEPTH_PRIORITY=1 -s SCHEDULER_DISK_QUEUE=scrapy.squeue.PickleFifoDiskQueue -s SCHEDULER_MEMORY_QUEUE=scrapy.squeue.FifoMemoryQueue
popd

python manage.py import_bugimporter_data "$SCRAPY_RESULT_FILE"
