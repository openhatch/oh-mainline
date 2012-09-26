wget https://openhatch.org/+api/v1/customs/tracker_model/\?format\=yaml\&limit\=500 -O /tmp/bug-trackers.yaml

pushd ../oh-bugimporters
env/bin/scrapy runspider bugimporters/main.py  -a input_filename=/tmp/bug-trackers.yaml  -s FEED_FORMAT=jsonlines -s FEED_URI=/tmp/results.jsonlines  -s LOG_FILE=/tmp/scrapy-log -s CONCURRENT_REQUESTS_PER_DOMAIN=1 -s CONCURRENT_REQUESTS=200 -s DEPTH_PRIORITY=1 -s SCHEDULER_DISK_QUEUE=scrapy.squeue.PickleFifoDiskQueue -s SCHEDULER_MEMORY_QUEUE=scrapy.squeue.FifoMemoryQueue
popd

python manage.py import_bugimporter_data /tmp/results.jsonlines
