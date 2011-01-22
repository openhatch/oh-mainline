#!../../bin/python

# This file is part of OpenHatch.
# Copyright (C) 2010 OpenHatch
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import getopt

import sisynala.main

def parseApacheLine(s):
    '''Input is in Combined Log Format plus musec, vhost, responsebytes'''
    normal, musecs, vhost, responsebytes = s.rsplit(' ', 3)
    extracted = sisynala.main.logline(normal)
    extracted.update(dict(musecs=musecs, vhost=vhost, responsebytes=responsebytes))
    return extracted

def parsed2datadict(d):
    '''Input: raw data from parsing
    Output: A dict with keys (url, musecs, bytes)'''
    if d['uri'] is None:
        uri = '/'
    else:
        uri = d['uri']
    url = 'http://' + d['vhost'] + uri
    musecs = int(d['musecs'])
    if '+' in d['musecs']:
        url = url.replace('http', 'wrong')
    if d['responsebytes'].strip() == '-':
        responsebytes = 0
    else:
        responsebytes = int(d['responsebytes'].strip())
    return dict(url=url, musecs=musecs, responsebytes=responsebytes)

def gen_aggregate_stats_from_files(input_files):
    url2musecs = {}
    url2bytes = {}
    url2hitcount = {}

    for file in input_files:
        fd = open(file)
        for line in fd:
            data = parsed2datadict(parseApacheLine(line))
            for d in url2hitcount, url2musecs, url2bytes:
                if data['url'] not in d:
                    d[data['url']] = 0
            url2musecs[data['url']] += data['musecs']
            url2bytes[data['url']] += data['responsebytes']
            url2hitcount[data['url']] += 1

    return url2musecs, url2bytes, url2hitcount

def aggregate_stats_to_fake_du_in_cwd(**kwargs):
    for stat_name in kwargs:
        fd = open(stat_name, 'w')
        stat_dict = kwargs[stat_name]
        urls = stat_dict.keys()
        urls.sort() # du output is sorted
        ## du output comes summed into directories
        ## this is dumb and slow
        ends_with_slash = []
        for url in urls:
            if url[-1] == '/':
                ends_with_slash.append(url)
        # These are the "directories"
        # they must be summed up
        ends_with_slash.sort()
        ends_with_slash.reverse()
        ## O(n^2); there is a constant-time speedup which is to associate
        ## the urls that end in the thing with the thing earlier
        for directory in ends_with_slash:
            for url in urls:
                if url.startswith(directory):
                    stat_dict[directory] += stat_dict[url]
        ## NOW the directories have been bloated correctly
        for url in urls:
            print >> fd, stat_dict[url], url
        fd.close()

def main():
    import glob
    musecs, bytes, hitcount = gen_aggregate_stats_from_files(sys.argv[1:])
    aggregate_stats_to_fake_du_in_cwd(musecs=musecs, bytes=bytes, hitcount=hitcount)

if __name__ == '__main__':
    main()
