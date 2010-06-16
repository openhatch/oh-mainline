import datetime
import logging

import mysite.search.models
import mysite.customs.bugtrackers.trac

class TracBugTracker(object):
    enabled = False

    def __init__(self, base_url, project_name, bitesized_keyword):
        self.base_url = base_url
        self.project_name = project_name
        self.bitesized_keyword = bitesized_keyword

    def update(self):
        logging.info("Started refreshing all %s bugs." % self.project_name)

        # First, go through and refresh all the bugs specifically marked
        # as bugs to look at.

        must_look_at_these = self.generate_list_of_bug_ids_to_look_at()
        for bug_id in must_look_at_these:
            self.refresh_one_bug_id(bug_id)

        # Then, refresh them all
        self.refresh_all_bugs()

    def refresh_all_bugs(self):
        for bug in mysite.search.models.Bug.all_bugs.filter(
            canonical_bug_link__contains=self.base_url):
            tb = mysite.customs.bugtrackers.trac.TracBug.from_url(
                bug.canonical_bug_link)
            self.refresh_one_bug_id(tb.bug_id)

    def refresh_one_bug_id(self, bug_id):
        tb = mysite.customs.bugtrackers.trac.TracBug(
            bug_id=bug_id,
            BASE_URL=self.base_url,
            bitesized_keyword=self.bitesized_keyword)
        bug_url = tb.as_bug_specific_url()
    
        try:
            bug = mysite.search.models.Bug.all_bugs.get(
                canonical_bug_link=bug_url)
        except mysite.search.models.Bug.DoesNotExist:
            bug = mysite.search.models.Bug(canonical_bug_link = bug_url)

        # Hopefully, the bug is so fresh it needs no refreshing.
        if bug.data_is_more_fresh_than_one_day():
            logging.info("Bug %d from %s is fresh. Doing nothing!" % (bug_id, self.project_name))
            return # sweet

        # Okay, fine, we need to actually refresh it.
        logging.info("Refreshing bug %d from %s." %
                     (bug_id, self.project_name))
        data = tb.as_data_dict_for_bug_object()

        for key in data:
            value = data[key]
            setattr(bug, key, value)

        # And save the project onto it
        project_from_name, _ = mysite.search.models.Project.objects.get_or_create(name=self.project_name)
        if bug.project_id != project_from_name.id:
            bug.project = project_from_name
        bug.last_polled = datetime.datetime.utcnow()
        bug.save()
        logging.info("Finished with %d from %s." % (bug_id, self.project_name))
            
class TahoeLafsTrac(TracBugTracker):
    enabled = True

    def __init__(self):
        TracBugTracker.__init__(self,
                                project_name='Tahoe-LAFS',
                                base_url='http://tahoe-lafs.org/trac/tahoe-lafs/',
                                bitesized_keyword='easy')

    def generate_list_of_bug_ids_to_look_at(self):
        return mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
            mysite.customs.bugtrackers.trac.csv_of_bugs(
                'http://tahoe-lafs.org/trac/tahoe-lafs/query?status=assigned&status=new&status=reopened&max=10000&reporter=~&col=id&col=summary&col=keywords&col=reporter&col=status&col=owner&col=type&col=priority&col=milestone&keywords=~&owner=~&desc=1&order=id&format=csv'))

class TwistedTrac(TracBugTracker):
    enabled = True

    def __init__(self):
        TracBugTracker.__init__(self,
                                project_name='Twisted',
                                base_url='http://twistedmatrix.com/trac/',
                                bitesized_keyword='easy')

    def generate_list_of_bug_ids_to_look_at(self):
        # Just index bitesized bugs
        return mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
            mysite.customs.bugtrackers.trac.csv_of_bugs(
                'http://twistedmatrix.com/trac/query?status=new&status=assigned&status=reopened&format=csv&keywords=%7Eeasy&order=priority'))

class SugarLabsTrac(TracBugTracker):
    enabled = True

    def __init__(self):
        TracBugTracker.__init__(self,
                                project_name='Sugar Labs',
                                base_url='http://bugs.sugarlabs.org/',
                                bitesized_keyword='sugar-love')

    def generate_list_of_bug_ids_to_look_at(self):
        # Just index bitesized bugs
        return mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
            mysite.customs.bugtrackers.trac.csv_of_bugs(
                'http://bugs.sugarlabs.org/query?status=new&status=assigned&status=reopened&format=csv&keywords=%7Esugar-love&order=priority'))

