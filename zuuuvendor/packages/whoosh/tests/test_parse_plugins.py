from __future__ import with_statement
import inspect
from datetime import datetime
import sys

from nose.tools import assert_equal  #@UnresolvedImport

from whoosh import analysis, fields, formats, qparser, query
from whoosh.compat import u, text_type, xrange
from whoosh.filedb.filestore import RamStorage
from whoosh.qparser import dateparse, default, plugins, syntax
from whoosh.support.times import adatetime


def _plugin_classes(ignore):
    # Get all the subclasses of Plugin in whoosh.qparser.plugins
    return [c for _, c in inspect.getmembers(plugins, inspect.isclass)
            if plugins.Plugin in c.__bases__ and c not in ignore]


def test_combos():
    qs = 'w:a "hi there"^4.2 AND x:b^2.3 OR c AND (y:d OR e) (apple ANDNOT bear)^2.3'

    init_args = {plugins.MultifieldPlugin: (["content", "title"], {"content": 1.0, "title": 1.2}),
                 plugins.FieldAliasPlugin: ({"content": ("text", "body")},),
                 plugins.MultifieldPlugin: (["title", "content"],),
                 plugins.CopyFieldPlugin: ({"name": "phone"},),
                 plugins.PseudoFieldPlugin: ({"name": lambda x: x}),
                 }

    pis = _plugin_classes(())
    for i, plugin in enumerate(pis):
        try:
            pis[i] = plugin(*init_args.get(plugin, ()))
        except TypeError:
            raise TypeError("Error instantiating %s" % plugin)

    count = 0
    for i, first in enumerate(pis):
        for j in xrange(len(pis)):
            if i == j: continue
            plist = [p for p in pis[:j] if p is not first] + [first]
            qp = qparser.QueryParser("text", None, plugins=plist)
            try:
                qp.parse(qs)
            except Exception:
                e = sys.exc_info()[1]
                raise Exception(str(e) + " combo: %s %r" % (count, plist))
            count += 1

def test_field_alias():
    qp = qparser.QueryParser("content", None)
    qp.add_plugin(plugins.FieldAliasPlugin({"title": ("article", "caption")}))
    q = qp.parse("alfa title:bravo article:charlie caption:delta")
    assert_equal(text_type(q), u("(content:alfa AND title:bravo AND title:charlie AND title:delta)"))

def test_dateparser():
    schema = fields.Schema(text=fields.TEXT, date=fields.DATETIME)
    qp = default.QueryParser("text", schema)

    errs = []
    def cb(arg):
        errs.append(arg)
    basedate = datetime(2010, 9, 20, 15, 16, 6, 454000)
    qp.add_plugin(dateparse.DateParserPlugin(basedate, callback=cb))

    q = qp.parse(u("hello date:'last tuesday'"))
    assert_equal(q.__class__, query.And)
    assert_equal(q[1].__class__, query.DateRange)
    assert_equal(q[1].startdate, adatetime(2010, 9, 14).floor())
    assert_equal(q[1].enddate, adatetime(2010, 9, 14).ceil())

    q = qp.parse(u("date:'3am to 5pm'"))
    assert_equal(q.__class__, query.DateRange)
    assert_equal(q.startdate, adatetime(2010, 9, 20, 3).floor())
    assert_equal(q.enddate, adatetime(2010, 9, 20, 17).ceil())

    q = qp.parse(u("date:blah"))
    assert_equal(q, query.NullQuery)
    assert_equal(errs[0], "blah")

    q = qp.parse(u("hello date:blarg"))
    assert_equal(q.__unicode__(), "(text:hello AND <_NullQuery>)")
    assert_equal(q[1].error, "blarg")
    assert_equal(errs[1], "blarg")

    q = qp.parse(u("hello date:20055x10"))
    assert_equal(q.__unicode__(), "(text:hello AND <_NullQuery>)")
    assert_equal(q[1].error, "20055x10")
    assert_equal(errs[2], "20055x10")

    q = qp.parse(u("hello date:'2005 19 32'"))
    assert_equal(q.__unicode__(), "(text:hello AND <_NullQuery>)")
    assert_equal(q[1].error, "2005 19 32")
    assert_equal(errs[3], "2005 19 32")

    q = qp.parse(u("date:'march 24 to dec 12'"))
    assert_equal(q.__class__, query.DateRange)
    assert_equal(q.startdate, adatetime(2010, 3, 24).floor())
    assert_equal(q.enddate, adatetime(2010, 12, 12).ceil())

    q = qp.parse(u("date:('30 june' OR '10 july') quick"))
    assert_equal(q.__class__, query.And)
    assert_equal(len(q), 2)
    assert_equal(q[0].__class__, query.Or)
    assert_equal(q[0][0].__class__, query.DateRange)
    assert_equal(q[0][1].__class__, query.DateRange)

