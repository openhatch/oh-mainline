#!/usr/env/python

import mysite.profile.search_indexes
for person in Person.objects.all():
    pi  = mysite.profile.search_indexes.PersonIndex(person)
    print '.', pi.update_object(person)
