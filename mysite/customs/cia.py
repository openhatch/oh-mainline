from ircbot import SingleServerIRCBot
import re

def ansi2tokens(line):
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
    parsed['project'], rest = tokens[0], tokens[1:]

    # Remove final colon from project name
    assert parsed['project'].endswith(':')
    parsed['project'] = parsed['project'][:-1]
    
    message_lines = []
    if len(rest) > 1:
        # then verify that the second to last token is a colon
        # that's what always happens for first lines.
        assert rest[-2] == ':'
        parsed['identifier'] = rest.pop(0).lstrip()
        revision_junk = rest.pop(0)
        parsed['revision'] = rest.pop(0)
        if revision_junk == ' * r':
            parsed['revision'] = 'r' + parsed['revision']
        space = rest.pop(0)
        assert space == ' '
        parsed['path'] = rest.pop(0)
        colon = rest.pop(0)
        assert colon == ':'
        message = rest.pop(0)
        message_lines.append(message.lstrip())

    parsed['message'] = '\n'.join(message_lines)
    return parsed

def parse_cia_message(msg):
    ret = {}

    message_lines = []

    
    for line in msg.split('\n'):
        tokens = re.split(r'[\x02](.*?)[\x0f]', line)
        project, rest = line.split(':', 1)
        
        # Initialize project in ret if it's not there
        if 'project' not in ret:
            ret['project'] = project
        # otherwise, verify it hasn't changed
        assert project == ret['project']

        # Initialize identifier in ret if it's not there
        if 'identifier' not in ret:
            ret['identifier'], rest = rest.split('*', 1)
            ret['identifier'] = ret['identifier'].strip()

        # Initialize revision in ret if it's not there
        if 'revision' not in ret:
            blank, ret['revision'], rest = rest.split(' ', 2)
            assert blank == ''
            ret['revision'] = ret['revision'].strip()

        # Initialize path if it's not there
        if 'path' not in ret:
            ret['path'], rest = rest.split(':', 1)
            ret['path'] = ret['path'].strip()

        # append the rest to message_lines
        if rest:
            blank, rest = rest.split(' ', 1)
            assert blank == ''
            message_lines.append(rest)

    ret['message'] = '\n'.join(message_lines)
    return ret

class LineAcceptingAgent(object):
    def __init__(self):
        self.unhandled_messages = []
    def handle_message(self, message):
        print repr(message)

class CiaIrcWatcher(SingleServerIRCBot):
    def __init__(self):
        SingleServerIRCBot.__init__(self, [('chat.freenode.net', 6667)],
                                    'oh_listener', 'oh_listener')
        self.channel = '#commits'
        self.lia = LineAcceptingAgent()
        
    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + '_')

    def on_welcome(self, c, e):
        c.join(self.channel)

    def on_pubmsg(self, c, e):
        text = e.arguments()[0]
        source_nick = e._source
        if source_nick.startswith('CIA-'):
            self.lia.handle_message(text)

def main():
    import sys
    bot = CiaIrcWatcher()
    bot.start()
