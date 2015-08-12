# -*- coding: utf-8 -*-
"""
    sphinx.domains.std
    ~~~~~~~~~~~~~~~~~~

    The standard domain.

    :copyright: Copyright 2007-2013 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
import unicodedata

from docutils import nodes
from docutils.parsers.rst import directives
from docutils.statemachine import ViewList

from sphinx import addnodes
from sphinx.roles import XRefRole
from sphinx.locale import l_, _
from sphinx.domains import Domain, ObjType
from sphinx.directives import ObjectDescription
from sphinx.util import ws_re
from sphinx.util.nodes import clean_astext, make_refnode
from sphinx.util.compat import Directive


# RE for option descriptions
option_desc_re = re.compile(
    r'((?:/|-|--)[-_a-zA-Z0-9]+)(\s*.*?)(?=,\s+(?:/|-|--)|$)')


class GenericObject(ObjectDescription):
    """
    A generic x-ref directive registered with Sphinx.add_object_type().
    """
    indextemplate = ''
    parse_node = None

    def handle_signature(self, sig, signode):
        if self.parse_node:
            name = self.parse_node(self.env, sig, signode)
        else:
            signode.clear()
            signode += addnodes.desc_name(sig, sig)
            # normalize whitespace like XRefRole does
            name = ws_re.sub('', sig)
        return name

    def add_target_and_index(self, name, sig, signode):
        targetname = '%s-%s' % (self.objtype, name)
        signode['ids'].append(targetname)
        self.state.document.note_explicit_target(signode)
        if self.indextemplate:
            colon = self.indextemplate.find(':')
            if colon != -1:
                indextype = self.indextemplate[:colon].strip()
                indexentry = self.indextemplate[colon+1:].strip() % (name,)
            else:
                indextype = 'single'
                indexentry = self.indextemplate % (name,)
            self.indexnode['entries'].append((indextype, indexentry,
                                              targetname, ''))
        self.env.domaindata['std']['objects'][self.objtype, name] = \
            self.env.docname, targetname


class EnvVar(GenericObject):
    indextemplate = l_('environment variable; %s')


class EnvVarXRefRole(XRefRole):
    """
    Cross-referencing role for environment variables (adds an index entry).
    """

    def result_nodes(self, document, env, node, is_ref):
        if not is_ref:
            return [node], []
        varname = node['reftarget']
        tgtid = 'index-%s' % env.new_serialno('index')
        indexnode = addnodes.index()
        indexnode['entries'] = [
            ('single', varname, tgtid, ''),
            ('single', _('environment variable; %s') % varname, tgtid, '')
        ]
        targetnode = nodes.target('', '', ids=[tgtid])
        document.note_explicit_target(targetnode)
        return [indexnode, targetnode, node], []


class Target(Directive):
    """
    Generic target for user-defined cross-reference types.
    """
    indextemplate = ''

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}

    def run(self):
        env = self.state.document.settings.env
        # normalize whitespace in fullname like XRefRole does
        fullname = ws_re.sub(' ', self.arguments[0].strip())
        targetname = '%s-%s' % (self.name, fullname)
        node = nodes.target('', '', ids=[targetname])
        self.state.document.note_explicit_target(node)
        ret = [node]
        if self.indextemplate:
            indexentry = self.indextemplate % (fullname,)
            indextype = 'single'
            colon = indexentry.find(':')
            if colon != -1:
                indextype = indexentry[:colon].strip()
                indexentry = indexentry[colon+1:].strip()
            inode = addnodes.index(entries=[(indextype, indexentry,
                                             targetname, '')])
            ret.insert(0, inode)
        name = self.name
        if ':' in self.name:
            _, name = self.name.split(':', 1)
        env.domaindata['std']['objects'][name, fullname] = \
            env.docname, targetname
        return ret


class Cmdoption(ObjectDescription):
    """
    Description of a command-line option (.. cmdoption).
    """

    def handle_signature(self, sig, signode):
        """Transform an option description into RST nodes."""
        count = 0
        firstname = ''
        for m in option_desc_re.finditer(sig):
            optname, args = m.groups()
            if count:
                signode += addnodes.desc_addname(', ', ', ')
            signode += addnodes.desc_name(optname, optname)
            signode += addnodes.desc_addname(args, args)
            if not count:
                firstname = optname
            count += 1
        if not firstname:
            raise ValueError
        return firstname

    def add_target_and_index(self, name, sig, signode):
        targetname = name.replace('/', '-')
        currprogram = self.env.temp_data.get('std:program')
        if currprogram:
            targetname = '-' + currprogram + targetname
        targetname = 'cmdoption' + targetname
        signode['ids'].append(targetname)
        self.state.document.note_explicit_target(signode)
        self.indexnode['entries'].append(
            ('pair', _('%scommand line option; %s') %
             ((currprogram and currprogram + ' ' or ''), sig),
             targetname, ''))
        self.env.domaindata['std']['progoptions'][currprogram, name] = \
            self.env.docname, targetname


class Program(Directive):
    """
    Directive to name the program for which options are documented.
    """

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}

    def run(self):
        env = self.state.document.settings.env
        program = ws_re.sub('-', self.arguments[0].strip())
        if program == 'None':
            env.temp_data['std:program'] = None
        else:
            env.temp_data['std:program'] = program
        return []


class OptionXRefRole(XRefRole):
    innernodeclass = addnodes.literal_emphasis

    def process_link(self, env, refnode, has_explicit_title, title, target):
        program = env.temp_data.get('std:program')
        if not has_explicit_title:
            if ' ' in title and not (title.startswith('/') or
                                     title.startswith('-')):
                program, target = re.split(' (?=-|--|/)', title, 1)
                program = ws_re.sub('-', program)
                target = target.strip()
        elif ' ' in target:
            program, target = re.split(' (?=-|--|/)', target, 1)
            program = ws_re.sub('-', program)
        refnode['refprogram'] = program
        return title, target


def make_termnodes_from_paragraph_node(env, node, new_id=None):
    gloss_entries = env.temp_data.setdefault('gloss_entries', set())
    objects = env.domaindata['std']['objects']

    termtext = node.astext()
    if new_id is None:
        new_id = 'term-' + nodes.make_id(termtext)
    if new_id in gloss_entries:
        new_id = 'term-' + str(len(gloss_entries))
    gloss_entries.add(new_id)
    objects['term', termtext.lower()] = env.docname, new_id

    # add an index entry too
    indexnode = addnodes.index()
    indexnode['entries'] = [('single', termtext, new_id, 'main')]
    new_termnodes = []
    new_termnodes.append(indexnode)
    new_termnodes.extend(node.children)
    new_termnodes.append(addnodes.termsep())
    for termnode in new_termnodes:
        termnode.source, termnode.line = node.source, node.line

    return new_id, termtext, new_termnodes


def make_term_from_paragraph_node(termnodes, ids):
    # make a single "term" node with all the terms, separated by termsep
    # nodes (remove the dangling trailing separator)
    term = nodes.term('', '', *termnodes[:-1])
    term.source, term.line = termnodes[0].source, termnodes[0].line
    term.rawsource = term.astext()
    term['ids'].extend(ids)
    term['names'].extend(ids)
    return term


class Glossary(Directive):
    """
    Directive to create a glossary with cross-reference targets for :term:
    roles.
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {
        'sorted': directives.flag,
    }

    def run(self):
        env = self.state.document.settings.env
        node = addnodes.glossary()
        node.document = self.state.document

        # This directive implements a custom format of the reST definition list
        # that allows multiple lines of terms before the definition.  This is
        # easy to parse since we know that the contents of the glossary *must
        # be* a definition list.

        # first, collect single entries
        entries = []
        in_definition = True
        was_empty = True
        messages = []
        for line, (source, lineno) in zip(self.content, self.content.items):
            # empty line -> add to last definition
            if not line:
                if in_definition and entries:
                    entries[-1][1].append('', source, lineno)
                was_empty = True
                continue
            # unindented line -> a term
            if line and not line[0].isspace():
                # enable comments
                if line.startswith('.. '):
                    continue
                # first term of definition
                if in_definition:
                    if not was_empty:
                        messages.append(self.state.reporter.system_message(
                            2, 'glossary term must be preceded by empty line',
                            source=source, line=lineno))
                    entries.append(([(line, source, lineno)], ViewList()))
                    in_definition = False
                # second term and following
                else:
                    if was_empty:
                        messages.append(self.state.reporter.system_message(
                            2, 'glossary terms must not be separated by empty '
                            'lines', source=source, line=lineno))
                    if entries:
                        entries[-1][0].append((line, source, lineno))
                    else:
                        messages.append(self.state.reporter.system_message(
                            2, 'glossary seems to be misformatted, check '
                        'indentation', source=source, line=lineno))
            else:
                if not in_definition:
                    # first line of definition, determines indentation
                    in_definition = True
                    indent_len = len(line) - len(line.lstrip())
                if entries:
                    entries[-1][1].append(line[indent_len:], source, lineno)
                else:
                    messages.append(self.state.reporter.system_message(
                        2, 'glossary seems to be misformatted, check '
                    'indentation', source=source, line=lineno))
            was_empty = False

        # now, parse all the entries into a big definition list
        items = []
        for terms, definition in entries:
            termtexts = []
            termnodes = []
            system_messages = []
            ids = []
            for line, source, lineno in terms:
                # parse the term with inline markup
                res = self.state.inline_text(line, lineno)
                system_messages.extend(res[1])

                # get a text-only representation of the term and register it
                # as a cross-reference target
                tmp = nodes.paragraph('', '', *res[0])
                tmp.source = source
                tmp.line = lineno
                new_id, termtext, new_termnodes = \
                        make_termnodes_from_paragraph_node(env, tmp)
                ids.append(new_id)
                termtexts.append(termtext)
                termnodes.extend(new_termnodes)

            term = make_term_from_paragraph_node(termnodes, ids)
            term += system_messages

            defnode = nodes.definition()
            if definition:
                self.state.nested_parse(definition, definition.items[0][1],
                                        defnode)

            items.append((termtexts,
                          nodes.definition_list_item('', term, defnode)))

        if 'sorted' in self.options:
            items.sort(key=lambda x:
                       unicodedata.normalize('NFD', x[0][0].lower()))

        dlist = nodes.definition_list()
        dlist['classes'].append('glossary')
        dlist.extend(item[1] for item in items)
        node += dlist
        return messages + [node]


