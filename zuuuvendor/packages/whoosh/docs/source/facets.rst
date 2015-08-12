====================
Sorting and faceting
====================

.. note::
    The API for sorting and faceting changed in Whoosh 2.0.

Overview
========

Sorting and faceting search results in Whoosh is based on **facets**. Each
facet associates a value with each document in the search results, allowing you
to sort by the keys or use them group the documents. Whoosh includes a variety
of **facet types** you can use for sorting and grouping (see below).


Sorting
=======

By default, the results of a search are sorted with the highest-scoring
documents first. You can use the ``sortedby`` keyword argument to order the
results by some other criteria instead, such as the value of a field.


A note about sorting by fields
------------------------------

When sorting by fields, the **indexed terms** in the field are used as the
"value" to sort by, **not** the stored values. For example, take this index::

    schema = fields.Schema(title=fields.TEXT(stored=True))
    ix = index.create_in("indexdir", schema)
    w = ix.writer()
    w.add_document(title=u"Best Bet")
    w.add_document(title=u"First Action")
    w.commit()
    
If you sort this index by "title", you might expect the results to be
"Best Bet" followed by "First Action", but in fact it will be the reverse! This
is because Whoosh is sorting by **terms**, not the original text you indexed.
For fields with multiple terms, it just picks the (alphabetically) first one,
so the document containing "action" sorts before the one with "best".

For this reason, you don't want to sort by TEXT fields. Instad, you should set
up separate, single-term fields that you can sort by. You can duplicate content
if you want to be able to sort by the original value of a TEXT field::

    schema = fields.Schema(title=fields.TEXT(stored=True),
                           sort_title=fields.ID)
    ix = index.create_in("indexdir", schema)
    w = ix.writer()
    for title in titles:
        w.add_document(title=title, sort_title=title)
    w.commit()


The sortedby keyword argument
-----------------------------

You can use the following objects as ``sortedby`` values:

A ``FacetType`` object
    Uses this object to sort the documents. See below for the available facet
    types.

A field name string
    Converts the field name into a ``FieldFacet`` (see below) and uses it to
    sort the documents.

A list of ``FacetType`` objects and/or field name strings
    Bundles the facets together into a ``MultiFacet`` so you can sort by
    multiple keys. Note that this shortcut does not allow you to reverse
    the sort direction of individual facets. To do that, you need to construct
    the ``MultiFacet`` object yourself.

.. note::
    You can use the ``reverse=True`` keyword argument to the
    ``Searcher.search()`` method to reverse the overall sort direction. This
    is more efficient than reversing each individual facet.


Examples
--------

Sort by the value of the size field::

    results = searcher.search(myquery, sortedby="size")
    
Sort by the reverse (highest-to-lowest) order of the "price" field::

    facet = sorting.FieldFacet("price", reverse=True)
    results = searcher.search(myquery, sortedby=facet)

Sort by ascending size and then descending price::

    mf = sorting.MultiFacet()
    mf.add_field("size")
    mf.add_field("price", reverse=True)
    results = searcher.search(myquery, sortedby=mf)
    
    # or...
    sizes = sorting.FieldFacet("size")
    prices = sorting.FieldFacet("price", reverse=True)
    results = searcher.search(myquery, sortedby=[sizes, prices])
    
Sort by the "category" field, then by the document's score::

    cats = sorting.FieldFacet("category")
    scores = sorting.ScoreFacet()
    results = searcher.search(myquery, sortedby=[cats, scores])


Grouping
========

It is often very useful to present "faceted" search results to the user.
Faceting is dynamic grouping of search results into categories. The
categories let users view a slice of the total results based on the categories
they're interested in.

For example, if you are programming a shopping website, you might want to
display categories with the search results such as the manufacturers and price
ranges.

==================== =================
Manufacturer         Price
-------------------- -----------------
Apple (5)            $0 - $100 (2)
Sanyo (1)            $101 - $500 (10)          
Sony (2)             $501 - $1000 (1)
Toshiba (5)
==================== =================

You can let your users click the different facet values to only show results
in the given categories.

Another useful UI pattern is to show, say, the top 5 results for different
types of found documents, and let the user click to see more results from a
category they're interested in, similarly to how the Spotlight quick results
work on Mac OS X.


The groupedby keyword argument
------------------------------

You can use the following objects as ``groupedby`` values:

A ``FacetType`` object
    Uses this object to group the documents. See below for the available facet
    types.

A field name string
    Converts the field name into a ``FieldFacet`` (see below) and uses it to
    sort the documents. The name of the field is used as the facet name.