class StatusNetTrac(TracBugTracker):
    enabled = True

    def __init__(self):
        TracBugTracker.__init__(self,
                                project_name='StatusNet',
                                base_url='http://status.net/trac/',
                                bitesized_keyword='easy')

    def generate_list_of_bug_ids_to_look_at(self):
        # Only gives a list of bitesized bugs - confirm if devels want all bugs indexed
        return mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
            mysite.customs.bugtrackers.trac.csv_of_bugs(
                'http://status.net/trac/query?status=accepted&status=assigned&status=new&status=reopened&format=csv&order=priority&keywords=%7Eeasy'))

class XiphTrac(TracBugTracker):
    enabled = True

    def __init__(self):
        TracBugTracker.__init__(self,
                                project_name='Xiph',
                                base_url='http://trac.xiph.org/',
                                bitesized_keyword='easy') # Unconfirmed, there were no such bugs at the time

    def generate_list_of_bug_ids_to_look_at(self):
        # Only gives a list of bitesized bugs - confirm if devels want all bugs indexed
        return mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
            mysite.customs.bugtrackers.trac.csv_of_bugs(
                'https://trac.xiph.org/query?status=assigned&status=new&status=reopened&order=priority&format=csv&keywords=%7Eeasy'))

class OLPCTrac(TracBugTracker):
    enabled = True

    def __init__(self):
        TracBugTracker.__init__(self,
                                project_name='OLPC',
                                base_url='http://dev.laptop.org/',
                                bitesized_keyword='easy') # Also uses 'sugar-love'.

    def generate_list_of_bug_ids_to_look_at(self):
        return mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
            mysite.customs.bugtrackers.trac.csv_of_bugs(
                'http://dev.laptop.org/query?status=assigned&status=new&status=reopened&order=priority&format=csv'))

class DjangoTrac(TracBugTracker):
    enabled = False # Opened' and 'Last modified' fields aren't hyperlinked

    def __init__(self):
        TracBugTracker.__init__(self,
                                project_name='Django',
                                base_url='http://code.djangoproject.com/',
                                bitesized_keyword='easy')

    def generate_list_of_bug_ids_to_look_at(self):
        return mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
            mysite.customs.bugtrackers.trac.csv_of_bugs(
                'http://code.djangoproject.com/query?status=new&status=assigned&status=reopened&order=priority&format=csv'))

class HelenOSTrac(TracBugTracker):
    enabled = True

    def __init__(self):
        TracBugTracker.__init__(self,
                                project_name='HelenOS',
                                base_url='http://trac.helenos.org/trac.fcgi/',
                                bitesized_keyword='easy') # Unconfirmed, there were no such bugs at the time

    def generate_list_of_bug_ids_to_look_at(self):
        return mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
            mysite.customs.bugtrackers.trac.csv_of_bugs(
                'http://trac.helenos.org/trac.fcgi/query?status=accepted&status=assigned&status=new&status=reopened&order=priority&format=csv'))

class Bcfg2Trac(TracBugTracker):
    enabled = True

    def __init__(self):
        TracBugTracker.__init__(self,
                                project_name='Bcfg2',
                                base_url='https://trac.mcs.anl.gov/projects/bcfg2/',
                                bitesized_keyword='easy') # Unconfirmed, there were no such bugs at the time

    def generate_list_of_bug_ids_to_look_at(self):
        return mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
            mysite.customs.bugtrackers.trac.csv_of_bugs(
                'https://trac.mcs.anl.gov/projects/bcfg2/query?status=accepted&status=assigned&status=new&status=reopened&order=priority&format=csv'))

class WarFoundryTrac(TracBugTracker):
    enabled = True

    def __init__(self):
        TracBugTracker.__init__(self,
                                project_name='WarFoundry',
                                base_url='http://dev.ibboard.co.uk/projects/warfoundry/',
                                bitesized_keyword='papercut')

    def generate_list_of_bug_ids_to_look_at(self):
        return mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
            mysite.customs.bugtrackers.trac.csv_of_bugs(
                'http://dev.ibboard.co.uk/projects/warfoundry/query?status=accepted&status=assigned&status=confirmed&status=needinfo&status=needinfo_new&status=new&status=reopened&order=priority&format=csv'))

