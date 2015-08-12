import logging
import logging.handlers
from django.conf import settings

from django_assets.filter import Filter


__all__ = ('CSSUtilsFilter',)


class CSSUtilsFilter(Filter):
    """Minifies CSS by removing whitespace, comments etc., using the Python
    `cssutils <http://cthedot.de/cssutils/>`_ library.

    Note that since this works as a parser on the syntax level, so invalid
    CSS input could potentially result in data loss.
    """

    name = 'cssutils'

    def setup(self):
        import cssutils
        self.cssutils = cssutils

        try:
            # cssutils logs to stdout by default, hide that in production
            if not settings.DEBUG:
                log = logging.getLogger('assets.cssutils')
                log.addHandler(logging.handlers.MemoryHandler(10))

                # Newer versions of cssutils print a deprecation warning
                # for 'setlog'.
                if hasattr(cssutils.log, 'setLog'):
                    func = cssutils.log.setLog
                else:
                    func = cssutils.log.setlog
                func(log)
        except ImportError:
            # During doc generation, Django is not going to be setup and will
            # fail when the settings object is accessed. That's ok though.
            pass

    def apply(self, _in, out):
        sheet = self.cssutils.parseString(_in.read())
        self.cssutils.ser.prefs.useMinified()
        out.write(sheet.cssText)