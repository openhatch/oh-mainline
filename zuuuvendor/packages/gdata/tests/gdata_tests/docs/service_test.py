#!/usr/bin/python
#
# Copyright 2009 Google Inc. All Rights Reserved.
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

__author__ = ('api.jfisher (Jeff Fisher), '
              'api.eric@google.com (Eric Bidelman)')

import getpass
import os
import re
import StringIO
import time
import unittest

import gdata.docs.service
import gdata.spreadsheet.service


username = ''
password = ''

client = gdata.docs.service.DocsService()
editClient = gdata.docs.service.DocsService()
spreadsheets = gdata.spreadsheet.service.SpreadsheetsService()


class DocumentsListServiceTest(unittest.TestCase):
  def setUp(self):
    self.client = client
    self.editClient = editClient
    self.editClient.SetClientLoginToken(client.GetClientLoginToken())
    self.editClient.additional_headers = {'If-Match': '*'}
    self.spreadsheets = spreadsheets
    self.DOCUMENT_CATEGORY = client._MakeKindCategory(gdata.docs.service.DOCUMENT_LABEL)
    self.SPREADSHEET_CATEGORY = client._MakeKindCategory(gdata.docs.service.SPREADSHEET_LABEL)
    self.PRESENTATION_CATEGORY = client._MakeKindCategory(gdata.docs.service.PRESENTATION_LABEL)


class DocumentListQueryTest(DocumentsListServiceTest):

  def setUp(self):
    DocumentsListServiceTest.setUp(self)
    self.feed = self.client.GetDocumentListFeed()

  def testGetDocumentsListFeed(self):
    self.assert_(isinstance(self.feed, gdata.docs.DocumentListFeed))
    uri = 'http://docs.google.com/feeds/documents/private/full/?max-results=1'

    # Query using GetDocumentListFeed()
    feed = self.client.GetDocumentListFeed(uri)
    self.assert_(isinstance(feed, gdata.docs.DocumentListFeed))
    self.assertEqual(len(feed.entry), 1)
    self.assertEqual(self.feed.entry[0].id.text, feed.entry[0].id.text)
    self.assertEqual(self.feed.entry[0].title.text, feed.entry[0].title.text)

    # Query using QueryDocumentListFeed()
    feed2 = self.client.QueryDocumentListFeed(uri)
    self.assertEqual(len(feed2.entry), 1)
    self.assertEqual(self.feed.entry[0].id.text, feed2.entry[0].id.text)
    self.assertEqual(self.feed.entry[0].title.text, feed2.entry[0].title.text)

  def testGetDocumentsListEntry(self):
    self_link = self.feed.entry[0].GetSelfLink().href
    entry = self.client.GetDocumentListEntry(self_link)
    self.assert_(isinstance(entry, gdata.docs.DocumentListEntry))
    self.assertEqual(self.feed.entry[0].id.text, entry.id.text)
    self.assertEqual(self.feed.entry[0].title.text, entry.title.text)

    self.assert_(self.feed.entry[0].resourceId.text is not None)
    self.assert_(self.feed.entry[0].lastModifiedBy is not None)
    self.assert_(self.feed.entry[0].lastViewed is not None)

  def testGetDocumentsListAclFeed(self):
    uri = ('http://docs.google.com/feeds/documents/private/full/'
           '-/mine?max-results=1')
    feed = self.client.GetDocumentListFeed(uri)
    feed_link = feed.entry[0].GetAclLink().href
    acl_feed = self.client.GetDocumentListAclFeed(feed_link)
    self.assert_(isinstance(acl_feed, gdata.docs.DocumentListAclFeed))
    self.assert_(isinstance(acl_feed.entry[0], gdata.docs.DocumentListAclEntry))
    self.assert_(acl_feed.entry[0].scope is not None)
    self.assert_(acl_feed.entry[0].role is not None)


