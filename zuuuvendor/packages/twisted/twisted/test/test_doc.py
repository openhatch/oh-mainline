from twisted.trial import unittest
import inspect, glob, os
from os import path

from twisted.python import reflect

import twisted

def errorInFile(f, line=17, name=''):
    """Return a filename formatted so emacs will recognize it as an error point

    @param line: Line number in file.  Defaults to 17 because that's about how
        long the copyright headers are.
    """
    return '%s:%d:%s' % (f, line, name)
    # return 'File "%s", line %d, in %s' % (f, line, name)

class DocCoverage(unittest.TestCase):
    def setUp(self):
        remove = len(os.path.dirname(os.path.dirname(twisted.__file__)))+1
        def visit(dirlist, directory, files):
            if '__init__.py' in files:
                d = directory[remove:].replace('/','.')
                dirlist.append(d)
        self.packageNames = []
        os.path.walk(os.path.dirname(twisted.__file__),
                     visit, self.packageNames)

    def testModules(self):
        """Looking for docstrings in all modules."""
        docless = []
        for packageName in self.packageNames:
            if packageName in ('twisted.test',):
                # because some stuff in here behaves oddly when imported
                continue
            try:
                package = reflect.namedModule(packageName)
            except ImportError, e:
                # This is testing doc coverage, not importability.
                # (Really, I don't want to deal with the fact that I don't
                #  have pyserial installed.)
                # print e
                pass
            else:
                docless.extend(self.modulesInPackage(packageName, package))
        self.failIf(docless, "No docstrings in module files:\n"
                    "%s" % ('\n'.join(map(errorInFile, docless)),))

    def modulesInPackage(self, packageName, package):
        docless = []
        directory = path.dirname(package.__file__)
        for modfile in glob.glob(path.join(directory, '*.py')):
            moduleName = inspect.getmodulename(modfile)
            if moduleName == '__init__':
                # These are tested by test_packages.
                continue
            elif moduleName in ('spelunk_gnome','gtkmanhole'):
                # argh special case pygtk evil argh.  How does epydoc deal
                # with this?
                continue
            try:
                module = reflect.namedModule('.'.join([packageName,
                                                       moduleName]))
            except Exception, e:
                # print moduleName, "misbehaved:", e
                pass
            else:
                if not inspect.getdoc(module):
                    docless.append(modfile)
        return docless

    def testPackages(self):
        """Looking for docstrings in all packages."""
        docless = []
        for packageName in self.packageNames:
            try:
                package = reflect.namedModule(packageName)
            except Exception, e:
                # This is testing doc coverage, not importability.
                # (Really, I don't want to deal with the fact that I don't
                #  have pyserial installed.)
                # print e
                pass
            else:
                if not inspect.getdoc(package):
                    docless.append(package.__file__.replace('.pyc','.py'))
        self.failIf(docless, "No docstrings for package files\n"
                    "%s" % ('\n'.join(map(errorInFile, docless),)))


    # This test takes a while and doesn't come close to passing.  :(
    testModules.skip = "Activate me when you feel like writing docstrings, and fixing GTK crashing bugs."
