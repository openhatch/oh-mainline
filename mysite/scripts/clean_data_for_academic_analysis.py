#!/usr/bin/python

# This file is part of OpenHatch.
# Copyright (C) 2010 OpenHatch, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

### The purpose of this script is to create a version of the database
### that helps a U Mass Amherst researcher look through the OpenHatch
### data and perform text classification and other text analysis.

### To protect our users' privacy, we:
### * set the password column to the empty string
### * set the email column to the empty string
### * delete (from the database) any PortfolioEntry that is_deleted
### * delete (from the database) any Citation that is_deleted
### * delete all WebResponse objects

import mysite.profile.models
import django.contrib.auth.models

### set the email and password columns to the empty string
for user in django.contrib.auth.models.User.objects.all():
    user.email = ''
    user.password = ''
    user.save()

### delete PortfolioEntry instances that is_deleted
for pfe in mysite.profile.models.PortfolioEntry.objects.all():
    if pfe.is_deleted:
        pfe.delete()

### delete Citation instances that is_deleted
for citation in mysite.profile.models.Citation.objects.all():
    if citation.is_deleted:
        citation.delete()

### delete all WebResponse objects
for wr in mysite.customs.models.WebResponse.objects.all():
    wr.delete()