def test_date_range():
    schema = fields.Schema(text=fields.TEXT, date=fields.DATETIME)
    qp = qparser.QueryParser("text", schema)
    basedate = datetime(2010, 9, 20, 15, 16, 6, 454000)
    qp.add_plugin(dateparse.DateParserPlugin(basedate))

    q = qp.parse(u("date:['30 march' to 'next wednesday']"))
    assert_equal(q.__class__, query.DateRange)
    assert_equal(q.startdate, adatetime(2010, 3, 30).floor())
    assert_equal(q.enddate, adatetime(2010, 9, 22).ceil())

    q = qp.parse(u("date:[to 'next wednesday']"))
    assert_equal(q.__class__, query.DateRange)
    assert_equal(q.startdate, None)
    assert_equal(q.enddate, adatetime(2010, 9, 22).ceil())

    q = qp.parse(u("date:['30 march' to]"))
    assert_equal(q.__class__, query.DateRange)
    assert_equal(q.startdate, adatetime(2010, 3, 30).floor())
    assert_equal(q.enddate, None)

    print("!!!!!!!!!!!!!!!!!!!!")
    q = qp.parse(u("date:[30 march to next wednesday]"))
    print("q=", q)
    assert_equal(q.__class__, query.DateRange)
    assert_equal(q.startdate, adatetime(2010, 3, 30).floor())
    assert_equal(q.enddate, adatetime(2010, 9, 22).ceil())

    q = qp.parse(u("date:[to next wednesday]"))
    assert_equal(q.__class__, query.DateRange)
    assert_equal(q.startdate, None)
    assert_equal(q.enddate, adatetime(2010, 9, 22).ceil())

    q = qp.parse(u("date:[30 march to]"))
    assert_equal(q.__class__, query.DateRange)
    assert_equal(q.startdate, adatetime(2010, 3, 30).floor())
    assert_equal(q.enddate, None)

def test_daterange_empty_field():
    schema = fields.Schema(test=fields.DATETIME)
    ix = RamStorage().create_index(schema)

    writer = ix.writer()
    writer.add_document(test=None)
    writer.commit()

    with ix.searcher() as s:
        q = query.DateRange("test", datetime.fromtimestamp(0), datetime.today())
        r = s.search(q)
        assert_equal(len(r), 0)

def test_free_dates():
    a = analysis.StandardAnalyzer(stoplist=None)
    schema = fields.Schema(text=fields.TEXT(analyzer=a), date=fields.DATETIME)
    qp = qparser.QueryParser("text", schema)
    basedate = datetime(2010, 9, 20, 15, 16, 6, 454000)
    qp.add_plugin(dateparse.DateParserPlugin(basedate, free=True))

    q = qp.parse(u("hello date:last tuesday"))
    assert_equal(q.__class__, query.And)
    assert_equal(len(q), 2)
    assert_equal(q[0].__class__, query.Term)
    assert_equal(q[0].text, "hello")
    assert_equal(q[1].__class__, query.DateRange)
    assert_equal(q[1].startdate, adatetime(2010, 9, 14).floor())
    assert_equal(q[1].enddate, adatetime(2010, 9, 14).ceil())

    q = qp.parse(u("date:mar 29 1972 hello"))
    assert_equal(q.__class__, query.And)
    assert_equal(len(q), 2)
    assert_equal(q[0].__class__, query.DateRange)
    assert_equal(q[0].startdate, adatetime(1972, 3, 29).floor())
    assert_equal(q[0].enddate, adatetime(1972, 3, 29).ceil())
    assert_equal(q[1].__class__, query.Term)
    assert_equal(q[1].text, "hello")

    q = qp.parse(u("date:2005 march 2"))
    assert_equal(q.__class__, query.DateRange)
    assert_equal(q.startdate, adatetime(2005, 3, 2).floor())
    assert_equal(q.enddate, adatetime(2005, 3, 2).ceil())

    q = qp.parse(u("date:'2005' march 2"))
    assert_equal(q.__class__, query.And)
    assert_equal(len(q), 3)
    assert_equal(q[0].__class__, query.DateRange)
    assert_equal(q[0].startdate, adatetime(2005).floor())
    assert_equal(q[0].enddate, adatetime(2005).ceil())
    assert_equal(q[1].__class__, query.Term)
    assert_equal(q[1].fieldname, "text")
    assert_equal(q[1].text, "march")

    q = qp.parse(u("date:march 24 to dec 12"))
    assert_equal(q.__class__, query.DateRange)
    assert_equal(q.startdate, adatetime(2010, 3, 24).floor())
    assert_equal(q.enddate, adatetime(2010, 12, 12).ceil())

    q = qp.parse(u("date:5:10pm"))
    assert_equal(q.__class__, query.DateRange)
    assert_equal(q.startdate, adatetime(2010, 9, 20, 17, 10).floor())
    assert_equal(q.enddate, adatetime(2010, 9, 20, 17, 10).ceil())

    q = qp.parse(u("(date:30 june OR date:10 july) quick"))
    assert_equal(q.__class__, query.And)
    assert_equal(len(q), 2)
    assert_equal(q[0].__class__, query.Or)
    assert_equal(q[0][0].__class__, query.DateRange)
    assert_equal(q[0][1].__class__, query.DateRange)

