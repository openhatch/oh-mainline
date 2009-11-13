from mysite.customs.models import RoundupBugTracker
from mysite.search.models import Project

p = RoundupBugTracker()
p.roundup_root_url = 'http://bugs.python.org'
p.project = Project.objects.get_or_create(name='Python', language='Python')[0]
p.csv_keyword = '6'
p.save()
p.grab()