A list or tuple of field name strings
    Sets up multiple field grouping criteria.

A dictionary mapping facet names to FacetType objects
    Sets up multiple grouping criteria.

A ``Facets`` object
    This object is a lot like using a dictionary, but has some convenience
    methods to make setting up multiple groupings a little easier.


Examples
--------

Group by the value of the "category" field::

    results = searcher.search(myquery, groupedby="category")
    
Group by the value of the "category" field and also by the value of the "tags"
field and a date range::

    cats = sorting.FieldFacet("category")
    tags = sorting.FieldFacet("tags", allow_overlap=True)
    results = searcher.search(myquery, groupedby={"category": cats, "tags": tags})
    
    # ...or, using a Facets object has a little less duplication
    facets = sorting.Facets()
    facets.add_field("category")
    facets.add_field("tags", allow_overlap=True)
    results = searcher.search(myquery, groupedby=facets)

To group results by the *intersected values of multiple fields*, use a
``MultiFacet`` object (see below). For example, if you have two fields named
``tag`` and ``size``, you could group the results by all combinations of the
``tag`` and ``size`` field, such as ``('tag1', 'small')``,
``('tag2', 'small')``, ``('tag1', 'medium')``, and so on::

    # Generate a grouping from the combination of the "tag" and "size" fields
    mf = MultiField("tag", "size")
    results = searcher.search(myquery, groupedby={"tag/size": mf})


Getting the faceted groups
--------------------------

The ``Results.groups("facetname")`` method  returns a dictionary mapping
category names to lists of **document IDs**::

    myfacets = sorting.Facets().add_field("size").add_field("tag")
    results = mysearcher.search(myquery, groupedby=myfacets)
    results.groups("size")
    # {"small": [8, 5, 1, 2, 4], "medium": [3, 0, 6], "large": [7, 9]}

If there is only one facet, you can just use ``Results.groups()`` with no
argument to access its groups::

    results = mysearcher.search(myquery, groupedby=myfunctionfacet)
    results.groups()

By default, the values in the dictionary returned by ``groups()`` are lists of
document numbers in the same relative order as in the results. You can use the
``Searcher`` object's ``stored_fields()`` method to take a document number and
return the document's stored fields as a dictionary::

    for category_name in categories:
        print "Top 5 documents in the %s category" % category_name
        doclist = categories[category_name]
        for docnum, score in doclist[:5]:
            print "  ", searcher.stored_fields(docnum)
        if len(doclist) > 5:
            print "  (%s more)" % (len(doclist) - 5)

If you want different information about the groups, for example just the count
of documents in each group, or you don't need the groups to be ordered, you can
specify a :class:`whoosh.sorting.FacetMap` type or instance with the
``maptype`` keyword argument when creating the ``FacetType``::

    # This is the same as the default
    myfacet = FieldFacet("size", maptype=sorting.OrderedList)
    results = mysearcher.search(myquery, groupedby=myfacet)
    results.groups()
    # {"small": [8, 5, 1, 2, 4], "medium": [3, 0, 6], "large": [7, 9]}
    
    # Don't sort the groups to match the order of documents in the results
    # (faster)
    myfacet = FieldFacet("size", maptype=sorting.UnorderedList)
    results = mysearcher.search(myquery, groupedby=myfacet)
    results.groups()
    # {"small": [1, 2, 4, 5, 8], "medium": [0, 3, 6], "large": [7, 9]}

    # Only count the documents in each group
    myfacet = FieldFacet("size", maptype=sorting.Count)
    results = mysearcher.search(myquery, groupedby=myfacet)
    results.groups()
    # {"small": 5, "medium": 3, "large": 2}
    
    # Only remember the "best" document in each group
    myfacet = FieldFacet("size", maptype=sorting.Best)
    results = mysearcher.search(myquery, groupedby=myfacet)
    results.groups()
    # {"small": 8, "medium": 3, "large": 7}

Alternatively you can specify a ``maptype`` argument in the
``Searcher.search()`` method call which applies to all facets::

    results = mysearcher.search(myquery, groupedby=["size", "tag"],
                                maptype=sorting.Count)

(You can override this overall ``maptype`` argument on individual facets by
specifying the ``maptype`` argument for them as well.)


Facet types
===========

FieldFacet
----------

This is the most common facet type. It sorts or groups based on the
value in a certain field in each document. This generally works best
(or at all) if each document has only one term in the field (e.g. an ID
field)::

    # Sort search results by the value of the "path" field
    facet = sorting.FieldFacet("path")
    results = searcher.search(myquery, sortedby=facet)
    
    # Group search results by the value of the "parent" field
    facet = sorting.FieldFacet("parent")
    results = searcher.search(myquery, groupedby=facet)
    parent_groups = results.groups("parent")

