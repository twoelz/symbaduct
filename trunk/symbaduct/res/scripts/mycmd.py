#!/usr/bin/env python
# -*- coding: UTF-8 -*-

'''
Lineages

Amp Commands (network commands)
'''

from twisted.protocols import amp
# from amptypes import amptypes #uncomment if needed, otherwise leave it here

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# client to server
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class AddClient(amp.Command):
    arguments = [('observer', amp.Boolean())]
    response = [('added', amp.Boolean()),
                ('reason', amp.Unicode()),
                ('ready', amp.Boolean()),
                ('player_count', amp.Integer()),
                ('experiment_pickle', amp.String())]

class ReadyPlayers(amp.Command):
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

# class StartExperiment(amp.Command):
#     response = [('started', amp.Boolean())]

# class SendAdminConfig(amp.Command):
#     response = [('expcfg', amp.String())]

# class Pause(amp.Command):
#     response = []
#
# class UnPause(amp.Command):
#     response = []

# class AllowEndSession(amp.Command):
#     response = []
#
# class AllowEndStableSession(amp.Command):
#     response = []


# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# server to client
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class GameReady(amp.Command):
    response = []

class PlayerLeft(amp.Command):
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

# class ObsLineInfoBeforeConfirm(amp.Command):
#     arguments = [('ident', amp.Integer()),
#                  ('line', amp.Integer()),
#                  ]
#     response = []
#
# class ObsLineInfo(amp.Command):
#     arguments = [('ident', amp.Integer()),
#                  ('line', amp.Integer())
#                  ]
#     response = []
#
# class ObsLineRejection(amp.Command):
#     arguments = [('ident', amp.Integer())]
#     response = []
#
# class ObsHideEndTrialButton(amp.Command):
#     response = []
#
# class GetChat(amp.Command):
#     arguments = [('result', amp.String())]
#     response = []
#
# class ClientPause(amp.Command):
#     arguments = [('pause', amp.Boolean())]
#     response = []

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



class SetButtonHover(amp.Command): # TO SERVER
    arguments = [('button', amp.String()),
                 ('forced', amp.Boolean())]
    response = []

class SetButtonHovered(amp.Command): # FROM SERVER
    arguments = [('button', amp.String()),
                 ('forced', amp.Boolean())]
    response = []

class SetButtonHoverLeave(amp.Command): # TO SERVER
    arguments = [('button', amp.String()),
                 ('forced', amp.Boolean())]
    response = []

class SetButtonHoverLeft(amp.Command): # FROM SERVER
    arguments = [('button', amp.String()),
                 ('forced', amp.Boolean())]
    response = []

class SetButtonPress(amp.Command): # TO SERVER
    arguments = [('button', amp.String())]
    response = []

class SetButtonPressed(amp.Command): # FROM SERVER
    arguments = [('button', amp.String())]
    response = []

class ColorButtonHover(amp.Command): # TO SERVER
    arguments = [('button', amp.Integer()),
                 ('forced', amp.Boolean())]
    response = []

class ColorButtonHovered(amp.Command): # FROM SERVER
    arguments = [('button', amp.Integer()),
                 ('forced', amp.Boolean())]
    response = []

class ColorButtonHoverLeave(amp.Command): # TO SERVER
    arguments = [('button', amp.Integer()),
                 ('forced', amp.Boolean())]
    response = []

class ColorButtonHoverLeft(amp.Command): # FROM SERVER
    arguments = [('button', amp.Integer()),
                 ('forced', amp.Boolean())]
    response = []

class ColorButtonPress(amp.Command): # TO SERVER
    arguments = [('button', amp.Integer())]
    response = []

class ColorButtonPressed(amp.Command): # FROM SERVER
    arguments = [('button', amp.Integer())]
    response = []


class SizeButtonHover(amp.Command): # TO SERVER
    arguments = [('button', amp.Integer()),
                 ('forced', amp.Boolean())]
    response = []

class SizeButtonHovered(amp.Command): # FROM SERVER
    arguments = [('button', amp.Integer()),
                 ('forced', amp.Boolean())]
    response = []

class SizeButtonHoverLeave(amp.Command): # TO SERVER
    arguments = [('button', amp.Integer()),
                 ('forced', amp.Boolean())]
    response = []

class SizeButtonHoverLeft(amp.Command): # FROM SERVER
    arguments = [('button', amp.Integer()),
                 ('forced', amp.Boolean())]
    response = []

class SizeButtonPress(amp.Command): # TO SERVER
    arguments = [('button', amp.Integer())]
    response = []

class SizeButtonPressed(amp.Command): # FROM SERVER
    arguments = [('button', amp.Integer())]
    response = []

    #########################################

class ShapeButtonHover(amp.Command):  # TO SERVER
    arguments = [('button', amp.Integer()),
                 ('forced', amp.Boolean())]
    response = []

class ShapeButtonHovered(amp.Command):  # FROM SERVER
    arguments = [('button', amp.Integer()),
                 ('forced', amp.Boolean())]
    response = []

class ShapeButtonHoverLeave(amp.Command):  # TO SERVER
    arguments = [('button', amp.Integer()),
                 ('forced', amp.Boolean())]
    response = []

class ShapeButtonHoverLeft(amp.Command):  # FROM SERVER
    arguments = [('button', amp.Integer()),
                 ('forced', amp.Boolean())]
    response = []

class ShapeButtonPress(amp.Command):  # TO SERVER
    arguments = [('button', amp.Integer())]
    response = []

class ShapeButtonPressed(amp.Command):  # FROM SERVER
    arguments = [('button', amp.Integer())]
    response = []

class CompositeButtonPress(amp.Command):
    response = []

class CompositeButtonPressed(amp.Command):
    response = []


###########################################
# BIG EVENTS

class EndSession(amp.Command):   # FROM SERVER - TO ALL
    arguments = [('status', amp.String())]
    response = []

class StartFeedback(amp.Command): # FROM SERVER - TO ALL
    arguments = [('points', amp.Integer()),
                 ('total_points', amp.Integer()),
                 ('reset_color', amp.Integer()),
                 ('reset_shape', amp.Integer()),
                 ('reset_size', amp.Integer()),
                 ]
    response = []

class RestartChoice(amp.Command):  # FROM SERVER - TO ALL
    response = []

class ChangePoints(amp.Command):  # FROM SERVER - TO ALL
    response = []

    ##############################
## OBSERVER EVENTS

class UpdateObserver(amp.Command): # FROM SERVER - TO OBSERVER
    arguments = [('cycle', amp.Integer()),
                 ('percent_correct', amp.Float()),
                 ('consec_correct', amp.Integer()),
                 ]
    response = []