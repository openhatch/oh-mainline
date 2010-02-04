import datetime
from haystack import indexes
from haystack import site
import mysite.profile.models
from django.db.models import Q

class PersonIndex(indexes.SearchIndex):
    null_document = indexes.CharField(document=True)
    all_tag_texts = indexes.MultiValueField()
    user__username = indexes.CharField()

    def prepare_null_document(self, person_instance):
        return '' # lollerskates

    def prepare_user__username(self, person_instance):
        return person_instance.user.username

    def prepare_all_tag_texts(self, person_instance):
        return person_instance.get_tag_texts_for_map()

    def get_queryset(self):
        everybody = mysite.profile.models.Person.objects.all()
        mappable_filter = ( ~Q(location_display_name='') &
                            Q(location_confirmed=True) )
        return everybody.filter(mappable_filter)

site.register(mysite.profile.models.Person, PersonIndex)