class DocumentListAclTest(DocumentsListServiceTest):

  def setUp(self):
    DocumentsListServiceTest.setUp(self)
    uri = ('http://docs.google.com/feeds/documents/private/full'
           '/-/mine?max-results=1')
    self.feed = self.client.GetDocumentListFeed(uri)

    self.EMAIL = 'x@example.com'
    self.SCOPE_TYPE = 'user'
    self.ROLE_VALUE = 'reader'

  def testCreateAndUpdateAndDeleteAcl(self):
    # Add new ACL
    scope = gdata.docs.Scope(value=self.EMAIL, type=self.SCOPE_TYPE)
    role = gdata.docs.Role(value=self.ROLE_VALUE)

    acl_entry = self.client.Post(
        gdata.docs.DocumentListAclEntry(scope=scope, role=role),
        self.feed.entry[0].GetAclLink().href,
        converter=gdata.docs.DocumentListAclEntryFromString)
    self.assert_(isinstance(acl_entry, gdata.docs.DocumentListAclEntry))
    self.assertEqual(acl_entry.scope.value, self.EMAIL)
    self.assertEqual(acl_entry.scope.type, self.SCOPE_TYPE)
    self.assertEqual(acl_entry.role.value, self.ROLE_VALUE)

    # Update the user's role
    ROLE_VALUE = 'writer'
    acl_entry.role.value = ROLE_VALUE

    updated_acl_entry = self.editClient.Put(
        acl_entry, acl_entry.GetEditLink().href,
        converter=gdata.docs.DocumentListAclEntryFromString)

    self.assertEqual(updated_acl_entry.scope.value, self.EMAIL)
    self.assertEqual(updated_acl_entry.scope.type, self.SCOPE_TYPE)
    self.assertEqual(updated_acl_entry.role.value, ROLE_VALUE)

    # Delete the ACL
    self.editClient.Delete(updated_acl_entry.GetEditLink().href)

    # Make sure entry was actually deleted
    acl_feed = self.client.GetDocumentListAclFeed(
        self.feed.entry[0].GetAclLink().href)
    for acl_entry in acl_feed.entry:
      self.assert_(acl_entry.scope.value != self.EMAIL)


class DocumentListCreateAndDeleteTest(DocumentsListServiceTest):
  def setUp(self):
    DocumentsListServiceTest.setUp(self)
    self.BLANK_TITLE = "blank.txt"
    self.TITLE = 'Test title'
    self.new_entry = gdata.docs.DocumentListEntry()
    self.new_entry.category.append(self.DOCUMENT_CATEGORY)

  def testCreateAndDeleteEmptyDocumentSlugHeaderTitle(self):
    created_entry = self.client.Post(self.new_entry,
                                      '/feeds/documents/private/full',
                                      extra_headers={'Slug': self.BLANK_TITLE})
    self.editClient.Delete(created_entry.GetEditLink().href)
    self.assertEqual(created_entry.title.text, self.BLANK_TITLE)
    self.assertEqual(created_entry.category[0].label, 'document')

  def testCreateAndDeleteEmptyDocumentAtomTitle(self):
    self.new_entry.title = gdata.atom.Title(text=self.TITLE)
    created_entry = self.client.Post(self.new_entry,
                                      '/feeds/documents/private/full')
    self.editClient.Delete(created_entry.GetEditLink().href)
    self.assertEqual(created_entry.title.text, self.TITLE)
    self.assertEqual(created_entry.category[0].label, 'document')

  def testCreateAndDeleteEmptySpreadsheet(self):
    self.new_entry.title = gdata.atom.Title(text=self.TITLE)
    self.new_entry.category[0] = self.SPREADSHEET_CATEGORY
    created_entry = self.client.Post(self.new_entry,
                                      '/feeds/documents/private/full')
    self.editClient.Delete(created_entry.GetEditLink().href)
    self.assertEqual(created_entry.title.text, self.TITLE)
    self.assertEqual(created_entry.category[0].label, 'viewed')
    self.assertEqual(created_entry.category[1].label, 'spreadsheet')

  def testCreateAndDeleteEmptyPresentation(self):
    self.new_entry.title = gdata.atom.Title(text=self.TITLE)
    self.new_entry.category[0] = self.PRESENTATION_CATEGORY
    created_entry = self.client.Post(self.new_entry,
                                      '/feeds/documents/private/full')
    self.editClient.Delete(created_entry.GetEditLink().href)
    self.assertEqual(created_entry.title.text, self.TITLE)
    self.assertEqual(created_entry.category[0].label, 'viewed')
    self.assertEqual(created_entry.category[1].label, 'presentation')

  def testCreateAndDeleteFolder(self):
    folder_name = 'TestFolder'
    folder = self.client.CreateFolder(folder_name)
    self.assertEqual(folder.title.text, folder_name)
    self.editClient.Delete(folder.GetEditLink().href)

  def testCreateAndDeleteFolderInFolder(self):
    DEST_FOLDER_NAME = 'TestFolder'
    dest_folder = self.client.CreateFolder(DEST_FOLDER_NAME)

    CREATED_FOLDER_NAME = 'TestFolder2'
    new_folder = self.client.CreateFolder(CREATED_FOLDER_NAME, dest_folder)

    for category in new_folder.category:
      if category.scheme.startswith(gdata.docs.service.FOLDERS_SCHEME_PREFIX):
        self.assertEqual(new_folder.category[0].label, DEST_FOLDER_NAME)
        break

    # delete the folders we created, this will also delete the child folder
    dest_folder = self.client.Get(dest_folder.GetSelfLink().href)
    self.editClient.Delete(dest_folder.GetEditLink().href)


