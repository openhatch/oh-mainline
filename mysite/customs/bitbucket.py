"""
This module includes method for working with the bitbucket json api.
"""

import simplejson
import urllib

ROOT_URL = 'http://api.bitbucket.org/1.0/'

def get_user_repos(username): 
    """
    This method takes a string input of user name and 
    returns a dict containing the respositories the
    user has associated with their account.
    
    Returned values are:
    slug: The url slug for the project
    name: The name of the project
    website: The website associated wit the project, defined by the user
    followers_count: Number of followers
    description: The project description
    """
        
    json_url = ROOT_URL + ('users/%s/' % username)
    
    try:
        result = simplejson.load(urllib.urlopen(json_url))
    except:
        return []
    
    return result['repositories']


     

