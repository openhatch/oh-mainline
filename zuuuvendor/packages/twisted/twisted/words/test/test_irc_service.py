# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Tests for IRC portions of L{twisted.words.service}.
"""

from twisted.trial import unittest
from twisted.test import proto_helpers
from twisted.words.service import InMemoryWordsRealm, IRCFactory, IRCUser
from twisted.words.protocols import irc
from twisted.cred import checkers, portal

class IRCUserTestCase(unittest.TestCase):
    """
    Isolated tests for L{IRCUser}
    """

    def setUp(self):
        """
        Sets up a Realm, Portal, Factory, IRCUser, Transport, and Connection
        for our tests.
        """
        self.wordsRealm = InMemoryWordsRealm("example.com")
        self.portal = portal.Portal(self.wordsRealm,
            [checkers.InMemoryUsernamePasswordDatabaseDontUse(john="pass")])
        self.factory = IRCFactory(self.wordsRealm, self.portal)
        self.ircUser = self.factory.buildProtocol(None)
        self.stringTransport = proto_helpers.StringTransport()
        self.ircUser.makeConnection(self.stringTransport)


    def test_sendMessage(self):
        """
        Sending a message to a user after they have sent NICK, but before they
        have authenticated, results in a message from "example.com".
        """
        self.ircUser.irc_NICK("", ["mynick"])
        self.stringTransport.clear()
        self.ircUser.sendMessage("foo")
        self.assertEquals(":example.com foo mynick\r\n",
                          self.stringTransport.value())


    def response(self):
        """
        Grabs our responses and then clears the transport
        """
        response = self.ircUser.transport.value().splitlines()
        self.ircUser.transport.clear()
        return map(irc.parsemsg, response)


    def scanResponse(self, response, messageType):
        """
        Gets messages out of a response

        @param response: The parsed IRC messages of the response, as returned
        by L{IRCServiceTestCase.response}

        @param messageType: The string type of the desired messages.

        @return: An iterator which yields 2-tuples of C{(index, ircMessage)}
        """
        for n, message in enumerate(response):
            if (message[1] == messageType):
                yield n, message


    def test_sendNickSendsGreeting(self):
        """
        Receiving NICK without authenticating sends the MOTD Start and MOTD End
        messages, which is required by certain popular IRC clients (such as
        Pidgin) before a connection is considered to be fully established.
        """
        self.ircUser.irc_NICK("", ["mynick"])
        response = self.response()
        start = list(self.scanResponse(response, irc.RPL_MOTDSTART))
        end = list(self.scanResponse(response, irc.RPL_ENDOFMOTD))
        self.assertEquals(start,
            [(0, ('example.com', '375', ['mynick', '- example.com Message of the Day - ']))])
        self.assertEquals(end,
            [(1, ('example.com', '376', ['mynick', 'End of /MOTD command.']))])


    def test_fullLogin(self):
        """
        Receiving USER, PASS, NICK will log in the user, and transmit the
        appropriate response messages.
        """
        self.ircUser.irc_USER("", ["john doe"])
        self.ircUser.irc_PASS("", ["pass"])
        self.ircUser.irc_NICK("", ["john"])

        version = ('Your host is example.com, running version %s' %
            (self.factory._serverInfo["serviceVersion"],))

        creation = ('This server was created on %s' %
            (self.factory._serverInfo["creationDate"],))

        self.assertEquals(self.response(),
            [('example.com', '375',
              ['john', '- example.com Message of the Day - ']),
             ('example.com', '376', ['john', 'End of /MOTD command.']),
             ('example.com', '001', ['john', 'connected to Twisted IRC']),
             ('example.com', '002', ['john', version]),
             ('example.com', '003', ['john', creation]),
             ('example.com', '004',
              ['john', 'example.com', self.factory._serverInfo["serviceVersion"],
               'w', 'n'])])



class MocksyIRCUser(IRCUser):
    def __init__(self):
        self.mockedCodes = []

    def sendMessage(self, code, *_, **__):
        self.mockedCodes.append(code)

BADTEXT = '\xff'

class IRCUserBadEncodingTestCase(unittest.TestCase):
    """
    Verifies that L{IRCUser} sends the correct error messages back to clients
    when given indecipherable bytes
    """
    # TODO: irc_NICK -- but NICKSERV is used for that, so it isn't as easy.

    def setUp(self):
        self.ircuser = MocksyIRCUser()

    def assertChokesOnBadBytes(self, irc_x, error):
        """
        Asserts that IRCUser sends the relevant error code when a given irc_x
        dispatch method is given undecodable bytes.

        @param irc_x: the name of the irc_FOO method to test.
        For example, irc_x = 'PRIVMSG' will check irc_PRIVMSG

        @param error: the error code irc_x should send. For example,
        irc.ERR_NOTONCHANNEL
        """
        getattr(self.ircuser, 'irc_%s' % irc_x)(None, [BADTEXT])
        self.assertEqual(self.ircuser.mockedCodes, [error])

    # no such channel

    def test_JOIN(self):
        """
        Tests that irc_JOIN sends ERR_NOSUCHCHANNEL if the channel name can't
        be decoded.
        """
        self.assertChokesOnBadBytes('JOIN', irc.ERR_NOSUCHCHANNEL)

    def test_NAMES(self):
        """
        Tests that irc_NAMES sends ERR_NOSUCHCHANNEL if the channel name can't
        be decoded.
        """
        self.assertChokesOnBadBytes('NAMES', irc.ERR_NOSUCHCHANNEL)

    def test_TOPIC(self):
        """
        Tests that irc_TOPIC sends ERR_NOSUCHCHANNEL if the channel name can't
        be decoded.
        """
        self.assertChokesOnBadBytes('TOPIC', irc.ERR_NOSUCHCHANNEL)

    def test_LIST(self):
        """
        Tests that irc_LIST sends ERR_NOSUCHCHANNEL if the channel name can't
        be decoded.
        """
        self.assertChokesOnBadBytes('LIST', irc.ERR_NOSUCHCHANNEL)

    # no such nick

    def test_MODE(self):
        """
        Tests that irc_MODE sends ERR_NOSUCHNICK if the target name can't
        be decoded.
        """
        self.assertChokesOnBadBytes('MODE', irc.ERR_NOSUCHNICK)

    def test_PRIVMSG(self):
        """
        Tests that irc_PRIVMSG sends ERR_NOSUCHNICK if the target name can't
        be decoded.
        """
        self.assertChokesOnBadBytes('PRIVMSG', irc.ERR_NOSUCHNICK)

    def test_WHOIS(self):
        """
        Tests that irc_WHOIS sends ERR_NOSUCHNICK if the target name can't
        be decoded.
        """
        self.assertChokesOnBadBytes('WHOIS', irc.ERR_NOSUCHNICK)

    # not on channel

    def test_PART(self):
        """
        Tests that irc_PART sends ERR_NOTONCHANNEL if the target name can't
        be decoded.
        """
        self.assertChokesOnBadBytes('PART', irc.ERR_NOTONCHANNEL)

    # probably nothing

    def test_WHO(self):
        """
        Tests that irc_WHO immediately ends the WHO list if the target name
        can't be decoded.
        """
        self.assertChokesOnBadBytes('WHO', irc.RPL_ENDOFWHO)
