import ConfigParser
import cStringIO as StringIO
import os.path

from lpconstants import CONFIG

class Config(dict):
    """ Config system for python-launchpad-bugs
    
    this is working in layers, first the default values (CONFIG.DEFAULT)
    are used, hen the ones defined in the global config file located in
    CONFIG.FILE and at last the configuration set in the file with the
    given filename
    """
    
    MAPPING = dict()
    
    def __init__(self, filename=None, ignore=None):
        d = {}
        self.__filename = filename
        self.__config = ConfigParser.ConfigParser()
        self.__config.readfp(StringIO.StringIO(CONFIG.DEFAULT))
        try:
            self.__config.read(CONFIG.FILE)
        except ConfigParser.MissingSectionHeaderError:
            # if file exists it may be an old style config file which
            # only contains the username
            if os.path.exists(CONFIG.FILE):
                f = file(CONFIG.FILE, "r")
                try:
                    self.__config.set("user", "username", f.read().strip(" \n"))
                finally:
                    f.close()
        if not self.__filename is None:
            self.__config.read(self.__filename)
        ignore = self._create_ignore_dict(ignore)
        for section in self.__config.sections():
            d[section] = {}
            for key, value in self.__config.items(section):
                if key in ignore[section]:
                    value = ""
                try:
                    func = self.MAPPING[section][key][0]
                except (KeyError, IndexError):
                    d[section][key] = value
                else:
                    d[section][key] = func(value)
        dict.__init__(self, d)
        
    def save(self):
        for section in self.__config.sections():
            for key, value in self.__config.items(section):
                try:
                    func = self.MAPPING[section][key][1]
                except (KeyError, IndexError):
                    self.__config.set(section, key, self[section][key])
                else:
                    self.__config.set(section, key, func(self[section][key]))
        f = file(self.__filename or CONFIG.FILE, "w")
        try:
            f.write(CONFIG.COMMENT)
            self.__config.write(f)
        finally:
            f.close()

    def _create_ignore_dict(self, ignore_list):
        ret_dict = dict((s, set()) for s in self.__config.sections())
        if ignore_list is None:
            return ret_dict
        ignore = map(lambda x: x.split("."), ignore_list)
        for i in ignore:
            if i[0] not in ret_dict:
                continue
            try:
                ret_dict[i[0]].add(i[1])
            except IndexError:
                ret_dict[i[0]] = set(self.__config.options(i[0]))
        return ret_dict
