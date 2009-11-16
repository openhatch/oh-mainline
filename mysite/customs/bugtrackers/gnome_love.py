import urllib2
import mysite.customs.miro

def get_remote_bug_ids_to_read():
    return mysite.customs.miro.bugzilla_query_to_bug_ids(
        urllib2.urlopen(
            'https://bugzilla.gnome.org/buglist.cgi?columnlist=id&keywords=gnome-love&query_format=advanced&resolution=---&ctype=csv'))

def grab():
    """Loops over GNOME Bugzilla's list of gnome-love bugs and stores/updates
    them in our DB.
    
    For now, just grab the gnome-love bugs to be kind to their servers."""

    bug_ids = flatten([get_remote_bug_ids_to_read(), get_remote_bug_ids_already_stored()])

    for bug_id in bug_ids:
        # Sometimes create_bug_object_for_remote_bug_id will fail to create
        # a bug because it's somehow gone missing. For those cases:

        # create canonical_bug_link in this function to avoid assuming the
        # returned bug is not None.
        canonical_bug_link = BUG_URL_PREFIX + str(bug_id)

        # Try to create a bug. Now, it might return None...
        bug = create_bug_object_for_remote_bug_id(bug_id)

        # If there is already a bug with this canonical_bug_link in
        # the DB, just delete it. Same story if the bug doens't 404!
        bugs_this_one_replaces = Bug.all_bugs.filter(canonical_bug_link=
                                                     canonical_bug_link)
        for delete_me in bugs_this_one_replaces:
            delete_me.delete()

        # If the bug is None, we're done here.
        if bug is None:
            continue

        # Otherwise, print and save the sucker!
        print bug
        bug.save()
