#!/usr/bin/env python
#
# Copyright (C) 2009 Google Inc.
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


# This module is used for version 2 of the Google Data APIs.
# These tests attempt to connect to Google servers.


__author__ = 'j.s@google.com (Jeff Scudder)'


import os
import unittest
import gdata.client
import atom.http_core
import atom.mock_http_core
import atom.core
import gdata.data
import gdata.core
# TODO: switch to using v2 atom data once it is available.
import atom
import gdata.test_config as conf


conf.options.register_option(conf.BLOG_ID_OPTION)


class BloggerTest(unittest.TestCase):

  def setUp(self):
    self.client = None
    if conf.options.get_value('runlive') == 'true':
      self.client = gdata.client.GDClient()
      conf.configure_client(self.client, 'BloggerTest', 'blogger')

  def tearDown(self):
    conf.close_client(self.client)

  def test_create_update_delete(self):
    if not conf.options.get_value('runlive') == 'true':
      return
    # Either load the recording or prepare to make a live request.
    conf.configure_cache(self.client, 'test_create_update_delete')

    blog_post = atom.Entry(
        title=atom.Title(text='test from python BloggerTest'),
        content=atom.Content(text='This is only a test.'))
    http_request = atom.http_core.HttpRequest()
    http_request.add_body_part(str(blog_post), 'application/atom+xml')

    def entry_from_string_wrapper(response):
      self.assert_(response.getheader('content-type') is not None)
      self.assert_(response.getheader('gdata-version') is not None)
      return atom.EntryFromString(response.read())

    entry = self.client.request('POST', 
        'http://www.blogger.com/feeds/%s/posts/default' % (
            conf.options.get_value('blogid')),
         converter=entry_from_string_wrapper, http_request=http_request)
    self.assertEqual(entry.title.text, 'test from python BloggerTest')
    self.assertEqual(entry.content.text, 'This is only a test.')

    # Edit the test entry.
    edit_link = None
    for link in entry.link:
      # Find the edit link for this entry. 
      if link.rel == 'edit':
        edit_link = link.href
    entry.title.text = 'Edited'
    http_request = atom.http_core.HttpRequest()
    http_request.add_body_part(str(entry), 'application/atom+xml')
    edited_entry = self.client.request('PUT', edit_link,
         converter=entry_from_string_wrapper, http_request=http_request)
    self.assertEqual(edited_entry.title.text, 'Edited')
    self.assertEqual(edited_entry.content.text, entry.content.text)

    # Delete the test entry from the blog.
    edit_link = None
    for link in edited_entry.link:
      if link.rel == 'edit':
        edit_link = link.href
    response = self.client.request('DELETE', edit_link)
    self.assertEqual(response.status, 200)

  def test_use_version_two(self):
    if not conf.options.get_value('runlive') == 'true':
      return
    conf.configure_cache(self.client, 'test_use_version_two')

    # Use version 2 of the Blogger API. 
    self.client.api_version = '2'

    # Create a v2 blog post entry to post on the blog.
    entry = create_element('entry')
    entry._other_elements.append(
        create_element('title', text='Marriage!', 
            attributes={'type': 'text'}))
    entry._other_elements.append(
        create_element('content', attributes={'type': 'text'},
            text='Mr. Darcy has proposed marriage to me!'))
    entry._other_elements.append(
        create_element('category', 
            attributes={'scheme': TAG, 'term': 'marriage'})) 
    entry._other_elements.append(
        create_element('category', 
            attributes={'scheme': TAG, 'term': 'Mr. Darcy'}))

    http_request = atom.http_core.HttpRequest()
    http_request.add_body_part(entry.to_string(), 'application/atom+xml')
    posted = self.client.request('POST', 
        'http://www.blogger.com/feeds/%s/posts/default' % (
            conf.options.get_value('blogid')),
         converter=element_from_string, http_request=http_request)
    # Verify that the blog post content is correct.
    self.assertEqual(posted.get_elements('title', ATOM)[0].text, 'Marriage!')
    # TODO: uncomment once server bug is fixed.
    #self.assertEqual(posted.get_elements('content', ATOM)[0].text,
    #    'Mr. Darcy has proposed marriage to me!')
    found_tags = [False, False]
    categories = posted.get_elements('category', ATOM)
    self.assertEqual(len(categories), 2)
    for category in categories:
      if category.get_attributes('term')[0].value == 'marriage':
        found_tags[0] = True
      elif category.get_attributes('term')[0].value == 'Mr. Darcy':
        found_tags[1] = True
    self.assert_(found_tags[0])
    self.assert_(found_tags[1])

    # Find the blog post on the blog.
    self_link = None
    edit_link = None
    for link in posted.get_elements('link', ATOM):
      if link.get_attributes('rel')[0].value == 'self':
        self_link = link.get_attributes('href')[0].value
      elif link.get_attributes('rel')[0].value == 'edit':
        edit_link = link.get_attributes('href')[0].value
    self.assert_(self_link is not None)
    self.assert_(edit_link is not None)

    queried = self.client.request('GET', self_link, 
        converter=element_from_string)
    # TODO: add additional asserts to check content and etags.

    # Test queries using ETags.
    entry = self.client.get_entry(self_link)
    self.assert_(entry.etag is not None)
    self.assertRaises(gdata.client.NotModified, self.client.get_entry,
                      self_link, etag=entry.etag)

    # Delete the test blog post.
    self.client.request('DELETE', edit_link)


