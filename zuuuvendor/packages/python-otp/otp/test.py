from __future__ import generators
import unittest
import otp

# [(hash, passwd, seed, seq, rawkey, [(format, key), ...]), ...]
DATA = [
    # RFC2289 MD4 tests
    ("md4", "This is a test.", "TeSt", 0, 15097546000631008081, [
        ("hex8",   "D1 85 42 18 EB BB 0B 51"),
        ("hex4",   "D185 4218 EBBB 0B51"),
        ("hex2",   "D1854218 EBBB0B51"),
        ("hex1",   "D1854218EBBB0B51"),
        ("hex",    "d1854218ebbb0b51"),
        ("*hex",   " D 1   8  5  4 2   1 8E  b   B b  0  B   5   1   "),
        ("words",  "ROME MUG FRED SCAN LIVE LACE"),
        ("*words", "   RoMe    mUg  fReD    sCaN  lIvE lAcE    "),
    ]),
    ("md4", "This is a test.", "TeSt", 1, 7153755734097835076, [
        ("hex8",   "63 47 3E F0 1C D0 B4 44"),
        ("hex4",   "6347 3EF0 1CD0 B444"),
        ("hex2",   "63473EF0 1CD0B444"),
        ("hex1",   "63473EF01CD0B444"),
        ("hex",    "63473ef01cd0b444"),
        ("*hex",   "6 3 4 7 3 e f 0 1 c d 0 b 4 4 4"),
        ("words",  "CARD SAD MINI RYE COL KIN"),
        ("*words", "   CaRd  SaD   MiNi  RyE   COl  KiN  "),
    ]),
    ("md4", "This is a test.", "TeSt", 99, 14260105574278243194, [
        ("hex8",   "C5 E6 12 77 6E 6C 23 7A"),
        ("hex4",   "C5E6 1277 6E6C 237A"),
        ("hex2",   "C5E61277 6E6C237A"),
        ("hex1",   "C5E612776E6C237A"),
        ("hex",    "c5e612776e6c237a"),
        ("*hex",   "c5 E6127 7 6e6 C237a"),
        ("words",  "NOTE OUT IBIS SINK NAVE MODE"),
        ("*words", " nOTe OuT IBiS  SINK NaVE   MoDE"),
    ]),

    ("md4", "AbCdEfGhIjK", "alpha1", 0, 5766700202548977230, [
        ("hex4",   "5007 6F47 EB1A DE4E"),
        ("words",  "AWAY SEN ROOK SALT LICE MAP"),
    ]),
    ("md4", "AbCdEfGhIjK", "alpha1", 1, 7336941145201964971, [
        ("hex4",   "65D2 0D19 49B5 F7AB"),
        ("words",  "CHEW GRIM WU HANG BUCK SAID"),
    ]),
    ("md4", "AbCdEfGhIjK", "alpha1", 99, 15082775246831313617, [
        ("hex4",   "D150 C82C CE6F 62D1"),
        ("words",  "ROIL FREE COG HUNK WAIT COCA"),
    ]),

    ("md4", "OTP's are good", "correct", 0, 9555646464956650376, [
        ("hex4",   "849C 79D4 F6F5 5388"),
        ("words",  "FOOL STEM DONE TOOL BECK NILE"),
    ]),
    ("md4", "OTP's are good", "correct", 1, 10090758047456053169, [
        ("hex4",   "8C09 92FB 2508 47B1"),
        ("words",  "GIST AMOS MOOT AIDS FOOD SEEM"),
    ]),
    ("md4", "OTP's are good", "correct", 99, 4556504502288504651, [
        ("hex4",   "3F3B F4B4 145F D74B"),
        ("words",  "TAG SLOW NOV MIN WOOL KENO"),
    ]),

    # RFC2289 MD5 tests
    ("md5", "This is a test.", "TeSt", 0, 11423205859455703517, [
        ("hex4",   "9E87 6134 D904 99DD"),
        ("words",  "INCH SEA ANNE LONG AHEM TOUR"),
    ]),
    ("md5", "This is a test.", "TeSt", 1, 8747644503540957855, [
        ("hex4",   "7965 E054 36F5 029F"),
        ("words",  "EASE OIL FUM CURE AWRY AVIS"),
    ]),
    ("md5", "This is a test.", "TeSt", 99, 5836130079114418304, [
        ("hex4",   "50FE 1962 C496 5880"),
        ("words",  "BAIL TUFT BITS GANG CHEF THY"),
    ]),

    ("md5", "AbCdEfGhIjK", "alpha1", 0, 9729584825438564870, [
        ("hex4",   "8706 6DD9 644B F206"),
        ("words",  "FULL PEW DOWN ONCE MORT ARC"),
    ]),
    ("md5", "AbCdEfGhIjK", "alpha1", 1, 8994616513477333323, [
        ("hex4",   "7CD3 4C10 40AD D14B"),
        ("words",  "FACT HOOF AT FIST SITE KENT"),
    ]),
    ("md5", "AbCdEfGhIjK", "alpha1", 99, 6531198583147992172, [
        ("hex4",   "5AA3 7A81 F212 146C"),
        ("words",  "BODE HOP JAKE STOW JUT RAP"),
    ]),

    ("md5", "OTP's are good", "correct", 0, 17439474020874341625, [
        ("hex4",   "F205 7539 43DE 4CF9"),
        ("words",  "ULAN NEW ARMY FUSE SUIT EYED"),
    ]),
    ("md5", "OTP's are good", "correct", 1, 15982620410422446391, [
        ("hex4",   "DDCD AC95 6F23 4937"),
        ("words",  "SKIM CULT LOB SLAM POE HOWL"),
    ]),
    ("md5", "OTP's are good", "correct", 99, 12827345270260219463, [
        ("hex4",   "B203 E28F A525 BE47"),
        ("words",  "LONG IVY JULY AJAR BOND LEE"),
    ]),

    # RFC2289 MD5 tests
    ("sha1", "This is a test.", "TeSt", 0, 13519360648556679156, [
        ("hex4",   "BB9E 6AE1 979D 8FF4"),
        ("words",  "MILT VARY MAST OK SEES WENT"),
    ]),
    ("sha1", "This is a test.", "TeSt", 1, 7194841681067522139, [
        ("hex4",   "63D9 3663 9734 385B"),
        ("words",  "CART OTTO HIVE ODE VAT NUT"),
    ]),
    ("sha1", "This is a test.", "TeSt", 99, 9799489151164468473, [
        ("hex4",   "87FE C776 8B73 CCF9"),
        ("words",  "GAFF WAIT SKID GIG SKY EYED"),
    ]),

    ("sha1", "AbCdEfGhIjK", "alpha1", 0, 12503670802239161289, [
        ("hex4",   "AD85 F658 EBE3 83C9"),
        ("words",  "LEST OR HEEL SCOT ROB SUIT"),
    ]),
    ("sha1", "AbCdEfGhIjK", "alpha1", 1, 15023131125772915099, [
        ("hex4",   "D07C E229 B5CF 119B"),
        ("words",  "RITE TAKE GELD COST TUNE RECK"),
    ]),
    ("sha1", "AbCdEfGhIjK", "alpha1", 99, 2863287722321067462, [
        ("hex4",   "27BC 7103 5AAF 3DC6"),
        ("words",  "MAY STAR TIN LYON VEDA STAN"),
    ]),

    ("sha1", "OTP's are good", "correct", 0, 15357062084421381899, [
        ("hex4",   "D51F 3E99 BF8E 6F0B"),
        ("words",  "RUST WELT KICK FELL TAIL FRAU"),
    ]),
    ("sha1", "OTP's are good", "correct", 1, 9416663078243103972, [
        ("hex4",   "82AE B52D 9437 74E4"),
        ("words",  "FLIT DOSE ALSO MEW DRUM DEFY"),
    ]),
    ("sha1", "OTP's are good", "correct", 99, 5704207453753010156, [
        ("hex4",   "4F29 6A74 FE15 67EC"),
        ("words",  "AURA ALOE HURL WING BERG WAIT"),
    ]),

    # Alternative Dictionaries
    ("md4", "This is a test.", "TeSt", 0, 15097546000631008081, [
        ("*words",  "msc intact pellew invoke guido flush"),
    ]),
    ("md5", "AbCdEfGhIjK", "alpha1", 1, 8994616513477333323, [
        ("*words",  " every  calls zcomix  inthe psf  hotfix"),
    ]),
    ("sha1", "OTP's are good", "correct", 99, 5704207453753010156, [
        ("*words",  " maim means cm shaped exempt router "),
    ]),
]

