import datetime
from haystack import indexes
from haystack import site
import mysite.profile.models

class PersonIndex(indexes.SearchIndex):
    null_document = indexes.CharField(document=True)
    all_tag_texts = indexes.MultiValueField()

    def prepare_null_document(self, person_instance):
        return '' # lollerskates

    def prepare_all_tag_texts(self, person_instance):
        return person_instance.get_tag_texts_for_map()

site.register(mysite.profile.models.Person, PersonIndex)
