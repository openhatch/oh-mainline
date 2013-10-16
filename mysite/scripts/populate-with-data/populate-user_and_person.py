import random
import sqlite3
import sys
import time
from datetime import datetime

DATABASE_FILE_PATH='../../site.db'
MAX_USERS = 100
user_data = []
person_data = []

for arg in sys.argv:
    argument = str(arg)
    if argument.startswith('db='):
        DATABASE_FILE_PATH = argument.split('=')[1]
    else:
        if argument.startswith('users='):
            MAX_USERS = int(argument.split('=')[1])

print 'Using database path: %s' % DATABASE_FILE_PATH
print 'Users to generate: %s' % MAX_USERS

connection = sqlite3.connect(DATABASE_FILE_PATH)
cursor = connection.cursor()
cursor.execute('SELECT * FROM auth_user ORDER BY id DESC LIMIT 1')
next_id = cursor.fetchone()[0] + 1
print 'Starting with id: %s' % next_id

for u in xrange(0, MAX_USERS):
    id = next_id
    next_id += 1
    username = u'user_%s' % id
    first_name = u'first_name_%s' % id
    last_name = u'last_name_%s' % id
    email = u'email_%s@email.org' % id
    # Password: user
    password = u'sha1$e6e97$9968be01c90fc1658c9d640902e83f36b511c018'
    last_login = datetime.now()
    date_joined = datetime.now()
    user_data.append((id, username, first_name, last_name, email, password, 0, 1, 0, last_login, date_joined))

next_id -= MAX_USERS
for p in xrange(next_id, next_id + MAX_USERS):
    photo = ''
    photo_thumbnail_30px_wide = ''
    photo_thumbnail = ''
    irc_nick = u'nick_%s' % p
    user_id = p
    photo_thumbnail_20px_wide = ''
    last_polled = datetime.now()
    opensource = False
    if random.randint(0, 1) == 1:
        opensource = True
    company_name = u'company_%s' % p
    dont_guess_my_location = False
    bio = u'bio_%s' % p
    contact_blurb = ''
    show_email = True
    location_confirmed = True
    linked_in_url = 'http://127.0.0.1/'
    expand_next_steps = True
    location_display_name = u'location_display_name_%s' % p
    time_to_commit_id = random.randint(1, 4)
    homepage_url = ''
    gotten_name_from_ohloh = False
    email_me_re_projects = False
    google_code_name = ''
    comment = ''
    language_spoken = 'English'
    other_name = ''
    github_name = ''
    subscribed = False
    experience_id = random.randint(1, 3)
    person_data.append((photo, photo_thumbnail_30px_wide, photo_thumbnail, irc_nick, user_id, photo_thumbnail_20px_wide,
                        last_polled, opensource, company_name, dont_guess_my_location, bio, contact_blurb, show_email,
                        location_confirmed, linked_in_url, expand_next_steps, location_display_name, time_to_commit_id,
                        homepage_url, gotten_name_from_ohloh, email_me_re_projects, google_code_name, comment,
                        language_spoken, other_name, github_name, subscribed, experience_id))

print 'Adding user rows...'
user_sql = u'INSERT INTO auth_user (id, username, first_name, last_name, email, password, is_staff, is_active,' \
           u'is_superuser, last_login, date_joined) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
cursor.executemany(
    user_sql,
    user_data)
connection.commit()
print '%s user rows added.' % MAX_USERS

print 'Adding person rows...'
person_sql = u'INSERT INTO profile_person (photo, photo_thumbnail_30px_wide, photo_thumbnail, irc_nick, user_id,' \
             u'photo_thumbnail_20px_wide, last_polled, opensource, company_name, dont_guess_my_location, bio,' \
             u'contact_blurb, show_email, location_confirmed, linked_in_url, expand_next_steps, location_display_name,' \
             u'time_to_commit_id, homepage_url, gotten_name_from_ohloh, email_me_re_projects, google_code_name,' \
             u'comment, language_spoken, other_name, github_name, subscribed, experience_id)' \
             u'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
cursor.executemany(person_sql, person_data)
connection.commit()
print '%s person rows added.' % MAX_USERS
