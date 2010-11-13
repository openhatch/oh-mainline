#!/bin/bash
set -e

### Which buildout-generated wrapper are we using?
PROGRAM="$1"

### What is the path to the twisted-ping-file?
TWISTED_PING_PATH="$("$PROGRAM" customs_twist_print_ping_file_location)"

### Now we watch that file for changes. If there are any changes,
### we run the customs_twist command.
while inotifywait -e close_write "$TWISTED_PING_PATH"; do
    echo -n "Started Twisting on..."
    date
    "$PROGRAM" customs_twist
done
