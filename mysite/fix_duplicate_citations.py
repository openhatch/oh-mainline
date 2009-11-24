for citation in Citation.objects.all().order_by('pk'):
    citation.ignored_due_to_duplicate = False
    citation.save()
    citation.save_and_check_for_duplicates()
