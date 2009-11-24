from mysite.profile.models import Citation

for citation in Citation.objects.all().order_by('pk'):
    citation.ignored_due_to_duplicate = False
    citation.save()
    older_duplicates = [dupe for dupe in
            Citation.objects.filter(portfolio_entry=citation.portfolio_entry)
            if (dupe.date_created <= citation.date_created) 
            and (dupe.pk != citation.pk)
            and (dupe.summary == citation.summary)]
    if older_duplicates:
        citation.ignored_due_to_duplicate = True
    citation.save()

