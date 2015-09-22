from otp import OTPHashFactory
from dict import DEFAULT_RDICT
from types import StringTypes
import re

VC = VALIDCHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
UC = UNSUFFICIENTCHARS = "abcdefABCDEF"
PC = PUNCTUATION = "?!.,<>{}[]()\"'"

FILEHEADER = re.compile(r"^\[(?P<hash>.*)\]\s*$")
FILEENTRY = re.compile(r"^\s*(?P<pos>\d+)\s*=\s*(?P<words>.*)$")

class OTPDictGenerator:
    def __init__(self, hashes=["md5"], maxsize=6, hfactory=OTPHashFactory):
        self._hfactory = hfactory()
        self._maxsize = maxsize
        self._dict = {} # {"hash": [["word", ...], ... ]}
        self._hashfunc = {}
        self._seen = {}
        for hash in hashes:
            self._hashfunc[hash] = self._hfactory[hash].hash
            l = self._dict.setdefault(hash, [])
            for i in range(2048):
                l.append([])

    def validate(self, word):
        if len(word) > self._maxsize or \
           filter(VC.__contains__, word) != word or \
           not filter(UC.__contains__, word) or \
           word.upper() in DEFAULT_RDICT:
            return 0
        return 1

    def transform(self, word):
        while word[-1] in PC:
            word = word[:-1]
            if not word:
                return None
        while word[0] in PC:
            word = word[1:]
            if not word:
                return None
        return word.lower()

    def push_string(self, s):
        words = []
        for word in s.split():
            if word:
                word = self.transform(word)
                if word and word not in self._seen:
                    self._seen[word] = 1
                    if self.validate(word):
                        words.append(word)
        if words:
            for hash, wordlist in self._dict.items():
                hashfunc = self._hashfunc[hash]
                for word in words:
                    poslist = wordlist[hashfunc(word)%2048]
                    if word not in poslist:
                        poslist.append(word)

    def push_file(self, file):
        if type(file) in StringTypes:
            stream = open(file)
        else:
            stream = file
        for line in stream.readlines():
            self.push_string(line)
        if stream != file:
            stream.close()

    def write(self, file):
        if type(file) in StringTypes:
            stream = open(file, "w")
        else:
            stream = file
        stream.write("; When multiple entries are used for the same\n"
                     "; position, the first one will be used.\n")
        for hash, wordlist in self._dict.items():
            stream.write("[%s]\n" % hash)
            for i in range(len(wordlist)):
                stream.write("%d = %s\n" % (i, ' '.join(wordlist[i])))
            stream.write("\n")
        if stream != file:
            stream.close()

    def read(self, file):
        if type(file) in StringTypes:
            stream = open(file)
        else:
            stream = file
        wordlist = None
        for line in stream.readlines():
            m = FILEHEADER.match(line)
            if m:
                wordlist = self._dict.setdefault(m.group("hash"), [])
                if not wordlist:
                    for i in range(2048):
                        wordlist.append([])
            elif wordlist:
                m = FILEENTRY.match(line)
                if m:
                    poslist = wordlist[int(m.group("pos"))]
                    for word in m.group("words").strip().split():
                        if word not in poslist:
                            poslist.append(word)
        if stream != file:
            stream.close()

    def export_dict(self):
        dict = {}
        for hash, wordlist in self._dict.items():
            l = dict.setdefault(hash, [])
            for i in range(2048):
                try:
                    l.append(wordlist[i][0])
                except IndexError:
                    l.append("")
        return dict

    def export(self, file, dictname="DICT"):
        if type(file) in StringTypes:
            stream = open(file, "w")
        else:
            stream = file
        stream.write("%s = {\n" % dictname)
        for hash, wordlist in self._dict.items():
            stream.write("%s: [\n" % `hash`)
            linepos = 0
            linesize = 0
            for i in range(len(wordlist)):
                poslist = wordlist[i]
                if poslist:
                    wordrepr = `poslist[0]`+','
                else:
                    wordrepr = "'',"
                if linepos > 6:
                    linepos = 0
                    linesize = 0
                    stream.write('\n')
                else:
                    blanksize = linepos*10-linesize
                    stream.write(" "*blanksize)
                    linesize += blanksize
                stream.write(wordrepr)
                linesize += len(wordrepr)
                linepos += 1
            stream.write("],\n")
        stream.write("}\n")
        if stream != file:
            stream.close()
