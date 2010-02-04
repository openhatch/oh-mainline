import datetime
from haystack import indexes
from haystack import site
import mysite.profile.models

class PersonIndex(indexes.SearchIndex):
    null_document = indexes.CharField(document=True)
    all_tag_texts = MultiValueField()

    def prepare_null_document(self, person_instance):
        return '' # lollerskates

    def prepare_all_tag_texts(self, person_instance):
        return ['your', 'mom bbq']

site.register(mysite.profile.models.Person, PersonIndex)