class DocumentListMoveInAndOutOfFolderTest(DocumentsListServiceTest):
  def setUp(self):
    DocumentsListServiceTest.setUp(self)
    self.folder_name = 'TestFolder'
    self.folder = self.client.CreateFolder(self.folder_name)

    self.doc_title = 'TestDoc'
    self.ms = gdata.MediaSource(file_path='test.doc',
                                content_type='application/msword')

  def tearDown(self):
    folder = self.client.Get(self.folder.GetSelfLink().href)
    self.editClient.Delete(folder.GetEditLink().href)

  def testUploadDocumentToFolder(self):
    created_entry = self.client.Upload(self.ms, self.doc_title,
                                        self.folder)
    for category in created_entry.category:
      if category.scheme.startswith(gdata.docs.service.FOLDERS_SCHEME_PREFIX):
        self.assertEqual(category.label, self.folder_name)
        break

    # delete the doc we created
    created_entry = self.client.Get(created_entry.GetSelfLink().href)
    match = re.search('\/(document%3A[^\/]*)\/?.*?\/(.*)$',
                      created_entry.GetEditLink().href)
    edit_uri = 'http://docs.google.com/feeds/documents/private/full/'
    edit_uri += '%s/%s' % (match.group(1), match.group(2))
    self.editClient.Delete(edit_uri)

  def testMoveDocumentInAndOutOfFolder(self):
    created_entry = self.client.Upload(self.ms, self.doc_title)
    moved_entry = self.client.MoveIntoFolder(created_entry,
                                             self.folder)
    for category in moved_entry.category:
      if category.scheme.startswith(gdata.docs.service.FOLDERS_SCHEME_PREFIX):
        self.assertEqual(category.label, self.folder_name)
        break

    self.editClient.MoveOutOfFolder(moved_entry)
    moved_entry = self.client.Get(moved_entry.GetSelfLink().href)
    for category in moved_entry.category:
      starts_with_folder__prefix = category.scheme.startswith(
          gdata.docs.service.FOLDERS_SCHEME_PREFIX)
      self.assert_(not starts_with_folder__prefix)

    created_entry = self.client.Get(created_entry.GetSelfLink().href)
    self.editClient.Delete(created_entry.GetEditLink().href)

  def testMoveFolderIntoFolder(self):
    dest_folder_name = 'DestFolderName'
    dest_folder = self.client.CreateFolder(dest_folder_name)
    self.client.MoveIntoFolder(self.folder, dest_folder)

    self.folder = self.client.Get(self.folder.GetSelfLink().href)
    folder_was_moved = False
    for category in self.folder.category:
      if category.term == dest_folder_name:
        folder_was_moved = True
        break
    self.assert_(folder_was_moved)

    #cleanup
    dest_folder = self.client.Get(dest_folder.GetSelfLink().href)
    self.editClient.Delete(dest_folder.GetEditLink().href)


class DocumentListUploadTest(DocumentsListServiceTest):

  def testUploadAndDeleteDocument(self):
    ms = gdata.MediaSource(file_path='test.doc',
                           content_type='application/msword')
    entry = self.client.Upload(ms, 'test doc')
    self.assertEqual(entry.title.text, 'test doc')
    self.assertEqual(entry.category[0].label, 'document')
    self.assert_(isinstance(entry, gdata.docs.DocumentListEntry))
    self.editClient.Delete(entry.GetEditLink().href)

  def testUploadAndDeletePresentation(self):
    ms = gdata.MediaSource(file_path='test.ppt',
                           content_type='application/vnd.ms-powerpoint')
    entry = self.client.Upload(ms, 'test preso')
    self.assertEqual(entry.title.text, 'test preso')
    self.assertEqual(entry.category[0].label, 'viewed')
    self.assertEqual(entry.category[1].label, 'presentation')
    self.assert_(isinstance(entry, gdata.docs.DocumentListEntry))
    self.editClient.Delete(entry.GetEditLink().href)

  def testUploadAndDeleteSpreadsheet(self):
    ms = gdata.MediaSource(file_path='test.csv',
                           content_type='text/csv')
    entry = self.client.Upload(ms, 'test spreadsheet')
    self.assert_(entry.title.text == 'test spreadsheet')
    self.assertEqual(entry.category[0].label, 'viewed')
    self.assertEqual(entry.category[1].label, 'spreadsheet')
    self.assert_(isinstance(entry, gdata.docs.DocumentListEntry))
    self.editClient.Delete(entry.GetEditLink().href)


