import mysite.search.models

def similar_project_names(project_name):
    # HOPE: One day, order this by relevance.
    return mysite.search.models.Project.objects.filter(
        name__icontains=project_name)

def note_in_session_we_control_answer_id(session, answer_id):
    key = 'answer_ids_that_are_ours'
    if key not in session:
        session[key] = []
    session[key].append(answer_id)

def take_control_of_our_answers(user, session):
    key = 'answer_ids_that_are_ours'
    for answer_id in session.get(key, []):
        answer = mysite.search.models.Answer.all_even_unowned.get(pk=answer_id)
        answer.author = user
        answer.save()

