#!/usr/bin/env python
"""Generate coverage reports"""

import os

print('Running code coverage. This will take a minute or two to run the tests.')
os.system("coverage run --rcfile=.coveragerc manage.py test -v1")
print('Tests completed.')

print('Generating code coverage report')
os.system("coverage report")

print('Generating html report of code coverage')
os.system("coverage html")
print('html report completed. See "oh-mainline/coverage_html_report/index.html"')
