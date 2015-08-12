# -*- coding: utf-8 -*-
"""
    sphinx.builders.manpage
    ~~~~~~~~~~~~~~~~~~~~~~~

    Manual pages builder.

    :copyright: Copyright 2007-2013 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from os import path

from docutils.io import FileOutput
from docutils.frontend import OptionParser

from sphinx import addnodes
from sphinx.errors import SphinxError
from sphinx.builders import Builder
from sphinx.environment import NoUri
from sphinx.util.nodes import inline_all_toctrees
from sphinx.util.console import bold, darkgreen
from sphinx.writers.manpage import ManualPageWriter, has_manpage_writer


class ManualPageBuilder(Builder):
    """
    Builds groff output in manual page format.
    """
    name = 'man'
    format = 'man'
    supported_image_types = []

    def init(self):
        if not has_manpage_writer:
            raise SphinxError('The docutils manual page writer can\'t be '
                              'found; it is only available as of docutils 0.6.')
        if not self.config.man_pages:
            self.warn('no "man_pages" config value found; no manual pages '
                      'will be written')

    def get_outdated_docs(self):
        return 'all manpages' # for now

    def get_target_uri(self, docname, typ=None):
        if typ == 'token':
            return ''
        raise NoUri

    def write(self, *ignored):
        docwriter = ManualPageWriter(self)
        docsettings = OptionParser(
            defaults=self.env.settings,
            components=(docwriter,),
            read_config_files=True).get_default_values()

        self.info(bold('writing... '), nonl=True)

        for info in self.config.man_pages:
            docname, name, description, authors, section = info
            if isinstance(authors, basestring):
                if authors:
                    authors = [authors]
                else:
                    authors = []

            targetname = '%s.%s' % (name, section)
            self.info(darkgreen(targetname) + ' { ', nonl=True)
            destination = FileOutput(
                destination_path=path.join(self.outdir, targetname),
                encoding='utf-8')

            tree = self.env.get_doctree(docname)
            docnames = set()
            largetree = inline_all_toctrees(self, docnames, docname, tree,
                                            darkgreen)
            self.info('} ', nonl=True)
            self.env.resolve_references(largetree, docname, self)
            # remove pending_xref nodes
            for pendingnode in largetree.traverse(addnodes.pending_xref):
                pendingnode.replace_self(pendingnode.children)

            largetree.settings = docsettings
            largetree.settings.title = name
            largetree.settings.subtitle = description
            largetree.settings.authors = authors
            largetree.settings.section = section

            docwriter.write(largetree, destination)
        self.info()

    def finish(self):
        pass
