=================
WordPress theming
=================

Overview
========

The OpenHatch blog is powered by WordPress. This Django-based codebase
has some minimal hooks that enable us to style the WordPress blog by
making changes to this Django codebase.

Details
=======

On a local instance, if you visit
http://localhost:8000/+wp-theme/index , you will see an amusing
absurdity: a Django template has been rendered, but the template
blocks have been filled with placeholder strings.

The purpose of this page is to provide a machine-readable version of
our theme which can, in turn, be processed by a separate engine to be
turned into a WordPress theme.

(In the future, we may use this to generate a MediaWiki theme... and
maybe a Roundup theme? Who knows.)

It is controlled by the template in mysite/base/templates/base/wordpress_index.html.

Related
=======

* See also https://github.com/paulproteus/oh-wordpress-theme , the project with code and documentation on generating a fully-functional WordPress theme from this page.