def test_prefix_plugin():
    schema = fields.Schema(id=fields.ID, text=fields.TEXT)
    ix = RamStorage().create_index(schema)

    w = ix.writer()
    w.add_document(id=u("1"), text=u("alfa"))
    w.add_document(id=u("2"), text=u("bravo"))
    w.add_document(id=u("3"), text=u("buono"))
    w.commit()

    with ix.searcher() as s:
        qp = qparser.QueryParser("text", schema)
        qp.remove_plugin_class(plugins.WildcardPlugin)
        qp.add_plugin(plugins.PrefixPlugin)

        q = qp.parse(u("b*"))
        r = s.search(q, limit=None)
        assert_equal(len(r), 2)

        q = qp.parse(u("br*"))
        r = s.search(q, limit=None)
        assert_equal(len(r), 1)

def test_custom_tokens():
    qp = qparser.QueryParser("text", None)
    qp.remove_plugin_class(plugins.OperatorsPlugin)

    cp = plugins.OperatorsPlugin(And="&", Or="\\|", AndNot="&!", AndMaybe="&~",
                                 Not="-")
    qp.add_plugin(cp)

    q = qp.parse("this | that")
    assert_equal(q.__class__, query.Or)
    assert_equal(q[0].__class__, query.Term)
    assert_equal(q[0].text, "this")
    assert_equal(q[1].__class__, query.Term)
    assert_equal(q[1].text, "that")

    q = qp.parse("this&!that")
    assert_equal(q.__class__, query.AndNot)
    assert_equal(q.a.__class__, query.Term)
    assert_equal(q.a.text, "this")
    assert_equal(q.b.__class__, query.Term)
    assert_equal(q.b.text, "that")

    q = qp.parse("alfa -bravo NOT charlie")
    assert_equal(len(q), 4)
    assert_equal(q[1].__class__, query.Not)
    assert_equal(q[1].query.text, "bravo")
    assert_equal(q[2].text, "NOT")

def test_copyfield():
    qp = qparser.QueryParser("a", None)
    qp.add_plugin(plugins.CopyFieldPlugin({"b": "c"}, None))
    assert_equal(text_type(qp.parse("hello b:matt")), "(a:hello AND b:matt AND c:matt)")

    qp = qparser.QueryParser("a", None)
    qp.add_plugin(plugins.CopyFieldPlugin({"b": "c"}, syntax.AndMaybeGroup))
    assert_equal(text_type(qp.parse("hello b:matt")), "(a:hello AND (b:matt ANDMAYBE c:matt))")

    qp = qparser.QueryParser("a", None)
    qp.add_plugin(plugins.CopyFieldPlugin({"b": "c"}, syntax.RequireGroup))
    assert_equal(text_type(qp.parse("hello (there OR b:matt)")), "(a:hello AND (a:there OR (b:matt REQUIRE c:matt)))")

    qp = qparser.QueryParser("a", None)
    qp.add_plugin(plugins.CopyFieldPlugin({"a": "c"}, syntax.OrGroup))
    assert_equal(text_type(qp.parse("hello there")), "((a:hello OR c:hello) AND (a:there OR c:there))")

    qp = qparser.QueryParser("a", None)
    qp.add_plugin(plugins.CopyFieldPlugin({"b": "c"}, mirror=True))
    assert_equal(text_type(qp.parse("hello c:matt")), "(a:hello AND (c:matt OR b:matt))")

    qp = qparser.QueryParser("a", None)
    qp.add_plugin(plugins.CopyFieldPlugin({"c": "a"}, mirror=True))
    assert_equal(text_type(qp.parse("hello c:matt")), "((a:hello OR c:hello) AND (c:matt OR a:matt))")

    ana = analysis.RegexAnalyzer(r"\w+") | analysis.DoubleMetaphoneFilter()
    fmt = formats.Frequency()
    schema = fields.Schema(name=fields.KEYWORD, name_phone=fields.FieldType(fmt, ana, multitoken_query="or"))
    qp = qparser.QueryParser("name", schema)
    qp.add_plugin(plugins.CopyFieldPlugin({"name": "name_phone"}))
    assert_equal(text_type(qp.parse(u("spruce view"))), "((name:spruce OR name_phone:SPRS) AND (name:view OR name_phone:F OR name_phone:FF))")

