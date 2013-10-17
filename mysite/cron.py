import logging
from django.db.models import Q
from mysite.profile.models import Person
import datetime
import mysite

def push_volunteers_to_zoho_crm(*job_args, **job_kwargs):
    people = None

    try:
        people = Person.objects.filter(Q(date_added=datetime.date.today) and Q(uploaded_to_zoho=False))
        mysite.profile.view_helpers.add_people_to_zoho_CRM(people)
    except Exception as e:
        logging.error(e.message)
        return

    if people is None or len(people) <= 0:
        return

    people.update(uploaded_to_zoho=True)
