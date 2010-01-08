from ircbot import SingleServerIRCBot

def parse_cia_message(msg):
    ret = {}

    message_lines = []
    
    for line in msg.split('\n'):
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
        print message

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
            lia.handle_message(text)

def main():
    import sys
    bot = CiaIrcWatcher()
    bot.start()
