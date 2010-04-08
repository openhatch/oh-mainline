from django.core.mail import send_mail
import datetime
import celery.decorators
import staticgenerator

@celery.decorators.task
def send_email_to_all_because_project_icon_was_marked_as_wrong(project__pk, project__name, project_icon_url):
    # links you to the project page
    # links you to the secret, wrong project icon
    # TODO:figure out if we should be worried about project icons getting deleted
        # i think that we dont.  provide a justification here.
    project_page_url = 'https://openhatch.org/+projects/' + project__name
    # FIXME: this url
    hidden_project_icon_url = 'https://openhatch.org/static/images/icons/projects/'
    subject = '[OH]- ' + project__name + ' icon was marked as incorrect'
    body = ''
    body += 'project name: ' + project__name + '\n'
    body += 'project url: ' + project_page_url + '\n'
    body += 'project icon url (currently not displayed): ' + project_icon_url + '\n'
    body += 'thanks'
    return send_mail(subject, body, 'all@openhatch.org', ['all@openhatch.org'], fail_silently=False)

@celery.decorators.periodic_task(run_every=datetime.timedelta(minutes=5))
def refresh_project_page_cache():
    staticgenerator.quick_publish('/+projects/')