class ContactsTest(unittest.TestCase):

  def setUp(self):
    self.client = None
    if conf.options.get_value('runlive') == 'true':
      self.client = gdata.client.GDClient()
      conf.configure_client(self.client, 'ContactsTest', 'cp')

  def tearDown(self):
    conf.close_client(self.client)
  
  # Run this test and profiles fails
  def test_crud_version_two(self):
    if not conf.options.get_value('runlive') == 'true':
      return

    conf.configure_cache(self.client, 'test_crud_version_two')

    self.client.api_version = '2'

    entry = create_element('entry')
    entry._other_elements.append(
        create_element('title', ATOM, 'Jeff', {'type': 'text'}))
    entry._other_elements.append(
        create_element('email', GD, 
            attributes={'address': 'j.s@google.com', 'rel': WORK_REL}))

    http_request = atom.http_core.HttpRequest()
    http_request.add_body_part(entry.to_string(), 'application/atom+xml')
    posted = self.client.request('POST', 
        'http://www.google.com/m8/feeds/contacts/default/full',
        converter=element_from_string, http_request=http_request)

    self_link = None
    edit_link = None
    for link in posted.get_elements('link', ATOM):
      if link.get_attributes('rel')[0].value == 'self':
        self_link = link.get_attributes('href')[0].value
      elif link.get_attributes('rel')[0].value == 'edit':
        edit_link = link.get_attributes('href')[0].value
    self.assert_(self_link is not None)
    self.assert_(edit_link is not None)

    etag = posted.get_attributes('etag')[0].value
    self.assert_(etag is not None)
    self.assert_(len(etag) > 0)

    # Delete the test contact.
    http_request = atom.http_core.HttpRequest()
    http_request.headers['If-Match'] = etag
    self.client.request('DELETE', edit_link, http_request=http_request)


class VersionTwoClientContactsTest(unittest.TestCase):

  def setUp(self):
    self.client = None
    if conf.options.get_value('runlive') == 'true':
      self.client = gdata.client.GDClient()
      self.client.api_version = '2'
      conf.configure_client(self.client, 'VersionTwoClientContactsTest', 'cp')
    self.old_proxy = os.environ.get('https_proxy')

  def tearDown(self):
    if self.old_proxy:
      os.environ['https_proxy'] = self.old_proxy
    elif 'https_proxy' in os.environ:
      del os.environ['https_proxy']
    conf.close_client(self.client)

  def test_version_two_client(self):
    if not conf.options.get_value('runlive') == 'true':
      return
    conf.configure_cache(self.client, 'test_version_two_client')

    entry = gdata.data.GDEntry()
    entry._other_elements.append(
        create_element('title', ATOM, 'Test', {'type': 'text'}))
    entry._other_elements.append(
        create_element('email', GD, 
            attributes={'address': 'test@example.com', 'rel': WORK_REL}))

    # Create the test contact.
    posted = self.client.post(entry,
        'https://www.google.com/m8/feeds/contacts/default/full')
    self.assert_(isinstance(posted, gdata.data.GDEntry))
    self.assertEqual(posted.get_elements('title')[0].text, 'Test')
    self.assertEqual(posted.get_elements('email')[0].get_attributes(
        'address')[0].value, 'test@example.com')

    posted.get_elements('title')[0].text = 'Doug'
    edited = self.client.update(posted)
    self.assert_(isinstance(edited, gdata.data.GDEntry))
    self.assertEqual(edited.get_elements('title')[0].text, 'Doug')
    self.assertEqual(edited.get_elements('email')[0].get_attributes(
        'address')[0].value, 'test@example.com')

    # Delete the test contact.
    self.client.delete(edited)

  def notest_crud_over_https_proxy(self):
    import urllib
    PROXY_ADDR = '98.192.125.23'
    try:
      response = urllib.urlopen('http://' + PROXY_ADDR)
    except IOError:
      return
    # Only bother running the test if the proxy is up
    if response.getcode() == 200:
      os.environ['https_proxy'] = PROXY_ADDR
      # Perform the CRUD test above, this time over a proxy.
      self.test_version_two_client()

class JsoncRequestTest(unittest.TestCase):

  def setUp(self):
    self.client = gdata.client.GDClient()

  def test_get_jsonc(self):
    jsonc = self.client.get_feed(
        'http://gdata.youtube.com/feeds/api/videos?q=surfing&v=2&alt=jsonc',
        converter=gdata.core.parse_json_file)
    self.assertTrue(len(jsonc.data.items) > 0)


# Utility methods.
# The Atom XML namespace.
ATOM = 'http://www.w3.org/2005/Atom'
# URL used as the scheme for a blog post tag.
TAG = 'http://www.blogger.com/atom/ns#'
# Namespace for Google Data API elements.
GD = 'http://schemas.google.com/g/2005'
WORK_REL = 'http://schemas.google.com/g/2005#work'


def create_element(tag, namespace=ATOM, text=None, attributes=None):
  element = atom.core.XmlElement()
  element._qname = '{%s}%s' % (namespace, tag)
  if text is not None:
    element.text = text
  if attributes is not None:
    element._other_attributes = attributes.copy()
  return element


def element_from_string(response):
  return atom.core.xml_element_from_string(response.read(),
                                           atom.core.XmlElement)


def suite():
  return conf.build_suite([BloggerTest, ContactsTest, 
                           VersionTwoClientContactsTest,
                           JsoncRequestTest])


if __name__ == '__main__':
  unittest.TextTestRunner().run(suite())
