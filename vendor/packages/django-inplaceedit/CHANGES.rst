Releases
========

1.3.0 (2013-10-04)
------------------

* Improvements in the travis file
* Improvements in the testing project and in the tests
* Support to python2.6 (this does not work from django-inplaceedit>=0.96 to django-inplaceedit<=1.2.6)
* Thanks to:
    * `Pavel Nedrigaylov <https://github.com/shadow-identity>`_


1.2.6 (2013-09-27)
------------------

* Fix an error in the default of the INPLACE_ENABLE_CLASS
* Fix litte error in the documentation
* Improvements in the testing project, before transmeta was required
* Thanks to:
    * `Nathan Fain <https://github.com/cyphunk>`_
    * `Siecje <https://github.com/Siecje>`_


1.2.5 (2013-09-17)
------------------

* Fix a bug when you have a filter when you call to the imnplace_edit tag::

    {% inplace_edit "obj.field|filter" %}

1.2.4 (2013-09-17)
------------------

* Fix a bug is you want to overwrite can_auto_save in the get_config method
* Improvements in the testing project (django-inplaceedit-extra-fields)


1.2.3 (2013-09-17)
------------------

* Improvements in the testing project (django-inplaceedit-extra-fields)


1.2.2 (2013-09-17)
------------------

* Fix a bug when you use inplace_static
* Improvements in the documentation

1.2.1 (2013-09-16)
------------------

* New options fieldTypes, and focusWhenEditing
* Fix some details of getting the value, now there is a getValue function
* Python 2/3 unicode compatible in testing project
* Details of image/file adaptor
* Add static file recolector
* Refactor date adaptors

1.2.0 (2013-09-10)
------------------

* Now the js options of jquery.inplaceeditform.js can be overwritten
* Now every methods of jquery.inplaceeditform.js can be overwritten
* Now the user can not do two post consecutives. The user have to wait that the first post end
* Fix an error when the width or height were a float number
* Update the version of jquery.form from 2.77 to 3.43
* Support to EmailField
* Improvements in the jquery plugin (jquery.inplaceeditform.js)
* Improvements in the documentation
* Improvements in css


1.1.0 (2013-09-06)
------------------

* Improvements in css


1.0.0 (2013-09-05)
------------------

* Support to NullBooleanField, DecimalField and TimeField (you got an error)
* Support to IntegerField, FloatField and URLField (improvements over BaseAdaptorField)
* Improvement in DateField and DateTimeField
* Create a doc in `readthedocs <https://django-inplaceedit.readthedocs.org/>`_
* Add unit test and integrate with `travis <https://travis-ci.org/Yaco-Sistemas/django-inplaceedit>`_
* The django-inplaceedit now is less intrusive. **Attention** if you have customize django-inplaceedit, see this `changeset <https://github.com/Yaco-Sistemas/django-inplaceedit/commit/c5cfdcce190b4fa8166b7500db711400baa9ea86>`_
* Support Django 1.2 or higher version
* Fix some errors with IE browser
* Improvement in testing project
* Move the settings to the module
* Detail of Python3 compatibility
* Details of the toolbar css
* A lot of little improvements and fix bugs
* Fix translations errors, thanks to `Pfeyz <https://github.com/pfeyz>`_


0.96 (2013-08-14)
-----------------

* Python3 compatible
* Compatible with the future version  of Django (>=1.6)
* Fix a little error with the boolean fields


0.95 (2013-08-09)
-----------------

* Fix a small typo error
* Fix a little error when you use DEFAULT_INPLACE_EDIT_OPTIONS
* Thanks to:
    * `Kartik Agaram <https://github.com/akkartik>`_
    * `Iwaszko <https://github.com/iwaszko>`_



0.94 (2013-04-25)
-----------------

* Fix errors when you use `filters <https://docs.djangoproject.com/en/dev/ref/templates/builtins/>`_ for the fk fields or m2m fields
* Fix css errors
* Fix a small typo error
* Thanks to:
    * `Anton <https://github.com/fynjah>`_
    * `Tobias Lorenz <https://github.com/Tyrdall>`_


0.93 (2013-04-10)
-----------------

* Fix a erros with INPLACEEDIT_AUTO_SAVE = True
* Thanks to:
    * `Anton <https://github.com/fynjah>`_


0.92 (2013-04-05)
-----------------

* Make javascript extendable and refactor success handler
* Thanks to:
    * `Jens Nistler <https://github.com/lociii>`_

0.91 (2013-04-01)
-----------------

* Now works with Django 1.5 and **the older versions of Django**
* Thanks to:
    * `Yuego <https://github.com/Yuego>`_


0.90 (2013-02-18)
-----------------

* Now works with jQuery 1.9
* Thanks to:
    * `Tobias Birmili <https://github.com/toabi/>`_

0.89 (2012-10-08)
-----------------

* Fix a problem when the model that you are editing had a Generic Foreign key
* Thanks to `Altimore <https://github.com/altimore>`_

0.88 (2012-10-05)
-----------------

