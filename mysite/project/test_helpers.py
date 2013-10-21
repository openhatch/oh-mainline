from datetime import datetime
from mysite.base.models import Duration, Organization, Skill, Language
from mysite.search.models import Project


class ProjectHelper():
    @classmethod
    def create_test_project(cls):
        duration = Duration.objects.get(pk__exact=1)
        url = 'http://127.0.0.1'
        languages = Language.objects.all()
        organization = Organization.objects.all()[0]
        skills = Skill.objects.all()
        project = Project.objects.create(cached_contributor_count=1, created_date=datetime.now(),
                                         date_icon_was_fetched_from_ohloh=datetime.now(), display_name='test_project',
                                         duration=duration, homepage=url, icon_for_profile=None,
                                         icon_for_search_result=None, icon_raw=None, icon_smaller_for_badge=None,
                                         icon_url="", language='English',
                                         logo_contains_name=False, modified_date=datetime.now(), name='test_project',
                                         organization=organization)
        project.skills = skills
        project.languages = languages
        project.save()

        return project
