rm -vf mysite/site.db
python manage.py syncdb --noinput
python manage.py migrate
cat ./mysite/scripts/sql/add_admin.sql | sqlite3 ./mysite/site.db

