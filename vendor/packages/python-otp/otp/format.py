from dict import DEFAULT_DICT, DEFAULT_RDICT
from otp import FormatError

class FormatHex:
    """bb9e6ae1979d8ff4, BB9E 6AE1 979D 8FF4, etc"""
    def __init__(self, name, tokens=0, upper=0):
        self.name = name
        self.tokens = tokens
        self.upper = upper

    def encode(self, hash, hashobj):
        hash = '%016x' % hash
        if self.upper:
            hash = hash.upper()
        if self.tokens:
            tokens = []
            l = range(0,16+1,16/self.tokens)
            hash = ' '.join([hash[l[i]:l[i+1]] for i in range(len(l)-1)])
        return hash

    def decode(self, hash, hashobj, detect=0):
        if not detect and (self.tokens or self.upper):
            # When not detecting, only "hex" matches. Otherwise,
            # a failing entry would get through all the 'hex'es
            # unnecessarily.
            return None
        result = hash.replace(' ','').replace('\t','')
        if len(result) != 16:
            return None
        try:
            result = long(result, 16)
        except ValueError:
            return None
        if detect and (self.tokens or self.upper):
            if self.encode(result, hashobj) != hash:
                return None
        return result

class FormatLong:
    """13519360648556679156"""
    
    def __init__(self, name):
        self.name = name

    def encode(self, hash, hashobj):
        return hash
    
    def decode(self, hash, hashobj, detect=0):
        if type(hash) is not long:
            try:
                return long(hash)
            except ValueError:
                return None
        return hash

class FormatWords:
    """MILT VARY MAST OK SEES WENT"""

    def __init__(self, name, dict=DEFAULT_DICT):
        self.worddict = dict
        self.name = name

    def encode(self, hash, hashobj):
        worddict = self.worddict
        if self.worddict is not DEFAULT_DICT:
            try:
                worddict = self.worddict[hashobj.name]
            except KeyError:
                raise FormatError, \
                        "alternative dictionary '%s' doesn't support " \
                        "hash '%s'" % (self.name, hashobj.name)
        n = hash
        sum = 0L
        for _ in range(32):
            sum += n%4
            n >>= 2
        hash <<= 2
        hash |= sum%4
        words = []
        for _ in range(6):
            words.insert(0, worddict[hash%2048])
            hash >>= 11
        return ' '.join(words)

    def decode(self, hash, hashobj, detect=0):
        validword = 0
        words = hash.split()
        if len(words) != 6:
            return None
        worddict = self.worddict
        if worddict is not DEFAULT_DICT:
            if not detect:
                # When not detecting, only "words" matches. Otherwise,
                # a failing entry would get through all the 'words'
                # alternatives unnecessarily.
                return None
            try:
                worddict = worddict[hashobj.name]
            except KeyError:
                return None
            for word in words:
                if word not in worddict:
                    return None
        try:
            n = 0L
            for word in words:
                n <<= 11
                n |= DEFAULT_RDICT[word.upper()]
                validword = 1
        except KeyError:
            # Alternative Dictionary Algorithm
            #
            # The RFC says that *no* words from the standard dictionary
            # should be used. We'll be permissive here, and accept
            # broken generators.
            #
            #if validword:
            #    return None
            n = 0L
            for word in words:
                # Ditto.
                #
                #if DEFAULT_RDICT.has_key(word.upper()):
                #    return None
                n <<= 11
                n |= hashobj.hash(word)%2048
        hashsum = n%4
        n >>= 2
        result = n
        sum = 0L
        for _ in range(32):
            sum += n%4
            n >>= 2
        if hashsum != sum%4:
            return None
        return result
