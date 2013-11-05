#!/bin/bash
set -e

rm -vf mysite/site.db
python manage.py syncdb --noinput
python manage.py migrate
cat ./mysite/scripts/sql/add_admin.sql | sqlite3 ./mysite/site.db
sudo pip install xmlbuilder
sudo pip install django-crontab
if [[ `crontab -l` == *manage.py* ]]
then
    crontab -r
fi
python manage.py crontab add
