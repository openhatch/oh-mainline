# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Resource traversal integration with L{twisted.cred} to allow for
authentication and authorization of HTTP requests.
"""

# Expose HTTP authentication classes here.
from twisted.web._auth.wrapper import HTTPAuthSessionWrapper
from twisted.web._auth.basic import BasicCredentialFactory
from twisted.web._auth.digest import DigestCredentialFactory

__all__ = [
    "HTTPAuthSessionWrapper",

    "BasicCredentialFactory", "DigestCredentialFactory"]