ERRORDATA = [
# (hash, passwd, seed, seq, error)
("md5", "Too_short", "iamvalid", 99, otp.InvalidPassError),
("sha1", "0"*64, "iamvalid", 99, otp.InvalidPassError),
#("md5", "A_Valid_Pass_Phrase", "Length_Okay", 99, otp.InvalidSeedError),
("md5", "A_Valid_Pass_Phrase", "LengthOfSeventeen", 99, otp.InvalidSeedError),
("sha1", "A_Valid_Pass_Phrase", "A Seed", 99, otp.InvalidSeedError),
]

NEEDEDHASHES = ["md5", "sha1"]

class Data:
    def __init__(self, **keywd):
        self.__dict__.update(keywd)

class OTPTest(unittest.TestCase):
    def setUp(self):
        self.hashes = [x[0] for x in otp.OTPHashFactory()]
        for hash in NEEDEDHASHES:
            if hash not in self.hashes:
                raise otp.UnknownHashError, "md5"

    def walk_data(self):
        hashes = self.hashes
        del self
        for hash, passwd, seed, seq, rawkey, pairs in DATA:
            if hash not in hashes:
                continue
            for format, key in pairs:
                if format[0] == '*':
                    format = format[1:]
                    reverse = 0
                else:
                    reverse = 1
                yield Data(**locals()) # ;-)
        
    def walk_error_data(self):
        del self
        for hash, passwd, seed, seq, error in ERRORDATA:
            yield Data(**locals()) # ;-)

    def test_generate(self):
        o = otp.OTP()
        for d in self.walk_data():
            if not d.reverse:
                continue
            key = o.generate(d.passwd, d.seq, d.seed,
                             hash=d.hash, format=d.format)[0]
            self.assertEqual(key, d.key)

    def test_generate_many(self):
        o = otp.OTP()
        for d in self.walk_data():
            if not d.reverse:
                continue
            keylist = o.generate(d.passwd, 0, d.seed,
                                 hash=d.hash, format=d.format,
                                 length=d.seq+10)
            self.assertEqual(keylist[d.seq], d.key)

    def test_reformat(self):
        o = otp.OTP()
        for d in self.walk_data():
            self.assertEqual(o.reformat(d.key, format="long", hash=d.hash),
                             d.rawkey)

    def test_detect_format(self):
        o = otp.OTP()
        for d in self.walk_data():
            format = o.detect_format(d.key, hash=d.hash)
            self.assertEqual(format, d.format)

    def test_compare(self):
        o = otp.OTP()
        nextlasttuple = None
        nextlastd = None
        for d in self.walk_data():
            tuple = (d.hash, d.passwd, d.seed, d.seq)
            lastd, nextlastd = nextlastd, d
            lasttuple, nextlasttuple = nextlasttuple, tuple
            id = "%s/%d" % (d.key, d.rawkey)
            self.assertEqual(o.compare(d.key, d.rawkey, hash=d.hash), 1, id)
            if tuple != lasttuple:
                continue
            id = "%s/%s" % (d.key, lastd.key)
            self.assertEqual(o.compare(d.key, lastd.key, hash=d.hash), 1, id)

    def test_check_with_passwd_info(self):
        o = otp.OTP()
        for d in self.walk_data():
            valid = o.check_with_passwd(d.passwd, d.key, sequence=d.seq,
                                        seed=d.seed, hash=d.hash)
            self.assertEqual(valid, d.rawkey)

    def test_check_with_passwd_challenge(self):
        o = otp.OTP()
        for d in self.walk_data():
            challenge = " foo otp-%s  %d\t%s bar " % \
                        (d.hash, d.seq, d.seed)
            valid = o.check_with_passwd(d.passwd, d.key, challenge=challenge)
            self.assertEqual(valid, d.rawkey)

    def test_check_with_nexthash(self):
        o = otp.OTP()
        nextlasttuple = None
        nextlastd = None
        for d in self.walk_data():
            tuple = (d.hash, d.passwd, d.seed)
            lastd, nextlastd = nextlastd, d
            lasttuple, nextlasttuple = nextlasttuple, tuple
            if tuple != lasttuple or lastd.seq != d.seq-1:
                continue
            valid = o.check_with_nexthash(d.rawkey, lastd.key, hash=d.hash)
            self.assertEqual(valid, lastd.rawkey)

    def test_parse_challenge(self):
        o = otp.OTP()
        for d in self.walk_data():
            challenge = " foo otp-%s  %d\t%s bar " % \
                        (d.hash, d.seq, d.seed)
            dict = o.parse_challenge(challenge)
            self.assertEqual(dict["hash"], d.hash)
            self.assertEqual(dict["sequence"], d.seq)
            self.assertEqual(dict["seed"], d.seed)

    def test_generate_validate_seed(self):
        o = otp.OTP()
        for i in range(1000):
            seed = o.generate_seed(length=(i%15)+1)
            o.validate(seed=seed)

    def test_change_seed(self):
        o = otp.OTP()
        for i in range(100):
            seed = o.generate_seed(length=(i%15)+1)
            newseed = o.change_seed(seed)
            o.validate(seed=newseed)
            self.assertNotEqual(newseed, seed)

    def test_validate(self):
        o = otp.OTP()
        for d in self.walk_error_data():
            self.assertRaises(d.error, o.generate,
                              d.passwd, d.seq, d.seed, hash=d.hash)

if __name__ == "__main__":
    unittest.main()
