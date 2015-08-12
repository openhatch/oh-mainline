#!/usr/bin/python
#
# Copyright 2011 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Sample for the Provisioning API and the Email Settings API with OAuth 2.0"""

__author__ = 'Shraddha Gupta <shraddhag@google.com>'

from optparse import OptionParser
import gdata.apps
import gdata.apps.emailsettings.client
import gdata.client
import gdata.gauth


API_VERSION = '2.0'
BASE_URL = '/a/feeds/group/%s' % API_VERSION
SCOPE = ('https://apps-apis.google.com/a/feeds/group '
         'https://apps-apis.google.com/a/feeds/emailsettings/2.0/')
HOST = 'apps-apis.google.com'


class OAuth2ClientSample(object):
  """ OAuth2ClientSample object demos the use of OAuth2Token for retrieving
  Members of a Group and updating Email Settings for them."""

  def __init__(self, domain, client_id, client_secret):
    """
    Args:
      domain: string Domain name (e.g. domain.com)
      client_id: string Client_id of domain admin account.
      client_secret: string Client_secret of domain admin account.
    """
    try:
      self.token = gdata.gauth.OAuth2Token(client_id=client_id,
                                           client_secret=client_secret,
                                           scope=SCOPE,
                                           user_agent='oauth2-provisioningv2')
      self.uri = self.token.generate_authorize_url()
      print 'Please visit this URL to authorize the application:'
      print self.uri
      # Get the verification code from the standard input.
      code = raw_input('What is the verification code? ').strip()
      self.token.get_access_token(code)
    except gdata.gauth.OAuth2AccessTokenError, e:
      print 'Invalid Access token, Check your credentials %s' % e
      exit(0)
    self.domain = domain
    self.baseuri = '%s/%s' % (BASE_URL, domain)
    self.client = gdata.client.GDClient(host=HOST)
    self.client.domain = self.domain
    # Authorize the client. 
    # This will add the Authorization header to all future requests.
    self.token.authorize(self.client)
    self.email_client = gdata.apps.emailsettings.client.EmailSettingsClient(
        domain=self.domain, auth_token=self.token)
    self.token.authorize(self.email_client)

  def get_users(self, group):
    """Retrieves members from the given group.
    
    Args:
      group: string Id of the group
      
    Returns:
      Member feed for the given group
    """
    uri = '%s/%s/member' % (self.baseuri, group)
    try:
      feed = self.client.GetFeed(uri=uri)
      return gdata.apps.PropertyFeedFromString(str(feed))
    except gdata.client.RequestError, e:
      print 'Exception %s' % e

  def create_filter(self, feed):
    """Creates a mail filter that marks as read all messages not containing 
    Domain name as one of their words for each member of the group.
    
    Args:
      feed: PropertyFeed Member feed whose emailsettings need to be updated
    """
    for entry in feed.entry:
      memberType = None
      memberId = None
      domain = None
      for i, property in enumerate(entry.property):
        if property.name == 'memberType':
          memberType = property.value
        if property.name == 'memberId':
          user_name, domain = property.value.split('@', 1)
          memberId = property.value
      # Check that the member is a User belonging to the primary Domain.
      if memberType == 'User' and domain == self.domain:
        print 'creating filter for %s' % memberId
        self.email_client.CreateFilter(user_name,
                                       does_not_have_the_word=self.domain,
                                       mark_as_read=True)
      elif memberType == 'User':
        print 'User belongs to other Domain %s' %memberId
      else:
        print 'Member is a group %s' %memberId

  def run(self, group):
    feed = self.get_users(group)
    self.create_filter(feed)


def main():
  """Demos the Provisioning API and the Email Settings API with OAuth 2.0."""
  usage = 'usage: %prog [options]'
  parser = OptionParser(usage=usage)
  parser.add_option('--DOMAIN',
                    help='Google Apps Domain, e.g. "domain.com".')
  parser.add_option('--CLIENT_ID',
                    help='Registered CLIENT_ID of Domain.')
  parser.add_option('--CLIENT_SECRET',
                    help='Registered CLIENT_SECRET of Domain.')
  parser.add_option('--GROUP',
                    help='Group identifier')
  (options, args) = parser.parse_args()

  if None in (options.DOMAIN, options.CLIENT_ID, options.CLIENT_SECRET,
      options.GROUP):
    parser.print_help()
    return
  
  sample = OAuth2ClientSample(options.DOMAIN,
      options.CLIENT_ID, options.CLIENT_SECRET)
  sample.run(options.GROUP)
    

if __name__ == '__main__':
  main()
