# -*- coding: utf-8 -*-
"""
    sphinx.ext.pngmath
    ~~~~~~~~~~~~~~~~~~

    Render math in HTML via dvipng.

    :copyright: Copyright 2007-2013 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
import codecs
import shutil
import tempfile
import posixpath
from os import path, getcwd, chdir
from subprocess import Popen, PIPE
try:
    from hashlib import sha1 as sha
except ImportError:
    from sha import sha

from docutils import nodes

from sphinx.errors import SphinxError
from sphinx.util.png import read_png_depth, write_png_depth
from sphinx.util.osutil import ensuredir, ENOENT
from sphinx.util.pycompat import b
from sphinx.ext.mathbase import setup_math as mathbase_setup, wrap_displaymath

class MathExtError(SphinxError):
    category = 'Math extension error'

    def __init__(self, msg, stderr=None, stdout=None):
        if stderr:
            msg += '\n[stderr]\n' + stderr
        if stdout:
            msg += '\n[stdout]\n' + stdout
        SphinxError.__init__(self, msg)


DOC_HEAD = r'''
\documentclass[12pt]{article}
\usepackage[utf8x]{inputenc}
\usepackage{amsmath}
\usepackage{amsthm}
\usepackage{amssymb}
\usepackage{amsfonts}
\usepackage{bm}
\pagestyle{empty}
'''

DOC_BODY = r'''
\begin{document}
%s
\end{document}
'''

DOC_BODY_PREVIEW = r'''
\usepackage[active]{preview}
\begin{document}
\begin{preview}
%s
\end{preview}
\end{document}
'''

depth_re = re.compile(b(r'\[\d+ depth=(-?\d+)\]'))

def render_math(self, math):
    """Render the LaTeX math expression *math* using latex and dvipng.

    Return the filename relative to the built document and the "depth",
    that is, the distance of image bottom and baseline in pixels, if the
    option to use preview_latex is switched on.

    Error handling may seem strange, but follows a pattern: if LaTeX or
    dvipng aren't available, only a warning is generated (since that enables
    people on machines without these programs to at least build the rest
    of the docs successfully).  If the programs are there, however, they
    may not fail since that indicates a problem in the math source.
    """
    use_preview = self.builder.config.pngmath_use_preview

    shasum = "%s.png" % sha(math.encode('utf-8')).hexdigest()
    relfn = posixpath.join(self.builder.imgpath, 'math', shasum)
    outfn = path.join(self.builder.outdir, '_images', 'math', shasum)
    if path.isfile(outfn):
        depth = read_png_depth(outfn)
        return relfn, depth

    # if latex or dvipng has failed once, don't bother to try again
    if hasattr(self.builder, '_mathpng_warned_latex') or \
       hasattr(self.builder, '_mathpng_warned_dvipng'):
        return None, None

    latex = DOC_HEAD + self.builder.config.pngmath_latex_preamble
    latex += (use_preview and DOC_BODY_PREVIEW or DOC_BODY) % math

    # use only one tempdir per build -- the use of a directory is cleaner
    # than using temporary files, since we can clean up everything at once
    # just removing the whole directory (see cleanup_tempdir)
    if not hasattr(self.builder, '_mathpng_tempdir'):
        tempdir = self.builder._mathpng_tempdir = tempfile.mkdtemp()
    else:
        tempdir = self.builder._mathpng_tempdir

    tf = codecs.open(path.join(tempdir, 'math.tex'), 'w', 'utf-8')
    tf.write(latex)
    tf.close()

    # build latex command; old versions of latex don't have the
    # --output-directory option, so we have to manually chdir to the
    # temp dir to run it.
    ltx_args = [self.builder.config.pngmath_latex, '--interaction=nonstopmode']
    # add custom args from the config file
    ltx_args.extend(self.builder.config.pngmath_latex_args)
    ltx_args.append('math.tex')

    curdir = getcwd()
    chdir(tempdir)

    try:
        try:
            p = Popen(ltx_args, stdout=PIPE, stderr=PIPE)
        except OSError, err:
            if err.errno != ENOENT:   # No such file or directory
                raise
            self.builder.warn('LaTeX command %r cannot be run (needed for math '
                              'display), check the pngmath_latex setting' %
                              self.builder.config.pngmath_latex)
            self.builder._mathpng_warned_latex = True
            return None, None
    finally:
        chdir(curdir)

    stdout, stderr = p.communicate()
    if p.returncode != 0:
        raise MathExtError('latex exited with error', stderr, stdout)

    ensuredir(path.dirname(outfn))
    # use some standard dvipng arguments
    dvipng_args = [self.builder.config.pngmath_dvipng]
    dvipng_args += ['-o', outfn, '-T', 'tight', '-z9']
    # add custom ones from config value
    dvipng_args.extend(self.builder.config.pngmath_dvipng_args)
    if use_preview:
        dvipng_args.append('--depth')
    # last, the input file name
    dvipng_args.append(path.join(tempdir, 'math.dvi'))
    try:
        p = Popen(dvipng_args, stdout=PIPE, stderr=PIPE)
    except OSError, err:
        if err.errno != ENOENT:   # No such file or directory
            raise
        self.builder.warn('dvipng command %r cannot be run (needed for math '
                          'display), check the pngmath_dvipng setting' %
                          self.builder.config.pngmath_dvipng)
        self.builder._mathpng_warned_dvipng = True
        return None, None
    stdout, stderr = p.communicate()
    if p.returncode != 0:
        raise MathExtError('dvipng exited with error', stderr, stdout)
    depth = None
    if use_preview:
        for line in stdout.splitlines():
            m = depth_re.match(line)
            if m:
                depth = int(m.group(1))
                write_png_depth(outfn, depth)
                break

    return relfn, depth

def cleanup_tempdir(app, exc):
    if exc:
        return
    if not hasattr(app.builder, '_mathpng_tempdir'):
        return
    try:
        shutil.rmtree(app.builder._mathpng_tempdir)
    except Exception:
        pass

def get_tooltip(self, node):
    if self.builder.config.pngmath_add_tooltips:
        return ' alt="%s"' % self.encode(node['latex']).strip()
    return ''

def html_visit_math(self, node):
    try:
        fname, depth = render_math(self, '$'+node['latex']+'$')
    except MathExtError, exc:
        msg = unicode(str(exc), 'utf-8', 'replace')
        sm = nodes.system_message(msg, type='WARNING', level=2,
                                  backrefs=[], source=node['latex'])
        sm.walkabout(self)
        self.builder.warn('display latex %r: ' % node['latex'] + str(exc))
        raise nodes.SkipNode
    if fname is None:
        # something failed -- use text-only as a bad substitute
        self.body.append('<span class="math">%s</span>' %
                         self.encode(node['latex']).strip())
    else:
        c  = ('<img class="math" src="%s"' % fname) + get_tooltip(self, node)
        if depth is not None:
            c += ' style="vertical-align: %dpx"' % (-depth)
        self.body.append(c + '/>')
    raise nodes.SkipNode

def html_visit_displaymath(self, node):
    if node['nowrap']:
        latex = node['latex']
    else:
        latex = wrap_displaymath(node['latex'], None)
    try:
        fname, depth = render_math(self, latex)
    except MathExtError, exc:
        sm = nodes.system_message(str(exc), type='WARNING', level=2,
                                  backrefs=[], source=node['latex'])
        sm.walkabout(self)
        self.builder.warn('inline latex %r: ' % node['latex'] + str(exc))
        raise nodes.SkipNode
    self.body.append(self.starttag(node, 'div', CLASS='math'))
    self.body.append('<p>')
    if node['number']:
        self.body.append('<span class="eqno">(%s)</span>' % node['number'])
    if fname is None:
        # something failed -- use text-only as a bad substitute
        self.body.append('<span class="math">%s</span></p>\n</div>' %
                         self.encode(node['latex']).strip())
    else:
        self.body.append(('<img src="%s"' % fname) + get_tooltip(self, node)
                         + '/></p>\n</div>')
    raise nodes.SkipNode


def setup(app):
    mathbase_setup(app, (html_visit_math, None), (html_visit_displaymath, None))
    app.add_config_value('pngmath_dvipng', 'dvipng', 'html')
    app.add_config_value('pngmath_latex', 'latex', 'html')
    app.add_config_value('pngmath_use_preview', False, 'html')
    app.add_config_value('pngmath_dvipng_args',
                         ['-gamma', '1.5', '-D', '110', '-bg', 'Transparent'],
                         'html')
    app.add_config_value('pngmath_latex_args', [], 'html')
    app.add_config_value('pngmath_latex_preamble', '', 'html')
    app.add_config_value('pngmath_add_tooltips', True, 'html')
    app.connect('build-finished', cleanup_tempdir)
