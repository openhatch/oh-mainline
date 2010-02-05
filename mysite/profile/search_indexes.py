from haystack import indexes
from haystack import site
import mysite.profile.models
from django.db.models import Q

class PersonIndex(indexes.SearchIndex):
    def _pull_lowercase_tag_texts(self, tag_type_name, person_instance):
        return person_instance.get_tags_as_dict().get(tag_type_name, [])

    null_document = indexes.CharField(document=True)
    def prepare_null_document(self, person_instance):
        return '' # lollerskates

    studying_lowercase_exact = indexes.MultiValueField() 
    def prepare_studying_lowercase_exact(self, person_instance):
        return self._pull_lowercase_tag_texts('currently_studying', person_instance)

    understands_not_lowercase_exact = indexes.MultiValueField()
    def prepare_understands_not_lowercase_exact(self, person_instance):
        return self._pull_lowercase_tag_texts('understands_not', person_instance)

    can_mentor_lowercase_exact = indexes.MultiValueField()
    def prepare_can_mentor_lowercase_exact(self, person_instance):
        return self._pull_lowercase_tag_texts('can_mentor', person_instance)

    seeking_lowercase_exact = indexes.MultiValueField()
    def prepare_seeking_lowercase_exact(self, person_instance):
        return self._pull_lowercase_tag_texts('seeking', person_instance)

    understands_lowercase_exact = indexes.MultiValueField()
    def prepare_understands_lowercase_exact(self, person_instance):
        return self._pull_lowercase_tag_texts('understands', person_instance)

    all_public_projects_lowercase_exact = indexes.MultiValueField() # NOTE: Hack the xml to make type="string"
    def prepare_all_public_projects_lowercase_exact(self, person_instance):
        return list(map(lambda x: x.lower(),
                        person_instance.get_list_of_project_names()))

    def get_queryset(self):
        everybody = mysite.profile.models.Person.objects.all()
        mappable_filter = ( ~Q(location_display_name='') &
                            Q(location_confirmed=True) )
        return everybody.filter(mappable_filter)

site.register(mysite.profile.models.Person, PersonIndex)
