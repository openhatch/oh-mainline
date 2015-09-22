from nose.tools import assert_equal  #@UnresolvedImport

from whoosh import analysis, fields, query
from whoosh.compat import u, text_type
from whoosh.qparser import default
from whoosh.qparser import plugins


def test_whitespace():
    p = default.QueryParser("t", None, [plugins.WhitespacePlugin()])
    assert_equal(repr(p.tag("hello there amiga")), "<AndGroup <None:'hello'>, < >, <None:'there'>, < >, <None:'amiga'>>")

def test_singlequotes():
    p = default.QueryParser("t", None, [plugins.WhitespacePlugin(),
                                        plugins.SingleQuotePlugin()])
    assert_equal(repr(p.process("a 'b c' d")), "<AndGroup <None:'a'>, <None:'b c'>, <None:'d'>>")

def test_prefix():
    p = default.QueryParser("t", None, [plugins.WhitespacePlugin(),
                                        plugins.PrefixPlugin()])
    assert_equal(repr(p.process("a b* c")), "<AndGroup <None:'a'>, <None:'b'*>, <None:'c'>>")

def test_wild():
    p = default.QueryParser("t", None, [plugins.WhitespacePlugin(),
                                        plugins.WildcardPlugin()])
    assert_equal(repr(p.process("a b*c? d")), "<AndGroup <None:'a'>, <None:Wild 'b*c?'>, <None:'d'>>")

def test_range():
    p = default.QueryParser("t", None, [plugins.WhitespacePlugin(),
                                        plugins.RangePlugin()])
    ns = p.tag("a [b to c} d")
    assert_equal(repr(ns), "<AndGroup <None:'a'>, < >, <None:['b' 'c'}>, < >, <None:'d'>>")

    assert_equal(repr(p.process("a {b to]")), "<AndGroup <None:'a'>, <None:{'b' None]>>")
    assert_equal(repr(p.process("[to c] d")), "<AndGroup <None:[None 'c']>, <None:'d'>>")
    assert_equal(repr(p.process("[to]")), "<AndGroup <None:[None None]>>")

def test_sq_range():
    p = default.QueryParser("t", None, [plugins.WhitespacePlugin(),
                                        plugins.SingleQuotePlugin(),
                                        plugins.RangePlugin()])
    assert_equal(repr(p.process("['a b' to ']']")), "<AndGroup <None:['a b' ']']>>")

def test_phrase():
    p = default.QueryParser("t", None, [plugins.WhitespacePlugin(),
                                        plugins.PhrasePlugin()])
    assert_equal(repr(p.process('a "b c"')), "<AndGroup <None:'a'>, <None:PhraseNode 'b c'~1>>")
    assert_equal(repr(p.process('"b c" d')), "<AndGroup <None:PhraseNode 'b c'~1>, <None:'d'>>")
    assert_equal(repr(p.process('"b c"')), "<AndGroup <None:PhraseNode 'b c'~1>>")

def test_groups():
    p = default.QueryParser("t", None, [plugins.WhitespacePlugin(),
                                        plugins.GroupPlugin()])

    ns = p.process("a ((b c) d) e")
    assert_equal(repr(ns), "<AndGroup <None:'a'>, <AndGroup <AndGroup <None:'b'>, <None:'c'>>, <None:'d'>>, <None:'e'>>")

def test_fieldnames():
    p = default.QueryParser("t", None, [plugins.WhitespacePlugin(),
                                        plugins.FieldsPlugin(),
                                        plugins.GroupPlugin()])
    ns = p.process("a:b c d:(e f:(g h)) i j:")
    assert_equal(repr(ns), "<AndGroup <'a':'b'>, <None:'c'>, <AndGroup <'d':'e'>, <AndGroup <'f':'g'>, <'f':'h'>>>, <None:'i'>, <None:'j:'>>")
    assert_equal(repr(p.process("a:b:")), "<AndGroup <'a':'b:'>>")

def test_operators():
    p = default.QueryParser("t", None, [plugins.WhitespacePlugin(),
                                        plugins.OperatorsPlugin()])
    ns = p.process("a OR b")
    assert_equal(repr(ns), "<AndGroup <OrGroup <None:'a'>, <None:'b'>>>")

