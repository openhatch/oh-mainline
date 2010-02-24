import csv
import mysite.customs.ohloh

def twisted_csv_of_easy_bugs():
    b = mysite.customs.ohloh.mechanize_get(
        'http://twistedmatrix.com/trac/query?status=new&status=assigned&status=reopened&format=csv&keywords=%7Eeasy&order=priority')
    return b.response()

def csv_url2list_of_bug_ids(csv_fd):
    dictreader = csv.DictReader(csv_fd)
    return [int(line['id']) for line in dictreader]

class TracBug:
    def __init__(self, bug_id, BASE_URL):
        self.bug_id = int(bug_id)
        self.BASE_URL = BASE_URL
    def as_bug_specific_csv_url(self):
        return self.BASE_URL + "%d?format=csv" % self.bug_id
    def as_bug_specific_csv_data(self):
        return {}
    def as_data_dict_for_bug_object(self):
        trac_data = self.as_bug_specific_csv_data()
        
        
