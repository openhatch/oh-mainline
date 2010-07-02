#!/bin/bash

# Calculate lockfile by passing args to md5sum
lockfile=/tmp/lockfile-"$(echo "$@" | md5sum | cut -d' ' -f1)"

if [ ! -e $lockfile ]; then
   trap "rm -f $lockfile; exit" INT TERM EXIT
   echo "$@" >> "$lockfile"
   echo running under PID $$ > "$lockfile"
   "$@"
   RESULT="$?"
   rm "$lockfile"
   exit "$RESULT"
   trap - INT TERM EXIT
else
   echo "critical-section is already running"
fi
