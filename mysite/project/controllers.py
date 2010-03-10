import mysite.search.models
KEY='answer_ids_that_are_ours'

def similar_project_names(project_name):
    # HOPE: One day, order this by relevance.
    return mysite.search.models.Project.objects.filter(
        name__icontains=project_name)

def note_in_session_we_control_answer_id(session, answer_id, KEY=KEY):
    if KEY not in session:
        session[KEY] = []
    session[KEY].append(answer_id)

def take_control_of_our_answers(user, session, KEY=KEY):
    # FIXME: This really ought to be some sort of thread-safe queue,
    # or stored in the database, or something.
    for answer_id in session.get(KEY, []):
        answer = mysite.search.models.Answer.all_even_unowned.get(pk=answer_id)
        answer.author = user
        answer.save()
    # It's unsafe to remove this KEY from the session, in case of concurrent access.
    # But we do anyway. God help us.
    if KEY in session:
        del session[KEY]
