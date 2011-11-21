#!/bin/bash

### Exit on failure
set -e

### Switch into the right place
cd ~/milestone-a

### Check if there are any untracked changes to versioned files.
### If so, abort.
if git ls-files -m | grep -q . ; then
    echo "Untracked changes exist; bailing out."
    exit 1
fi

### Do a git fetch to get the latest code from "origin"
git fetch origin

### Pull the latest code from origin/master into the current repo
git merge origin/master --ff-only

### Initialize new databases, if necessary
python manage.py syncdb

### Migrate databases, if necessary
python manage.py migrate --merge

### Update the WSGI file so that Apache reloads the app.
touch mysite/scripts/app.wsgi
