# vim: ai ts=4 sts=4 et sw=4

# Imports {{{
from mysite.profile.models import Person, ProjectExp, Tag, TagType, Link_ProjectExp_Tag, Link_Project_Tag, Link_SF_Proj_Dude_FM, Link_Person_Tag
# }}}

def queryset_of_people():
    return Person.objects.all()
