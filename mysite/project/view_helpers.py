# This file is part of OpenHatch.
# Copyright (C) 2010 Parker Phinney
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

import mysite.search.models
import logging
KEY='answer_ids_that_are_ours'
PROJECTS_TO_HELP_OUT_KEY='projects_we_want_to_help_out'

def similar_project_names(project_name):
    # HOPE: One day, order this by relevance.
    return mysite.search.models.Project.objects.filter(
        name__icontains=project_name)

def note_in_session_we_control_answer_id(session, answer_id, KEY=KEY):
    if KEY not in session:
        session[KEY] = []
    session[KEY].append(answer_id)

def get_unsaved_answers_from_session(session):
    ret = []
    for answer_id in session.get(KEY, []):
        try:
            ret.append(mysite.search.models.Answer.all_even_unowned.get(id=answer_id))
        except mysite.search.models.Answer.DoesNotExist:
            logging.warn("Whoa, the answer has gone away. Session and Answer IDs: " +
                         str(session) + str(answer_id))
    return ret

def take_control_of_our_answers(user, session, KEY=KEY):
    # FIXME: This really ought to be some sort of thread-safe queue,
    # or stored in the database, or something.
    for answer in get_unsaved_answers_from_session(session):
        if answer.author != user:
            answer.author = user
            answer.save()
    # It's unsafe to remove this KEY from the session, in case of concurrent access.
    # But we do anyway. God help us.
    if KEY in session:
        del session[KEY]

def flush_session_wanna_help_queue_into_database(user, session,
                                                 PROJECTS_TO_HELP_OUT_KEY=PROJECTS_TO_HELP_OUT_KEY):
    # FIXME: This really ought to be some sort of thread-safe queue,
    # or stored in the database, or something.
    for project_id in session.get(PROJECTS_TO_HELP_OUT_KEY, []):
        project = mysite.search.models.Project.objects.get(id=project_id)
        project.people_who_wanna_help.add(user.get_profile())
        mysite.search.models.WannaHelperNote.add_person_project(user.get_profile(), project)
        project.save()
    # It's unsafe to remove this KEY from the session, in case of concurrent access.
    # But we do anyway. God help us.
    if PROJECTS_TO_HELP_OUT_KEY in session:
        del session[PROJECTS_TO_HELP_OUT_KEY]

def get_wanna_help_queue_from_session(session):
    """Get a list of projects that the user said, while browsing anonymously,
    they would be willing to help out with."""
    ret = []
    for project_id in session.get(PROJECTS_TO_HELP_OUT_KEY, []):
        try:
            project = mysite.search.models.Project.objects.get(id=project_id)
        except mysite.search.models.Project.DoesNotExist:
            continue # uhhh, get the next ID...
        ret.append(project)
    ret = list(set(ret))
    return ret
