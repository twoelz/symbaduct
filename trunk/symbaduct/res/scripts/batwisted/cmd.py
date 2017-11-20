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

'''BehavAn Amp Commands (network commands)'''

from twisted.protocols import amp
from amptypes import amptypes #@UnusedImport

# client to server

class AddClient(amp.Command):
    response = []

class ClientReady(amp.Command):
    response = []

# observer to server:

class AddObserver(amp.Command):
    response = []

# admin to server

class AddAdmin(amp.Command):
#    response = [('accepted', amp.Boolean())]
    response = []

class StopServer(amp.Command):
    response = []

# server to client

class AskReady(amp.Command):
    response = []

class SetClientID(amp.Command):
    arguments = [('client_id', amp.Integer())]
    response = []


class ClientLeft(amp.Command):
    response = []


class ObserverLeft(amp.Command):
    response = []


class RejectClient(amp.Command):
    response = []

#class GetConfig(amp.Command):
#    arguments = [('pickle_regioncfg', amp.String()),
#                 ('pickle_expcfg', amp.String()),
#                 ('pickle_s_msg', amp.String()),
#                 ('pickle_net_msg', amp.String()),
#                 ('pickle_message', amp.String()),
#                 ('pickle_layout', amp.String()),
#                 ('pickle_guicfg', amp.String()),
#                 ('pickle_save', amp.String())]
#    response = []
    
class GetConfigRegion(amp.Command):
    arguments = [('pickle_cfg', amp.String())]
    response = []

class GetConfigExp(amp.Command):
    arguments = [('pickle_cfg', amp.String())]
    response = []

class GetConfigS_msg(amp.Command):
    arguments = [('pickle_cfg', amp.String())]
    response = []

class GetConfigNet_msg(amp.Command):
    arguments = [('pickle_cfg', amp.String())]
    response = []

class GetConfigMessage(amp.Command):
    arguments = [('pickle_cfg', amp.String())]
    response = []
class GetConfigLayout(amp.Command):
    arguments = [('pickle_cfg', amp.String())]
    response = []

class GetConfigGUI(amp.Command):
    arguments = [('pickle_cfg', amp.String())]
    response = []

class GetConfigSave(amp.Command):
    arguments = [('pickle_cfg', amp.String())]
    response = []
    
class FixConfigs(amp.Command):
    response = []

class Start(amp.Command):
    response = []
    # TODO: Change Start references to "StartSession", check tests
    
class EndSession(amp.Command):
    arguments = [('status', amp.String())]
    response = []

class StopClient(amp.Command):
    response = []

# server-to-observer

class AcceptObserver(amp.Command):
#    arguments = [('n_clients', amp.Integer())]
    response = []
    
# server-to-admin

class AcceptAdmin(amp.Command):
    response = []

class RejectAdmin(amp.Command):
    response = []    


#class RejectObserver(amp.Command):
#    response = []

# TODO: _z use reject observer?


# example

#class Example(amp.Command):
#    arguments = [('bool', amp.Boolean()),
#                 ('int', amp.Integer()),
#                 ('float', amp.Float()),
#                 ('string', amp.String()),
#                 ('unicode', amp.Unicode()),
#                 ('intlist', amptypes.TypedList(amp.Integer())),
#                 ('stringlist', amptypes.TypedList(amp.String())),
#                 ('floatlist', amptypes.TypedList(amp.Float())),
#                ]
#    response = []
