import re
import mysite
Person = mysite.profile.models.Person

people_with_weird_locations = Person.objects.filter(location_display_name__regex=', [0-9][0-9],')

for p in people_with_weird_locations:
    location_pieces = re.split(r', \d\d', p.location_display_name)
    unweirded_location = "".join(location_pieces)
    p.location_display_name = unweirded_location
    p.save()
