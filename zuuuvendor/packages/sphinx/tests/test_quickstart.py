# -*- coding: utf-8 -*-
"""
    test_quickstart
    ~~~~~~~~~~~~~~~

    Test the sphinx.quickstart module.

    :copyright: Copyright 2007-2013 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys
import time
from StringIO import StringIO
import tempfile

from util import raises, with_tempdir, with_app, SkipTest

from sphinx import application
from sphinx import quickstart as qs
from sphinx.util.console import nocolor, coloron
from sphinx.util.pycompat import execfile_


warnfile = StringIO()


def setup_module():
    nocolor()

def mock_raw_input(answers, needanswer=False):
    called = set()
    def raw_input(prompt):
        if prompt in called:
            raise AssertionError('answer for %r missing and no default '
                                 'present' % prompt)
        called.add(prompt)
        if sys.version_info < (3, 0):
            prompt = str(prompt)  # Python2.x raw_input emulation
            # `raw_input` encode `prompt` by default encoding to print.
        else:
            prompt = unicode(prompt)  # Python3.x input emulation
            # `input` decode prompt by default encoding before print.
        for question in answers:
            if prompt.startswith(qs.PROMPT_PREFIX + question):
                return answers[question]
        if needanswer:
            raise AssertionError('answer for %r missing' % prompt)
        return ''
    return raw_input

try:
    real_raw_input = raw_input
except NameError:
    real_raw_input = input

def teardown_module():
    qs.term_input = real_raw_input
    qs.TERM_ENCODING = getattr(sys.stdin, 'encoding', None)
    coloron()


def test_quickstart_inputstrip():
    d = {}
    answers = {
        'Q1': 'Y\r',  # input() return with '\r' on Python-3.2.0 for Windows
        'Q2': ' Yes \r',
        'Q3': 'N',
        'Q4': 'N ',
    }
    qs.term_input = mock_raw_input(answers)
    qs.do_prompt(d, 'k1', 'Q1')
    assert d['k1'] == 'Y'
    qs.do_prompt(d, 'k2', 'Q2')
    assert d['k2'] == 'Yes'
    qs.do_prompt(d, 'k3', 'Q3')
    assert d['k3'] == 'N'
    qs.do_prompt(d, 'k4', 'Q4')
    assert d['k4'] == 'N'


def test_do_prompt():
    d = {}
    answers = {
        'Q2': 'v2',
        'Q3': 'v3',
        'Q4': 'yes',
        'Q5': 'no',
        'Q6': 'foo',
    }
    qs.term_input = mock_raw_input(answers)
    try:
        qs.do_prompt(d, 'k1', 'Q1')
    except AssertionError:
        assert 'k1' not in d
    else:
        assert False, 'AssertionError not raised'
    qs.do_prompt(d, 'k1', 'Q1', default='v1')
    assert d['k1'] == 'v1'
    qs.do_prompt(d, 'k3', 'Q3', default='v3_default')
    assert d['k3'] == 'v3'
    qs.do_prompt(d, 'k2', 'Q2')
    assert d['k2'] == 'v2'
    qs.do_prompt(d, 'k4', 'Q4', validator=qs.boolean)
    assert d['k4'] is True
    qs.do_prompt(d, 'k5', 'Q5', validator=qs.boolean)
    assert d['k5'] is False
    raises(AssertionError, qs.do_prompt, d, 'k6', 'Q6', validator=qs.boolean)


def test_do_prompt_with_nonascii():
    d = {}
    answers = {
        'Q1': u'\u30c9\u30a4\u30c4',
    }
    qs.term_input = mock_raw_input(answers)
    try:
        qs.do_prompt(d, 'k1', 'Q1', default=u'\u65e5\u672c')
    except UnicodeEncodeError:
        raise SkipTest(
            'non-ASCII console input not supported on this encoding: %s',
            qs.TERM_ENCODING)
    assert d['k1'] == u'\u30c9\u30a4\u30c4'


@with_tempdir
def test_quickstart_defaults(tempdir):
    answers = {
        'Root path': tempdir,
        'Project name': 'Sphinx Test',
        'Author name': 'Georg Brandl',
        'Project version': '0.1',
    }
    qs.term_input = mock_raw_input(answers)
    d = {}
    qs.ask_user(d)
    qs.generate(d)

    conffile = tempdir / 'conf.py'
    assert conffile.isfile()
    ns = {}
    execfile_(conffile, ns)
    assert ns['extensions'] == []
    assert ns['templates_path'] == ['_templates']
    assert ns['source_suffix'] == '.rst'
    assert ns['master_doc'] == 'index'
    assert ns['project'] == 'Sphinx Test'
    assert ns['copyright'] == '%s, Georg Brandl' % time.strftime('%Y')
    assert ns['version'] == '0.1'
    assert ns['release'] == '0.1'
    assert ns['html_static_path'] == ['_static']
    assert ns['latex_documents'] == [
        ('index', 'SphinxTest.tex', 'Sphinx Test Documentation',
         'Georg Brandl', 'manual')]

    assert (tempdir / '_static').isdir()
    assert (tempdir / '_templates').isdir()
    assert (tempdir / 'index.rst').isfile()
    assert (tempdir / 'Makefile').isfile()
    assert (tempdir / 'make.bat').isfile()


@with_tempdir
def test_quickstart_all_answers(tempdir):
    answers = {
        'Root path': tempdir,
        'Separate source and build': 'y',
        'Name prefix for templates': '.',
        'Project name': u'STASI™'.encode('utf-8'),
        'Author name': u'Wolfgang Schäuble & G\'Beckstein'.encode('utf-8'),
        'Project version': '2.0',
        'Project release': '2.0.1',
        'Source file suffix': '.txt',
        'Name of your master document': 'contents',
        'autodoc': 'y',
        'doctest': 'yes',
        'intersphinx': 'no',
        'todo': 'n',
        'coverage': 'no',
        'pngmath': 'N',
        'mathjax': 'no',
        'ifconfig': 'no',
        'viewcode': 'no',
        'Create Makefile': 'no',
        'Create Windows command file': 'no',
        'Do you want to use the epub builder': 'yes',
    }
    qs.term_input = mock_raw_input(answers, needanswer=True)
    qs.TERM_ENCODING = 'utf-8'
    d = {}
    qs.ask_user(d)
    qs.generate(d)

    conffile = tempdir / 'source' / 'conf.py'
    assert conffile.isfile()
    ns = {}
    execfile_(conffile, ns)
    assert ns['extensions'] == ['sphinx.ext.autodoc', 'sphinx.ext.doctest']
    assert ns['templates_path'] == ['.templates']
    assert ns['source_suffix'] == '.txt'
    assert ns['master_doc'] == 'contents'
    assert ns['project'] == u'STASI™'
    assert ns['copyright'] == u'%s, Wolfgang Schäuble & G\'Beckstein' % \
           time.strftime('%Y')
    assert ns['version'] == '2.0'
    assert ns['release'] == '2.0.1'
    assert ns['html_static_path'] == ['.static']
    assert ns['latex_documents'] == [
        ('contents', 'STASI.tex', u'STASI™ Documentation',
         u'Wolfgang Schäuble \\& G\'Beckstein', 'manual')]
    assert ns['epub_author'] == u'Wolfgang Schäuble & G\'Beckstein'
    assert ns['man_pages'] == [
        ('contents', 'stasi', u'STASI™ Documentation',
         [u'Wolfgang Schäuble & G\'Beckstein'], 1)]
    assert ns['texinfo_documents'] == [
        ('contents', 'STASI', u'STASI™ Documentation',
         u'Wolfgang Schäuble & G\'Beckstein', 'STASI',
         'One line description of project.', 'Miscellaneous'),]

    assert (tempdir / 'build').isdir()
    assert (tempdir / 'source' / '.static').isdir()
    assert (tempdir / 'source' / '.templates').isdir()
    assert (tempdir / 'source' / 'contents.txt').isfile()


@with_tempdir
def test_generated_files_eol(tempdir):
    answers = {
        'Root path': tempdir,
        'Project name': 'Sphinx Test',
        'Author name': 'Georg Brandl',
        'Project version': '0.1',
    }
    qs.term_input = mock_raw_input(answers)
    d = {}
    qs.ask_user(d)
    qs.generate(d)

    def assert_eol(filename, eol):
        content = filename.bytes().decode('unicode-escape')
        assert all([l[-len(eol):]==eol for l in content.splitlines(True)])

    assert_eol(tempdir / 'make.bat', '\r\n')
    assert_eol(tempdir / 'Makefile', '\n')


@with_tempdir
def test_quickstart_and_build(tempdir):
    answers = {
        'Root path': tempdir,
        'Project name': u'Fullwidth characters: \u30c9\u30a4\u30c4',
        'Author name': 'Georg Brandl',
        'Project version': '0.1',
    }
    qs.term_input = mock_raw_input(answers)
    d = {}
    qs.ask_user(d)
    qs.generate(d)

    app = application.Sphinx(
            tempdir,  #srcdir
            tempdir,  #confdir
            (tempdir / '_build' / 'html'),  #outdir
            (tempdir / '_build' / '.doctree'),  #doctreedir
            'html',  #buildername
            status=StringIO(),
            warning=warnfile)
    app.builder.build_all()
    warnings = warnfile.getvalue()
    assert not warnings


@with_tempdir
def test_default_filename(tempdir):
    answers = {
        'Root path': tempdir,
        'Project name': u'\u30c9\u30a4\u30c4', #Fullwidth characters only
        'Author name': 'Georg Brandl',
        'Project version': '0.1',
    }
    qs.term_input = mock_raw_input(answers)
    d = {}
    qs.ask_user(d)
    qs.generate(d)

    conffile = tempdir / 'conf.py'
    assert conffile.isfile()
    ns = {}
    execfile_(conffile, ns)
    assert ns['latex_documents'][0][1] == 'sphinx.tex'
    assert ns['man_pages'][0][1] == 'sphinx'
    assert ns['texinfo_documents'][0][1] == 'sphinx'
