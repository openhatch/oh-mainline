from __future__ import generators

import re
CHALLENGE = re.compile("otp-(?P<hash>\S+)\s+"
                       "(?P<sequence>\d+)\s+"
                       "(?P<seed>\S+)")

class Error(Exception): pass
class UnknownHashError(Error):
    def __init__(self, hash):
        self.hash = hash
        Exception.__init__(self, "unknown hash '%s'" % hash)
class UnknownFormatError(Error):
    def __init__(self, format):
        self.format = format
        Exception.__init__(self, "unknown format '%s'" % format)
class InvalidPassError(Error): pass
class InvalidSeedError(Error): pass
class InvalidSequenceError(Error): pass
class InvalidChallengeError(Error): pass
class FormatError(Error): pass

class OTPHashFactory:

    _hashclass = {}
    _hashinst = {}

    def register(klass, name, hashclass, parms={}):
        """Make a new hash algorithm known to the OTP system."""
        # Insert it at start so that users may override default classes
        klass._hashclass.setdefault(name, []).insert(0, (hashclass, parms))
    register = classmethod(register)

    def get(self, name):
        try:
            hashinst = self._hashinst[name]
        except KeyError:
            try:
                for klass, kwparms in self._hashclass[name]:
                    if not hasattr(klass, 'test') or klass.test():
                        break
                else:
                    raise KeyError
            except KeyError:
                raise UnknownHashError, name
            hashinst = self._hashinst.setdefault(name, klass(name, **kwparms))
        return hashinst

    def __getitem__(self, name):
        return self.get(name)

    def __iter__(self):
        for name in self._hashclass:
            try:
                hashinst = self.get(name)
            except UnknownHashError:
                continue
            yield name, hashinst


class OTPFormatFactory:

    _formatorder = []
    _formatclass = {}
    _formatinst = {}

    def register(klass, name, formatclass, parms={}, before=None):
        """Make a new format algorithm known to the OTP system."""
        formattuple = (formatclass, parms)
        klass._formatclass[name] = formattuple
        if before:
            try:
                index = klass._formatorder.index(before)
                klass._formatorder.insert(index, name)
            except ValueError:
                klass._formatorder.append(name)
        else:
            klass._formatorder.append(name)
    register = classmethod(register)

    def get(self, name):
        try:
            formatinst = self._formatinst[name]
        except KeyError:
            try:
                klass, kwparms = self._formatclass[name]
            except KeyError:
                raise UnknownHashError, name
            formatinst = self._formatinst.setdefault(name,
                                                     klass(name, **kwparms))
        return formatinst

    def __getitem__(self, name):
        return self.get(name)

    def __iter__(self):
        seen = {}
        for name in self._formatorder:
            formatinst = self.get(name)
            if not formatinst in seen:
                seen[formatinst] = 1
                yield name, formatinst

