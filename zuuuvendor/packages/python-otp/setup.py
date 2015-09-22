#!/usr/bin/python
from distutils.core import setup

setup(name="python-otp",
      version = "1.0",
      description = "Python module for one-time passwords",
      author = "Gustavo Niemeyer",
      author_email = "niemeyer@conectiva.com",
      url = "http://moin.conectiva.com.br/PythonOtp",
      license = "GPL",
      long_description =
"""python-otp is a module which implements support for all requirements,
recommendations, and optional features described in RFC2289. This RFC
defines a standard for the implementation of OTP, or one-time passwords.
""",
      packages = ["otp"],
      )
