import datetime
import logging

import mysite.search.models
import mysite.customs.bugtrackers.trac

class TracBugTracker(object):
    enabled = False

    def __init__(self, base_url, project_name, bug_project_name_format):
        self.base_url = base_url
        self.project_name = project_name
        self.bug_project_name_format = bug_project_name_format

    def generate_bug_project_name(self, trac_bug):
        return self.bug_project_name_format.format(project=self.project_name,
                                                   component=trac_bug.component)

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
            BASE_URL=self.base_url)
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
        data = tb.as_data_dict_for_bug_object(self.extract_tracker_specific_data)

        for key in data:
            value = data[key]
            setattr(bug, key, value)

        # And save the project onto it
        # Project name is taken from either overall project name or individual component name
        # based on the value of the boolean set in the __init__ method.
        project_from_name, _ = mysite.search.models.Project.objects.get_or_create(name=self.generate_bug_project_name(tb))
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
                                bug_project_name_format='{project}')

    def generate_list_of_bug_ids_to_look_at(self):
        return mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
            mysite.customs.bugtrackers.trac.csv_of_bugs(
                'http://tahoe-lafs.org/trac/tahoe-lafs/query?status=assigned&status=new&status=reopened&max=10000&reporter=~&col=id&col=summary&col=keywords&col=reporter&col=status&col=owner&col=type&col=priority&col=milestone&keywords=~&owner=~&desc=1&order=id&format=csv'))

    @staticmethod
    def extract_tracker_specific_data(trac_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        # Check for the bitesized keyword
        ret_dict['bite_size_tag_name'] = 'easy'
        ret_dict['good_for_newcomers'] = ('easy' in trac_data['keywords'])
        # Check whether this is a documentation bug.
        ret_dict['concerns_just_documentation'] = ('docs' in trac_data['keywords'])
        # Then pass ret_dict back
        return ret_dict

class TwistedTrac(TracBugTracker):
    enabled = True

    def __init__(self):
        TracBugTracker.__init__(self,
                                project_name='Twisted',
                                base_url='http://twistedmatrix.com/trac/',
                                bug_project_name_format='{project}')

    def generate_list_of_bug_ids_to_look_at(self):
        # Just index bitesized bugs
        return mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
            mysite.customs.bugtrackers.trac.csv_of_bugs(
                'http://twistedmatrix.com/trac/query?status=new&status=assigned&status=reopened&format=csv&keywords=%7Eeasy&order=priority'))

    @staticmethod
    def extract_tracker_specific_data(trac_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        # Check for the bitesized keyword
        ret_dict['bite_size_tag_name'] = 'easy'
        ret_dict['good_for_newcomers'] = ('easy' in trac_data['keywords'])
        # Check whether this is a documentation bug.
        ret_dict['concerns_just_documentation'] = ('documentation' in trac_data['keywords'])
        # Then pass ret_dict back
        return ret_dict

class SugarLabsTrac(TracBugTracker):
    enabled = True

    def __init__(self):
        TracBugTracker.__init__(self,
                                project_name='Sugar Labs',
                                base_url='http://bugs.sugarlabs.org/',
                                bug_project_name_format='{component}')

    def generate_list_of_bug_ids_to_look_at(self):
        # Just index bitesized bugs
        return mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
            mysite.customs.bugtrackers.trac.csv_of_bugs(
                'http://bugs.sugarlabs.org/query?status=new&status=assigned&status=reopened&format=csv&keywords=%7Esugar-love&order=priority'))

    @staticmethod
    def extract_tracker_specific_data(trac_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        # Check for the bitesized keyword
        ret_dict['bite_size_tag_name'] = 'sugar-love'
        ret_dict['good_for_newcomers'] = ('sugar-love' in trac_data['keywords'])
        # Check whether this is a documentation bug.
        ret_dict['concerns_just_documentation'] = ('documentation' in trac_data['keywords'])
        # Then pass ret_dict back
        return ret_dict

class StatusNetTrac(TracBugTracker):
    enabled = False # No longer Bugzilla?

    def __init__(self):
        TracBugTracker.__init__(self,
                                project_name='StatusNet',
                                base_url='http://status.net/trac/',
                                bug_project_name_format='{project}')

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
                                bug_project_name_format='{project}')

    def generate_list_of_bug_ids_to_look_at(self):
        # Only gives a list of bitesized bugs - confirm if devels want all bugs indexed
        return mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
            mysite.customs.bugtrackers.trac.csv_of_bugs(
                'https://trac.xiph.org/query?status=assigned&status=new&status=reopened&order=priority&format=csv&keywords=%7Eeasy'))

    @staticmethod
    def extract_tracker_specific_data(trac_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        # Check for the bitesized keyword
        ret_dict['bite_size_tag_name'] = 'easy' # Unconfirmed, there were no such bugs at the time
        ret_dict['good_for_newcomers'] = ('easy' in trac_data['keywords'])
        # Check whether this is a documentation bug.
        #ret_dict['concerns_just_documentation'] = ('docs' in trac_data['keywords'])
        # Then pass ret_dict back
        return ret_dict

class OLPCTrac(TracBugTracker):
    enabled = False # Need to sort out naming for bug projects

    def __init__(self):
        TracBugTracker.__init__(self,
                                project_name='OLPC',
                                base_url='http://dev.laptop.org/',
                                bug_project_name_format='{project}')

    def generate_list_of_bug_ids_to_look_at(self):
        return mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
            mysite.customs.bugtrackers.trac.csv_of_bugs(
                'http://dev.laptop.org/query?status=assigned&status=new&status=reopened&order=priority&format=csv'))

    @staticmethod
    def extract_tracker_specific_data(trac_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        # Check for the bitesized keyword
        ret_dict['bite_size_tag_name'] = 'easy'
        ret_dict['good_for_newcomers'] = ('easy' in trac_data['keywords']) or ('sugar-love' in trac_data['keywords'])
        # Check whether this is a documentation bug.
        ret_dict['concerns_just_documentation'] = ('doc' in trac_data['keywords'])
        # Then pass ret_dict back
        return ret_dict

class DjangoTrac(TracBugTracker):
    enabled = False # Opened' and 'Last modified' fields aren't hyperlinked

    def __init__(self):
        TracBugTracker.__init__(self,
                                project_name='Django',
                                base_url='http://code.djangoproject.com/',
                                bug_project_name_format='{project}')

    def generate_list_of_bug_ids_to_look_at(self):
        return mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
            mysite.customs.bugtrackers.trac.csv_of_bugs(
                'http://code.djangoproject.com/query?status=new&status=assigned&status=reopened&order=priority&format=csv'))

    @staticmethod
    def extract_tracker_specific_data(trac_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        # Check for the bitesized keyword
        ret_dict['bite_size_tag_name'] = 'easy'
        ret_dict['good_for_newcomers'] = ('easy' in trac_data['keywords'])
        # Check whether this is a documentation bug.
        # FIXME: No standard. Check which to use, or just look for  all?
        #ret_dict['concerns_just_documentation'] = ('doc' in trac_data['keywords'])
        # Then pass ret_dict back
        return ret_dict

class HelenOSTrac(TracBugTracker):
    enabled = True

    def __init__(self):
        TracBugTracker.__init__(self,
                                project_name='HelenOS',
                                base_url='http://trac.helenos.org/trac.fcgi/',
                                bug_project_name_format='{project}')

    def generate_list_of_bug_ids_to_look_at(self):
        return mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
            mysite.customs.bugtrackers.trac.csv_of_bugs(
                'http://trac.helenos.org/trac.fcgi/query?status=accepted&status=assigned&status=new&status=reopened&order=priority&format=csv'))

    @staticmethod
    def extract_tracker_specific_data(trac_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        # Check for the bitesized keyword
        ret_dict['bite_size_tag_name'] = 'easy' # Unconfirmed, there were no such bugs at the time
        ret_dict['good_for_newcomers'] = ('easy' in trac_data['keywords'])
        # Check whether this is a documentation bug. FIXME: Need better example - doc keyword or component?
        #ret_dict['concerns_just_documentation'] = ('doc' in trac_data['keywords'])
        # Then pass ret_dict back
        return ret_dict

class Bcfg2Trac(TracBugTracker):
    enabled = True

    def __init__(self):
        TracBugTracker.__init__(self,
                                project_name='Bcfg2',
                                base_url='https://trac.mcs.anl.gov/projects/bcfg2/',
                                bug_project_name_format='{project}')

    def generate_list_of_bug_ids_to_look_at(self):
        return mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
            mysite.customs.bugtrackers.trac.csv_of_bugs(
                'https://trac.mcs.anl.gov/projects/bcfg2/query?status=accepted&status=assigned&status=new&status=reopened&order=priority&format=csv'))

    @staticmethod
    def extract_tracker_specific_data(trac_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        # Check for the bitesized keyword
        ret_dict['bite_size_tag_name'] = 'easy' # Unconfirmed, there were no such bugs at the time
        ret_dict['good_for_newcomers'] = ('easy' in trac_data['keywords'])
        # Check whether this is a documentation bug.
        ret_dict['concerns_just_documentation'] = ('bcfg2-doc' in trac_data['component'])
        # Then pass ret_dict back
        return ret_dict

class WarFoundryTrac(TracBugTracker):
    enabled = True

    def __init__(self):
        TracBugTracker.__init__(self,
                                project_name='WarFoundry',
                                base_url='http://dev.ibboard.co.uk/projects/warfoundry/',
                                bug_project_name_format='{project}')

    def generate_list_of_bug_ids_to_look_at(self):
        return mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
            mysite.customs.bugtrackers.trac.csv_of_bugs(
                'http://dev.ibboard.co.uk/projects/warfoundry/query?status=accepted&status=assigned&status=confirmed&status=needinfo&status=needinfo_new&status=new&status=reopened&order=priority&format=csv'))

    @staticmethod
    def extract_tracker_specific_data(trac_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        # Check for the bitesized keyword
        ret_dict['bite_size_tag_name'] = 'papercut'
        ret_dict['good_for_newcomers'] = ('papercut' in trac_data['keywords'])
        # Check whether this is a documentation bug.
        #ret_dict['concerns_just_documentation'] = ('docs' in trac_data['keywords'])
        # Then pass ret_dict back
        return ret_dict

class FedoraPythonModulesTrac(TracBugTracker):
    enabled = False # 'Opened' and 'Last modified' bug fields aren't hyperlinked

    def __init__(self):
        TracBugTracker.__init__(self,
                                project_name='Fedora Python Modules',
                                base_url='https://fedorahosted.org/python-fedora/',
                                bug_project_name_format='{project}')

    def generate_list_of_bug_ids_to_look_at(self):
        return mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
            mysite.customs.bugtrackers.trac.csv_of_bugs(
                'https://fedorahosted.org/python-fedora/query?status=new&status=assigned&status=reopened&order=priority&format=csv'))

    @staticmethod
    def extract_tracker_specific_data(trac_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        # Check for the bitesized keyword
        #ret_dict['bite_size_tag_name'] = 'easy'
        #ret_dict['good_for_newcomers'] = ('easy' in trac_data['keywords'])
        # Check whether this is a documentation bug.
        #ret_dict['concerns_just_documentation'] = ('doc' in trac_data['keywords'])
        # Then pass ret_dict back
        return ret_dict

class AngbandTrac(TracBugTracker):
    enabled = True

    def __init__(self):
        TracBugTracker.__init__(self,
                                project_name='Angband',
                                base_url='http://trac.rephial.org/',
                                bug_project_name_format='{project}')

    def generate_list_of_bug_ids_to_look_at(self):
        return mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
            mysite.customs.bugtrackers.trac.csv_of_bugs(
                'http://trac.rephial.org/query?status=assigned&status=confirmed&status=new&status=reopened&order=priority&format=csv'))

    @staticmethod
    def extract_tracker_specific_data(trac_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        # Check for the bitesized keyword
        ret_dict['bite_size_tag_name'] = 'easy' # Unconfirmed, there were no such bugs at the time
        ret_dict['good_for_newcomers'] = ('easy' in trac_data['keywords'])
        # Check whether this is a documentation bug.
        ret_dict['concerns_just_documentation'] = ('doc' in trac_data['keywords'])
        # Then pass ret_dict back
        return ret_dict

class GHCTrac(TracBugTracker):
    enabled = True

    def __init__(self):
        TracBugTracker.__init__(self,
                                project_name='GHC',
                                base_url='http://hackage.haskell.org/trac/ghc/',
                                bug_project_name_format='{project}')

    def generate_list_of_bug_ids_to_look_at(self):
        return mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
            mysite.customs.bugtrackers.trac.csv_of_bugs(
                'http://hackage.haskell.org/trac/ghc/query?status=new&status=assigned&status=reopened&group=priority&order=id&desc=1&format=csv'))

    @staticmethod
    def extract_tracker_specific_data(trac_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        # Check for the bitesized keyword
        ret_dict['bite_size_tag_name'] = 'Easy (less than 1 hour)'
        ret_dict['good_for_newcomers'] = ('Easy (less than 1 hour)' in trac_data['difficulty'])
        # Check whether this is a documentation bug.
        ret_dict['concerns_just_documentation'] = ('Documentation' in trac_data['component'])
        # Then pass ret_dict back
        return ret_dict

class TracTrac(TracBugTracker):
    enabled = True

    def __init__(self):
        TracBugTracker.__init__(self,
                                project_name='Trac',
                                base_url='http://trac.edgewall.org/',
                                bug_project_name_format='{project}')

    def generate_list_of_bug_ids_to_look_at(self):
        # Just index bitesized bugs
        return mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
            mysite.customs.bugtrackers.trac.csv_of_bugs(
                'http://trac.edgewall.org/query?status=!closed&keywords=~bitesized&format=csv'))

    @staticmethod
    def extract_tracker_specific_data(trac_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        # Check for the bitesized keyword
        ret_dict['bite_size_tag_name'] = 'bitesized'
        ret_dict['good_for_newcomers'] = ('bitesized' in trac_data['keywords'])
        # Check whether this is a documentation bug.
        #ret_dict['concerns_just_documentation'] = ('doc' in trac_data['keywords'])
        # Then pass ret_dict back
        return ret_dict

class SSSDTrac(TracBugTracker):
    enabled = False # 'Opened' and 'Last modified' fields aren't hyperlinked

    def __init__(self):
        TracBugTracker.__init__(self,
                                project_name='SSSD',
                                base_url='https://fedorahosted.org/sssd/',
                                bug_project_name_format='{project}')

    def generate_list_of_bug_ids_to_look_at(self):
        return mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
            mysite.customs.bugtrackers.trac.csv_of_bugs(
                'https://fedorahosted.org/sssd/query?status=new&status=assigned&status=reopened&order=priority&format=csv'))

    @staticmethod
    def extract_tracker_specific_data(trac_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        # Check for the bitesized keyword
        ret_dict['bite_size_tag_name'] = 'trivial'
        ret_dict['good_for_newcomers'] = ('trivial' in trac_data['priority'])
        # Check whether this is a documentation bug.
        #ret_dict['concerns_just_documentation'] = ('doc' in trac_data['keywords'])
        # Then pass ret_dict back
        return ret_dict

class I2PTrac(TracBugTracker):
    enabled = True

    def __init__(self):
        TracBugTracker.__init__(self,
                                project_name='I2P',
                                base_url='http://trac.i2p2.de/',
                                bug_project_name_format='{project}')

    def generate_list_of_bug_ids_to_look_at(self):
        return mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
            mysite.customs.bugtrackers.trac.csv_of_bugs(
                'http://trac.i2p2.de/query?status=accepted&status=assigned&status=new&status=reopened&order=priority&format=csv'))

    @staticmethod
    def extract_tracker_specific_data(trac_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        # Check for the bitesized keyword
        ret_dict['bite_size_tag_name'] = 'easy'
        ret_dict['good_for_newcomers'] = ('easy' in trac_data['keywords'])
        # Check whether this is a documentation bug.
        #ret_dict['concerns_just_documentation'] = ('doc' in trac_data['keywords'])
        # Then pass ret_dict back
        return ret_dict

# Copy this generic class to add a new Trac bugtracker
# Remember to set 'enabled' to True
# Notes:
# Base URL: the URL of a bug for the bugtracker, without the 'ticket/1234'
# Tracking URL: go to BASE_URL/query and search for the bugs you want tracked
# bug_project_name_format: the format to be used for the bug's project name
# "{project}" will be replaced by project_name, and "{component}" by the
# component the bug is part of (as taken from the bug's ticket).
class GenTrac(TracBugTracker):
    enabled = False

    def __init__(self):
        TracBugTracker.__init__(self,
                                project_name='',
                                base_url='',
                                bug_project_name_format='')

    def generate_list_of_bug_ids_to_look_at(self):
        return mysite.customs.bugtrackers.trac.csv_url2list_of_bug_ids(
            mysite.customs.bugtrackers.trac.csv_of_bugs(
                ''))

    @staticmethod
    def extract_tracker_specific_data(trac_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        # Check for the bitesized keyword
        ret_dict['bite_size_tag_name'] = ''
        ret_dict['good_for_newcomers'] = ('' in trac_data['keywords'])
        # Check whether this is a documentation bug.
        ret_dict['concerns_just_documentation'] = ('' in trac_data['keywords'])
        # Then pass ret_dict back
        return ret_dict

