import os.path

##########
#BASEURL
##########
class BASEURL(object):
    # urls have to server independent
    _MAP = (
        ("BUG", "https://bugs.launchpad.net"),
        # https://bugs.edge.launchpad.net/ubuntu/+source/bughelper/+bug/153846/+text
        ("BUGLIST", "https://bugs.launchpad.net"),
        ("BUGPAGE", "https://bugs.launchpad.net"),
        ("BLUEPRINT", "https://blueprints.launchpad.net"),
        ("BLUEPRINTLIST", "https://blueprints.launchpad.net"),
        ("PROJECTLIST", "https://launchpad.net"),
    )
for i in BASEURL._MAP:
    setattr(BASEURL, *i)
    
##########
#Bug
##########
class BUG:
    STATUS = {  'statusNEW': 'New',
                "statusINCOMPLETE": 'Incomplete',
                'statusINVALID': 'Invalid',
                "statusWONTFIX": 'Won\'t Fix',
                "statusCONFIRMED": 'Confirmed',
                "statusTRIAGED": 'Triaged',
                "statusINPROGRESS": 'In Progress',
                'statusFIXCOMMITTED': 'Fix Committed',
                'statusFIXRELEASED': 'Fix Released'}
                
    STATUS_INCOMPLETE_ADD = { 'INCOMPLETE_WITH_RESPONSE': 'Incomplete w/',
                              "INCOMPLETE_WITHOUT_RESPONSE": 'Incomplete w/o'}
                
    SORT_STATUS = ["Fix Released","Fix Committed","In Progress",\
            "Triaged", "Confirmed","Won\'t Fix","Invalid","Incomplete", "New"]
                
    IMPORTANCE = {  "importanceUNDECIDED": "Undecided",
                    "importanceWISHLIST": "Wishlist",
                    "importanceLOW": "Low",
                    "importanceMEDIUM": "Medium",
                    "importanceHIGH": "High",
                    "importanceCRITICAL": "Critical"}

    SORT_IMPORTANCE = ["Critical","High","Medium","Low","Wishlist","Undecided"]


##########
#Buglist
##########
class BUGLIST:
    DEFAULT_DISTRO = "ubuntu"
    
    COMPONENT_DICT = { "main": 1,
                       "restricted": 2,
                       "universe": 3,
                       "multiverse": 4,
                       "contrib": 5,
                       "non-free": 6,
                       "partner": 7}


##########
#Blueprint
##########
class BLUEPRINT:
    PRIORITY = {
        "specpriorityESSENTIAL" : "Essential",
        "specpriorityHIGH" : "High",
        "specpriorityMEDIUM" : "Medium",
        "specpriorityLOW" : "Low",
        "specpriorityUNDEFINED" : "Undefined",
        "specpriorityNOTFORUS": "Not"
        #MORE?
    }
    SORT_PRIORITY = ["Essential", "High", "Medium", "Low", "Undefined", "Not"]

    STATUS = {
        "specstatusAPPROVED" : "Approved",
        "specstatusPENDINGAPPROVAL" : "Pending Approval",
        "specstatusPENDINGREVIEW" : "Review",
        "specstatusDRAFT" : "Drafting",
        "specstatusDISCUSSION" : "Discussion",
        "specstatusNEW" : "New",
        "specstatusSUPERSEDED" : "Superseded",
        "specstatusOBSOLETE" : "Obsolete"
    }
    SORT_STATUS = ["Approved", "Pending Approval", "Review", "Drafting",
                    "Discussion", "New", "Superseded", "Obsolete"]

    DELIVERY = {
        "specdeliveryUNKNOWN" : "Unknown",
        "specdeliveryINFORMATIONAL" : "Informational",
        "specdeliveryIMPLEMENTED" : "Implemented",
        "specdeliveryNOTSTARTED" : "Not started",
        "specdeliveryBETA" : "Beta Available",
        "specdeliverySTARTED" : "Started",
        "specdeliveryDEFERRED" : "Deferred",
        "specdeliveryBLOCKED" : "Blocked",
        "specdeliveryGOOD" : "Good progress",
        "specdeliveryAWAITINGDEPLOYMENT" : "Awaiting deployment",
        "specdeliverySLOW"  : "Slow progress",
        "specdeliveryNEEDSREVIEW" : "Needs code review",
        "specdeliveryNEEDSINFRASTRUCTURE" : "Needs Infrastructure"
    }
    SORT_DELIVERY = ["Unknown", "Not started", "Deferred",
            "Needs Infrastructure", "Blocked", "Started", "Slow progress",
            "Good progress", "Beta Available", "Needs Code Review",
            "Deployment", "Implemented", "Informational"]
            
            
################
#ATTACHMENTS
################
class ATTACHMENTS:
    ATTACHMENT_PATH = "~/.bughelper/attachments-cache" # default should be None
    CONTENT_TYPES = ["text/html"] # default should be an empty-list
    
    
################
#HTTPConnection
################
class HTTPCONNECTION:
    class MODE:
        DEFAULT, EDGE, STABLE, STAGING = range(4)
        
class CONFIG:
    FILE = os.path.expanduser("~/.python-launchpad-bugs.conf")
    COMMENT = """# global configuration for python-launchpad-bugs.
# user.username: user related identifier shown in the user-agent header
# test_examples.*: example data for unittests
# test_config.*:
# cookies.*: default cookies, please do not modify the values, if you
#    delete one entry, a new cookie will be generated\n\n"""
    DEFAULT = """
[user]
lplogin =

[cookies]
lp =
edge =
staging =
inhibit_beta_redirect =

[test_examples]
password =
email =
cookiefile =

[test_config]
tests =
ignore =
mail_cmd =
"""
class _MODE_WRAPPER(object):
    def __init__(self, id, identifier):
        self.__id = id
        self.__identifier = identifier
        
    def __int__(self):
        return int(self.__id)
        
    def __str__(self):
        return self.__identifier
    
    def __repr__(self):
        return "<MODE '%s'>" %self.__identifier

class CONNECTOR:
    class MODES:
        _MAP = ("HTML", "TEXT")
        HTML, TEXT = map(lambda x: _MODE_WRAPPER(*x), enumerate(_MAP))
        DEFAULT = HTML
        
    CONNECTIONS = {
        MODES.HTML : {
            "Bug": ("html_bug", ("http_connection", "HTTPConnection")),
            "BugList": ("html_buglist", ("http_connection", "HTTPConnection")),

            "Blueprint": ("html_blueprint", ("http_connection", "HTTPConnection")),
            "BlueprintList": ("html_blueprintlist", ("http_connection", "HTTPConnection")),

            "ProjectList": ("html_projectlist", ("http_connection", "HTTPConnection")),
            "ProjectPackageList": ("html_projectlist", ("http_connection", "HTTPConnection")),
        },
        MODES.TEXT : {
            "Bug": ("text_bug", ("http_connection", "HTTPConnection")),
            "BugList": ("text_buglist", ("http_connection", "HTTPConnection")),
        },
    }
