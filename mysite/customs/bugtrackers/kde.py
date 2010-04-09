import logging

import mysite.customs.bugtrackers.bugzilla_general

QUERY_URL='https://bugs.kde.org/buglist.cgi?query_format=advanced&short_desc_type=allwordssubstr&short_desc=&long_desc_type=allwordssubstr&long_desc=&bug_file_loc_type=allwordssubstr&bug_file_loc=&keywords_type=allwords&keywords=junior-jobs&bug_status=UNCONFIRMED&bug_status=NEW&bug_status=REOPENED&bug_status=NEEDSINFO&bug_status=VERIFIED&resolution=---&emailtype1=substring&email1=&emailtype2=substring&email2=&bugidtype=include&bug_id=&votes=&chfieldfrom=&chfieldto=Now&chfieldvalue=&cmdtype=doit&order=Reuse+same+sort+as+last+time&field0-0-0=noop&type0-0-0=noop&value0-0-0='
BUG_URL_PREFIX = 'https://bugs.kde.org/show_bug.cgi?id='

def project_finder_plugin(bug_xml_elt):
    import mysite.search.models
    product = bug_xml_elt.xpath('product')[0].text
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
    component = bug_xml_elt.xpath('component')[0].text
    things = (product, component)

    if product in reasonable_products:
        project_name = product
    else:
        if product in products_to_be_renamed:
            project_name = products_to_be_renamed[product]
        else:
            logging.info("Guessing on KDE subproject name. Found %s" %  things)
            project_name = product

    project, _ = mysite.search.models.Project.objects.get_or_create(
        name=project_name)
    return project

def detect_if_good_for_newcomers_plugin(bug_xml_elt, bug_object):
    keywords_blob = bug_xml_elt.xpath('keywords')[0].text
    splitted = keywords_blob.split(',')
    splitted_and_stripped = [k.strip() for k in splitted]
    if 'junior_jobs' in splitted:
        bug_object.good_for_newcomers = True
    else:
        bug_object.good_for_newcomers = False
    if bug_object.project.name == 'KDE documentation':
        bug_object.concerns_just_documentation = True

def get_current_bug_id2bug_objs():
    return mysite.customs.bugtrackers.bugzilla_general.query_url2bug_objects(
        BUG_URL_PREFIX=BUG_URL_PREFIX,
        QUERY_URL=QUERY_URL,
        project_finder_plugin=project_finder_plugin,
        detect_if_good_for_newcomers_plugin=detect_if_good_for_newcomers_plugin)

def grab():
    current_bug_id2bug_objs = get_current_bug_id2bug_objs()
    mysite.customs.bugtrackers.bugzilla_general.grab(
        current_bug_id2bug_objs,
        BUG_URL_PREFIX=BUG_URL_PREFIX)