def test_boost():
    p = default.QueryParser("t", None, [plugins.WhitespacePlugin(),
                                        plugins.GroupPlugin(),
                                        plugins.BoostPlugin()])
    ns = p.tag("a^3")
    assert_equal(repr(ns), "<AndGroup <None:'a'>, <^ 3.0>>")
    ns = p.filterize(ns)
    assert_equal(repr(ns), "<AndGroup <None:'a' ^3.0>>")

    assert_equal(repr(p.process("a (b c)^2.5")), "<AndGroup <None:'a'>, <AndGroup <None:'b'>, <None:'c'> ^2.5>>")
    assert_equal(repr(p.process("a (b c)^.5 d")), "<AndGroup <None:'a'>, <AndGroup <None:'b'>, <None:'c'> ^0.5>, <None:'d'>>")
    assert_equal(repr(p.process("^2 a")), "<AndGroup <None:'^2'>, <None:'a'>>")
    assert_equal(repr(p.process("a^2^3")), "<AndGroup <None:'a^2' ^3.0>>")


#

def test_empty_querystring():
    s = fields.Schema(content=fields.TEXT, title=fields.TEXT, id=fields.ID)
    qp = default.QueryParser("content", s)
    q = qp.parse(u(""))
    assert_equal(q, query.NullQuery)

def test_fields():
    s = fields.Schema(content=fields.TEXT, title=fields.TEXT, id=fields.ID)
    qp = default.QueryParser("content", s)
    q = qp.parse(u("test"))
    assert_equal(q.__class__, query.Term)
    assert_equal(q.fieldname, "content")
    assert_equal(q.text, "test")

    mq = default.MultifieldParser(("title", "content"), s)
    q = mq.parse(u("test"))
    assert_equal(q.__class__, query.Or)
    assert_equal(q[0].__class__, query.Term)
    assert_equal(q[1].__class__, query.Term)
    assert_equal(q[0].fieldname, "title")
    assert_equal(q[1].fieldname, "content")
    assert_equal(q[0].text, "test")
    assert_equal(q[1].text, "test")

    q = mq.parse(u("title:test"))
    assert_equal(q.__class__, query.Term)
    assert_equal(q.fieldname, "title")
    assert_equal(q.text, "test")

def test_multifield():
    schema = fields.Schema(content=fields.TEXT, title=fields.TEXT,
                           cat=fields.KEYWORD, date=fields.DATETIME)

    qs = u("a (b c cat:d) OR (b c cat:e)")
    qp = default.MultifieldParser(['x', 'y'], schema)

    q = qp.parse(qs)
    assert_equal(text_type(q), "((x:a OR y:a) AND (((x:b OR y:b) AND (x:c OR y:c) AND cat:d) OR ((x:b OR y:b) AND (x:c OR y:c) AND cat:e)))")

def test_fieldname_chars():
    s = fields.Schema(abc123=fields.TEXT, nisbah=fields.KEYWORD)
    qp = default.QueryParser("content", s)
    fieldmap = {'nisbah': [u('\u0646\u0633\u0628\u0629')],
                'abc123': ['xyz']}
    qp.add_plugin(plugins.FieldAliasPlugin(fieldmap))

    q = qp.parse(u("abc123:456"))
    assert_equal(q.__class__, query.Term)
    assert_equal(q.fieldname, u('abc123'))
    assert_equal(q.text, u('456'))

    q = qp.parse(u("abc123:456 def"))
    assert_equal(text_type(q), u("(abc123:456 AND content:def)"))

    q = qp.parse(u('\u0646\u0633\u0628\u0629:\u0627\u0644\u0641\u0644\u0633\u0637\u064a\u0646\u064a'))
    assert_equal(q.__class__, query.Term)
    assert_equal(q.fieldname, u('nisbah'))
    assert_equal(q.text, u('\u0627\u0644\u0641\u0644\u0633\u0637\u064a\u0646\u064a'))

    q = qp.parse(u("abc123 (xyz:123 OR qrs)"))
    assert_equal(text_type(q), "(content:abc123 AND (abc123:123 OR content:qrs))")

def test_colonspace():
    s = fields.Schema(content=fields.TEXT, url=fields.ID)
    qp = default.QueryParser("content", s)
    q = qp.parse(u("url:test"))
    assert_equal(q.__class__, query.Term)
    assert_equal(q.fieldname, "url")
    assert_equal(q.text, "test")

    q = qp.parse(u("url: test"))
    assert_equal(q.__class__, query.And)
    assert_equal(q[0].__class__, query.Term)
    assert_equal(q[1].__class__, query.Term)
    assert_equal(q[0].fieldname, "content")
    assert_equal(q[1].fieldname, "content")
    assert_equal(q[0].text, "url")
    assert_equal(q[1].text, "test")

    q = qp.parse(u("url:"))
    assert_equal(q.__class__, query.Term)
    assert_equal(q.fieldname, "content")
    assert_equal(q.text, "url")

    s = fields.Schema(foo=fields.KEYWORD)
    qp = default.QueryParser("foo", s)
    q = qp.parse(u("blah:"))
    assert_equal(q.__class__, query.Term)
    assert_equal(q.fieldname, "foo")
    assert_equal(q.text, "blah:")

