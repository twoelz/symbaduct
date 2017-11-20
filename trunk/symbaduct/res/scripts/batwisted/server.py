#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# ----------------------------------------------------------------------------
# BehavAn
# Copyright (c) 2010 Thomas Anatol da Rocha Woelz
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of BehavAn nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

'''
BehavAn

Server
'''


import sys
import cPickle as pickle


from behavan import app
from behavan.app import my, options, net_options, exit_app, configobj, ConfigObj, flatten_errors, Validator #@UnusedImport
from behavan.helper import key_generator
#from behavan.convert import utostr #@UnresolvedImport


from twisted.internet import reactor
from twisted.internet.protocol import Factory
from twisted.protocols import amp
from twisted.python import log
import cmd #package import

def bailout(reason):
    ''' close network due to error '''
    reason.printTraceback()
    shutdown()

def shutdown():
    ''' close network gracefully '''
    if options.use_log:
        my.stout.close()
    reactor.stop()

class BAProtocol(amp.AMP):

    def initialize(self):
        self.asked_ready = False
        self.ready = False
        self.obs = False
        self.admin = False

    # AMP methods

    def makeConnection(self, transport):
        '''overrides default TCP delay with no delay'''
        if not transport.getTcpNoDelay():
            transport.setTcpNoDelay(True)
        super(BAProtocol, self).makeConnection(transport)
        self.initialize()

    def connectionLost(self, reason):
        if self.admin:
            self.admin = False
            fac.admin = None
        elif not self.obs:
            if 'c_id' in self.__dict__:
                try:
                    del fac.clients[self.c_id]
                except KeyError:
                    pass
                if fac.session_started and not fac.session_ended:
                    for p in fac.clients.itervalues():
                        p.callRemote(cmd.ClientLeft).addErrback(bailout)
                    if fac.obs_in and fac.observer:
                        fac.observer.callRemote(cmd.ClientLeft
                                            ).addErrback(bailout)
        elif fac.session_started and not fac.session_ended:
            for p in fac.clients.itervalues():
                p.callRemote(cmd.ObserverLeft).addErrback(bailout)
        elif self.obs:
            fac.obs_in = False

        super(BAProtocol, self).connectionLost(reason)

    # command methods

    @cmd.StopServer.responder
    def stop_server(self):
        fac.stop_server()
        return {}

    @cmd.AddClient.responder
    def add_client(self):
        '''client attempts to connect: server allows it if there is
           a free spot'''
        reject = False
        clients = self.get_client_list()
        if len(clients) >= net_options.max_clients or fac.session_started:
            print 'len(clients) is larger than net_options.max_clients, or session was started'
            reject = True
        else:
            c_id = self.next_available_spot(clients)
            if c_id != None:
                self.c_id = c_id
                fac.clients[c_id] = self
                self.send_configs()
                self.callRemote(cmd.SetClientID,
                                client_id = c_id).addCallback(self.client_added\
                                ).addErrback(bailout)
            else:
                reject=True
        if reject:
            print 'client rejected'
            self.callRemote(cmd.RejectClient).addErrback(bailout)
        return{}

    @cmd.AddObserver.responder
    def add_observer(self):
        '''observer attempts to connect: server allows it if there is
           a free spot'''
        if fac.obs_in or fac.session_started:
            msg = my.net_msg['rejected connection']
            self.callRemote(cmd.RejectClient,
                            msg=msg).addErrback(bailout)
        else:
            self.c_id = net_options.observer_id
            fac.observer = self
            self.obs = True
            fac.obs_in = True
            self.send_configs()
            self.callRemote(cmd.AcceptObserver).addErrback(bailout)
        return{}

