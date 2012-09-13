"""
Scrapy signals

These signals are documented in docs/topics/signals.rst. Please don't add new
signals here without documenting them there.
"""

engine_started = object()
engine_stopped = object()
spider_opened = object()
spider_idle = object()
spider_closed = object()
spider_error = object()
request_received = object()
response_received = object()
response_downloaded = object()
item_scraped = object()
item_dropped = object()
stats_spider_opened = object()
stats_spider_closing = object()
stats_spider_closed = object()

item_passed = item_scraped # for backwards compatibility