def test_andor():
    qp = default.QueryParser("a", None)
    q = qp.parse("a AND b OR c AND d OR e AND f")
    assert_equal(text_type(q), "((a:a AND a:b) OR (a:c AND a:d) OR (a:e AND a:f))")

    q = qp.parse("aORb")
    assert_equal(q, query.Term("a", "aORb"))

    q = qp.parse("aOR b")
    assert_equal(q, query.And([query.Term("a", "aOR"), query.Term("a", "b")]))

    q = qp.parse("a ORb")
    assert_equal(q, query.And([query.Term("a", "a"), query.Term("a", "ORb")]))

    assert_equal(qp.parse("OR"), query.Term("a", "OR"))

def test_andnot():
    qp = default.QueryParser("content", None)
    q = qp.parse(u("this ANDNOT that"))
    assert_equal(q.__class__, query.AndNot)
    assert_equal(q.a.__class__, query.Term)
    assert_equal(q.b.__class__, query.Term)
    assert_equal(q.a.text, "this")
    assert_equal(q.b.text, "that")

    q = qp.parse(u("foo ANDNOT bar baz"))
    assert_equal(q.__class__, query.And)
    assert_equal(len(q), 2)
    assert_equal(q[0].__class__, query.AndNot)
    assert_equal(q[1].__class__, query.Term)

    q = qp.parse(u("foo fie ANDNOT bar baz"))
    assert_equal(q.__class__, query.And)
    assert_equal(len(q), 3)
    assert_equal(q[0].__class__, query.Term)
    assert_equal(q[1].__class__, query.AndNot)
    assert_equal(q[2].__class__, query.Term)

    q = qp.parse(u("a AND b ANDNOT c"))
    assert_equal(q.__class__, query.AndNot)
    assert_equal(text_type(q), "((content:a AND content:b) ANDNOT content:c)")

def test_boost_query():
    qp = default.QueryParser("content", None)
    q = qp.parse(u("this^3 fn:that^0.5 5.67 hi^5x"))
    assert_equal(q[0].boost, 3.0)
    assert_equal(q[1].boost, 0.5)
    assert_equal(q[1].fieldname, "fn")
    assert_equal(q[2].text, "5.67")
    assert_equal(q[3].text, "hi^5x")

    q = qp.parse("alfa (bravo OR charlie)^2.5 ^3")
    assert_equal(len(q), 3)
    assert_equal(q[0].boost, 1.0)
    assert_equal(q[1].boost, 2.5)
    assert_equal(q[2].text, "^3")

def test_boosts():
    qp = default.QueryParser("t", None)
    q = qp.parse("alfa ((bravo^2)^3)^4 charlie")
    assert_equal(q.__unicode__(), "(t:alfa AND t:bravo^24.0 AND t:charlie)")

def test_wildcard1():
    qp = default.QueryParser("content", None)
    q = qp.parse(u("hello *the?e* ?star*s? test"))
    assert_equal(len(q), 4)
    assert_equal(q[0].__class__, query.Term)
    assert_equal(q[0].text, "hello")
    assert_equal(q[1].__class__, query.Wildcard)
    assert_equal(q[1].text, "*the?e*")
    assert_equal(q[2].__class__, query.Wildcard)
    assert_equal(q[2].text, "?star*s?")
    assert_equal(q[3].__class__, query.Term)
    assert_equal(q[3].text, "test")

def test_wildcard2():
    qp = default.QueryParser("content", None)
    q = qp.parse(u("*the?e*"))
    assert_equal(q.__class__, query.Wildcard)
    assert_equal(q.text, "*the?e*")

def test_parse_fieldname_underscores():
    s = fields.Schema(my_name=fields.ID(stored=True), my_value=fields.TEXT)
    qp = default.QueryParser("my_value", schema=s)
    q = qp.parse(u("my_name:Green"))
    assert_equal(q.__class__, query.Term)
    assert_equal(q.fieldname, "my_name")
    assert_equal(q.text, "Green")

def test_endstar():
    qp = default.QueryParser("text", None)
    q = qp.parse(u("word*"))
    assert_equal(q.__class__, query.Prefix)
    assert_equal(q.text, "word")

    q = qp.parse(u("first* second"))
    assert_equal(q[0].__class__, query.Prefix)
    assert_equal(q[0].text, "first")

