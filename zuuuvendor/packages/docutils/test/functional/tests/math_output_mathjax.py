# Source and destination file names.
test_source = "data/math.txt"
test_destination = "math_output_mathjax.html"

# Keyword parameters passed to publish_file.
reader_name = "standalone"
parser_name = "rst"
writer_name = "html"

# Settings
settings_overrides['math_output'] = 'MathJax'
# local copy of default stylesheet:
settings_overrides['stylesheet_path'] = ( 
    'functional/input/data/html4css1.css')
    
