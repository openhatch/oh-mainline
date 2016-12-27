"""OpenHatch documentation config"""

import sys, os

# Import OpenHatch version
project_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
sys.path.insert(0,project_path)
from setup import __version__

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = 'OpenHatch'
copyright = '2012-2015, OpenHatch contributors. Permission to re-use granted under the terms of CC Zero 1.0'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
version = '01.01.02'
release = '2015.01.01'

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = 'default'

# Output file base name for HTML help builder.
htmlhelp_basename = 'OpenHatchdoc'

# Stop converting quotes and dashes to typographically correct entities. Useful for placing code into notes, ie.
html_use_smartypants = False