def test_singlequotes_query():
    qp = default.QueryParser("text", None)
    q = qp.parse("hell's hot 'i stab at thee'")
    assert_equal(q.__class__.__name__, 'And')
    assert_equal(len(q), 3)
    assert_equal(q[0].__class__, query.Term)
    assert_equal(q[1].__class__, query.Term)
    assert_equal(q[2].__class__, query.Term)
    assert_equal(q[0].text, "hell's")
    assert_equal(q[1].text, "hot")
    assert_equal(q[2].text, "i stab at thee")

    q = qp.parse("alfa zulu:'bravo charlie' delta")
    assert_equal(q.__class__.__name__, 'And')
    assert_equal(len(q), 3)
    assert_equal(q[0].__class__, query.Term)
    assert_equal(q[1].__class__, query.Term)
    assert_equal(q[2].__class__, query.Term)
    assert_equal((q[0].fieldname, q[0].text), ("text", "alfa"))
    assert_equal((q[1].fieldname, q[1].text), ("zulu", "bravo charlie"))
    assert_equal((q[2].fieldname, q[2].text), ("text", "delta"))

    q = qp.parse("The rest 'is silence")
    assert_equal(q.__class__, query.And)
    assert_equal(len(q), 4)
    assert_equal([t.text for t in q.subqueries], ["The", "rest", "'is" , "silence"])

    q = qp.parse("I don't like W's stupid face")
    assert_equal(q.__class__, query.And)
    assert_equal(len(q), 6)
    assert_equal([t.text for t in q.subqueries], ["I", "don't", "like" , "W's", "stupid", "face"])

    q = qp.parse("I forgot the drinkin' in '98")
    assert_equal(q.__class__, query.And)
    assert_equal(len(q), 6)
    assert_equal([t.text for t in q.subqueries], ["I", "forgot", "the" , "drinkin'", "in", "'98"])

#    def test_escaping():
#        qp = default.QueryParser("text", None)
#        
#        q = qp.parse(r'big\small')
#        assert q.__class__, query.Term, q)
#        assert q.text, "bigsmall")
#        
#        q = qp.parse(r'big\\small')
#        assert q.__class__, query.Term)
#        assert q.text, r'big\small')
#        
#        q = qp.parse(r'http\:example')
#        assert q.__class__, query.Term)
#        assert q.fieldname, "text")
#        assert q.text, "http:example")
#        
#        q = qp.parse(r'hello\ there')
#        assert q.__class__, query.Term)
#        assert q.text, "hello there")
#        
#        q = qp.parse(r'\[start\ TO\ end\]')
#        assert q.__class__, query.Term)
#        assert q.text, "[start TO end]")
#    
#        schema = fields.Schema(text=fields.TEXT)
#        qp = default.QueryParser("text", None)
#        q = qp.parse(r"http\:\/\/www\.example\.com")
#        assert q.__class__, query.Term)
#        assert q.text, "http://www.example.com")
#        
#        q = qp.parse(u("\u005c\u005c"))
#        assert q.__class__, query.Term)
#        assert q.text, "\\")

#    def test_escaping_wildcards():
#        qp = default.QueryParser("text", None)
#        
#        q = qp.parse(u("a*b*c?d"))
#        assert q.__class__, query.Wildcard)
#        assert q.text, "a*b*c?d")
#        
#        q = qp.parse(u("a*b\u005c*c?d"))
#        assert q.__class__, query.Wildcard)
#        assert q.text, "a*b*c?d")
#        
#        q = qp.parse(u("a*b\u005c\u005c*c?d"))
#        assert q.__class__, query.Wildcard)
#        assert q.text, u('a*b\u005c*c?d'))
#        
#        q = qp.parse(u("ab*"))
#        assert q.__class__, query.Prefix)
#        assert q.text, u("ab"))
#        
#        q = qp.parse(u("ab\u005c\u005c*"))
#        assert q.__class__, query.Wildcard)
#        assert q.text, u("ab\u005c*"))

def test_phrase_phrase():
    qp = default.QueryParser("content", None)
    q = qp.parse('"alfa bravo" "charlie delta echo"^2.2 test:"foxtrot golf"')
    assert_equal(q[0].__class__, query.Phrase)
    assert_equal(q[0].words, ["alfa", "bravo"])
    assert_equal(q[1].__class__, query.Phrase)
    assert_equal(q[1].words, ["charlie", "delta", "echo"])
    assert_equal(q[1].boost, 2.2)
    assert_equal(q[2].__class__, query.Phrase)
    assert_equal(q[2].words, ["foxtrot", "golf"])
    assert_equal(q[2].fieldname, "test")

def test_weird_characters():
    qp = default.QueryParser("content", None)
    q = qp.parse(u(".abcd@gmail.com"))
    assert_equal(q.__class__, query.Term)
    assert_equal(q.text, ".abcd@gmail.com")
    q = qp.parse(u("r*"))
    assert_equal(q.__class__, query.Prefix)
    assert_equal(q.text, "r")
    q = qp.parse(u("."))
    assert_equal(q.__class__, query.Term)
    assert_equal(q.text, ".")
    q = qp.parse(u("?"))
    assert_equal(q.__class__, query.Wildcard)
    assert_equal(q.text, "?")

