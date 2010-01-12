import github2.client
from django.conf import settings
import mysite.customs.ohloh
import simplejson

_github = None

# Always initialize this at module import time
# If this web app ran on an OLPC laptop, we'd be making
# children sad by running unnecessary code at module
# import time. But this seems just fine to me for a long-
# running server process.
_github = github2.client.Github(username=settings.GITHUB_USERNAME,
                               api_token=settings.GITHUB_API_TOKEN)

def repos_by_username(username):
    repos = _github.repos.list(username)
    for repo in repos:
        yield repo

def find_primary_language_of_repo(github_username, github_reponame):
    # FIXME: Make this handle a few situations
    # * Repo does not exist (or rather, raise ValueError then)
    # * We have hit the Github API limit, in which case, let the caller
    #   know it's safe to retry this later (it'd be nice to know when)
    assert '/' not in github_reponame
    assert '/' not in github_username

    json_url = 'http://github.com/api/v2/json/repos/show/%s/%s/languages' % (
        github_username, github_reponame)
    response = mysite.customs.ohloh.mechanize_get(json_url).response()
    data = simplejson.load(response)
    if 'languages' in data:
        language_name_count_tuples = data['languages'].items()
        sorted_by_count = sorted(language_name_count_tuples,
                                   lambda x: x[1])
        winning_lang_name, winning_lang_count = sorted_by_count[0]
        return winning_lang_name
    else:
        return '' # No best guess for primary language.
