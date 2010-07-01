import datetime
import logging

import mysite.search.models
import mysite.customs.bugtrackers.bugzilla

class BugzillaBugTracker(object):
    def __init__(self, base_url, project_name, bug_project_name_format, bug_id_list_only=False):
        self.base_url = base_url
        self.project_name = project_name
        self.bug_project_name_format = bug_project_name_format
        self.bug_id_list_only = bug_id_list_only

    def generate_bug_xml_from_queries(self, queries)
        for query_name in queries:
            query_url = queries[query_name]
            query_xml = mysite.customs.bugtrackers.bugzilla.url2bug_data(query_url)
            for bug_xml in query_xml.xpath('bug'):
                yield bug_xml

    def generate_bug_project_name(self, bb):
        return self.bug_project_name_format.format(
                project = self.project_name,
                product = bb.product,
                component = bb.component)

    def create_or_refresh_one_bugzilla_bug(self, bb):
        bug_id = bb.bug_id
        bug_url = bb.as_bug_specific_url()

        try:
            bug = mysite.search.models.Bug.all_bugs.get(
                    canonical_bug_link=bug_url)
            # Found an existing bug. Does it need refreshing?
            if bug.data_is_more_fresh_than_one_day():
                logging.info("[Bugzilla] Bug %d from %s is fresh. Doing nothing!" % (bug_id, self.project_name))
                return False # sweet
        except mysite.search.models.Bug.DoesNotExist:
            # This is a new bug
            bug = mysite.search.models.Bug(canonical_bug_link = bug_url)

        # Looks like we have some refreshing to do.
        logging.info("[Bugzilla] Refreshing bug %d from %s." % (bug_id, self.project_name))
        # Get the dictionary of data to put into the bug. The function for
        # obtaining tracker-specific data is passed in.
        data = bb.as_data_dict_for_bug_object(self.extract_tracker_specific_data)

        # Fill that bug!
        for key in data:
            value = data[key]
            setattr(bug, key, value)

        # Find or create the project for the bug and save it
        bug_project_name = self.generate_bug_project_name(bb)
        if bug_project_name == '':
            raise ValueError("Can't have bug_project_name as ''")
        project_from_name, _ = mysite.search.models.Project.objects.get_or_create(name=bug_project_name)
        if bug.project_id != project_from_name.id:
            bug.project = project_from_name
        bug.last_polled = datetime.datetime.utcnow()
        bug.save()
        logging.info("[Bugzilla] Finished with %d from %s." % (bug_id, self.project_name))
        return True

    def refresh_all_bugs(self):
        for bug in mysite.search.models.Bug.all_bugs.filter(
                canonical_bug_link__contains=self.base_url):
            bb = mysite.customs.bugtrackers.bugzilla.BugzillaBug.from_url(
                    bug.canonical_bug_link)
            self.create_or_refresh_one_bugzilla_bug(bb=bb)

    def update(self):
        logging.info("[Bugzilla] Started refreshing all %s bugs" % self.project_name)

        # First, go through and create or refresh all the bugs that
        # we are configured to track. This will add new bugs and
        # update current ones. Bugzilla doesn't return a nice
        # CSV list of bug ids, but instead gives an entire XML tree
        # of bug data for the bugs matching the query. To save on
        # network traffic, the bug data will be passed to the refresher.
        if self.bug_id_list_only:
            # If we have a tracking bug, then we can't get an xml tree
            # of bug data. Instead we have to use the bug ids pulled
            # from the dependencies of the tracking bug.
            current_bug_id_list = self.get_current_bug_id_list()
            for bug_id in current_bug_id_list:
                bb = mysite.customs.bugtrackers.bugzilla.BugzillaBug(
                        BASE_URL=self.base_url,
                        bug_id=bug_id)
                self.create_or_refresh_one_bugzilla_bug(bb=bb)
        else:
            logging.info("[Bugzilla] Fetching XML data for bugs in tracker...")
            for bug_data in self.generate_current_bug_xml():
                bb = mysite.customs.bugtrackers.bugzilla.BugzillaBug(
                        BASE_URL=self.base_url,
                        bug_data=bug_data)
                self.create_or_refresh_one_bugzilla_bug(bb=bb)

        # Then refresh all the bugs we have from this tracker. This
        # should skip over all the bugs except the ones that didn't
        # appear in the above query. Usually this is closed bugs.
        self.refresh_all_bugs()

