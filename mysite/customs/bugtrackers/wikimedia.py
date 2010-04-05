import mysite.customs.bugtrackers.bugzilla_general

QUERY_URL='https://bugzilla.wikimedia.org/buglist.cgi?keywords=easy&query_format=advanced&keywords_type=allwords&bug_status=NEW&bug_status=ASSIGNED&bug_status=REOPENED&bug_status=VERIFIED&resolution=LATER&resolution=---'
BUG_URL_PREFIX = 'https://bugzilla.wikimedia.org/show_bug.cgi?id='

def project_finder_plugin(bug_xml_elt):
    import mysite.search.models
    product = bug_xml_elt.xpath('product')[0].text
    if product == 'MediaWiki extensions':
        project_name = bug_xml_elt.xpath('component')[0].text
    else:
        project_name = product
        
    project, _ = mysite.search.models.Project.objects.get_or_create(
        name=project_name)
    return project

def detect_if_good_for_newcomers_plugin(bug_xml_elt, bug_object):
    keywords_blob = bug_xml_elt.xpath('keywords')[0].text
    splitted = keywords_blob.split(',')
    splitted_and_stripped = [k.strip() for k in splitted]
    if 'easy' in splitted:
        bug_object.good_for_newcomers = True
    else:
        bug_object.good_for_newcomers = False        

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
                                         
                                         


