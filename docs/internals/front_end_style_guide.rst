=====================
Front-end style guide
=====================

This **style guide** covers the interaction of HTML, CSS, and JavaScript on
OpenHatch's main website.

The "front end" refers to what people see in their web browsers. We create
that experience using HTML, CSS, and JavaScript. We tend to use the jQuery
library so we write less JavaScript, and we try to follow good conventions.

This document contains links to high-quality style suggestions from others,
and also names some common problems that have occurred in the OpenHatch
code in the past.

NOTE: Most of the HTML/CSS advice applies to the upcoming site redesign,
so it may not cross-apply well to the live site for the moment.


HTML/CSS
========

Colors
~~~~~~

Main background: lightest grey, #f8f8f8, with light-hatch.png background image.
Header and footer: dark grey, #333, with dark-hatch.png background image.

Default text color: darkest grey, #222; black is used sometimes for emphasis.

Links: orange, #FF6D3D; white; darkest grey, #222;

Links don't ever change color; on mouseover, they get underlined.

Borders: translucent light blue, rgba(100, 200, 255, .3); dashed light
grey, #e4e4e4;

Module interiors are slightly translucent white: rgba(255,255,255,.6);
Occasionally (e.g. the front page) a module can have a full-white
interior for emphasis.

Try to avoid font-weight: bold; if possible; differentiate headers
and so forth by size, or maybe color, instead.

Try to store styles in our CSS files or LESS files, rather than inline
in the element.

Cartoons
~~~~~~~~

Cartoons are always 141px high. They should always be flush with the module
beneath them. They are only used on one-column pages (even if there are
multiple-column areas farther down the page, the first module should be
a full-width module).

Layout
~~~~~~

There are two base template layouts for pages: one-column and two-columns.
Two-columns has a left 1/3 column and a main 2/3 column, cut on the same
lines as a three-columns outline.

The template that a page uses should be based on what the first module set
on the page looks like. If you want to add more columns on a one-column page,
just create the appropriate divs. If you want one or three columns on a
two-column page, put them inside the {% more_content %} block.

Two column CSS layout::

    <column column-left> <column column-right>

Three column CSS layout::

    <column three-column> <column three-column> <column three-column three-column-last>

Modules and submodules
~~~~~~~~~~~~~~~~~~~~~~

Modules have the following structure::

    <module>
        <module-head>
        Optional.
        The name of the module goes here, inside a h3.
        Inside of the h3 tag, you can make the title a link, if you want.
        </module-head>
        <module-body>
        Has a white background, the module contents all go in here, including submodules.
        </module-body>
        <module-foot>
        Optional.
        Want one of those clever links below your module content on the bottom right? Put it in here.
        If you want a link to also appear on the left, give it the "module-foot-left" class.
        </module-foot>
    </module>

Submodules have the following structure::

    <submodule>
        <submodule-head>
        Optional.
        This is where the title for the submodule goes, if you want to differentiate it somehow.
        Styling for this isn't standardized yet... see /missions/ for an example.
        Recommended to put the title inside an <h3>.
        </submodule-head>
        <submodule-body>
        Also optional.
        If you don't want to bother with a head/body distinction, you can just put content straight inside the submodule.
        </submodule-body>
    </submodule>

(all tags are the class names of the relevant divs, unless otherwise stated)

You may want to put your submodules inside a <submodule-container> with
a <clearer>, if you're floating them but don't want other content to ride up.

CSS
~~~

Name IDs and classes using hyphens, not underscores or camelcase.
(e.g. "#front-page", not "#front_page" or "#frontPage"). CSS file names
should use the same convention. (Not all of them do, but hopefully that
can eventually be corrected.)


Usage instructions for the code, pre and tt tags
================================================

If you're interested in modifying the 'Hints' sections of the training
missions, here are some guidelines regarding the usage variations of the
code, pre and tt tags to keep in mind.

The CSS properties for the pre tag and the code tag are such that a pre element
has a newline before and after it and is on a newline itself and a code element
does not have a newline before or after it but is on a newline itself. A tt
element neither has a newline before or after it nor it is on a newline itself.

Note: As of HTML5, the tt tag has been deprecated.

Here are a few examples:

If you write::

    <p>If you are on Linux, type: <opening tag>man diff<closing tag> at the command line.</p>

If you replace the "<opening tag>" and the "<closing tag>" above in the code
with pre tags, the output would be as follows::

    If you are on Linux, type:

    man diff

    at the command line.

If you replace the "<opening tag>" and the "<closing tag>" above in the code
with code tags, the output would be as follows::

    If you are on Linux, type:
    man diff
    at the command line.

If you replace the "<opening tag>" and the "<closing tag>" above in the code
with tt tags, the output would be as follows::

    If you are on Linux, type: man diff at the command line.


Editing the training mission hints
==================================

While working on `Issue 958`_, it was found that in the hints for training
missions, the "low" hint sometimes had trouble laying out its child elements
properly due to the CSS properties of its parent div and this caused the "low"
hints to display weirdly. To fix this issue, a new CSS property for '#low' was
added to mysite/static/css/missions/base.css. However, here are some guidelines
for how to phrase things when editing the training mission hints:

The first sentence of a training mission hint should be a paragraph (p tag).

The first sentence of a training mission hint should be a full sentence.

Full sentences start with capital letters and end with periods.

.. _Issue 958: https://openhatch.org/bugs/issue958


JavaScript
==========

This is a list of strategies for avoiding problems that have plagued OpenHatch
code in the past. **Note:** that the OpenHatch code does not yet follow this
guide. It ought to. Perhaps it can be a release goal in the future.

If it's not a link, don't make it a link
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If there's no fallback for non-JS users, don't use the <A> tag.

`Issue 478`_ covered a problem where a user was clicking on what appeared
to be a link. Because there is no JavaScript equivalent for the functionality
the user clicked, it simply should not be a link. (Though style-wise it
may **look** the same to the user.)

.. _Issue 478: http://openhatch.org/bugs/issue478

Don't rely on "return false;"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is easy to mistakenly use "return false;" at the end of a JavaScript
callback when you really mean event.preventDefault(). You can `read more`_ about
this problem.

.. _read more: http://fuelyourcoding.com/jquery-events-stop-misusing-return-false/


Good references
===============

This `document by isobar`_ looks great.

.. _document by isobar: http://na.isobar.com/standards/