exec(open('functional/tests/_standalone_rst_defaults.py').read())

# Source and destination file names.
test_source = "standalone_rst_latex.txt"
test_destination = "standalone_rst_latex.tex"

# Keyword parameters passed to publish_file.
writer_name = "latex"

# Settings
# use "smartquotes" transition:
settings_overrides['smart_quotes'] = True