def test_euro_chars():
    schema = fields.Schema(text=fields.TEXT)
    qp = default.QueryParser("text", schema)
    q = qp.parse(u("stra\xdfe"))
    assert_equal(q.__class__, query.Term)
    assert_equal(q.text, u("stra\xdfe"))

def test_star():
    schema = fields.Schema(text=fields.TEXT(stored=True))
    qp = default.QueryParser("text", schema)
    q = qp.parse(u("*"))
    assert_equal(q.__class__, query.Every)
    assert_equal(q.fieldname, "text")

    q = qp.parse(u("*h?ll*"))
    assert_equal(q.__class__, query.Wildcard)
    assert_equal(q.text, "*h?ll*")

    q = qp.parse(u("h?pe"))
    assert_equal(q.__class__, query.Wildcard)
    assert_equal(q.text, "h?pe")

    q = qp.parse(u("*? blah"))
    assert_equal(q.__class__, query.And)
    assert_equal(q[0].__class__, query.Wildcard)
    assert_equal(q[0].text, "*?")
    assert_equal(q[1].__class__, query.Term)
    assert_equal(q[1].text, "blah")

    q = qp.parse(u("*ending"))
    assert_equal(q.__class__, query.Wildcard)
    assert_equal(q.text, "*ending")

    q = qp.parse(u("*q"))
    assert_equal(q.__class__, query.Wildcard)
    assert_equal(q.text, "*q")

def test_star_field():
    schema = fields.Schema(text=fields.TEXT)
    qp = default.QueryParser("text", schema)

    q = qp.parse(u("*:*"))
    assert_equal(q.__class__, query.Every)
    assert_equal(q.fieldname, None)

    # This gets parsed to a term with text="*:test" which is then analyzed down
    # to just "test"
    q = qp.parse(u("*:test"))
    assert_equal(q.__class__, query.Term)
    assert_equal(q.fieldname, "text")
    assert_equal(q.text, "test")

def test_range_query():
    schema = fields.Schema(name=fields.ID(stored=True), text=fields.TEXT(stored=True))
    qp = default.QueryParser("text", schema)

    q = qp.parse(u("[alfa to bravo}"))
    assert_equal(q.__class__, query.TermRange)
    assert_equal(q.start, "alfa")
    assert_equal(q.end, "bravo")
    assert_equal(q.startexcl, False)
    assert_equal(q.endexcl, True)

    q = qp.parse(u("['hello there' to 'what ever']"))
    assert_equal(q.__class__, query.TermRange)
    assert_equal(q.start, "hello there")
    assert_equal(q.end, "what ever")
    assert_equal(q.startexcl, False)
    assert_equal(q.endexcl, False)

    q = qp.parse(u("name:{'to' to 'b'}"))
    assert_equal(q.__class__, query.TermRange)
    assert_equal(q.start, "to")
    assert_equal(q.end, "b")
    assert_equal(q.startexcl, True)
    assert_equal(q.endexcl, True)

    q = qp.parse(u("name:{'a' to 'to']"))
    assert_equal(q.__class__, query.TermRange)
    assert_equal(q.start, "a")
    assert_equal(q.end, "to")
    assert_equal(q.startexcl, True)
    assert_equal(q.endexcl, False)

    q = qp.parse(u("name:[a to to]"))
    assert_equal(q.__class__, query.TermRange)
    assert_equal(q.start, "a")
    assert_equal(q.end, "to")

    q = qp.parse(u("name:[to to b]"))
    assert_equal(q.__class__, query.TermRange)
    assert_equal(q.start, "to")
    assert_equal(q.end, "b")

    q = qp.parse(u("[alfa to alfa]"))
    assert_equal(q.__class__, query.Term)
    assert_equal(q.text, "alfa")

    q = qp.parse(u("Ind* AND name:[d TO]"))
    assert_equal(q.__class__, query.And)
    assert_equal(q[0].__class__, query.Prefix)
    assert_equal(q[1].__class__, query.TermRange)
    assert_equal(q[0].text, "ind")
    assert_equal(q[1].start, "d")
    assert_equal(q[1].fieldname, "name")

    q = qp.parse(u("name:[d TO]"))
    assert_equal(q.__class__, query.TermRange)
    assert_equal(q.start, "d")
    assert_equal(q.fieldname, "name")

