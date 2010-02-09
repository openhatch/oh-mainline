################ We could, import haystack, but what's the point?
#import haystack

################# The docs suggest we do this:
#haystack.autodiscover()
################# but we will NOT because this causes explosions in the sky.
################# We should talk to the Haystack folks. It seems that they have
################# already run into mod_wsgi woes before; here's a new one for them.

# Note that when you want to re-generate the XML file that is the Solr configuration,
# you may need to uncomment the above. That's fine, just do not send code that calls
# haystack.autodiscover() to the git repository, and CERTAINTLY don't send it to the
# production server.

# Sorry to be vague. Ask me if you have questions!

# -- Asheesh 2010-02-09.