def test_gtlt():
    schema = fields.Schema(a=fields.KEYWORD, b=fields.NUMERIC,
                           c=fields.KEYWORD,
                           d=fields.NUMERIC(float), e=fields.DATETIME)
    qp = qparser.QueryParser("a", schema)
    qp.add_plugin(plugins.GtLtPlugin())
    qp.add_plugin(dateparse.DateParserPlugin())

    q = qp.parse(u("a:hello b:>100 c:<=z there"))
    assert_equal(q.__class__, query.And)
    assert_equal(len(q), 4)
    assert_equal(q[0], query.Term("a", "hello"))
    assert_equal(q[1], query.NumericRange("b", 100, None, startexcl=True))
    assert_equal(q[2], query.TermRange("c", None, 'z'))
    assert_equal(q[3], query.Term("a", "there"))

    q = qp.parse(u("hello e:>'29 mar 2001' there"))
    assert_equal(q.__class__, query.And)
    assert_equal(len(q), 3)
    assert_equal(q[0], query.Term("a", "hello"))
    # As of this writing, date ranges don't support startexcl/endexcl
    assert_equal(q[1], query.DateRange("e", datetime(2001, 3, 29, 0, 0), None))
    assert_equal(q[2], query.Term("a", "there"))

    q = qp.parse(u("a:> alfa c:<= bravo"))
    assert_equal(text_type(q), "(a:a: AND a:alfa AND a:c: AND a:bravo)")

    qp.remove_plugin_class(plugins.FieldsPlugin)
    qp.remove_plugin_class(plugins.RangePlugin)
    q = qp.parse(u("hello a:>500 there"))
    assert_equal(text_type(q), "(a:hello AND a:a: AND a:500 AND a:there)")

def test_regex():
    schema = fields.Schema(a=fields.KEYWORD, b=fields.TEXT)
    qp = qparser.QueryParser("a", schema)
    qp.add_plugin(plugins.RegexPlugin())

    q = qp.parse(u("a:foo-bar b:foo-bar"))
    assert_equal(q.__unicode__(), '(a:foo-bar AND b:foo AND b:bar)')

    q = qp.parse(u('a:r"foo-bar" b:r"foo-bar"'))
    assert_equal(q.__unicode__(), '(a:r"foo-bar" AND b:r"foo-bar")')

def test_pseudofield():
    schema = fields.Schema(a=fields.KEYWORD, b=fields.TEXT)

    def regex_maker(node):
        if node.has_text:
            node = qparser.RegexPlugin.RegexNode(node.text)
            node.set_fieldname("content")
            return node

    qp = qparser.QueryParser("a", schema)
    qp.add_plugin(qparser.PseudoFieldPlugin({"regex": regex_maker}))
    q = qp.parse(u("alfa regex:br.vo"))
    assert_equal(q.__unicode__(), '(a:alfa AND content:r"br.vo")')

    def rev_text(node):
        if node.has_text:
            # Create a word node for the reversed text
            revtext = node.text[::-1]  # Reverse the text
            rnode = qparser.WordNode(revtext)
            # Duplicate the original node's start and end char
            rnode.set_range(node.startchar, node.endchar)

            # Put the original node and the reversed node in an OrGroup
            group = qparser.OrGroup([node, rnode])

            # Need to set the fieldname here because the PseudoFieldPlugin
            # removes the field name syntax
            group.set_fieldname("reverse")

            return group

    qp = qparser.QueryParser("content", schema)
    qp.add_plugin(qparser.PseudoFieldPlugin({"reverse": rev_text}))
    q = qp.parse(u("alfa reverse:bravo"))
    assert_equal(q.__unicode__(), '(content:alfa AND (reverse:bravo OR reverse:ovarb))')