def test_numeric_range():
    schema = fields.Schema(id=fields.STORED, number=fields.NUMERIC)
    qp = default.QueryParser("number", schema)

    teststart = 40
    testend = 100

    q = qp.parse("[%s to *]" % teststart)
    assert_equal(q, query.NullQuery)

    q = qp.parse("[%s to]" % teststart)
    assert_equal(q.__class__, query.NumericRange)
    assert_equal(q.start, teststart)
    assert_equal(q.end, None)

    q = qp.parse("[to %s]" % testend)
    assert_equal(q.__class__, query.NumericRange)
    assert_equal(q.start, None)
    assert_equal(q.end, testend)

    q = qp.parse("[%s to %s]" % (teststart, testend))
    assert_equal(q.__class__, query.NumericRange)
    assert_equal(q.start, teststart)
    assert_equal(q.end, testend)

def test_regressions():
    qp = default.QueryParser("f", None)

    # From 0.3.18, these used to require escaping. Mostly good for
    # regression testing.
    assert_equal(qp.parse(u("re-inker")), query.Term("f", "re-inker"))
    assert_equal(qp.parse(u("0.7 wire")), query.And([query.Term("f", "0.7"), query.Term("f", "wire")]))
    assert (qp.parse(u("daler-rowney pearl 'bell bronze'"))
            == query.And([query.Term("f", "daler-rowney"),
                          query.Term("f", "pearl"),
                          query.Term("f", "bell bronze")]))

    q = qp.parse(u('22" BX'))
    assert_equal(q, query.And([query.Term("f", '22"'), query.Term("f", "BX")]))

def test_empty_ranges():
    schema = fields.Schema(name=fields.TEXT, num=fields.NUMERIC,
                           date=fields.DATETIME)
    qp = default.QueryParser("text", schema)

    for fname in ("name", "date"):
        q = qp.parse(u("%s:[to]") % fname)
        assert_equal(q.__class__, query.Every)

def test_empty_numeric_range():
    schema = fields.Schema(id=fields.ID, num=fields.NUMERIC)
    qp = default.QueryParser("num", schema)
    q = qp.parse("num:[to]")
    assert_equal(q.__class__, query.NumericRange)
    assert_equal(q.start, None)
    assert_equal(q.end, None)

def test_nonexistant_fieldnames():
    # Need an analyzer that won't mangle a URL
    a = analysis.SimpleAnalyzer("\\S+")
    schema = fields.Schema(id=fields.ID, text=fields.TEXT(analyzer=a))

    qp = default.QueryParser("text", schema)
    q = qp.parse(u("id:/code http://localhost/"))
    assert_equal(q.__class__, query.And)
    assert_equal(q[0].__class__, query.Term)
    assert_equal(q[0].fieldname, "id")
    assert_equal(q[0].text, "/code")
    assert_equal(q[1].__class__, query.Term)
    assert_equal(q[1].fieldname, "text")
    assert_equal(q[1].text, "http://localhost/")

def test_stopped():
    schema = fields.Schema(text=fields.TEXT)
    qp = default.QueryParser("text", schema)
    q = qp.parse(u("a b"), debug=True)
    assert_equal(q, query.NullQuery)

def test_analyzing_terms():
    schema = fields.Schema(text=fields.TEXT(analyzer=analysis.StemmingAnalyzer()))
    qp = default.QueryParser("text", schema)
    q = qp.parse(u("Indexed!"))
    assert_equal(q.__class__, query.Term)
    assert_equal(q.text, "index")

def test_simple():
    parser = default.SimpleParser("x", None)
    q = parser.parse(u("alfa bravo charlie delta"))
    assert_equal(text_type(q), "(x:alfa OR x:bravo OR x:charlie OR x:delta)")

    q = parser.parse(u("alfa +bravo charlie delta"))
    assert_equal(text_type(q), "(x:bravo ANDMAYBE (x:alfa OR x:charlie OR x:delta))")

    q = parser.parse(u("alfa +bravo -charlie delta"))
    assert_equal(text_type(q), "((x:bravo ANDMAYBE (x:alfa OR x:delta)) ANDNOT x:charlie)")

    q = parser.parse(u("- alfa +bravo + delta"))
    assert_equal(text_type(q), "((x:bravo AND x:delta) ANDNOT x:alfa)")

def test_dismax():
    parser = default.DisMaxParser({"body": 0.8, "title": 2.5}, None)
    q = parser.parse(u("alfa bravo charlie"))
    assert_equal(text_type(q), "(DisMax(body:alfa^0.8 title:alfa^2.5) OR DisMax(body:bravo^0.8 title:bravo^2.5) OR DisMax(body:charlie^0.8 title:charlie^2.5))")

    q = parser.parse(u("alfa +bravo charlie"))
    assert_equal(text_type(q), "(DisMax(body:bravo^0.8 title:bravo^2.5) ANDMAYBE (DisMax(body:alfa^0.8 title:alfa^2.5) OR DisMax(body:charlie^0.8 title:charlie^2.5)))")

    q = parser.parse(u("alfa -bravo charlie"))
    assert_equal(text_type(q), "((DisMax(body:alfa^0.8 title:alfa^2.5) OR DisMax(body:charlie^0.8 title:charlie^2.5)) ANDNOT DisMax(body:bravo^0.8 title:bravo^2.5))")

    q = parser.parse(u("alfa -bravo +charlie"))
    assert_equal(text_type(q), "((DisMax(body:charlie^0.8 title:charlie^2.5) ANDMAYBE DisMax(body:alfa^0.8 title:alfa^2.5)) ANDNOT DisMax(body:bravo^0.8 title:bravo^2.5))")

