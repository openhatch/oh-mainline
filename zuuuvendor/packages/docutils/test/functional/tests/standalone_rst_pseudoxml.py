exec(open('functional/tests/_standalone_rst_defaults.py').read())

# Source and destination file names.
test_source = "standalone_rst_pseudoxml.txt"
test_destination = "standalone_rst_pseudoxml.txt"

# Keyword parameters passed to publish_file.
writer_name = "pseudoxml"

# Settings
# enable INFO-level system messages in this test:
settings_overrides['report_level'] = 1
