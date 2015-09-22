import struct

class BaseHash:
    def __init__(self, name):
        self.name = name

    def prepare(self, hash):
        if type(hash) is long:
            newhash = ''
            for i in range(56, -8, -8):
                newhash += chr((hash>>i)%256)
            hash = newhash
        return hash

class HashMD5(BaseHash):
    def __init__(self, name):
        BaseHash.__init__(self, name)
        import md5
        self._hash = md5.md5
        self.name = name

    def hash(self, hash):
        hash = self.prepare(hash)
        return self.fold(self._hash(hash).digest())

    def fold(self, hash):
        result = map(ord, hash)
        n = 0L
        for i in range(8):
            result[i] ^= result[i+8]
            n <<= 8
            n |= result[i]
        return n

class HashSHA1(BaseHash):
    def __init__(self, name):
        BaseHash.__init__(self, name)
        import sha
        self._hash = sha.sha
        self.name = name

    def hash(self, hash):
        hash = self.prepare(hash)
        return self.fold(self._hash(hash).digest())

    def fold(self, hash):
        hash = map(ord, hash)
        n = 0L
        n |= hash[3]^hash[11]^hash[19]
        n <<= 8
        n |= hash[2]^hash[10]^hash[18]
        n <<= 8
        n |= hash[1]^hash[9]^hash[17]
        n <<= 8
        n |= hash[0]^hash[8]^hash[16]
        n <<= 8
        n |= hash[7]^hash[15]
        n <<= 8
        n |= hash[6]^hash[14]
        n <<= 8
        n |= hash[5]^hash[13]
        n <<= 8
        n |= hash[4]^hash[12]
        return n

class HashMD4MHASH(HashMD5):
    def __init__(self, name):
        BaseHash.__init__(self, name)
        import mhash
        self._hash = mhash.MHASH
        self._md4 = mhash.MHASH_MD4
        self.name = name

    def hash(self, hash):
        hash = self.prepare(hash)
        return self.fold(self._hash(self._md4, hash).digest())

    def test():
        try:
            import mhash
        except ImportError:
            return 0
        return 1
    test = staticmethod(test)

class HashMD4Crypto(HashMD5):
    def __init__(self, name):
        BaseHash.__init__(self, name)
        from Crypto.Hash import MD4
        self._hash = MD4.new
        self.name = name

    def test():
        try:
            from Crypto.Hash import MD4
        except ImportError:
            return 0
        return 1
    test = staticmethod(test)