token_re = re.compile('`(\w+)`', re.U)

def token_xrefs(text):
    retnodes = []
    pos = 0
    for m in token_re.finditer(text):
        if m.start() > pos:
            txt = text[pos:m.start()]
            retnodes.append(nodes.Text(txt, txt))
        refnode = addnodes.pending_xref(
            m.group(1), reftype='token', refdomain='std', reftarget=m.group(1))
        refnode += nodes.literal(m.group(1), m.group(1), classes=['xref'])
        retnodes.append(refnode)
        pos = m.end()
    if pos < len(text):
        retnodes.append(nodes.Text(text[pos:], text[pos:]))
    return retnodes


class ProductionList(Directive):
    """
    Directive to list grammar productions.
    """

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}

    def run(self):
        env = self.state.document.settings.env
        objects = env.domaindata['std']['objects']
        node = addnodes.productionlist()
        messages = []
        i = 0

        for rule in self.arguments[0].split('\n'):
            if i == 0 and ':' not in rule:
                # production group
                continue
            i += 1
            try:
                name, tokens = rule.split(':', 1)
            except ValueError:
                break
            subnode = addnodes.production()
            subnode['tokenname'] = name.strip()
            if subnode['tokenname']:
                idname = 'grammar-token-%s' % subnode['tokenname']
                if idname not in self.state.document.ids:
                    subnode['ids'].append(idname)
                self.state.document.note_implicit_target(subnode, subnode)
                objects['token', subnode['tokenname']] = env.docname, idname
            subnode.extend(token_xrefs(tokens))
            node.append(subnode)
        return [node] + messages


