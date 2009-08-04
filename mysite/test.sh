#!/bin/bash
APPS=$(for thing in *; do if [ -d $thing/templates ] ; then echo $thing; fi; done)
exec ./manage.py test $APPS