* Add to default parameter to inplace_css
* Translate to the string: "You have unsaved changes!"
* Fix a problem with the treatment of the sizes
* INPLACEEDIT_EDIT_EMPTY_VALUE settings
* Thanks to:
    * `Tobias Birmili <https://github.com/toabi/>`_
    * `Altimore <https://github.com/altimore>`_


0.87 (2012-09-05)
-----------------

* Add callback to onbeforeunload
* Refactor the jquery.inplaceeditform.js
* Now is not required the ADMIN_MEDIA_PREFIX in the settings, but this is backward compatible
* New options to the settings: DEFAULT_INPLACE_EDIT_OPTIONS and DEFAULT_INPLACE_EDIT_OPTIONS_ONE_BY_ONE
* Thanks to:
    * `Tobias Birmili <https://github.com/toabi/>`_
    * `Serpah <https://github.com/serpah/>`_
    * And spatially to `Altimore <https://github.com/altimore>`_


0.86 (2012-08-21)
-----------------

* Toolbar to edit inplace
* Auto save option
* New JS hook (extraConfig)
* Now you can choose the event to edit inplace, by default is doble click
* Now when you edit inline the input (or select) get the focus
* Now while there is a ajax request cannot do other ajax request to the same element
* Update the way to get the CSFRToken
* JSLint to jquery.inplaceeditform.js (There were some errors still)
* Refactor and remove little errors
* Refactor the css files


0.85 (2012-08-09)
-----------------

* A strange error with buildout
* I'm sorry but I removed the package by mistake

0.84 (2012-08-09)
-----------------

* Move the repository to `github <https://github.com/Yaco-Sistemas/django-inplaceedit/>`_

0.83 (2012-05-22)
-----------------

* Now django-inplaceedit managing `static files <https://docs.djangoproject.com/en/dev/howto/static-files/>`_ (backward compatible)

0.82 (2012-03-19)
-----------------
* Fix a error when a field contained "_id"

0.81 (2012-01-25)
-----------------
* A little error in AdminDjangoPermEditInline

0.80 (2012-01-24)
-----------------
* More robust when a user can edit a content
* SuperUserPermEditInline, before was a logic, and you can not inherit.
* AdminDjangoPermEditInline, a logic very useful. Thanks to `Raimon <https://github.com/zikzakmedia/django-inplaceeditform/commit/b6c5427563e77b23494312a7f50c66ba362709b8/>`_

0.79 (2012-01-11)
-----------------
* Messages configurables and translatables in the settings

0.78 (2012-01-9)
----------------
* Messages configurables in the settings

0.77 (2011-12-14)
-----------------
* Fixes a error in bolean adaptor

0.76 (2011-12-08)
-----------------
* More robust

0.75 (2011-11-24)
-----------------
* The resources dont't have dependencie of MEDIA_URL (in CSS file)

0.74 (2011-10-03)
-----------------
* Usability: edit inline works when you submit the form

0.73 (2011-09-22)
-----------------
* Image/File field compatibility with Django 1.1 (overwriting inplaceeditform/adaptor_file/inc.csrf_token.html) (Django 1.2 or above recommended)

0.72 (2011-09-16)
-----------------
* Compatibility with jQuery 1.2 (jQuery 1.5 or above recommended)
* Compatibility with Django 1.1 (Django 1.2 or above recommended)

0.71 (2011-09-5)
----------------
* Fixed error in 0.69 rendering text fields whose font size is not integer.

0.70 (2011-08-31)
-----------------
* Catalonia translations, by Raimon Esteve

0.69 (2011-08-18)
-----------------
* Compatible with the CSRF protection (CsrfViewMiddleware)
* Improvement in the rendering of the widgets (better calculate the height and width)
* More versatile the api

0.68 (2011-08-16)
-----------------
* Update the README

0.67 (2011-06-23)
-----------------
* Spanish translations

0.66 (2011-06-21)
-----------------
* Support to old browsers. Some browser have not a JSON library

0.65 (2011-06-7)
----------------
* Improved the inplace edit widget in images.

0.64 (2011-06-6)
----------------
* Inplace edit of imagefield and filefield works in IE (new), FF, Chrome (alpha)

0.63 (2011-05-24)
-----------------
* Inplace edit of imagefield and filefield (alpha)
* More versatile the api

0.62 (2011-03-18)
-----------------

* Fixes the warning when the error is for other field
* More versatile the api

0.60  (2011-02-18)
------------------

* Created a test project
* Inplace editof booleanfield
* Fixes some details of datetimefield and datefield
* Can't save datetime values on several browser
* The icons did not see
* autoheight and autowidth
* Improve the inplace edit with choices field
* Made less intrusive inplace edit form, now it's putting two spaces)

0.55  (2011-02-11)
------------------

* A new egg from django-inplaceedit-version1
* The js should be a plugin jQuery
* The generated html should be bit intrusive
* API to create adaptators
* Option to auto_height, and auto_width
* Error/ succes messages
* Two functions of render_value, with you can edit, and other when you cannot edit
* A function with empty value
* The files media should not be added if this is adding
* The inplaceedit should can edit some like this:

::

    {% inplace_edit "obj.field_x.field_y" %}
