from datetime import datetime
from django.contrib.auth.models import User
from mysite.base.models import Experience, Language, Organization, Skill
from mysite.profile.models import Person, Cause, TimeToCommit


class UserAndPersonHelper():
    @classmethod
    def create_test_user_and_person(cls):
        # Password: user
        user = User.objects.create(username='test_user', first_name='test', last_name='user', email='test@user.com',
                                   password='sha1$e6e97$9968be01c90fc1658c9d640902e83f36b511c018',
                                   is_staff='1', is_active='1', is_superuser='1', last_login=datetime.now(),
                                   date_joined=datetime.now())
        user.save()
        person = Person.objects.get(user=user)
        person.bio = 'test_bio'
        person.cause = Cause.objects.all()
        person.comment = 'test_comment'
        person.company_name = 'test_company'
        person.contact_blurb = ''
        person.date_added = datetime.now()
        person.dont_guess_my_location = False
        person.email_me_re_projects = False
        person.expand_next_steps = True
        person.experience = Experience.objects.get(pk__exact=1)
        person.github_name = 'test_github_name'
        person.google_code_name = 'test_google_code_name'
        person.gotten_name_from_ohloh = False
        person.homepage_url = 'http://127.0.0.1'
        person.irc_nick = 'test_nick'
        person.language = Language.objects.all()
        person.language_spoken = 'English'
        person.last_polled = datetime.now()
        person.linked_in_url = 'http://127.0.0.1'
        person.location_confirmed = True
        person.location_display_name = 'test_location'
        person.opensource = True
        person.organization = Organization.objects.all()
        person.other_name = 'test_other_name'
        person.photo = ''
        person.photo_thumbnail = ''
        person.photo_thumbnail_20px_wide = ''
        person.photo_thumbnail_30px_wide = ''
        person.private = True
        person.show_email = True
        person.skill = Skill.objects.all()
        person.subscribed = False
        person.time_to_commit = TimeToCommit.objects.get(pk__exact=1)
        person.uploaded_to_zoho = True
        person.save()

        return person
