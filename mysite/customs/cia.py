# This file is part of OpenHatch.
# Copyright (C) 2010 OpenHatch, Inc.
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

#from ircbot import SingleServerIRCBot
import re
import uuid
import mysite.customs.models

def ansi2tokens(line):
    is_metadata_line = ('\x03' in line)
    have_tokenized_one_star = False
    
    tokens = []
    current_token_chars = []

    def end_token():
        if tokens or current_token_chars:
            tokens.append(''.join(current_token_chars))
        current_token_chars[:] = []

    i = 0
    while i < len(line):
        byte = line[i]
        if byte == '\x02': # change color with no args
            end_token()
        elif byte == '\x03': # change color with 2 byte args
            i += 2 # skip those two bytes
        elif byte == '\x0f':
            end_token()
        elif byte == '*' and is_metadata_line and not have_tokenized_one_star:
            # The first star, on a metadata line, is tokenized.
            # This code is such trash.
            end_token()
            tokens.append('*')
            have_tokenized_one_star = True
            
        else:
            current_token_chars.append(line[i])
            
        i += 1
    end_token()
    
    return tokens

def parse_ansi_cia_message(line):
    tokens = ansi2tokens(line)
    return parse_cia_tokens(tokens)

def parse_cia_tokens(tokens):
    parsed = {}
    parsed['project_name'], rest = tokens[0], tokens[1:]

    # Remove final colon from project name
    assert parsed['project_name'].endswith(':')
    parsed['project_name'] = parsed['project_name'][:-1]

    message_lines = []
    message_lines.append(rest.pop().lstrip())

    # Now look for metadata
    if rest:
        # then verify that the second to last token is a colon
        # that's what always happens for first lines.
        assert rest[-1] == ':'

        # Pop off the colon
        colon = rest.pop()
        assert colon == ':'

        # then steal the path off the end
        parsed['path'] = rest.pop()
        assert parsed['path'].startswith('/')

        #parsed['path'] = parsed['path'][1:] # everything after that slash

        # The username is reliably at the start.
        parsed['committer_identifier'] = rest.pop(0).lstrip()

        # The module is reliably at the end.
        space_or_module = rest.pop()
        assert space_or_module.startswith(' ')
        module = space_or_module[1:]
        if module:
            parsed['module'] = module

        # The branch is reliably after the committer_identifier, if it's there
        if rest[0] != '*' and rest[0].strip():
            parsed['branch'] = rest.pop(0).strip()

        # If the last token has text and begins with ' ', then it's the module
        if rest[-1].startswith(' '):
            space_or_module = rest.pop()
            module = space_or_module[1:]
            if module:
                parsed['module'] = module

        # eat space tokens
        while rest[0] == ' ':
            rest = rest[1:]

        # if there is a star token, eat it
        if rest[0] == '*':
            rest.pop(0)

        if '*' in rest:
            import pdb
            pdb.set_trace()

        if rest: # Rest is version
            version = ''.join([tok for tok in rest if tok.strip()]).lstrip()
            if version:
                parsed['version'] = version
            
    parsed['message'] = '\n'.join(message_lines)
    return parsed

class LineAcceptingAgent(object):
    def __init__(self, callback):
        self.dict_so_far = {}
        self.unhandled_messages = []
        self.callback = callback

    def flush_object(self):
        if self.dict_so_far:
            self.dict_so_far['message'] = self.dict_so_far['message'].lstrip()
            self.callback(self.dict_so_far)
        
    def handle_message(self, message):
        #return
        # In the case the project_name changes, send the object to the callback
        parsed = parse_ansi_cia_message(message)
        if 'path' in parsed:
            self.flush_object()
            self.dict_so_far = parsed
        else:
            self.dict_so_far['message'] += '\n' + parsed['message']

class CiaIrcWatcher(): # SingleServerIRCBot):
    def __init__(self, callback):
        SingleServerIRCBot.__init__(self, [('chat.freenode.net', 6667)],
                                    'oh_listener', 'oh_listener')
        self.channel = '#commits'
        self.lia = LineAcceptingAgent(callback)
        
    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + '_')

    def on_welcome(self, c, e):
        c.join(self.channel)

    def on_pubmsg(self, c, e):
        text = e.arguments()[0]
        source_nick = e._source
        if source_nick.startswith('CIA-'):
            self.lia.handle_message(text)

def callback_that_adds_a_row(data_dict):
    # intentionally throw away data when it's too long
    data_dict['message'] = data_dict['message'][:256]
    obj = mysite.customs.models.RecentMessageFromCIA(**data_dict)
    obj.save()
    print obj.pk, data_dict

def main():
    import sys
    bot = CiaIrcWatcher(callback_that_adds_a_row)
    bot.start()