By default, ``FieldFacet`` only supports **non-overlapping** grouping, where a
document cannot belong to multiple facets at the same time (each document will
be sorted into one category arbitrarily.) To get overlapping groups with
multi-valued fields, use the ``allow_overlap=True`` keyword argument::

    facet = sorting.FieldFacet(fieldname, allow_overlap=True)

This supports overlapping group membership where documents have more than one
term in a field (e.g. KEYWORD fields). If you don't need overlapping, don't
use ``allow_overlap`` because it's *much* slower and uses more memory (see
the secion on ``allow_overlap`` below.


QueryFacet
----------

You can set up categories defined by arbitrary queries. For example, you can
group names using prefix queries::

    # Use queries to define each category
    # (Here I'll assume "price" is a NUMERIC field, so I'll use
    # NumericRange)
    qdict = {}
    qdict["A-D"] = query.TermRange("name", "a", "d")
    qdict["E-H"] = query.TermRange("name", "e", "h")
    qdict["I-L"] = query.TermRange("name", "i", "l")
    # ...
    
    qfacet = sorting.QueryFacet(qdict)
    r = searcher.search(myquery, groupedby={"firstltr": qfacet})
    
By default, ``QueryFacet`` only supports **non-overlapping** grouping, where a
document cannot belong to multiple facets at the same time (each document will
be sorted into one category arbitrarily.) To get overlapping groups with
multi-valued fields, use the ``allow_overlap=True`` keyword argument::

    facet = sorting.QueryFacet(querydict, allow_overlap=True)


RangeFacet
----------

The ``RangeFacet`` is for NUMERIC field types. It divides a range of possible
values into groups. For example, to group documents based on price into
buckets $100 "wide"::

    pricefacet = sorting.RangeFacet("price", 0, 1000, 100)
    
The first argument is the name of the field. The next two arguments are the
full range to be divided. Value outside this range (in this example, values
below 0 and above 1000) will be sorted into the "missing" (None) group. The
fourth argument is the "gap size", the size of the divisions in the range.

The "gap" can be a list instead of a single value. In that case, the values in
the list will be used to set the size of the initial divisions, with the last
value in the list being the size for all subsequent divisions. For example::

    pricefacet = sorting.RangeFacet("price", 0, 1000, [5, 10, 35, 50])
    
...will set up divisions of 0-5, 5-15, 15-50, 50-100, and then use 50 as the
size for all subsequent divisions (i.e. 100-150, 150-200, and so on).

The ``hardend`` keyword argument controls whether the last division is clamped
to the end of the range or allowed to go past the end of the range. For
example, this::

    facet = sorting.RangeFacet("num", 0, 10, 4, hardend=False)
    
...gives divisions 0-4, 4-8, and 8-12, while this::

    facet = sorting.RangeFacet("num", 0, 10, 4, hardend=True)
    
...gives divisions 0-4, 4-8, and 8-10. (The default is ``hardend=False``.)

.. note::
    The ranges/buckets are always **inclusive** at the start and **exclusive**
    at the end.


DateRangeFacet
--------------

This is like ``RangeFacet`` but for DATETIME fields. The start and end values
must be ``datetime.datetime`` objects, and the gap(s) is/are
``datetime.timedelta`` objects.

For example::

    from datetime import datetime, timedelta

    start = datetime(2000, 1, 1)
    end = datetime.now()
    gap = timedelta(days=365)
    bdayfacet = sorting.DateRangeFacet("birthday", start, end, gap)

As with ``RangeFacet``, you can use a list of gaps and the ``hardend`` keyword
argument.


ScoreFacet
----------

This facet is sometimes useful for sorting.

For example, to sort by the "category" field, then for documents with the same
category, sort by the document's score::

    cats = sorting.FieldFacet("category")
    scores = sorting.ScoreFacet()
    results = searcher.search(myquery, sortedby=[cats, scores])

The ``ScoreFacet`` always sorts higher scores before lower scores.

.. note::
    While using ``sortedby=ScoreFacet()`` should give the same results as using
    the default scored ordering (``sortedby=None``), using the facet will be
    slower because Whoosh automatically turns off many optimizations when
    sorting.


FunctionFacet
-------------

This facet lets you pass a custom function to compute the sorting/grouping key
for documents. (Using this facet type may be easier than subclassing FacetType
and Categorizer to set up some custom behavior.)