class FedoraPythonModulesTrac(TracBugTracker):
    enabled = False # 'Opened' and 'Last modified' bug fields aren't hyperlinked

    def __init__(self):
        TracBugTracker.__init__(self,
                                project_name='Fedora Python Modules',
                                base_url='https://fedorahosted.org/python-fedora/',
                                bitesized_keyword='')

    def generate_list_of_bug_ids_to_look_at(self):
        return mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
            mysite.customs.bugtrackers.trac.csv_of_bugs(
                'https://fedorahosted.org/python-fedora/query?status=new&status=assigned&status=reopened&order=priority&format=csv'))

class AngbandTrac(TracBugTracker):
    enabled = True

    def __init__(self):
        TracBugTracker.__init__(self,
                                project_name='Angband',
                                base_url='http://trac.rephial.org/',
                                bitesized_keyword='easy') # Unconfirmed, there were no such bugs at the time

    def generate_list_of_bug_ids_to_look_at(self):
        return mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
            mysite.customs.bugtrackers.trac.csv_of_bugs(
                'http://trac.rephial.org/query?status=assigned&status=confirmed&status=new&status=reopened&order=priority&format=csv'))

class GHCTrac(TracBugTracker):
    enabled = True

    def __init__(self):
        TracBugTracker.__init__(self,
                                project_name='GHC',
                                base_url='http://hackage.haskell.org/trac/ghc/',
                                bitesized_keyword='Easy (less than 1 hour)') # FIXME: Does OH support spaces in keywords?

    def generate_list_of_bug_ids_to_look_at(self):
        return mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
            mysite.customs.bugtrackers.trac.csv_of_bugs(
                'http://hackage.haskell.org/trac/ghc/query?status=new&status=assigned&status=reopened&group=priority&order=id&desc=1&format=csv'))

class TracTrac(TracBugTracker):
    enabled = True

    def __init__(self):
        TracBugTracker.__init__(self,
                                project_name='Trac',
                                base_url='http://trac.edgewall.org/',
                                bitesized_keyword='bitesized')

    def generate_list_of_bug_ids_to_look_at(self):
        # Just index bitesized bugs
        return mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
            mysite.customs.bugtrackers.trac.csv_of_bugs(
                'http://trac.edgewall.org/query?status=!closed&keywords=~bitesized&format=csv'))

class SSSDTrac(TracBugTracker):
    enabled = False # 'Opened' and 'Last modified' fields aren't hyperlinked

    def __init__(self):
        TracBugTracker.__init__(self,
                                project_name='SSSD',
                                base_url='https://fedorahosted.org/sssd/',
                                bitesized_keyword='easy') # They actually use the 'trivial' priority setting

    def generate_list_of_bug_ids_to_look_at(self):
        return mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
            mysite.customs.bugtrackers.trac.csv_of_bugs(
                'https://fedorahosted.org/sssd/query?status=new&status=assigned&status=reopened&order=priority&format=csv'))

class I2PTrac(TracBugTracker):
    enabled = True

    def __init__(self):
        TracBugTracker.__init__(self,
                                project_name='I2P',
                                base_url='http://trac.i2p2.de/',
                                bitesized_keyword='easy') # Unconfirmed, there were no such bugs at the time

    def generate_list_of_bug_ids_to_look_at(self):
        return mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
            mysite.customs.bugtrackers.trac.csv_of_bugs(
                'http://trac.i2p2.de/query?status=accepted&status=assigned&status=new&status=reopened&order=priority&format=csv'))

# Copy this generic class to add a new Trac bugtracker
# Remember to set 'enabled' to True
# Notes:
# Base URL: the URL of a bug for the bugtracker, without the 'ticket/1234'
# Tracking URL: go to BASE_URL/query and search for the bugs you want tracked
class GenTrac(TracBugTracker):
    enabled = False

    def __init__(self):
        TracBugTracker.__init__(self,
                                project_name='',
                                base_url='',
                                bitesized_keyword='')

    def generate_list_of_bug_ids_to_look_at(self):
        return mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
            mysite.customs.bugtrackers.trac.csv_of_bugs(
                ''))
