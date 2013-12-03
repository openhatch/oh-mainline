#!/bin/bash
set -e

sudo apt-get install python-pip
sudo apt-get install sqlite3
sudo apt-get install python-dev
sudo pip install xmlbuilder
sudo pip install django-crontab
sudo pip install django-file-resubmit
sudo pip install django-cors-headers
sudo pip install numpy
rm -vf mysite/site.db
python manage.py syncdb --noinput
python manage.py migrate
cat ./mysite/scripts/sql/questions_answers.sql | sqlite3 ./mysite/site.db
cat ./mysite/scripts/sql/add_admin.sql | sqlite3 ./mysite/site.db
cat ./mysite/scripts/sql/delete_from_zoho_trigger.sql | sqlite3 ./mysite/site.db

if [[ `crontab -l` == *manage.py* ]]
then
    crontab -r
fi
python manage.py crontab add