class OTP:
    def __init__(self, **keywd):
        # Force arguments to be used as keywords.
        self._default_format   = keywd.get("format", "hex")
        self._default_hash     = keywd.get("hash", "md5")

        self._ffactory = keywd.get("ffactory", OTPFormatFactory)()
        self._hfactory = keywd.get("hfactory", OTPHashFactory)()
 
    def mangle(self, passwd, seed):
        # Override this if you need a custom mangling behavior.
        return seed.lower()+passwd

    def validate(self, passwd=None, seed=None, **keywd):
        if keywd.get("force"):
            pass
        if passwd is not None:
            len_passwd = len(passwd)
            if len_passwd < 10:
                raise InvalidPassError, \
                    "passphrase must be at least 16 characters long"
            if len_passwd > 63 and not keywd.get("longpasswd"):
                raise InvalidPassError, \
                    "passphrase longer than the recommended length of 63 "\
                    " (use longpasswd=1 to force)"
        if seed is not None:
            len_seed = len(seed)
            if len_seed < 1:
                raise InvalidSeedError, "zero length seed"
            if len_seed > 16:
                raise InvalidSeedError, "seed longer than 16 characters"
            if filter(lambda x: x.isspace(), seed):
                raise InvalidSeedError, "seed must not contain spaces"

    def generate(self, passwd, sequence, seed, **keywd):
        length    = keywd.get("length", 1)
        format    = keywd.get("format", self._default_format)
        hash      = keywd.get("hash", self._default_hash)

        self.validate(passwd, seed, **keywd)

        if length < 1 or sequence < 0:
            return []
        hashobj = self._hfactory[hash]
        hashfunc = hashobj.hash
        firstkey = hashfunc(self.mangle(passwd, seed))
        for i in range(sequence):
            firstkey = hashfunc(firstkey)
        result = [firstkey]
        for i in range(1, length):
            result.append(hashfunc(result[-1]))
        if format is not None:
            encodefunc = self._ffactory[format].encode
            result = [encodefunc(x, hashobj) for x in result]
        return result

    def reformat(self, oldkey, **keywd):
        # Force arguments to be used as keywords.
        format     = keywd.get("format", self._default_format)
        hash       = keywd.get("hash", self._default_hash)
        fromformat = keywd.get("fromformat", None)

        hashobj = self._hfactory[hash]
        hashfunc = hashobj.hash
        if type(oldkey) != long:
            if fromformat is None:
                for name, formatobj in self._ffactory:
                    # It doesn't matter who decodes it here, so no 'detect'
                    raw = formatobj.decode(oldkey, hashobj)
                    if raw is not None:
                        break
                else:
                    return None
            else:
                raw = self._ffactory[fromformat].decode(oldkey, hashobj)
                if raw is None:
                    return None
        else:
            raw = oldkey
        return self._ffactory[format].encode(raw, hashobj)

    def parse_challenge(self, s, **keywd):
        match = CHALLENGE.search(s)
        if match:
            dict = match.groupdict()
            try:
                dict["sequence"] = int(dict["sequence"])
            except:
                raise InvalidSequenceError, \
                    "sequence '%s' is invalid" % dict["sequence"]
            self.validate(seed=dict["seed"], **keywd)
            return dict
        raise InvalidChallengeError, "invalid challenge"

    def generate_seed(self, **keywd):
        import string
        import random
        length = keywd.get("length", 10)
        if length < 1:
            raise InvalidSeedError, "zero length seed"
        if length > 16 and not keywd.get("force"):
            raise InvalidSeedError, "seed longer than 16 characters"
        characters = keywd.get("characters")
        if not characters:
            characters = "abcdefghijklmnopqrstuvxwyz0123456789"
        seed = ''
        for i in range(length):
            seed += random.choice(characters)
        return seed

    def change_seed(self, oldseed, **keywd):
        while 1:
            seed = self.generate_seed(**keywd)
            if seed != oldseed:
                return seed

    def generate_challenge(self, sequence, seed=None, **keywd):
        hash     = keywd.get("hash", self._default_hash)
        if seed is None:
            seed = self.generate_seed(**keywd)
        return "otp-%s %d %s" % (hash, sequence, seed)

    def _check(self, key, checkkey, hash, hashkey=0):
        hashobj = self._hfactory[hash]
        hashfunc = hashobj.hash
        # Accordingly to the RFC generator specification, two
        # different formats would never match. But the section 6.0
        # says that a checker must check for 'words', and if it is
        # not accepted, check with 'hex', here it is.
        for name, formatobj in self._ffactory:
            # It doesn't matter who decodes it here, so no 'detect'
            raw = formatobj.decode(key, hashobj)
            if raw is not None and \
               ((not hashkey and raw == checkkey) or
                (hashkey and hashfunc(raw) == checkkey)):
                # Return the parsed key, so that the user may store it for
                # the next check, using check_with_nexthash().
                return raw
        return None

    def check_with_passwd(self, passwd, key, **keywd):
        challenge = keywd.get("challenge")
        if challenge:
            dict = self.parse_challenge(challenge, **keywd)
            sequence = dict["sequence"]
            hash = dict["hash"]
            seed = dict["seed"]
        else:
            hash = keywd.get("hash", self._default_hash)
            sequence = keywd.get("sequence")
            if sequence is None:
                raise ValueError, "no sequence provided"
            seed = keywd.get("seed")
            if not seed:
                raise ValueError, "no seed provided"
        checkkey = self.generate(passwd, sequence, seed, hash=hash,
                                 format="long")[0]
        return self._check(key, checkkey, hash)

    def check_with_nexthash(self, nexthash, key, **keywd):
        hash = keywd.get("hash", self._default_hash)
        # nexthash must be provided in an unambigue form (providing
        # it in an ambigue form will be *very* hard anyway).
        checkkey = self.reformat(nexthash, format="long", **keywd)
        return self._check(key, checkkey, hash, hashkey=1)

    def compare(self, key1, key2, **keywd):
        key1 = self.reformat(key1, format="long", **keywd)
        key2 = self.reformat(key2, format="long", **keywd)
        return key1 == key2 and key1 is not None

    def detect_format(self, key, **keywd):
        hash = keywd.get("hash", self._default_hash)
        hashobj = self._hfactory[hash]
        hashfunc = hashobj.hash
        for name, formatobj in self._ffactory:
            raw = formatobj.decode(key, hashobj, detect=1)
            if raw is not None:
                return name
        return None

def register_hash(*parms, **kwparms):
    OTPHashFactory.register(*parms, **kwparms)

def register_format(*parms, **kwparms):
    OTPFormatFactory.register(*parms, **kwparms)

import hash
import format
register_hash("md5",  hash.HashMD5)
register_hash("sha1", hash.HashSHA1)
register_hash("md4",  hash.HashMD4MHASH)
register_hash("md4",  hash.HashMD4Crypto)

# Ordering here matters for detection.
register_format("words", format.FormatWords)
register_format("hex8",  format.FormatHex, {"tokens":8, "upper":1})
register_format("hex4",  format.FormatHex, {"tokens":4, "upper":1})
register_format("hex2",  format.FormatHex, {"tokens":2, "upper":1})
register_format("hex1",  format.FormatHex, {"upper":1})
register_format("hex",   format.FormatHex)
register_format("long",  format.FormatLong)

# The line below includes an alternative dictionary, considering
# that MY_DICT is a list with 2048 words following the specification in
# Appendix B of RFC2289 (that is, md5_64bits(MY_DICT[N])%2048 == N).
# Notice the usage of the "before" keyword. This is necessary for
# correctly detecting the format of your dict in OTP.detect_format().
#
#register_format("my-words", format.FormatWords,
#                {"dict": {"md5": MY_DICT}}, before="words")


