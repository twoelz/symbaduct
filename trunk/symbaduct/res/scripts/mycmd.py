#!/usr/bin/env python
# -*- coding: UTF-8 -*-

'''
Lineages

Amp Commands (network commands)
'''

from twisted.protocols import amp
import amptypes

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# client to server
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class AddClient(amp.Command):
    arguments = [('observer', amp.Boolean())]
    response = [('added', amp.Boolean()),
                ('reason', amp.Unicode()),
                ('ready', amp.Boolean()),
                ('player_count', amp.Integer()),
                ('experiment_pickle', amp.String()),
                ('conditions_pickle', amp.String()),
                ]

class ReadyPlayers(amp.Command):
    response = []

class RequestInstructionEnd(amp.Command):
    response = []

class PointPress(amp.Command):
    response = []

class NClick(amp.Command):
    response = []

class FClick(amp.Command):
    response = []



# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# observer to server
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# class AddObserver(amp.Command):
#     response = [('added', amp.Boolean())]


# class SendChat(amp.Command):
#     arguments = [('result', amp.String())]
#     response = []

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# admin to server
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class AddAdmin(amp.Command):
    response = [('experiment_pickle', amp.String()),
                ('group', amp.String())]

class GetModConfig(amp.Command):
    arguments = [('mod_config', amp.String())]
    response = []

class ForceUpdateConfig(amp.Command):
    response = []

class ForceGameReady(amp.Command):
    response = []

class ForcePause(amp.Command):
    response = []

class ForceUnPause(amp.Command):
    response = []


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# server to client
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class GameReady(amp.Command):
    response = []

class InstructionEnd(amp.Command):
    response = []

class PlayerLeft(amp.Command):
    response = []

class UnPauseSession(amp.Command):
    response = []

class PauseSession(amp.Command):
    response = []

class EndExperiment(amp.Command):
    response = []

class AddPoint(amp.Command):
    arguments = [('player', amp.Integer()),
                 ('points', amptypes.TypedList(amp.Integer()))]
    response = []


class ShowAdj(amp.Command):
    arguments = [('show', amp.Boolean())]
    response = []

class ShowInstruction(amp.Command):
    arguments = [('ref', amp.String()),
                 ('target', amp.String())]

    response = []


class RefBack(amp.Command):
    arguments = [('ref_back_pickle', amp.String())]
    response = []

class AdjBack(amp.Command):
    arguments = [('adj_back_pickle', amp.String())]
    response = []

# class NotifyEnd(amp.Command):
#     # arguments = [('end_experiment', amp.Boolean()),
#     #              ('stable', amp.Boolean()),
#     #              ('p_kick', amptypes.TypedList(amp.Integer())),
#     #              ('p_enter', amptypes.TypedList(amp.Integer())),
#     #              ('p_change', amp.Integer()),
#     #              ]
#     response = []

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# server to admin
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# class NotifyEndAdmin(amp.Command):
#     response = []

# class UpdateAdmin(amp.Command):
#     arguments = [('cycle', amp.Integer()),]
#     response = []

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# server to observer
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++



class UpdateObserver(amp.Command):
    arguments = [('info', amp.Unicode()),
                 ]
    response = []


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# examples
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

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


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# main actions
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++



###########################################
# BIG EVENTS

# class EndSession(amp.Command):   # FROM SERVER - TO ALL
#     arguments = [('status', amp.String())]
#     response = []