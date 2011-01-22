# This file is part of OpenHatch.
# Copyright (C) 2010 Parker Phinney
# Copyright (C) 2010 OpenHatch
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.core.mail import send_mail
import datetime
import celery.decorators

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