def test_many_clauses():
    qs = "1" + (" OR 1" * 1000)

    parser = default.QueryParser("content", None)
    parser.parse(qs)

def test_roundtrip():
    parser = default.QueryParser("a", None)
    q = parser.parse(u("a OR ((b AND c AND d AND e) OR f OR g) ANDNOT h"))
    assert_equal(text_type(q), "((a:a OR (a:b AND a:c AND a:d AND a:e) OR a:f OR a:g) ANDNOT a:h)")

def test_ngrams():
    schema = fields.Schema(grams=fields.NGRAM)
    parser = default.QueryParser('grams', schema)
    parser.remove_plugin_class(plugins.WhitespacePlugin)

    q = parser.parse(u("Hello There"))
    assert_equal(q.__class__, query.And)
    assert_equal(len(q), 8)
    assert_equal([sq.text for sq in q], ["hell", "ello", "llo ", "lo t", "o th", " the", "ther", "here"])

def test_ngramwords():
    schema = fields.Schema(grams=fields.NGRAMWORDS(queryor=True))
    parser = default.QueryParser('grams', schema)

    q = parser.parse(u("Hello Tom"))
    assert_equal(q.__class__, query.And)
    assert_equal(q[0].__class__, query.Or)
    assert_equal(q[1].__class__, query.Term)
    assert_equal(q[0][0].text, "hell")
    assert_equal(q[0][1].text, "ello")
    assert_equal(q[1].text, "tom")

def test_multitoken_default():
    textfield = fields.TEXT()
    assert textfield.multitoken_query == "default"
    schema = fields.Schema(text=textfield)
    parser = default.QueryParser('text', schema)
    qstring = u("chaw-bacon")

    texts = list(schema["text"].process_text(qstring))
    assert_equal(texts, ["chaw", "bacon"])

    q = parser.parse(qstring)
    assert_equal(q.__class__, query.And)
    assert_equal(len(q), 2)
    assert_equal(q[0].__class__, query.Term)
    assert_equal(q[0].text, "chaw")
    assert_equal(q[1].__class__, query.Term)
    assert_equal(q[1].text, "bacon")

def test_multitoken_or():
    textfield = fields.TEXT()
    textfield.multitoken_query = "or"
    schema = fields.Schema(text=textfield)
    parser = default.QueryParser('text', schema)
    qstring = u("chaw-bacon")

    texts = list(schema["text"].process_text(qstring))
    assert_equal(texts, ["chaw", "bacon"])

    q = parser.parse(qstring)
    assert_equal(q.__class__, query.Or)
    assert_equal(len(q), 2)
    assert_equal(q[0].__class__, query.Term)
    assert_equal(q[0].text, "chaw")
    assert_equal(q[1].__class__, query.Term)
    assert_equal(q[1].text, "bacon")

def test_multitoken_phrase():
    textfield = fields.TEXT()
    textfield.multitoken_query = "phrase"
    schema = fields.Schema(text=textfield)
    parser = default.QueryParser("text", schema)
    qstring = u("chaw-bacon")

    texts = list(schema["text"].process_text(qstring))
    assert_equal(texts, ["chaw", "bacon"])

    q = parser.parse(qstring)
    assert_equal(q.__class__, query.Phrase)

def test_singlequote_multitoken():
    schema = fields.Schema(text=fields.TEXT(multitoken_query="or"))
    parser = default.QueryParser("text", schema)
    q = parser.parse(u"foo bar")
    assert_equal(q.__unicode__(), "(text:foo AND text:bar)")

    q = parser.parse(u"'foo bar'")  # single quotes
    assert_equal(q.__unicode__(), "(text:foo OR text:bar)")

def test_operator_queries():
    qp = default.QueryParser("f", None)

    q = qp.parse("a AND b OR c AND d")
    assert_equal(text_type(q), "((f:a AND f:b) OR (f:c AND f:d))")

    q = qp.parse("a OR b OR c OR d")
    assert_equal(text_type(q), "(f:a OR f:b OR f:c OR f:d)")

    q = qp.parse("a ANDMAYBE b ANDNOT c REQUIRE d")
    assert_equal(text_type(q), "((f:a ANDMAYBE (f:b ANDNOT f:c)) REQUIRE f:d)")

