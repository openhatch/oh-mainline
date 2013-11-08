import logging
from django.db.models import Q
from mysite.profile.models import Person, PeopleToRemoveFromZoho
import datetime
import mysite

def push_volunteers_to_zoho_crm(*job_args, **job_kwargs):

    try:
        people_to_insert = Person.objects.filter(Q(date_added=datetime.date.today) and Q(uploaded_to_zoho=False))
        mysite.profile.view_helpers.add_people_to_zoho_CRM(people_to_insert)
        people_to_update = Person.objects.filter(Q(is_updated=True))
        mysite.profile.view_helpers.update_people_in_zoho_CRM(people_to_update)
        people_to_delete = PeopleToRemoveFromZoho.objects.all()
        mysite.profile.view_helpers.delete_people_from_zoho_CRM(people_to_delete)
    except Exception as e:
        logging.error(e.message)
        return

    if people_to_insert:
        people_to_insert.update(uploaded_to_zoho=True)

    if people_to_update:
        people_to_update.update(is_updated=False)
