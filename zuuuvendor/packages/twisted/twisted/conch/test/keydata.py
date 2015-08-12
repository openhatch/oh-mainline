# -*- test-case-name: twisted.conch.test.test_keys -*-
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Data used by test_keys as well as others.
"""
RSAData = {
        'n':long('1062486685755247411169438309495398947372127791189432809481'
            '382072971106157632182084539383569281493520117634129557550415277'
            '516685881326038852354459895734875625093273594925884531272867425'
            '864910490065695876046999646807138717162833156501L'),
        'e':35L,
        'd':long('6678487739032983727350755088256793383481946116047863373882'
            '973030104095847973715959961839578340816412167985957218887914482'
            '713602371850869127033494910375212470664166001439410214474266799'
            '85974425203903884190893469297150446322896587555L'),
        'q':long('3395694744258061291019136154000709371890447462086362702627'
            '9704149412726577280741108645721676968699696898960891593323L'),
        'p':long('3128922844292337321766351031842562691837301298995834258844'
            '4720539204069737532863831050930719431498338835415515173887L')}

DSAData = {
        'y':long('2300663509295750360093768159135720439490120577534296730713'
            '348508834878775464483169644934425336771277908527130096489120714'
            '610188630979820723924744291603865L'),
        'g':long('4451569990409370769930903934104221766858515498655655091803'
            '866645719060300558655677517139568505649468378587802312867198352'
            '1161998270001677664063945776405L'),
        'p':long('7067311773048598659694590252855127633397024017439939353776'
            '608320410518694001356789646664502838652272205440894335303988504'
            '978724817717069039110940675621677L'),
        'q':1184501645189849666738820838619601267690550087703L,
        'x':863951293559205482820041244219051653999559962819L}

publicRSA_openssh = ("ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAGEArzJx8OYOnJmzf4tfBE"
"vLi8DVPrJ3/c9k2I/Az64fxjHf9imyRJbixtQhlH9lfNjUIx+4LmrJH5QNRsFporcHDKOTwTTYL"
"h5KmRpslkYHRivcJSkbh/C+BR3utDS555mV comment")

privateRSA_openssh = """-----BEGIN RSA PRIVATE KEY-----
MIIByAIBAAJhAK8ycfDmDpyZs3+LXwRLy4vA1T6yd/3PZNiPwM+uH8Yx3/YpskSW
4sbUIZR/ZXzY1CMfuC5qyR+UDUbBaaK3Bwyjk8E02C4eSpkabJZGB0Yr3CUpG4fw
vgUd7rQ0ueeZlQIBIwJgbh+1VZfr7WftK5lu7MHtqE1S1vPWZQYE3+VUn8yJADyb
Z4fsZaCrzW9lkIqXkE3GIY+ojdhZhkO1gbG0118sIgphwSWKRxK0mvh6ERxKqIt1
xJEJO74EykXZV4oNJ8sjAjEA3J9r2ZghVhGN6V8DnQrTk24Td0E8hU8AcP0FVP+8
PQm/g/aXf2QQkQT+omdHVEJrAjEAy0pL0EBH6EVS98evDCBtQw22OZT52qXlAwZ2
gyTriKFVoqjeEjt3SZKKqXHSApP/AjBLpF99zcJJZRq2abgYlf9lv1chkrWqDHUu
DZttmYJeEfiFBBavVYIF1dOlZT0G8jMCMBc7sOSZodFnAiryP+Qg9otSBjJ3bQML
pSTqy7c3a2AScC/YyOwkDaICHnnD3XyjMwIxALRzl0tQEKMXs6hH8ToUdlLROCrP
EhQ0wahUTCk1gKA4uPD6TMTChavbh4K63OvbKg==
-----END RSA PRIVATE KEY-----"""

# some versions of OpenSSH generate these (slightly different keys)
privateRSA_openssh_alternate = """-----BEGIN RSA PRIVATE KEY-----
MIIBzjCCAcgCAQACYQCvMnHw5g6cmbN/i18ES8uLwNU+snf9z2TYj8DPrh/GMd/2
KbJEluLG1CGUf2V82NQjH7guaskflA1GwWmitwcMo5PBNNguHkqZGmyWRgdGK9wl
KRuH8L4FHe60NLnnmZUCASMCYG4ftVWX6+1n7SuZbuzB7ahNUtbz1mUGBN/lVJ/M
iQA8m2eH7GWgq81vZZCKl5BNxiGPqI3YWYZDtYGxtNdfLCIKYcElikcStJr4ehEc
SqiLdcSRCTu+BMpF2VeKDSfLIwIxANyfa9mYIVYRjelfA50K05NuE3dBPIVPAHD9
BVT/vD0Jv4P2l39kEJEE/qJnR1RCawIxAMtKS9BAR+hFUvfHrwwgbUMNtjmU+dql
5QMGdoMk64ihVaKo3hI7d0mSiqlx0gKT/wIwS6Rffc3CSWUatmm4GJX/Zb9XIZK1
qgx1Lg2bbZmCXhH4hQQWr1WCBdXTpWU9BvIzAjAXO7DkmaHRZwIq8j/kIPaLUgYy
d20DC6Uk6su3N2tgEnAv2MjsJA2iAh55w918ozMCMQC0c5dLUBCjF7OoR/E6FHZS
0TgqzxIUNMGoVEwpNYCgOLjw+kzEwoWr24eCutzr2yowAA==
------END RSA PRIVATE KEY------"""

privateRSA_openssh_encrypted = """-----BEGIN RSA PRIVATE KEY-----
Proc-Type: 4,ENCRYPTED
DEK-Info: DES-EDE3-CBC,FFFFFFFFFFFFFFFF