#def test_associativity():
#    left_andmaybe = (syntax.InfixOperator("ANDMAYBE", syntax.AndMaybeGroup, True), 0)
#    right_andmaybe = (syntax.InfixOperator("ANDMAYBE", syntax.AndMaybeGroup, False), 0)
#    not_ = (syntax.PrefixOperator("NOT", syntax.NotGroup), 0)
#    
#    def make_parser(*ops):
#        parser = default.QueryParser("f", None)
#        parser.replace_plugin(plugins.CompoundsPlugin(ops, clean=True))
#        return parser
#    
#    p = make_parser(left_andmaybe)
#    q = p.parse("a ANDMAYBE b ANDMAYBE c ANDMAYBE d")
#    assert_equal(text_type(q), "(((f:a ANDMAYBE f:b) ANDMAYBE f:c) ANDMAYBE f:d)")
#    
#    p = make_parser(right_andmaybe)
#    q = p.parse("a ANDMAYBE b ANDMAYBE c ANDMAYBE d")
#    assert_equal(text_type(q), "(f:a ANDMAYBE (f:b ANDMAYBE (f:c ANDMAYBE f:d)))")
#    
#    p = make_parser(not_)
#    q = p.parse("a NOT b NOT c NOT d", normalize=False)
#    assert_equal(text_type(q), "(f:a AND NOT f:b AND NOT f:c AND NOT f:d)")
#    
#    p = make_parser(left_andmaybe)
#    q = p.parse("(a ANDMAYBE b) ANDMAYBE (c ANDMAYBE d)")
#    assert_equal(text_type(q), "((f:a ANDMAYBE f:b) ANDMAYBE (f:c ANDMAYBE f:d))")
#    
#    p = make_parser(right_andmaybe)
#    q = p.parse("(a ANDMAYBE b) ANDMAYBE (c ANDMAYBE d)")
#    assert_equal(text_type(q), "((f:a ANDMAYBE f:b) ANDMAYBE (f:c ANDMAYBE f:d))")

def test_not_assoc():
    qp = default.QueryParser("text", None)
    q = qp.parse(u("a AND NOT b OR c"))
    assert_equal(text_type(q), "((text:a AND NOT text:b) OR text:c)")

    qp = default.QueryParser("text", None)
    q = qp.parse(u("a NOT (b OR c)"))
    assert_equal(text_type(q), "(text:a AND NOT (text:b OR text:c))")

def test_fieldname_space():
    qp = default.QueryParser("a", None)
    q = qp.parse("Man Ray: a retrospective")
    assert_equal(text_type(q), "(a:Man AND a:Ray: AND a:a AND a:retrospective)")

def test_fieldname_fieldname():
    qp = default.QueryParser("a", None)
    q = qp.parse("a:b:")
    assert_equal(q, query.Term("a", "b:"))

def test_paren_fieldname():
    schema = fields.Schema(kind=fields.ID, content=fields.TEXT)

    qp = default.QueryParser("content", schema)
    q = qp.parse(u("(kind:1d565 OR kind:7c584) AND (stuff)"))
    assert_equal(text_type(q), "((kind:1d565 OR kind:7c584) AND content:stuff)")

    q = qp.parse(u("kind:(1d565 OR 7c584) AND (stuff)"))
    assert_equal(text_type(q), "((kind:1d565 OR kind:7c584) AND content:stuff)")

def test_star_paren():
    qp = default.QueryParser("content", None)
    q = qp.parse(u("(*john*) AND (title:blog)"))

    assert_equal(q.__class__, query.And)
    assert_equal(q[0].__class__, query.Wildcard)
    assert_equal(q[1].__class__, query.Term)
    assert_equal(q[0].fieldname, "content")
    assert_equal(q[1].fieldname, "title")
    assert_equal(q[0].text, "*john*")
    assert_equal(q[1].text, "blog")

def test_dash():
    ana = analysis.StandardAnalyzer("[ \t\r\n()*?]+")
    schema = fields.Schema(title=fields.TEXT(analyzer=ana),
                           text=fields.TEXT(analyzer=ana), time=fields.ID)
    qtext = u("*Ben-Hayden*")

    qp = default.QueryParser("text", schema)
    q = qp.parse(qtext)
    assert_equal(repr(q), "Wildcard('text', u'*ben-hayden*')")

    qp = default.MultifieldParser(["title", "text", "time"], schema)
    q = qp.parse(qtext)
    assert_equal(repr(q), "Or([Wildcard('title', u'*ben-hayden*'), Wildcard('text', u'*ben-hayden*'), Wildcard('time', u'*Ben-Hayden*')])")


