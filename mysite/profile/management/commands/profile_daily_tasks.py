# This file is part of OpenHatch.
# Copyright (C) 2010 OpenHatch, Inc.
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

from django.core.management.base import BaseCommand
import django.db.models

import logging
import mysite.profile.tasks
import mysite.profile.management.commands.send_emails


class Command(BaseCommand):
    help = "Run this once daily for the OpenHatch profile app."

    def handle(self, *args, **options):
        # Garbage collect forwarders
        root_logger = logging.getLogger('')
        root_logger.setLevel(logging.WARN)

        # Note: This Forwarder.garbage_collect() method potentially
        # modifies a lot of Forwarder objects, which means that it
        # would repeatedly call the make_forwarder_actually_work()
        # function due to a post-save signal. That would incur
        # massive overhead, so we temporarily disable it.
        django.db.models.signals.post_save.disconnect(
            mysite.profile.models.make_forwarder_actually_work,
            sender=mysite.profile.models.Forwarder)
        # We do not bother to reconnect it because this is a management
        # command, and it will exit when it is done processing.

        # Now we ask the forwarders to garbage collect.
        made_any_changes = mysite.profile.tasks.GarbageCollectForwarders(
        ).run()
        # Since we disabled the post-save signal, we manually call
        # the function to make sure forwarders are working.
        if made_any_changes:
            mysite.profile.tasks.RegeneratePostfixAliasesForForwarder().run()

        # Try to send the emails. The command will only send emails
        # periodically.
        command = mysite.profile.management.commands.send_emails.Command()
        command.handle()
