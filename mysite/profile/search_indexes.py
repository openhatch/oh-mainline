from haystack import indexes
from haystack import site
import mysite.profile.models
from django.db.models import Q

class PersonIndex(indexes.SearchIndex):
    null_document = indexes.CharField(document=True)
    all_tag_texts = indexes.MultiValueField()
    all_public_projects_lowercase_exact = indexes.MultiValueField(indexed=False)

    def prepare_null_document(self, person_instance):
        return '' # lollerskates

    def prepare_all_tag_texts(self, person_instance):
        return person_instance.get_tag_texts_for_map()

    def prepare_all_public_projects_lowercase_exact(self, person_instance):
        return list(map(lambda x: x.lower(),
                        person_instance.get_list_of_project_names()))

    def get_queryset(self):
        everybody = mysite.profile.models.Person.objects.all()
        mappable_filter = ( ~Q(location_display_name='') &
                            Q(location_confirmed=True) )
        return everybody.filter(mappable_filter)

site.register(mysite.profile.models.Person, PersonIndex)