class MiroBugzilla(BugzillaBugTracker):
    enabled = True

    def __init__(self):
        BugzillaBugTracker.__init__(self,
                                    base_url='http://bugzilla.pculture.org/',
                                    project_name='Miro',
                                    bug_project_name_format='{project}')

    def generate_current_bug_xml(self):
        queries = {
                'Easy bugs':
                    'http://bugzilla.pculture.org/buglist.cgi?bug_status=NEW&bug_status=ASSIGNED&bug_status=REOPENED&field-1-0-0=bug_status&field-1-1-0=product&field-1-2-0=keywords&keywords=bitesized&product=Miro&query_format=advanced&remaction=&type-1-0-0=anyexact&type-1-1-0=anyexact&type-1-2-0=anywords&value-1-0-0=NEW%2CASSIGNED%2CREOPENED&value-1-1-0=Miro&value-1-2-0=bitesized',
                #'Documentation bugs':
                    #''
                }
        return self.generate_bug_xml_from_queries(queries)

    @staticmethod
    def extract_tracker_specific_data(xml_data, ret_dict):
        # Make modifications to ret_dict using provided xml data
        keywords_text = mysite.customs.bugtrackers.bugzilla.get_tag_text_from_xml(xml_data, 'keywords')
        keywords = map(lambda s: s.strip(),
                       keywords_text.split(','))
        ret_dict['good_for_newcomers'] = ('bitesized' in keywords)
        # Then pass ret_dict back
        return ret_dict

