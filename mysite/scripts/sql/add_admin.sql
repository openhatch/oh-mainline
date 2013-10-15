
INSERT OR IGNORE INTO auth_permission ('name', 'content_type_id', 'codename') VALUES ('Can view people', '38', 'can_view_people');
INSERT OR IGNORE INTO auth_permission ('name', 'content_type_id', 'codename') VALUES ('Can filter people', '38', 'can_filter_people');
INSERT OR IGNORE INTO auth_permission ('name', 'content_type_id', 'codename') VALUES ('Can view projects', '23', 'can_view_projects');

INSERT OR IGNORE INTO auth_group ('name') VALUES ('ADMIN');
INSERT OR IGNORE INTO auth_group ('name') VALUES ('PROJECT_PARTNER');
INSERT OR IGNORE INTO auth_group ('name') VALUES ('VOLUNTEER');

INSERT OR IGNORE INTO auth_group_permissions ('group_id', 'permission_id')
    SELECT 1 as 'group_id', id as 'permission_id' from auth_permission;

INSERT OR IGNORE INTO auth_user ('username', 'first_name', 'last_name', 'email', 'password', 'is_staff',
    'is_active', 'is_superuser', 'last_login', 'date_joined')
    VALUES ('admin', '', '', 'admin@admin.org', 'sha1$2e371$0230d0b7fa33dff4750ea4cdca98523cb75ae43b',
        '1', '1', '1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

INSERT OR IGNORE INTO profile_person ('photo', 'photo_thumbnail_30px_wide', 'photo_thumbnail',
    'irc_nick', 'user_id', 'photo_thumbnail_20px_wide', 'last_polled', 'opensource',
    'company_name', 'dont_guess_my_location', 'bio', 'contact_blurb', 'show_email',
    'location_confirmed', 'linked_in_url', 'expand_next_steps', 'location_display_name',
    'time_to_commit_id', 'homepage_url', 'gotten_name_from_ohloh', 'email_me_re_projects')
    VALUES ('', '', '', 'admin', '1', '', CURRENT_TIMESTAMP, '1', '', '0', '', '',
        '1', '1', '', '1', '', '1', '', '0', '0');

INSERT OR IGNORE INTO auth_user_groups ('user_id', 'group_id') VALUES ('1', '1');
