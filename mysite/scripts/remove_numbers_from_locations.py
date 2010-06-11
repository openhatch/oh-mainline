import re
import mysite
Person = mysite.profile.models.Person

people_with_weird_locations = Person.objects.filter(location_display_name__regex=', [0-9][0-9],')

count = 0
for p in people_with_weird_locations:
    location_pieces = re.split(r', \d\d,', p.location_display_name)
    unweirded_location = ",".join(location_pieces)
    if unweirded_location != p.location_display_name:
        #print p.location_display_name + "->" + unweirded_location
        p.location_display_name = unweirded_location
        print p.user.email + ","
        p.save()
        count += 1
