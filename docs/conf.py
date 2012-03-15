"""OpenHatch documentation config"""

import sys, os

# Import OpenHatch version
sys.path.insert(0,'..')
from setup import __version__

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = 'OpenHatch'
copyright = '2012, OpenHatch contributors. Permission to re-use granted under the terms of CC Zero 1.0'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
version = __version__
release = __version__

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = 'default'

# Output file base name for HTML help builder.
htmlhelp_basename = 'OpenHatchdoc'

