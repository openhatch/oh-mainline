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
    print tokens
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

        # revision_junk always has a '*" in it.
        # if that's not next, accept this as "branchname"
        # if not, eat the next token as the

        if '*' not in rest[0]:
            parsed['branchname'] = rest.pop(0)
            
        revision_junk = rest.pop(0)
        assert '*' in revision_junk
        
        parsed['revision'] = rest.pop(0)
        if revision_junk == ' * r':
            parsed['revision'] = 'r' + parsed['revision']
        space_or_subproject = rest.pop(0)
        if space_or_subproject != ' ':
            parsed['subproject'] = space_or_subproject.lstrip()
            
        parsed['path'] = rest.pop(0)
        colon = rest.pop(0)
        assert colon == ':'
        message = rest.pop(0)
        message_lines.append(message.lstrip())
    else:
        message_lines.append(rest[0].lstrip())
        
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
        # In the case the project changes, send the object to the callback
        parsed = parse_ansi_cia_message(message)
        if parsed['project'] == self.dict_so_far.get('project', None):
            self.dict_so_far['message'] += '\n' + parsed['message']
        else:
            self.flush_object()
            self.dict_so_far = parsed

class CiaIrcWatcher(SingleServerIRCBot):
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

def main():
    import sys
    def callback(s):
        pass
    bot = CiaIrcWatcher(callback)
    bot.start()
