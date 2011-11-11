#!/usr/bin/python
# -*- coding: UTF-8 -*-


import re
from lpconstants import BUG, BLUEPRINT



re_escape = re.compile(ur"\ufffd|\x0f|\x10|\x02|\x07")
def unicode_for_libxml2(text):
    """ helper function to fix encoding errors in libxml2 """
    u = unicode(text, "UTF-8")
    ret = re_escape.sub("??", u)
    return ret.encode("UTF-8")  


def _attr_ext(i, s):
    if i.startswith("__"):
        return "_%s%s" %(s.__class__.__name__,i)
    else:
        return i

def _gen_getter(attr):
    """ Returns a function to return the value of an attribute
    
    Example:
        get_example = _gen_getter("x.y")
    is like:
        def get_example(self):
            if not x.parsed:
                x.parse()
            return x.y
    
    """
    def func(s):
        attributes = attr.split(".")
        attributes = map(lambda a: _attr_ext(a, s), attributes)
        x = getattr(s, attributes[0])
        attributes.insert(0, s)
        if not x.parsed:
            x.parse()
        return reduce(getattr, attributes)
    return func

        
def _gen_setter(attr):
    """ Returns a function to set the value of an attribute
    
    Example:
        set_example = _gen_setter("x.y")
    is like:
        def set_example(self, value):
            if not x.parsed:
                x.parse()
            x.y = value
    
    """
    def func(s, value):
        attributes = attr.split(".")
        attributes = map(lambda a: _attr_ext(a, s), attributes)
        x = getattr(s, attributes[0])
        attributes.insert(0, s)
        if not x.parsed:
            x.parse()
        setattr(reduce(getattr, attributes[:-1]), attributes[-1], value)
    return func


def sort(x,y,sort):
    if sort == "nr":
        return cmp(int(x.bugnumber), int(y.bugnumber))
    elif sort == "importance":
        return cmp(BUG.SORT_IMPORTANCE.index(x.importance),
                        BUG.SORT_IMPORTANCE.index(y.importance))
    elif sort == "status":
        return cmp(BUG.SORT_STATUS.index(x.status),
                        BUG.SORT_STATUS.index(y.status))


def blueprint_sort(x,y,sort):
    if sort == "priority":
        return cmp(BLUEPRINT.SORT_PRIORITY.index(getattr(x,sort)),
                                BLUEPRINT.SORT_PRIORITY.index(getattr(y,sort)))
    elif sort == "status":
        return cmp(BLUEPRINT.SORT_STATUS.index(getattr(x,sort)),
                                BLUEPRINT.SORT_STATUS.index(getattr(y,sort)))
    elif sort == "delivery":
        return cmp(BLUEPRINT.SORT_DELIVERY.index(getattr(x,sort)),
                                BLUEPRINT.SORT_DELIVERY.index(getattr(y,sort)))
    else:
        return cmp(getattr(x,sort), getattr(y,sort))



class user(str):
    
    user_regex = re.compile(r"^(.+)\s\((\S+)\)$", re.UNICODE)
    
    @staticmethod
    def parse_text_user(usr):
        x = user.user_regex.search(unicode(usr, "UTF-8"))
        if x:
            return user(x.group(2), x.group(1))
        return usr
        
    @staticmethod
    def parse_html_user(node):
        """ takes a lp standard user node and returns a user object.
        
        Example for such a node:
        * <a href="/~ogra">Oliver Grawert</a>
        * <a href="https://blueprints.edge.launchpad.net/~ogra">
                <img alt="" width="14" height="14" src="/@@/person" />&nbsp;Oliver Grawert
          </a>
        """
        realname = unicode(node.content.strip("\n "), "UTF-8")
        realname = realname.lstrip(u"\xa0")
        return user(unicode(node.prop('href').split('~').pop().split("/")[0], "UTF-8"), realname)
    
    def __new__(cls, lplogin, realname=None, attributes=None):
        obj = super(user, cls).__new__(user, lplogin)
        obj.__lplogin = lplogin
        obj.__realname = realname
        if attributes is None:
            attributes = set()
        obj.__attributes = attributes
        return obj
        
    @property
    def realname(self):
        return self.__realname or "unknown"
        
    @property
    def lplogin(self):
        return self.__lplogin

    @property
    def _attributes(self):
        return self.__attributes

    def __repr__(self):
        # Does __repr__ really have to return an "ascii"-encoded string? how can we use an unicode one?
        f =  "<user %s (%s)>" %(self.__lplogin, self.realname)
        return f.encode("ascii", "replace")
        
    def __str__(self):
        return self.__lplogin or ""
        
    def __nonzero__(self):
        if self.__lplogin:
            return True
        else:
            return False



class product(str):
    
    product_regex = re.compile(r"^(\S+)(\s\(([\w ]+)\))?$", re.UNICODE)
    
    @staticmethod
    def parse_text_product(prod_str):
        x = product.product_regex.search(prod_str)
        if x:
            #print x.groups()
            target = None
            a = x.group(3)
            if a:
                a = a.split()
                if len(a) > 1:
                    target = a[-1]
                longname = "%s (%s)" %(x.group(1), a[0])
            else:
                longname = x.group(1)
            return product(x.group(1), longname), target
        # prod_str like 'Ubuntu Breezy' is also possible
        x = prod_str.split()
        if len(x) == 2:
            if x[0].istitle():
                return product(x[0].lower(), x[0]), x[1]
        return prod_str, None
    
    def __new__(cls, lpname, longname=None, type=None, tracked_in=None):
        obj = super(product, cls).__new__(product, lpname)
        obj.__lpname = lpname
        obj.__longname = longname
        obj.__type = type
        obj.__tracked_in = tracked_in
        return obj
        
    @property
    def longname(self):
        return self.__longname or self.__lpname or "unknown"
        
    @property
    def type(self):
        return self.__type
        
    @property
    def tracked_in(self):
        return self.__tracked_in
        
    def __str__(self):
        return self.__lpname or ""
        
    def __repr__(self):
        return "<product %s (%s, type=%s, tracked in=%s)>" %(self.__lpname,
                    self.longname, self.__type, self.__tracked_in)
        
    def __nonzero__(self):
        if self.__lpname:
            return True
        else:
            return False


class change_obj(object):
    """ shows the status of a changed object  """
    def __init__(self, attr, action="changed"):
        """
        * attr: edited attribute
        * action: describes the way the attribute was edited
        """
        self.__attr = attr
        self.__action = action
        
    @property
    def component(self):
        return self.__attr
        
    @property
    def action(self):
        return self.__action
        
    def __str__(self):
        if self.action == "changed":
            s = "(%s changed: %s)" %(repr(self.__attr), ", ".join([str(x) for x in getattr(self.__attr,"changed", [])]))
        else:
            s = "(%s %s)" %(repr(self.__attr), self.action)
        return s
        
    def __repr__(self):
        return "<Changes to %s>" %self.__attr
        

class LateBindingProperty(property) :
    ''' Allow late bindig properties.
    
    Thanks to Maric Michaud,
    http://mail.python.org/pipermail/python-list/2006-September/401908.html'''

    def __init__(self, fget=None, fset=None, fdel=None, doc=None) :
        if fget : fget = lambda s, n=fget.__name__ : getattr(s, n)()
        if fset : fset = lambda s, v, n=fset.__name__ : getattr(s, n)(v)
        if fdel : fdel = lambda s, n=fdel.__name__ : getattr(s, n)()
        property.__init__(self, fget, fset, fdel, doc)