30qUR7DYY/rpVJu159paRM1mUqt/IMibfEMTKWSjNhCVD21hskftZCJROw/WgIFt
ncusHpJMkjgwEpho0KyKilcC7zxjpunTex24Meb5pCdXCrYft8AyUkRdq3dugMqT
4nuWuWxziluBhKQ2M9tPGcEOeulU4vVjceZt2pZhZQVBf08o3XUv5/7RYd24M9md
WIo+5zdj2YQkI6xMFTP954O/X32ME1KQt98wgNEy6mxhItbvf00mH3woALwEKP3v
PSMxxtx3VKeDKd9YTOm1giKkXZUf91vZWs0378tUBrU4U5qJxgryTjvvVKOtofj6
4qQy6+r6M6wtwVlXBgeRm2gBPvL3nv6MsROp3E6ztBd/e7A8fSec+UTq3ko/EbGP
0QG+IG5tg8FsdITxQ9WAIITZL3Rc6hA5Ymx1VNhySp3iSiso8Jof27lku4pyuvRV
ko/B3N2H7LnQrGV0GyrjeYocW/qZh/PCsY48JBFhlNQexn2mn44AJW3y5xgbhvKA
3mrmMD1hD17ZvZxi4fPHjbuAyM1vFqhQx63eT9ijbwJ91svKJl5O5MIv41mCRonm
hxvOXw8S0mjSasyofptzzQCtXxFLQigXbpQBltII+Ys=
-----END RSA PRIVATE KEY-----"""

publicRSA_lsh = ("{KDEwOnB1YmxpYy1rZXkoMTQ6cnNhLXBrY3MxLXNoYTEoMTpuOTc6AK8yc"
"fDmDpyZs3+LXwRLy4vA1T6yd/3PZNiPwM+uH8Yx3/YpskSW4sbUIZR/ZXzY1CMfuC5qyR+UDUbB"
"aaK3Bwyjk8E02C4eSpkabJZGB0Yr3CUpG4fwvgUd7rQ0ueeZlSkoMTplMTojKSkp}")

privateRSA_lsh = ("(11:private-key(9:rsa-pkcs1(1:n97:\x00\xaf2q\xf0\xe6\x0e"
"\x9c\x99\xb3\x7f\x8b_\x04K\xcb\x8b\xc0\xd5>\xb2w\xfd\xcfd\xd8\x8f\xc0\xcf"
"\xae\x1f\xc61\xdf\xf6)\xb2D\x96\xe2\xc6\xd4!\x94\x7fe|\xd8\xd4#\x1f\xb8.j"
"\xc9\x1f\x94\rF\xc1i\xa2\xb7\x07\x0c\xa3\x93\xc14\xd8.\x1eJ\x99\x1al\x96F"
"\x07F+\xdc%)\x1b\x87\xf0\xbe\x05\x1d\xee\xb44\xb9\xe7\x99\x95)(1:e1:#)(1:d9"
"6:n\x1f\xb5U\x97\xeb\xedg\xed+\x99n\xec\xc1\xed\xa8MR\xd6\xf3\xd6e\x06\x04"
"\xdf\xe5T\x9f\xcc\x89\x00<\x9bg\x87\xece\xa0\xab\xcdoe\x90\x8a\x97\x90M\xc6"
'!\x8f\xa8\x8d\xd8Y\x86C\xb5\x81\xb1\xb4\xd7_,"\na\xc1%\x8aG\x12\xb4\x9a\xf8'
"z\x11\x1cJ\xa8\x8bu\xc4\x91\t;\xbe\x04\xcaE\xd9W\x8a\r\'\xcb#)(1:p49:\x00"
"\xdc\x9fk\xd9\x98!V\x11\x8d\xe9_\x03\x9d\n\xd3\x93n\x13wA<\x85O\x00p\xfd"
"\x05T\xff\xbc=\t\xbf\x83\xf6\x97\x7fd\x10\x91\x04\xfe\xa2gGTBk)(1:q49:\x00"
"\xcbJK\xd0@G\xe8ER\xf7\xc7\xaf\x0c mC\r\xb69\x94\xf9\xda\xa5\xe5\x03\x06v"
"\x83$\xeb\x88\xa1U\xa2\xa8\xde\x12;wI\x92\x8a\xa9q\xd2\x02\x93\xff)(1:a48:K"
"\xa4_}\xcd\xc2Ie\x1a\xb6i\xb8\x18\x95\xffe\xbfW!\x92\xb5\xaa\x0cu.\r\x9bm"
"\x99\x82^\x11\xf8\x85\x04\x16\xafU\x82\x05\xd5\xd3\xa5e=\x06\xf23)(1:b48:"
"\x17;\xb0\xe4\x99\xa1\xd1g\x02*\xf2?\xe4 \xf6\x8bR\x062wm\x03\x0b\xa5$\xea"
"\xcb\xb77k`\x12p/\xd8\xc8\xec$\r\xa2\x02\x1ey\xc3\xdd|\xa33)(1:c49:\x00\xb4"
"s\x97KP\x10\xa3\x17\xb3\xa8G\xf1:\x14vR\xd18*\xcf\x12\x144\xc1\xa8TL)5\x80"
"\xa08\xb8\xf0\xfaL\xc4\xc2\x85\xab\xdb\x87\x82\xba\xdc\xeb\xdb*)))")

privateRSA_agentv3 = ("\x00\x00\x00\x07ssh-rsa\x00\x00\x00\x01#\x00\x00\x00`"
"n\x1f\xb5U\x97\xeb\xedg\xed+\x99n\xec\xc1\xed\xa8MR\xd6\xf3\xd6e\x06\x04"
"\xdf\xe5T\x9f\xcc\x89\x00<\x9bg\x87\xece\xa0\xab\xcdoe\x90\x8a\x97\x90M\xc6"
'!\x8f\xa8\x8d\xd8Y\x86C\xb5\x81\xb1\xb4\xd7_,"\na\xc1%\x8aG\x12\xb4\x9a\xf8'
"z\x11\x1cJ\xa8\x8bu\xc4\x91\t;\xbe\x04\xcaE\xd9W\x8a\r\'\xcb#\x00\x00\x00a"
"\x00\xaf2q\xf0\xe6\x0e\x9c\x99\xb3\x7f\x8b_\x04K\xcb\x8b\xc0\xd5>\xb2w\xfd"
"\xcfd\xd8\x8f\xc0\xcf\xae\x1f\xc61\xdf\xf6)\xb2D\x96\xe2\xc6\xd4!\x94\x7fe|"
"\xd8\xd4#\x1f\xb8.j\xc9\x1f\x94\rF\xc1i\xa2\xb7\x07\x0c\xa3\x93\xc14\xd8."
"\x1eJ\x99\x1al\x96F\x07F+\xdc%)\x1b\x87\xf0\xbe\x05\x1d\xee\xb44\xb9\xe7"
"\x99\x95\x00\x00\x001\x00\xb4s\x97KP\x10\xa3\x17\xb3\xa8G\xf1:\x14vR\xd18*"
"\xcf\x12\x144\xc1\xa8TL)5\x80\xa08\xb8\xf0\xfaL\xc4\xc2\x85\xab\xdb\x87\x82"
"\xba\xdc\xeb\xdb*\x00\x00\x001\x00\xcbJK\xd0@G\xe8ER\xf7\xc7\xaf\x0c mC\r"
"\xb69\x94\xf9\xda\xa5\xe5\x03\x06v\x83$\xeb\x88\xa1U\xa2\xa8\xde\x12;wI\x92"
"\x8a\xa9q\xd2\x02\x93\xff\x00\x00\x001\x00\xdc\x9fk\xd9\x98!V\x11\x8d\xe9_"
"\x03\x9d\n\xd3\x93n\x13wA<\x85O\x00p\xfd\x05T\xff\xbc=\t\xbf\x83\xf6\x97"
"\x7fd\x10\x91\x04\xfe\xa2gGTBk")

publicDSA_openssh = ("ssh-dss AAAAB3NzaC1kc3MAAABBAIbwTOSsZ7Bl7U1KyMNqV13Tu7"
"yRAtTr70PVI3QnfrPumf2UzCgpL1ljbKxSfAi05XvrE/1vfCFAsFYXRZLhQy0AAAAVAM965Akmo"
"6eAi7K+k9qDR4TotFAXAAAAQADZlpTW964haQWS4vC063NGdldT6xpUGDcDRqbm90CoPEa2RmNO"
"uOqi8lnbhYraEzypYH3K4Gzv/bxCBnKtHRUAAABAK+1osyWBS0+P90u/rAuko6chZ98thUSY2kL"
"SHp6hLKyy2bjnT29h7haELE+XHfq2bM9fckDx2FLOSIJzy83VmQ== comment")

privateDSA_openssh = """-----BEGIN DSA PRIVATE KEY-----
MIH4AgEAAkEAhvBM5KxnsGXtTUrIw2pXXdO7vJEC1OvvQ9UjdCd+s+6Z/ZTMKCkv
WWNsrFJ8CLTle+sT/W98IUCwVhdFkuFDLQIVAM965Akmo6eAi7K+k9qDR4TotFAX
AkAA2ZaU1veuIWkFkuLwtOtzRnZXU+saVBg3A0am5vdAqDxGtkZjTrjqovJZ24WK
2hM8qWB9yuBs7/28QgZyrR0VAkAr7WizJYFLT4/3S7+sC6SjpyFn3y2FRJjaQtIe
nqEsrLLZuOdPb2HuFoQsT5cd+rZsz19yQPHYUs5IgnPLzdWZAhUAl1TqdmlAG/b4
nnVchGiO9sML8MM=
-----END DSA PRIVATE KEY-----"""

publicDSA_lsh = ("{KDEwOnB1YmxpYy1rZXkoMzpkc2EoMTpwNjU6AIbwTOSsZ7Bl7U1KyMNqV"
"13Tu7yRAtTr70PVI3QnfrPumf2UzCgpL1ljbKxSfAi05XvrE/1vfCFAsFYXRZLhQy0pKDE6cTIx"
"OgDPeuQJJqOngIuyvpPag0eE6LRQFykoMTpnNjQ6ANmWlNb3riFpBZLi8LTrc0Z2V1PrGlQYNwN"
"Gpub3QKg8RrZGY0646qLyWduFitoTPKlgfcrgbO/9vEIGcq0dFSkoMTp5NjQ6K+1osyWBS0+P90"
"u/rAuko6chZ98thUSY2kLSHp6hLKyy2bjnT29h7haELE+XHfq2bM9fckDx2FLOSIJzy83VmSkpK"
"Q==}")

privateDSA_lsh = ("(11:private-key(3:dsa(1:p65:\x00\x86\xf0L\xe4\xacg\xb0e"
"\xedMJ\xc8\xc3jW]\xd3\xbb\xbc\x91\x02\xd4\xeb\xefC\xd5#t'~\xb3\xee\x99\xfd"
"\x94\xcc()/Ycl\xacR|\x08\xb4\xe5{\xeb\x13\xfdo|!@\xb0V\x17E\x92\xe1C-)(1:q2"
"1:\x00\xcfz\xe4\t&\xa3\xa7\x80\x8b\xb2\xbe\x93\xda\x83G\x84\xe8\xb4P\x17)(1"
":g64:\x00\xd9\x96\x94\xd6\xf7\xae!i\x05\x92\xe2\xf0\xb4\xebsFvWS\xeb\x1aT"
"\x187\x03F\xa6\xe6\xf7@\xa8<F\xb6FcN\xb8\xea\xa2\xf2Y\xdb\x85\x8a\xda\x13<"
"\xa9`}\xca\xe0l\xef\xfd\xbcB\x06r\xad\x1d\x15)(1:y64:+\xedh\xb3%\x81KO\x8f"
"\xf7K\xbf\xac\x0b\xa4\xa3\xa7!g\xdf-\x85D\x98\xdaB\xd2\x1e\x9e\xa1,\xac\xb2"
"\xd9\xb8\xe7Ooa\xee\x16\x84,O\x97\x1d\xfa\xb6l\xcf_r@\xf1\xd8R\xceH\x82s"
"\xcb\xcd\xd5\x99)(1:x21:\x00\x97T\xeavi@\x1b\xf6\xf8\x9eu\\\x84h\x8e\xf6"
"\xc3\x0b\xf0\xc3)))")

privateDSA_agentv3 = ("\x00\x00\x00\x07ssh-dss\x00\x00\x00A\x00\x86\xf0L\xe4"
"\xacg\xb0e\xedMJ\xc8\xc3jW]\xd3\xbb\xbc\x91\x02\xd4\xeb\xefC\xd5#t'~\xb3"
"\xee\x99\xfd\x94\xcc()/Ycl\xacR|\x08\xb4\xe5{\xeb\x13\xfdo|!@\xb0V\x17E\x92"
"\xe1C-\x00\x00\x00\x15\x00\xcfz\xe4\t&\xa3\xa7\x80\x8b\xb2\xbe\x93\xda\x83G"
"\x84\xe8\xb4P\x17\x00\x00\x00@\x00\xd9\x96\x94\xd6\xf7\xae!i\x05\x92\xe2"
"\xf0\xb4\xebsFvWS\xeb\x1aT\x187\x03F\xa6\xe6\xf7@\xa8<F\xb6FcN\xb8\xea\xa2"
"\xf2Y\xdb\x85\x8a\xda\x13<\xa9`}\xca\xe0l\xef\xfd\xbcB\x06r\xad\x1d\x15\x00"
"\x00\x00@+\xedh\xb3%\x81KO\x8f\xf7K\xbf\xac\x0b\xa4\xa3\xa7!g\xdf-\x85D\x98"
"\xdaB\xd2\x1e\x9e\xa1,\xac\xb2\xd9\xb8\xe7Ooa\xee\x16\x84,O\x97\x1d\xfa\xb6"
"l\xcf_r@\xf1\xd8R\xceH\x82s\xcb\xcd\xd5\x99\x00\x00\x00\x15\x00\x97T\xeavi@"
"\x1b\xf6\xf8\x9eu\\\x84h\x8e\xf6\xc3\x0b\xf0\xc3")

__all__ = ['DSAData', 'RSAData', 'privateDSA_agentv3', 'privateDSA_lsh',
        'privateDSA_openssh', 'privateRSA_agentv3', 'privateRSA_lsh',
        'privateRSA_openssh', 'publicDSA_lsh', 'publicDSA_openssh',
        'publicRSA_lsh', 'publicRSA_openssh', 'privateRSA_openssh_alternate']

