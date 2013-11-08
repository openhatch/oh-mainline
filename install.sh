#!/bin/bash
set -e

rm -vf mysite/site.db
python manage.py syncdb --noinput
python manage.py migrate
cat ./mysite/scripts/sql/questions_answers.sql | sqlite3 ./mysite/site.db
cat ./mysite/scripts/sql/add_admin.sql | sqlite3 ./mysite/site.db
cat ./mysite/scripts/sql/delete_from_zoho_trigger.sql | sqlite3 ./mysite/site.db
sudo pip install xmlbuilder
sudo pip install django-crontab
sudo pip install django-file-resubmit
if [[ `crontab -l` == *manage.py* ]]
then
    crontab -r
fi
python manage.py crontab add