class KDEBugzilla(BugzillaBugTracker):
    enabled = True

    def __init__(self):
        BugzillaBugTracker.__init__(self,
                                    base_url='https://bugs.kde.org/',
                                    project_name='KDE',
                                    bug_project_name_format='')

    def get_current_xml_bug_tree(self):
        return mysite.customs.bugtrackers.bugzilla.url2bug_data(

    def generate_current_bug_xml(self):
        queries = {
                'Easy bugs':
                    'https://bugs.kde.org/buglist.cgi?query_format=advanced&keywords=junior-jobs&resolution=---',
                'Documentation bugs':
                    'https://bugs.kde.org/buglist.cgi?query_format=advanced&product=docs&resolution=---'
                }
        return self.generate_bug_xml_from_queries(queries)

    @staticmethod
    def extract_tracker_specific_data(xml_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        keywords_text = mysite.customs.bugtrackers.bugzilla.get_tag_text_from_xml(xml_data, 'keywords')
        keywords = map(lambda s: s.strip(),
                       keywords_text.split(','))
        ret_dict['good_for_newcomers'] = ('junior-jobs' in keywords)
        # Remove 'JJ:' from title if present
        if ret_dict['title'].startswith("JJ:"):
            ret_dict['title'] = ret_dict['title'][3:].strip()
        # Check whether documentation bug
        product = mysite.customs.bugtrackers.bugzilla.get_tag_text_from_xml(xml_data, 'product')
        ret_dict['concerns_just_documentation'] = (product == 'docs')
        # Then pass ret_dict back
        return ret_dict

    def generate_bug_project_name(self, bb):
        product = bb.product
        reasonable_products = set([
            'Akonadi',
            'Phonon'
            'kmail',
            'Rocs',
            'akregator',
            'amarok',
            'ark',
            'cervisia',
            'k3b',
            'kappfinder',
            'kbabel',
            'kdeprint',
            'kdesktop',
            'kfile',
            'kfourinline',
            'khotkeys',
            'kio',
            'kmail',
            'kmplot',
            'koffice',
            'kompare',
            'konqueror',
            'kopete',
            'kpat',
            'kphotoalbum',
            'krita',
            'ksmserver',
            'kspread',
            'ksysguard',
            'ktimetracker',
            'kwin',
            'kword',
            'marble',
            'okular',
            'plasma',
            'printer-applet',
            'rsibreak',
            'step',
            'systemsettings',
            'kdelibs',
            'kcontrol',
            'korganizer',
            'kipiplugins',
            'Phonon',
            'dolphin',
            'umbrello']
            )
        products_to_be_renamed = {
            'digikamimageplugins': 'digikam image plugins',
            'Network Management': 'KDE Network Management',
            'telepathy': 'telepathy for KDE',
            'docs': 'KDE documentation',
            }
        component = bb.component
        things = (product, component)

        if product in reasonable_products:
            bug_project_name = product
        else:
            if product in products_to_be_renamed:
                bug_project_name = products_to_be_renamed[product]
            else:
                logging.info("Guessing on KDE subproject name. Found %s" %  repr(things))
                bug_project_name = product
        return bug_project_name

class MediaWikiBugzilla(BugzillaBugTracker):
    enabled = True

    def __init__(self):
        BugzillaBugTracker.__init__(self,
                                    base_url='https://bugzilla.wikimedia.org/',
                                    project_name='MediaWiki',
                                    bug_project_name_format='')

    def generate_current_bug_xml(self):
        queries = {
                'Easy bugs':
                    'https://bugzilla.wikimedia.org/buglist.cgi?keywords=easy&query_format=advanced&resolution=LATER&resolution=---',
                'Documentation bugs':
                    'https://bugzilla.wikimedia.org/buglist.cgi?query_format=advanced&component=Documentation&resolution=---'
                }
        return self.generate_bug_xml_from_queries(queries)

    @staticmethod
    def extract_tracker_specific_data(xml_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        # Check for the bitesized keyword
        keywords_text = mysite.customs.bugtrackers.bugzilla.get_tag_text_from_xml(xml_data, 'keywords')
        keywords = map(lambda s: s.strip(),
                       keywords_text.split(','))
        ret_dict['good_for_newcomers'] = ('easy' in keywords)
        # Check whether documentation bug
        component = mysite.customs.bugtrackers.bugzilla.get_tag_text_from_xml(xml_data, 'component')
        ret_dict['concerns_just_documentation'] = (component == 'Documentation')
        # Then pass ret_dict back
        return ret_dict

    def generate_bug_project_name(self, bb):
        product = bb.product
        if product == 'MediaWiki extensions':
            bug_project_name = bb.component
            if bug_project_name in ('FCKeditor', 'Gadgets'):
                bug_project_name += ' for MediaWiki'
        else:
            bug_project_name = product
        return bug_project_name

class GnomeBugzilla(BugzillaBugTracker):
    enabled = True

    def __init__(self):
        BugzillaBugTracker.__init__(self,
                                    base_url='https://bugzilla.gnome.org/',
                                    project_name='Gnome',
                                    bug_project_name_format='')

    def generate_current_bug_xml(self):
        # Get all bugs that contain any of the keywords 'gnome-love'
        # or 'documentation'
        queries = {
                'Easy bugs':
                    'https://bugzilla.gnome.org/buglist.cgi?columnlist=id&keywords=gnome-love&query_format=advanced&resolution=---',
                # FIXME: Query with documentation keyword causes XML syntax errors
                #'Documentation bugs':
                    #'https://bugzilla.gnome.org/buglist.cgi?columnlist=id&keywords=gnome-love%2Cdocumentation&query_format=advanced&resolution=---'
                }
        return self.generate_bug_xml_from_queries(queries)

    @staticmethod
    def extract_tracker_specific_data(xml_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        # Check for the bitesized keyword
        keywords_text = mysite.customs.bugtrackers.bugzilla.get_tag_text_from_xml(xml_data, 'keywords')
        keywords = map(lambda s: s.strip(),
                       keywords_text.split(','))
        ret_dict['good_for_newcomers'] = ('gnome-love' in keywords)
        # Check whether this is a documentation bug.
        ret_dict['concerns_just_documentation'] = ('documentation' in keywords)
        # Then pass ret_dict back
        return ret_dict

    def generate_bug_project_name(self, bb):
        bug_project_name = bb.product
        gnome2openhatch = {'general': 'GNOME (general)',
                           'website': 'GNOME (website)'}
        if bug_project_name in gnome2openhatch:
            bug_project_name=gnome2openhatch[bug_project_name]
        return bug_project_name

class MozillaBugzilla(BugzillaBugTracker):
    enabled = True

    def __init__(self):
        BugzillaBugTracker.__init__(self,
                                    base_url='https://bugzilla.mozilla.org/',
                                    project_name='Mozilla',
                                    bug_project_name_format='')

    def generate_current_bug_xml(self):
        queries = {
                'Easy bugs':
                    'https://bugzilla.mozilla.org/buglist.cgi?resolution=---;status_whiteboard_type=substring;query_format=advanced;status_whiteboard=[good%20first%20bug]',
                #'Documentation bugs':
                    #''
                }
        return self.generate_bug_xml_from_queries(queries)

    @staticmethod
    def extract_tracker_specific_data(xml_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        # Check for the bitesized keyword
        whiteboard_text = mysite.customs.bugtrackers.bugzilla.get_tag_text_from_xml(xml_data, 'status_whiteboard')
        ret_dict['good_for_newcomers'] = (whiteboard_text == '[good first bug]')
        # Then pass ret_dict back
        return ret_dict

    def generate_bug_project_name(self, bb):
        ### Special-case the project names we know about
        mozilla2openhatch = {'Core': 'Mozilla Core',
                             'Firefox': 'Firefox',
                             'MailNews Core': 'Mozilla Messaging',
                             'addons.mozilla.org': 'addons.mozilla.org',
                             'Thunderbird': 'Thunderbird',
                             'Testing': 'Mozilla automated testing',
                             'Directory': 'Mozilla LDAP',
                             'mozilla.org': 'mozilla.org',
                             'SeaMonkey': 'SeaMonkey',
                             'Toolkit': 'Mozilla Toolkit',
                             'support.mozilla.com': 'support.mozilla.com',
                             'Camino': 'Camino',
                             'Calendar': 'Mozilla Calendar',
                             'Mozilla Localizations': 'Mozilla Localizations',
                             }
        if bb.product == 'Other Applications':
            bug_project_name = 'Mozilla ' + bb.component
        else:
            bug_project_name = mozilla2openhatch[bb.product]
        return bug_project_name

class FedoraBugzilla(BugzillaBugTracker):
    enabled = True

    def __init__(self):
        BugzillaBugTracker.__init__(self,
                                    base_url='https://bugzilla.redhat.com/',
                                    project_name='Fedora',
                                    bug_project_name_format='{component}',
                                    bug_id_list_only=True)

    def get_current_bug_id_list(self):
        return mysite.customs.bugtrackers.bugzilla.tracker_bug2bug_ids(
                'https://bugzilla.redhat.com/show_bug.cgi?ctype=xml&id=509829')

    @staticmethod
    def extract_tracker_specific_data(xml_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        # Check for the bitesized keyword
        keywords_text = mysite.customs.bugtrackers.bugzilla.get_tag_text_from_xml(xml_data, 'keywords')
        keywords = map(lambda s: s.strip(),
                       keywords_text.split(','))
        ret_dict['good_for_newcomers'] = True # Since they are 'fit and finish'
        # Set the distribution tag
        ret_dict['as_appears_in_distribution'] = 'Fedora'
        # Then pass ret_dict back
        return ret_dict

class SongbirdBugzilla(BugzillaBugTracker):
    enabled = True

    def __init__(self):
        BugzillaBugTracker.__init__(self,
                                    base_url='http://bugzilla.songbirdnest.com/',
                                    project_name='Songbird',
                                    bug_project_name_format='{project}')

    def generate_current_bug_xml(self):
        # Query below returns nearly 4000 bugs if we try to index everything.
        # For now, only import bugs with 'helpwanted' tag.
        # (This tag doesn't equate to 'bitesized'.)
        queries = {
                'Helpwanted bugs':
                    'http://bugzilla.songbirdnest.com/buglist.cgi?query_format=advanced&resolution=---&keywords=helpwanted',
                'Documentation bugs':
                    'http://bugzilla.songbirdnest.com/buglist.cgi?query_format=advanced&component=Documentation&resolution=---'
                }
        return self.generate_bug_xml_from_queries(queries)

    @staticmethod
    def extract_tracker_specific_data(xml_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        ret_dict['good_for_newcomers'] = False # 'helpwanted' doesn't just indicate bitesized.
        # Check whether documentation bug
        component = mysite.customs.bugtrackers.bugzilla.get_tag_text_from_xml(xml_data, 'component')
        ret_dict['concerns_just_documentation'] = (component == 'Documentation')
        # Then pass ret_dict back
        return ret_dict

class ApertiumBugzilla(BugzillaBugTracker):
    enabled = True

    def __init__(self):
        BugzillaBugTracker.__init__(self,
                                    base_url='http://bugs.apertium.org/cgi-bin/bugzilla/',
                                    project_name='Apertium',
                                    bug_project_name_format='{project}')

    def generate_current_bug_xml(self):
        queries = {
                'All bugs':
                    'http://bugs.apertium.org/cgi-bin/bugzilla/buglist.cgi?query_format=advanced&resolution=---'
                }
        return self.generate_bug_xml_from_queries(queries)

    @staticmethod
    def extract_tracker_specific_data(xml_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        ret_dict['good_for_newcomers'] = False # No bitesized keyword.
        # Then pass ret_dict back
        return ret_dict

class MusopenBugzilla(BugzillaBugTracker):
    enabled = False # FIXME: Haven't found actual bugtracker yet...

    def __init__(self):
        BugzillaBugTracker.__init__(self,
                                    base_url='',
                                    project_name='Musopen',
                                    bug_project_name_format='{project}')

    def generate_current_bug_xml(self):
        queries = {
                'Easy bugs':
                    '',
                'Documentation bugs':
                    ''
                }
        return self.generate_bug_xml_from_queries(queries)

    @staticmethod
    def extract_tracker_specific_data(xml_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        # Check for the bitesized keyword
        keywords_text = mysite.customs.bugtrackers.bugzilla.get_tag_text_from_xml(xml_data, 'keywords')
        keywords = map(lambda s: s.strip(),
                       keywords_text.split(','))
        ret_dict['good_for_newcomers'] = ('' in keywords)
        # Then pass ret_dict back
        return ret_dict

    # The formt string method for generating the project name can be
    # overloaded by uncommenting the function below.
    #def generate_bug_project_name(self, bb):
        #return bug_project_name

class RTEMSBugzilla(BugzillaBugTracker):
    enabled = True

    def __init__(self):
        BugzillaBugTracker.__init__(self,
                                    base_url='https://www.rtems.org/bugzilla/',
                                    project_name='RTEMS',
                                    bug_project_name_format='{project}')

    def generate_current_bug_xml(self):
        queries = {
                'All bugs':
                    'https://www.rtems.org/bugzilla/buglist.cgi?query_format=advanced&resolution=---'
                }
        return self.generate_bug_xml_from_queries(queries)

    @staticmethod
    def extract_tracker_specific_data(xml_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        ret_dict['good_for_newcomers'] = False # No bitesized keyword.
        # Check whether documentation bug
        component = mysite.customs.bugtrackers.bugzilla.get_tag_text_from_xml(xml_data, 'component')
        ret_dict['concerns_just_documentation'] = (component == 'doc')
        # Then pass ret_dict back
        return ret_dict

# This tracker could be extended to cover all of FreeDesktop.
# For now, just do X.Org since it is all that was requested.
class XOrgBugzilla(BugzillaBugTracker):
    enabled = True

    def __init__(self):
        BugzillaBugTracker.__init__(self,
                                    base_url='https://bugs.freedesktop.org/',
                                    project_name='XOrg',
                                    bug_project_name_format='{project}')

    def generate_current_bug_xml(self):
        # Query below returns over 2500 bugs if we try to index everything.
        # For now just index bitesized bugs - keyword filter added to query.
        queries = {
                'Easy bugs':
                    'https://bugs.freedesktop.org/buglist.cgi?query_format=advanced&keywords=janitor&resolution=---&product=xorg',
                'Documentation bugs':
                    'https://bugs.freedesktop.org/buglist.cgi?query_format=advanced&component=Docs%2Fother&component=Documentation&component=Fonts%2Fdoc&resolution=---&product=xorg'
                }
        return self.generate_bug_xml_from_queries(queries)

    @staticmethod
    def extract_tracker_specific_data(xml_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        # Check for the bitesized keyword
        keywords_text = mysite.customs.bugtrackers.bugzilla.get_tag_text_from_xml(xml_data, 'keywords')
        keywords = map(lambda s: s.strip(),
                       keywords_text.split(','))
        ret_dict['good_for_newcomers'] = ('janitor' in keywords)
        # Check whether documentation bug
        component = mysite.customs.bugtrackers.bugzilla.get_tag_text_from_xml(xml_data, 'component')
        documentation_components = [
                'Docs/other',
                'Documentation',
                'Fonts/doc']
        ret_dict['concerns_just_documentation'] = (component in documentation_components)
        # Then pass ret_dict back
        return ret_dict

class LocamotionBugzilla(BugzillaBugTracker):
    enabled = False # FIXME: Throws XML encoding error.

    def __init__(self):
        BugzillaBugTracker.__init__(self,
                                    base_url='http://bugs.locamotion.org/',
                                    project_name='Locamotion',
                                    bug_project_name_format='{product}')

    def generate_current_bug_xml(self):
        queries = {
                'All bugs':
                    'http://bugs.locamotion.org/buglist.cgi?query_format=advanced&resolution=---'
                }
        return self.generate_bug_xml_from_queries(queries)

    @staticmethod
    def extract_tracker_specific_data(xml_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        ret_dict['good_for_newcomers'] = False # No bitesized keyword.
        # Then pass ret_dict back
        return ret_dict

class HypertritonBugzilla(BugzillaBugTracker):
    enabled = True

    def __init__(self):
        BugzillaBugTracker.__init__(self,
                                    base_url='https://hypertriton.com/bugzilla/',
                                    project_name='Hypertriton',
                                    bug_project_name_format='{product}')

    def generate_current_bug_xml(self):
        queries = {
                'All bugs':
                    'https://hypertriton.com/bugzilla/buglist.cgi?query_format=advanced&resolution=---&product=Agar&product=EDAcious&product=FabBSD&product=FreeSG'
                }
        return self.generate_bug_xml_from_queries(queries)

    @staticmethod
    def extract_tracker_specific_data(xml_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        ret_dict['good_for_newcomers'] = False # No bitesized keyword
        # Then pass ret_dict back
        return ret_dict

class PygameBugzilla(BugzillaBugTracker):
    enabled = True

    def __init__(self):
        BugzillaBugTracker.__init__(self,
                                    base_url='http://pygame.motherhamster.org/bugzilla/',
                                    project_name='pygame',
                                    bug_project_name_format='{project}')

    def generate_current_bug_xml(self):
        queries = {
                'All bugs':
                    'http://pygame.motherhamster.org/bugzilla/buglist.cgi?query_format=advanced&resolution=---'
                }
        return self.generate_bug_xml_from_queries(queries)

    @staticmethod
    def extract_tracker_specific_data(xml_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        ret_dict['good_for_newcomers'] = False # No bitesized keyword
        # Then pass ret_dict back
        return ret_dict

# The generic class for Bugzilla trackers. Copy it.
# If the project has a tracker bug for the bugs to be imported,
# set bug_id_list_only=True in BugzillaBugTracker.__init__ and
# replace get_current_xml_bug_tree with get_current_bug_id_list
# bug_project_name_format can contain the tags {project},
# {product} and {component} which will be replaced accordingly.
class GenBugzilla(BugzillaBugTracker):
    enabled = False

    def __init__(self):
        BugzillaBugTracker.__init__(self,
                                    base_url='',
                                    project_name='',
                                    bug_project_name_format='')

    def generate_current_bug_xml(self):
        # Can replace both entries below with an 'All bugs' query.
        queries = {
                'Easy bugs':
                    '',
                'Documentation bugs':
                    ''
                }
        return self.generate_bug_xml_from_queries(queries)

    @staticmethod
    def extract_tracker_specific_data(xml_data, ret_dict):
        # Make modifications to ret_dict using provided metadata
        # Check for the bitesized keyword
        keywords_text = mysite.customs.bugtrackers.bugzilla.get_tag_text_from_xml(xml_data, 'keywords')
        keywords = map(lambda s: s.strip(),
                       keywords_text.split(','))
        ret_dict['good_for_newcomers'] = ('' in keywords)
        # Then pass ret_dict back
        return ret_dict

    # The format string method for generating the project name can be
    # overloaded by uncommenting the function below.
    #def generate_bug_project_name(self, bb):
        #return bug_project_name

