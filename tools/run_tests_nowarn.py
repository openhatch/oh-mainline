#!/usr/bin/env python
"""Run oh-mainline tests ignoring warnings"""

import os

os.system("python -Wignore manage.py test")
