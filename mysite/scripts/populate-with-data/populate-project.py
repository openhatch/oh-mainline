import random
import sqlite3
import sys
import time
from datetime import datetime

DATABASE_FILE_PATH = '../../site.db'
MAX_PROJECTS = 50
project_data = []
project_skill_data = []
project_language_data = []

for arg in sys.argv:
    argument = str(arg)
    if argument.startswith('db='):
        DATABASE_FILE_PATH = argument.split('=')[1]
    else:
        if argument.startswith('projects='):
            MAX_PROJECTS = int(argument.split('=')[1])

print 'Using database path: %s' % DATABASE_FILE_PATH
print 'Projects to generate: %s' % MAX_PROJECTS

connection = sqlite3.connect(DATABASE_FILE_PATH)
cursor = connection.cursor()
cursor.execute('SELECT id FROM search_project ORDER BY id DESC LIMIT 1')
next_id = cursor.fetchone()
if next_id is not None:
    next_id = next_id[0] + 1
else:
    next_id = 1
print 'Starting with id: %s' % next_id

for p in xrange(0, MAX_PROJECTS):
    id = next_id
    next_id += 1
    modified_date = datetime.now()
    date_icon_was_fetched_from_ohloh = datetime.now()
    duration_id = random.randint(1, 5)
    icon_smaller_for_badge = ''
    name = 'project_%s' % id
    language = random.choice(['English', 'French', 'German', 'Dutch'])
    icon_for_profile = ''
    created_date = datetime.now()
    cached_contributor_count = 1
    icon_raw = ''
    logo_contains_name = '0'
    homepage = ''
    display_name = 'project_%s' % id
    organization_id = random.randint(1, 7)
    project_data.append((id, modified_date, date_icon_was_fetched_from_ohloh, duration_id, icon_smaller_for_badge,
        name, language, icon_for_profile, created_date, cached_contributor_count, icon_raw, logo_contains_name,
        homepage, display_name, organization_id))
    # Many to Many
    skill_id = random.randint(1, 9)
    language_id = random.randint(1, 14)

    project_skill_data.append((id, skill_id))
    project_language_data.append((id, language_id))

print 'Adding project rows...'
project_sql = u'INSERT INTO search_project (id, modified_date, date_icon_was_fetched_from_ohloh, duration_id, ' \
              u'icon_smaller_for_badge, name, language, icon_for_profile, created_date, cached_contributor_count, ' \
              u'icon_raw, logo_contains_name, homepage, display_name, organization_id) ' \
              u'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
cursor.executemany(
    project_sql,
    project_data)
connection.commit()

project_skill_sql = u'INSERT INTO search_project_skills (project_id, skill_id) VALUES (?, ?)'
cursor.executemany(
    project_skill_sql,
    project_skill_data)

project_language_sql = u'INSERT INTO search_project_languages (project_id, language_id) VALUES(?, ?)';
cursor.executemany(
    project_language_sql,
    project_language_data)
connection.commit()

print '%s project rows added.' % MAX_PROJECTS
