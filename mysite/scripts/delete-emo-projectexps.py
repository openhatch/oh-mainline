from mysite.profile.models import ProjectExp, Person

project_exps = ProjectExp.objects.filter(
        person=Person.objects.get(user__username='emo'))[:19]
# Gonna limit to 20; damage mitigation just in case this query isn't right.
for exp in project_exps:
    exp.delete()
