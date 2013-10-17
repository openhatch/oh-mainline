from mysite.profile.models import Person
import datetime
import mysite

def push_volunteers_to_zoho_crm(*job_args, **job_kwargs):
      people = Person.objects.find(date_added=datetime.date.today)
      mysite.profile.view_helpers.add_people_to_zoho_CRM(people)