#!/bin/bash

# This file is part of OpenHatch.
# Copyright (C) 2010 OpenHatch
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