class StandardDomain(Domain):
    """
    Domain for all objects that don't fit into another domain or are added
    via the application interface.
    """

    name = 'std'
    label = 'Default'

    object_types = {
        'term': ObjType(l_('glossary term'), 'term', searchprio=-1),
        'token': ObjType(l_('grammar token'), 'token', searchprio=-1),
        'label': ObjType(l_('reference label'), 'ref', 'keyword',
                         searchprio=-1),
        'envvar': ObjType(l_('environment variable'), 'envvar'),
        'cmdoption': ObjType(l_('program option'), 'option'),
    }

    directives = {
        'program': Program,
        'cmdoption': Cmdoption,  # old name for backwards compatibility
        'option': Cmdoption,
        'envvar': EnvVar,
        'glossary': Glossary,
        'productionlist': ProductionList,
    }
    roles = {
        'option':  OptionXRefRole(innernodeclass=addnodes.literal_emphasis),
        'envvar':  EnvVarXRefRole(),
        # links to tokens in grammar productions
        'token':   XRefRole(),
        # links to terms in glossary
        'term':    XRefRole(lowercase=True, innernodeclass=nodes.emphasis,
                            warn_dangling=True),
        # links to headings or arbitrary labels
        'ref':     XRefRole(lowercase=True, innernodeclass=nodes.emphasis,
                            warn_dangling=True),
        # links to labels, without a different title
        'keyword': XRefRole(warn_dangling=True),
    }

    initial_data = {
        'progoptions': {},  # (program, name) -> docname, labelid
        'objects': {},      # (type, name) -> docname, labelid
        'labels': {         # labelname -> docname, labelid, sectionname
            'genindex': ('genindex', '', l_('Index')),
            'modindex': ('py-modindex', '', l_('Module Index')),
            'search':   ('search', '', l_('Search Page')),
        },
        'anonlabels': {     # labelname -> docname, labelid
            'genindex': ('genindex', ''),
            'modindex': ('py-modindex', ''),
            'search':   ('search', ''),
        },
    }

    dangling_warnings = {
        'term': 'term not in glossary: %(target)s',
        'ref':  'undefined label: %(target)s (if the link has no caption '
                'the label must precede a section header)',
        'keyword': 'unknown keyword: %(target)s',
    }

    def clear_doc(self, docname):
        for key, (fn, _) in self.data['progoptions'].items():
            if fn == docname:
                del self.data['progoptions'][key]
        for key, (fn, _) in self.data['objects'].items():
            if fn == docname:
                del self.data['objects'][key]
        for key, (fn, _, _) in self.data['labels'].items():
            if fn == docname:
                del self.data['labels'][key]
        for key, (fn, _) in self.data['anonlabels'].items():
            if fn == docname:
                del self.data['anonlabels'][key]

    def process_doc(self, env, docname, document):
        labels, anonlabels = self.data['labels'], self.data['anonlabels']
        for name, explicit in document.nametypes.iteritems():
            if not explicit:
                continue
            labelid = document.nameids[name]
            if labelid is None:
                continue
            node = document.ids[labelid]
            if name.isdigit() or node.has_key('refuri') or \
                   node.tagname.startswith('desc_'):
                # ignore footnote labels, labels automatically generated from a
                # link and object descriptions
                continue
            if name in labels:
                env.warn_node('duplicate label %s, ' % name + 'other instance '
                              'in ' + env.doc2path(labels[name][0]), node)
            anonlabels[name] = docname, labelid
            if node.tagname == 'section':
                sectname = clean_astext(node[0]) # node[0] == title node
            elif node.tagname == 'figure':
                for n in node:
                    if n.tagname == 'caption':
                        sectname = clean_astext(n)
                        break
                else:
                    continue
            elif node.tagname == 'table':
                for n in node:
                    if n.tagname == 'title':
                        sectname = clean_astext(n)
                        break
                else:
                    continue
            else:
                # anonymous-only labels
                continue
            labels[name] = docname, labelid, sectname

    def resolve_xref(self, env, fromdocname, builder,
                     typ, target, node, contnode):
        if typ == 'ref':
            if node['refexplicit']:
                # reference to anonymous label; the reference uses
                # the supplied link caption
                docname, labelid = self.data['anonlabels'].get(target, ('',''))
                sectname = node.astext()
            else:
                # reference to named label; the final node will
                # contain the section name after the label
                docname, labelid, sectname = self.data['labels'].get(target,
                                                                     ('','',''))
            if not docname:
                return None
            newnode = nodes.reference('', '', internal=True)
            innernode = nodes.emphasis(sectname, sectname)
            if docname == fromdocname:
                newnode['refid'] = labelid
            else:
                # set more info in contnode; in case the
                # get_relative_uri call raises NoUri,
                # the builder will then have to resolve these
                contnode = addnodes.pending_xref('')
                contnode['refdocname'] = docname
                contnode['refsectname'] = sectname
                newnode['refuri'] = builder.get_relative_uri(
                    fromdocname, docname)
                if labelid:
                    newnode['refuri'] += '#' + labelid
            newnode.append(innernode)
            return newnode
        elif typ == 'keyword':
            # keywords are oddballs: they are referenced by named labels
            docname, labelid, _ = self.data['labels'].get(target, ('','',''))
            if not docname:
                return None
            return make_refnode(builder, fromdocname, docname,
                                labelid, contnode)
        elif typ == 'option':
            progname = node['refprogram']
            docname, labelid = self.data['progoptions'].get((progname, target),
                                                            ('', ''))
            if not docname:
                return None
            return make_refnode(builder, fromdocname, docname,
                                labelid, contnode)
        else:
            objtypes = self.objtypes_for_role(typ) or []
            for objtype in objtypes:
                if (objtype, target) in self.data['objects']:
                    docname, labelid = self.data['objects'][objtype, target]
                    break
            else:
                docname, labelid = '', ''
            if not docname:
                return None
            return make_refnode(builder, fromdocname, docname,
                                labelid, contnode)

    def get_objects(self):
        for (prog, option), info in self.data['progoptions'].iteritems():
            yield (option, option, 'option', info[0], info[1], 1)
        for (type, name), info in self.data['objects'].iteritems():
            yield (name, name, type, info[0], info[1],
                   self.object_types[type].attrs['searchprio'])
        for name, info in self.data['labels'].iteritems():
            yield (name, info[2], 'label', info[0], info[1], -1)

    def get_type_name(self, type, primary=False):
        # never prepend "Default"
        return type.lname