#    @cmd.AddAdmin.responder
#    def add_admin(self):
#        '''admin attempts to connect: server allows it if there is
#           a free spot'''
#        if fac.admin:
#            print 'admin rejected, one is already active'
#            accepted = False
#        else:
#            self.admin = True
#            fac.admin = self
#            accepted = True
#        return{'accepted':accepted}

    @cmd.AddAdmin.responder
    def add_admin(self):
        '''admin attempts to connect: server allows it if there is
           a free spot'''
        print 'adding admin'
        if fac.admin:
            print 'admin rejected, one is already active'
            self.callRemote(cmd.RejectAdmin).addErrback(bailout)
        else:
            self.admin = True
            fac.admin = self
            self.callRemote(cmd.AcceptAdmin).addErrback(bailout)
        return{}

    @cmd.ClientReady.responder
    def client_ready(self):
        print 'client_ready (BAProtocol @batwisted:server)'
        self.ready = True
        count = 0
        for p in fac.clients.itervalues():
            if p.ready:
                count += 1
        if count >= net_options.min_clients:
            fac.start_session()
        return {}

    def client_added(self, *a, **kw):
        if len(fac.clients) >= net_options.min_clients:
            for p in fac.clients.itervalues():
                if not p.asked_ready:
                    p.callRemote(cmd.AskReady).addErrback(bailout)
                p.asked_ready = True

    # callRemote methods

    def send_configs(self):
        get_config_commands = dict(regioncfg=cmd.GetConfigRegion,
                                   expcfg=cmd.GetConfigExp,
                                   s_msg=cmd.GetConfigS_msg,
                                   net_msg=cmd.GetConfigNet_msg,
                                   message=cmd.GetConfigMessage,
                                   layout=cmd.GetConfigLayout,
                                   guicfg=cmd.GetConfigGUI,
                                   save=cmd.GetConfigSave)
        for config in (x for x in net_options.send_configs if x in my.__dict__.keys()):
            config_dict = my.__dict__[config]
            if not type(config_dict) == dict:
                config_dict = config_dict.dict()
            pickle_cfg = pickle.dumps(config_dict)
            self.callRemote(get_config_commands[config], 
                            pickle_cfg=pickle_cfg).addErrback(bailout)
        self.callRemote(cmd.FixConfigs).addErrback(bailout)

#    def start(self):
#        
#        fac.start()
#        # tell clients the server status and let them start
#        for p in fac.get_clients_and_observer():
#            p.callRemote(cmd.Start).addErrback(bailout)
#
#        # init time and recording vars
#        fac.start_session()

    def next_available_spot(self, clients):
        for number in xrange(0, net_options.max_clients):
            if number not in clients:
                return number
        return None

    def get_client_list(self):
        clients = []
        for client in fac.clients.iterkeys():
            clients.append(client)
        return clients

class BAFactory(Factory, app.ExperimentBase):
    '''A factory that creates and holds data and protocol instances.'''
    protocol = BAProtocol

    def __init__(self):
        app.ExperimentBase.__init__(self)
        self.clients = {}
        self.session_started = False
        self.session_ended = False
        self.observer = None
        self.admin = None

        # observer status
        self.obs_in = False
        
        # callID objects have a cancel method that will cancel the delayed call.
        # we dont need to use references to the functions themselves to cancel them
        del my.schedule_funcs
        my.call_key = key_generator()
        my.delay_calls = {}
        
    def start_session(self):
        # tell clients the server status and let them start
        for p in self.get_clients_and_observer():
            p.callRemote(cmd.Start).addErrback(bailout)
        
#        if 'session' in my.expcfg.keys() and 'time limit in minutes' in my.expcfg['session'].keys():
#            expire_delay = 60 * my.expcfg['session']['time limit in minutes']
#            if expire_delay > 0:
#                my.delay_calls['expire session'] = reactor.callLater(expire_delay, self.expire_session)

        # init time and recording vars
        super(BAFactory, self).start_session()
        self.time_cycle = self.now
#        self.start_session()
        
    def expire_session(self):
        self.unschedule_all()
        self.set_time()
        self.session_ended = True
        for p in self.get_clients_and_observer():
            p.callRemote(cmd.EndSession,
                         status = 'expired').addErrback(bailout)
        self.record_end(my.output_labels['session time ended'])

    def end_session(self):
        self.unschedule_all()
        self.set_time()
        self.session_ended = True
        for p in self.get_clients_and_observer():
            p.callRemote(cmd.EndSession,
                         status = '').addErrback(bailout)
        self.record_end()

    def get_clients_and_observer(self):
        ps = self.clients.values()
        if fac.obs_in:
            ps.append(self.observer)
        return ps
    
    def stop_server(self):
        self.session_ended = True
        self.unschedule_all()
        for p in self.get_clients_and_observer():
            p.callRemote(cmd.StopClient)
        reactor.callLater(2, shutdown)
        
    def unschedule_all(self):
        '''Unschedule every possible delayed function call.'''
        # callID objects have a cancel method that will cancel the delayed call.
        for call_id in my.delay_calls.values():
            if call_id.active():
                call_id.cancel()

fac = None
def main():
    global fac
    app.PrepareBase()
    fac = BAFactory()
    log.startLogging(sys.stdout)
    reactor.listenTCP(my.network['port'], fac)
    reactor.run()
    
    
if __name__ == "__main__":
    import traceback
    try:
        main()
    except:
        traceback.print_exc()
        if options.use_log:
            my.stout.close()