The function will be called with the index searcher and index document ID as
arguments. For example, if you have an index with term vectors::

    schema = fields.Schema(id=fields.STORED,
                           text=fields.TEXT(stored=True, vector=True))
    ix = RamStorage().create_index(schema)
    
...you could use a function to sort documents higher the closer they are to
having equal occurances of two terms:: 
    
    def fn(searcher, docnum):
        v = dict(searcher.vector_as("frequency", docnum, "text"))
        # Sort documents that have equal number of "alfa" and "bravo" first
        return 0 - (1.0 / (abs(v.get("alfa", 0) - v.get("bravo", 0)) + 1.0))

    facet = sorting.FunctionFacet(fn)
    results = searcher.search(myquery, sortedby=facet)


StoredFieldFacet
----------------

This facet lets you use stored field values as the sorting/grouping key for
documents. This is usually slower than using an indexed field, but when using
``allow_overlap`` it can actually be faster for large indexes just because it
avoids the overhead of reading posting lists.

:class:`~whoosh.sorting.StoredFieldFacet` supports ``allow_overlap`` by
splitting the stored value into separate keys. By default it calls the value's
``split()`` method (since most stored values are strings), but you can supply
a custom split function. See the section on ``allow_overlap`` below.


MultiFacet
==========

This facet type returns a composite of the keys returned by two or more
sub-facets, allowing you to sort/group by the intersected values of multiple
facets.

``MultiFacet`` has methods for adding facets::

    myfacet = sorting.RangeFacet(0, 1000, 10)

    mf = sorting.MultiFacet()
    mf.add_field("category")
    mf.add_field("price", reverse=True)
    mf.add_facet(myfacet)
    mf.add_score()

You can also pass a list of field names and/or ``FacetType`` objects to the
initializer::

    prices = sorting.FieldFacet("price", reverse=True)
    scores = sorting.ScoreFacet()
    mf = sorting.MultiFacet("category", prices, myfacet, scores)


Missing values
==============

* When sorting, documents without any terms in a given field, or whatever else
  constitutes "missing" for different facet types, will always sort to the end.

* When grouping, "missing" documents will appear in a group with the
  key ``None``.


Using overlapping groups
========================

The common supported workflow for grouping and sorting is where the given field
has *one value for document*, for example a ``path`` field containing the file
path of the original document. By default, facets are set up to support this
single-value approach.

Of course, there are situations where you want documents to be sorted into
multiple groups based on a field with multiple terms per document. The most
common example would be a ``tags`` field. The ``allow_overlap`` keyword
argument to the :class:`~whoosh.sorting.FieldFacet`,
:class:`~whoosh.sorting.QueryFacet`, and
:class:`~whoosh.sorting.StoredFieldFacet` allows this multi-value approach.

However, there is an important caveat: using ``allow_overlap=True`` is slower
than the default, potentially *much* slower for very large result sets. This is
because Whoosh must read every posting of every term in the field to
create a temporary "forward index" mapping documents to terms.

If a field is indexed with *term vectors*, ``FieldFacet`` will use them to
speed up ``allow_overlap`` faceting for small result sets, but for large result
sets, where Whoosh has to open the vector list for every matched document, this
can still be very slow.

For very large indexes and result sets, if a field is stored, you can get
faster overlapped faceting using :class:`~whoosh.sorting.StoredFieldFacet`
instead of ``FieldFacet``. While reading stored values is usually slower than
using the index, in this case avoiding the overhead of opening large numbers of
posting readers can make it worthwhile.

``StoredFieldFacet`` supports ``allow_overlap`` by loading the stored value for
the given field and splitting it into multiple values. The default is to call
the value's ``split()`` method.

For example, if you've stored the ``tags`` field as a string like
``"tag1 tag2 tag3"``::

    schema = fields.Schema(name=fields.TEXT(stored=True),
                           tags=fields.KEYWORD(stored=True))
    ix = index.create_in("indexdir")
    with ix.writer() as w:
        w.add_document(name="A Midsummer Night's Dream", tags="comedy fairies")
        w.add_document(name="Hamlet", tags="tragedy denmark")
        # etc.

...Then you can use a ``StoredFieldFacet`` like this::

    ix = index.open_dir("indexdir")
    with ix.searcher() as s:
        sff = sorting.StoredFieldFacet("tags", allow_overlap=True)
        results = s.search(myquery, groupedby={"tags": sff})

For stored Python objects other than strings, you can supply a split function
(using the ``split_fn`` keyword argument to ``StoredFieldFacet``). The function
should accept a single argument (the stored value) and return a list or tuple
of grouping keys.


Expert: writing your own facet
==============================

TBD.