class DocumentListUpdateTest(DocumentsListServiceTest):
  def setUp(self):
    DocumentsListServiceTest.setUp(self)
    self.TITLE = 'CreatedTestDoc'
    new_entry = gdata.docs.DocumentListEntry()
    new_entry.title = gdata.atom.Title(text=self.TITLE)
    new_entry.category.append(self.DOCUMENT_CATEGORY)
    self.created_entry = self.client.Post(new_entry,
                                          '/feeds/documents/private/full')

  def tearDown(self):
    # Delete the test doc we created
    self_link = self.created_entry.GetSelfLink().href
    entry = self.client.GetDocumentListEntry(self_link)
    self.editClient.Delete(entry.GetEditLink().href)

  def testUpdateDocumentMetadataAndContent(self):
    title = 'UpdatedTestDoc'
    # Update metadata
    self.created_entry.title.text = title
    updated_entry = self.editClient.Put(self.created_entry,
                                    self.created_entry.GetEditLink().href)
    self.assertEqual(updated_entry.title.text, title)

    # Update document's content
    ms = gdata.MediaSource(file_path='test.doc',
                           content_type='application/msword')
    uri = updated_entry.GetEditMediaLink().href
    updated_entry = self.editClient.Put(ms, uri)
    self.assertEqual(updated_entry.title.text, title)

    # Append content to document
    data = 'data to append'
    ms = gdata.MediaSource(file_handle=StringIO.StringIO(data),
                           content_type='text/plain',
                           content_length=len(data))
    uri = updated_entry.GetEditMediaLink().href + '?append=true'
    updated_entry = self.editClient.Put(ms, uri)


class DocumentListExportTest(DocumentsListServiceTest):

  def testExportDocument(self):
    query = ('https://docs.google.com/feeds/documents/private/full'
             '/-/document?max-results=1')
    feed = self.client.QueryDocumentListFeed(query)
    file_paths = ['./downloadedTest.doc', './downloadedTest.html',
                  './downloadedTest.odt', './downloadedTest.pdf',
                  './downloadedTest.png', './downloadedTest.rtf',
                  './downloadedTest.txt', './downloadedTest.zip']
    for path in file_paths:
      self.client.Export(feed.entry[0], path)
      self.assert_(os.path.exists(path))
      self.assert_(os.path.getsize(path))
      os.remove(path)

  def testExportPresentation(self):
    query = ('https://docs.google.com/feeds/documents/private/full'
             '/-/presentation?max-results=1')
    feed = self.client.QueryDocumentListFeed(query)
    file_paths = ['./downloadedTest.pdf', './downloadedTest.ppt',
                  './downloadedTest.swf', './downloadedTest.txt']
    for path in file_paths:
      self.client.Export(feed.entry[0].resourceId.text, path)
      self.assert_(os.path.exists(path))
      self.assert_(os.path.getsize(path))
      os.remove(path)

  def testExportSpreadsheet(self):
    query = ('https://docs.google.com/feeds/documents/private/full'
             '/-/spreadsheet?max-results=1')
    feed = self.client.QueryDocumentListFeed(query)
    file_paths = ['./downloadedTest.xls', './downloadedTest.csv',
                  './downloadedTest.pdf', './downloadedTest.ods',
                  './downloadedTest.tsv', './downloadedTest.html']
    docs_token = self.client.GetClientLoginToken()
    self.client.SetClientLoginToken(self.spreadsheets.GetClientLoginToken())
    for path in file_paths:
      self.client.Export(feed.entry[0], path)
      self.assert_(os.path.exists(path))
      self.assert_(os.path.getsize(path) > 0)
      os.remove(path)
    self.client.SetClientLoginToken(docs_token)

  def testExportNonExistentDocument(self):
    path = './ned.txt'
    exception_raised = False
    try:
      self.client.Export('non_existent_doc', path)
    except Exception, e:  # expected
      exception_raised = True
      self.assert_(exception_raised)
      self.assert_(not os.path.exists(path))

if __name__ == '__main__':
  print ('DocList API Tests\nNOTE: Please run these tests only with a test '
         'account. The tests may delete or update your data.')
  username = raw_input('Please enter your username: ')
  password = getpass.getpass()
  if client.GetClientLoginToken() is None:
    client.ClientLogin(username, password,
                       source='Document List Client Unit Tests')
  if spreadsheets.GetClientLoginToken() is None:
    spreadsheets.ClientLogin(username, password,
                             source='Document List Client Unit Tests')

  unittest.main()
