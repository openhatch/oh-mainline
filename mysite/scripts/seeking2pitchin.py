seeking = TagType.objects.get(name='seeking')
can_pitch_in = TagType.objects.get(name='can_pitch_in')
seeking_tags = seeking.tag_set.all()
for tag in seeking_tags:
    tag.tag_type = can_pitch_in
    tag.save()
