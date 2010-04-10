import cStringIO as StringIO
import lxml.etree as ET
import mysite.customs.ohloh

oh = mysite.customs.ohloh.get_ohloh()

def fix_all_ou():
    for c in Citation.objects.filter(data_import_attempt__source='ou'):
        if not c.url:
            import pdb
            pdb.set_trace()

def uni_text(s):
    if type(s) == unicode:
        return s
    return s.decode('utf-8')

def find_similar_citations(c):
    matching = Citation.objects.filter(portfolio_entry=c.portfolio_entry)
    summary = c.summary
    good = []
    for match in matching:
        if ((match.summary == summary) and
           (match != c)):
            good.append(match)
    return good

def fix_citation(c):
    assert c.data_import_attempt.source in ('rs', 'ou')

    if c.data_import_attempt.web_response:
        # Great! Return that.
        return c.data_import_attempt.web_response
        # else, look for one in similar ones
        similars = find_similar_citations(c)
        for similar in similars:
            if similar.data_import_attempt.web_response:
                return similar.data_import_attempt.web_response
    raise ValueError

def parse(s):
    return ET.parse(StringIO.StringIO(str(s))).getroot()

def web_response2url(web_response, project_name):
    contributor_id = 0
    tree = parse(web_response.text)
    interestings = tree.find('result/contributor_fact')
    ret = []
    for interesting in interestings:
        c_f = interesting.getparent()
        this = {}
        for child in c_f.getchildren():
            if child.text:
                this[unicode(child.tag)] = uni_text(child.text)
        eyedee = int(this['analysis_id'])
        this['project_name'] = oh.analysis2projectdata(eyedee)['url_name']
        this['permalink'] = mysite.customs.ohloh.generate_contributor_url(
            this['project_name'], int(this['contributor_id']))
        ret.append(this)

    return ret
    #return mysite.customs.ohloh.generate_contributor_url(project_name, contributor_id)

