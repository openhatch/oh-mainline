from haystack import indexes
from haystack import site
import mysite.profile.models
from django.db.models import Q

class PersonIndex(indexes.SearchIndex):
    null_document = indexes.CharField(document=True)
    all_tag_texts = indexes.MultiValueField()
    understands_lowercase_exact = indexes.MultiValueField()
    can_mentor_lowercase_exact = indexes.MultiValueField()
    seeking_lowercase_exact = indexes.MultiValueField()
    all_public_projects_lowercase_exact = indexes.MultiValueField(indexed=False)

    def _pull_lowercase_tag_texts(self, tag_type_name, person_instance):
        return person_instance.get_tags_as_dict().get(tag_type_name, [])

    def prepare_null_document(self, person_instance):
        return '' # lollerskates

    def prepare_all_tag_texts(self, person_instance):
        return person_instance.get_tag_texts_for_map()

    def prepare_can_mentor_with_lowercase_exact(self, person_instance):
        return self._pull_lowercase_tag_texts('can_mentor', person_instance)

    def prepare_seeking_lowercase_exact(self, person_instance):
        return self._pull_lowercase_tag_texts('seeking', person_instance)

    def prepare_understands_lowercase_exact(self, person_instance):
        return self._pull_lowercase_tag_texts('understands', person_instance)

    def prepare_all_public_projects_lowercase_exact(self, person_instance):
        return list(map(lambda x: x.lower(),
                        person_instance.get_list_of_project_names()))

    def get_queryset(self):
        everybody = mysite.profile.models.Person.objects.all()
        mappable_filter = ( ~Q(location_display_name='') &
                            Q(location_confirmed=True) )
        return everybody.filter(mappable_filter)

site.register(mysite.profile.models.Person, PersonIndex)
