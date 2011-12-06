
from lphelper import LateBindingProperty, user, change_obj

class LPSubscribers(dict):
    """
    keys[0] is default category
    """
    def __init__(self, keys):
        assert isinstance(keys, (list, tuple, set))
        self.__keys = keys
        self.__default = keys[0]
        self.__removed = set()
        self.__added = set()
        dict.__init__(self, ((i, set()) for i in self.__keys))
        
    def __setitem__(self, key, value):
        if not key in self.__keys:
            raise KeyError
        if key is None or key == self.__default:
            key = self.__default
        else:
            raise NotImplementedError, "It is impossible to subscribe to '%s'" %key
        assert isinstance(value, set)
        self.__removed = self[self.__default] - value
        self.__added = value - self[self.__default]
        super(LPSubscribers, self).__setitem__(key, value)
        
    def __iter__(self):
        for i in self.itervalues():
            for k in i:
                yield k
        
    def __repr__(self):
        return "<Subscribers>"
        
    def __len__(self):
        return sum(map(len, self.values()))
        
    def __str__(self):
        return "set([%s])" %", ".join(repr(i) for i in self)
        
    def add(self, lp_user, key=None):
        if key is None or key == self.__default:
            key = self.__default
        else:
            raise NotImplementedError, "It is impossible to subscribe to '%s'" %key
        if not isinstance(lp_user, user):
            lp_user = user(lp_user)
        if not lp_user in self[key]:
            if lp_user in self.__removed:
                self.__removed.remove(lp_user)
            else:
                self.__added.add(lp_user)
            self.__added.add(lp_user)
            self[key].add(lp_user)
        else:
            raise ValueError, "'%s' is already subscribed to this bug" %lp_user
        
    def remove(self, lp_user, key=None):
        if key is None or key == self.__default:
            key = self.__default
        else:
            raise NotImplementedError, "It is impossible to unsubscribe from '%s'" %key
        if not isinstance(lp_user, user):
            lp_user = user(lp_user)
        if lp_user in self[key]:
            if lp_user in self.__added:
                self.__added.remove(lp_user)
            else:
                self.__removed.add(lp_user)
            self[key].remove(lp_user)
        else:
            raise ValueError, "'%s' is not directly subscribed to this bug, can not be removed" %lp_user
        
        
        
    def get_subscriptions(self, key):
        return self[key]
        
    def parse(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
        
    @property
    def changed(self):
        changed = set()
        for i in self.__removed:
            changed.add(change_obj(i,"removed"))
        for i in self.__added:
            changed.add(change_obj(i,"added"))
        return changed
        
        
        
    def commit(self):
        raise NotImplementedError, 'this method must be implemented by a concrete subclass'
        
        
        
    
#some test-cases
if __name__ == '__main__':
    s = LPSubscribers(("direct","indirect","notified"))
    s.add("hallo")
    s.add("boo")
    s.add("boo","indirect")
    print s
    print repr(s)
    print len(s)
    print s.get_subscriptions("indirect")
     
