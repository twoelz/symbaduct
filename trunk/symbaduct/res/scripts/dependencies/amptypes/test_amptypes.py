from twisted.internet import reactor
from twisted.internet.protocol import Factory, ClientCreator
from twisted.protocols import amp
from twisted.trial import unittest

import amptypes



class TypedDictionaryProtocol1(amp.Command):
    arguments = [('d', amptypes.TypedDictionary(amp.String(), amp.String()))]
    response  = [('d', amptypes.TypedDictionary(amp.String(), amp.String()))]

class TypedDictionaryProtocol2(amp.Command):
    arguments = [('d', amptypes.TypedDictionary(amp.Unicode(), amp.Unicode()))]
    response  = [('d', amptypes.TypedDictionary(amp.Unicode(), amp.Unicode()))]

class TypedDictionaryProtocol3(amp.Command):
    arguments = [('d', amptypes.TypedDictionary(amp.Integer(), amp.Integer()))]
    response  = [('d', amptypes.TypedDictionary(amp.Integer(), amp.Integer()))]


class TypedListProtocol1(amp.Command):
    arguments = [('l', amptypes.TypedList(amp.String()))]
    response  = [('l', amptypes.TypedList(amp.String()))]

class TypedListProtocol2(amp.Command):
    arguments = [('l', amptypes.TypedList(amp.Unicode()))]
    response  = [('l', amptypes.TypedList(amp.Unicode()))]

class TypedListProtocol3(amp.Command):
    arguments = [('l', amptypes.TypedList(amp.Integer()))]
    response  = [('l', amptypes.TypedList(amp.Integer()))]



class TypedDictionaryResponder(amp.AMP):
    def s(self, d):
        return {'d': d}
    TypedDictionaryProtocol1.responder(s)
    TypedDictionaryProtocol2.responder(s)
    TypedDictionaryProtocol3.responder(s)


class TypedListResponder(amp.AMP):
    def s(self, l):
        return {'l': l}
    TypedListProtocol1.responder(s)
    TypedListProtocol2.responder(s)
    TypedListProtocol3.responder(s)



class AbstractAmptypesTest(unittest.TestCase):

    DEFAULT_PORT = 6001

    def setUp(self):
        self.client = None
        self.iport = None

    def tearDown(self):
        if self.client is not None:
            self.client.transport.loseConnection()
        if self.iport is not None:
            self.iport.stopListening()

    def setupListener(self, proto, port=DEFAULT_PORT):
        f = Factory()
        f.protocol = proto
        self.iport = reactor.listenTCP(port, f)

    def createClient(self, port=DEFAULT_PORT):
        def connected(proto):
            self.client = proto
            return proto

        client = ClientCreator(reactor, amp.AMP)
        d = client.connectTCP('127.0.0.1', port)
        d.addCallback(connected)
        return d



class TypedDictionaryTest(AbstractAmptypesTest):

    def abstractTest(self, data, call):
        self.setupListener(TypedDictionaryResponder)
        d = self.createClient()
        d.addCallback(lambda proto : proto.callRemote(call, d=data))
        return d

    def testString(self):
        data = {'one': 'two', 'three':'four'}
        call = TypedDictionaryProtocol1
        d = self.abstractTest(data, call)
        d.addCallback(lambda r : self.failUnlessEqual(r['d'], data))
        return d

    def testUnicode(self):
        data = {u'one': u'two', u'three':u'four'}
        call = TypedDictionaryProtocol2
        d = self.abstractTest(data, call)
        d.addCallback(lambda r : self.failUnlessEqual(r['d'], data))
        return d

    def testInteger(self):
        data = {1:2, 3:4}
        call = TypedDictionaryProtocol3
        d = self.abstractTest(data, call)
        d.addCallback(lambda r : self.failUnlessEqual(r['d'], data))
        return d


class TypedListTest(AbstractAmptypesTest):

    def abstractTest(self, data, call):
        self.setupListener(TypedListResponder)
        d = self.createClient()
        d.addCallback(lambda proto : proto.callRemote(call, l=data))
        return d

    def testString(self):
        data = ['one', 'two', 'three', 'four']
        call = TypedListProtocol1
        d = self.abstractTest(data, call)
        d.addCallback(lambda r : self.failUnlessEqual(r['l'], data))
        return d

    def testUnicode(self):
        data = [u'one', u'two', u'three', u'four']
        call = TypedListProtocol2
        d = self.abstractTest(data, call)
        d.addCallback(lambda r : self.failUnlessEqual(r['l'], data))
        return d

    def testInteger(self):
        data = [1, 2, 3, 4]
        call = TypedListProtocol3
        d = self.abstractTest(data, call)
        d.addCallback(lambda r : self.failUnlessEqual(r['l'], data))
        return d

 


