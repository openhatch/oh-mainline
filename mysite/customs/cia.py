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
