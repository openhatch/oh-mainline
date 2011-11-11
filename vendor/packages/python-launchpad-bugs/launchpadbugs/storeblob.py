'''Temporarily store a blob in Launchpad and get a ticket for it.

Copyright (C) 2007 Canonical Ltd.
Author: Martin Pitt <martin.pitt@ubuntu.com>

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation; either version 2 of the License, or (at your
option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
the full text of the license.
'''

import multipartpost_handler, urllib2, time, httplib
import socket

_https_upload_callback = None

#
# This progress code is based on KodakLoader by Jason Hildebrand
# <jason@opensky.ca>. See http://www.opensky.ca/~jdhildeb/software/kodakloader/
# for details.
class HTTPSProgressConnection(httplib.HTTPSConnection):
    '''Implement a HTTPSConnection with an optional callback function for
    upload progress.'''

    def send(self, data):
        global _https_upload_callback

        # if callback has not been set, call the old method
        if not _https_upload_callback:
            httplib.HTTPSConnection.send(self, data)
            return

        sent = 0
        total = len(data)
        chunksize = 1024
        while sent < total:
            _https_upload_callback(sent, total)
            t1 = time.time()
            httplib.HTTPSConnection.send(self, data[sent:sent+chunksize])
            sent += chunksize
            t2 = time.time()

            # adjust chunksize so that it takes between .5 and 2 
            # seconds to send a chunk
            if t2 - t1 < .5:
                chunksize *= 2
            elif t2 - t1 > 2:
                chunksize /= 2

class HTTPSProgressHandler(urllib2.HTTPSHandler):

    def https_open(self, req):
        return self.do_open(HTTPSProgressConnection, req)


def upload(blob, progress_callback = None, staging=False):
    '''Upload given blob (file-like object) to Malone and return the ticket for
    it.

    progress_callback can be set to a function(sent, total) which is regularly
    called with the number of bytes already sent and total number of bytes to
    send. It is called every 0.5 to 2 seconds (dynamically adapted to upload
    bandwidth).

    Return None on error.

    By default this uses the production Launchpad instance. Set staging=True to
    use staging.launchpad.net (for testing).
    '''
    
    # working around LP: #314212
    # python-apt sets a 2 seconds timeout in jaunty which results in
    # failing uploads. To workaround this temporary set timeout to None
    # (no timeout)
    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(30)
    ticket = None

    global _https_upload_callback
    _https_upload_callback = progress_callback

    opener = urllib2.build_opener(HTTPSProgressHandler, multipartpost_handler.MultipartPostHandler)
    if staging:
        url = 'https://staging.launchpad.net/+storeblob'
    else:
        url = 'https://launchpad.net/+storeblob'
    result = opener.open(url,
        { 'FORM_SUBMIT': '1', 'field.blob': blob })
    ticket = result.info().get('X-Launchpad-Blob-Token')
    socket.setdefaulttimeout(old_timeout)

    return ticket
