# Run tests, generate coverage report and open it on a browser
#
# Requires: coverage 3.3 or above from http://pypi.python.org/pypi/coverage

coverage run --branch $(which trial) --reporter=text scrapy.tests
coverage html -i
python -m webbrowser htmlcov/index.html
