#!/usr/bin/env python
# -*- coding: UTF-8 -*-

'''
symbaduct

Server
'''

# symbaduct server
# Copyright (c) 2017 Thomas Anatol da Rocha Woelz
# All rights reserved.
# BSD type license: check doc folder for details

__version__ = '0.0.1'
__docformat__ = 'restructuredtext'
__author__ = 'Thomas Anatol da Rocha Woelz'

# standard library imports
import sys
import os
import random
import csv
import codecs
import time
import copy
import cPickle as pickle
import datetime

# set local path constants
DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(DIR, 'res', 'scripts')))
for dependency_folder in ['standout',
                          'easygui',
                          'configobj',
                          'amptypes',
                          'configobj']:
    sys.path.insert(0, os.path.abspath(os.path.join(DIR,
                                                    'res',
                                                    'scripts',
                                                    'dependencies',
                                                    dependency_folder)))
# twisted imports
from twisted.internet import reactor
from twisted.internet.protocol import Factory
from twisted.protocols import amp
from twisted.python import log

# included dependency imports:
from standout import StandOut
from configobj import ConfigObj
from configobj import flatten_errors
from validate import Validator
from validate import ValidateError
import easygui as eg

# DECIMAL import
try:
    import cdecimal as decimal
    from cdecimal import Decimal
except ImportError:
    print 'cdecimal not found, using standard (slower) decimal module'
    import decimal
    from decimal import Decimal

# all further rounding for decimal class is rounded up
decimal.getcontext().rounding = decimal.ROUND_UP

# import my scripts
import mycmd as cmd
from common_code import validate_config, PORT, LOCALTIME, LANG, DECIMAL_SEPARATOR, CSV_SEPARATOR
from convert import utostr, n_uni


class Container(object):
    pass


def bailout(reason):
    ''' close network due to error '''
    reason.printTraceback()
    shutdown()


def shutdown():
    ''' close network gracefully '''
    if stout:
        stout.close()
    reactor.stop()


class Protocol(amp.AMP):
    def __init__(self, *args, **kwargs):
        super(Protocol, self).__init__(*args, **kwargs)
        self.admin = False
        self.observer = False
        self.client_count = None

    def initialize(self):
        pass
        # self.admin = False
        # self.observer = False
        # two above done by adding attribute directly to class

        # ADD PROTOCOL VARIABLES HERE
        # self.asked_ready = False
        # self.ready = False
        # self.obs = False

    # AMP methods

    def makeConnection(self, transport):
        '''overrides default TCP delay with no delay'''
        if not transport.getTcpNoDelay():
            transport.setTcpNoDelay(True)
        super(Protocol, self).makeConnection(transport)
        self.initialize()

    def connectionLost(self, reason):
        if self.admin:
            self.admin_lost()
        elif self.observer:
            self.observer_lost()
        else:
            self.player_lost()

        # elif not self.obs:
        #     if 'c_id' in self.__dict__:
        #         try:
        #             del fac.clients[self.c_id]
        #         except KeyError:
        #             pass
        #         if fac.session_started and not fac.session_ended:
        #             for p in fac.clients.itervalues():
        #                 p.callRemote(cmd.ClientLeft).addErrback(bailout)
        #             if fac.obs_in and fac.observer:
        #                 fac.observer.callRemote(cmd.ClientLeft
        #                                     ).addErrback(bailout)
        # elif fac.session_started and not fac.session_ended:
        #     for p in fac.clients.itervalues():
        #         p.callRemote(cmd.ObserverLeft).addErrback(bailout)
        # elif self.obs:
        #     fac.obs_in = False

        super(Protocol, self).connectionLost(reason)

    def admin_lost(self):
        self.admin = False
        fac.admin = None

    def observer_lost(self):
        self.observer = False

    def player_lost(self):
        if self.client_count is not None:
            fac.players.pop(self.client_count)
            self.client_count = None
        else:
            return
        if fac.session_started:
            # TODO: move below to fac method?
            fac.session_started = False
            if len(fac.players) < cfg.exp['main']['players']:
                fac.accept_player = True
            # TODO: reset cycle stuff here (or call method for it)
            for p in fac.players.itervalues():
                p.callRemote(cmd.PlayerLeft)
            for p in fac.observers.itervalues():
                p.callRemote(cmd.PlayerLeft)

                # if fac.experiment
                # check if observer left

    # command methods

    # @cmd.StopServer.responder
    # def stop_server(self):
    #     fac.stop_server()
    #     return {}

    @cmd.AddClient.responder
    def add_client(self, observer):
        '''client attempts to connect: server allows it if there is
           a free spot'''
        print 'try to add client'
        fac.set_time(event=False)
        accept = True
        ready = False
        reason = ''
        player_count = 0

        if observer:
            while player_count in fac.observers.keys():
                player_count += 1
            self.client_count = player_count
            print "observer count:", self.client_count
            fac.observers[player_count] = self
            fac.obs_in = True
            self.observer = True

        elif fac.accept_player and len(fac.players) < cfg.exp['main']['players']:
            print 'got a new player'

            while player_count in fac.players.keys():
                player_count += 1
            self.client_count = player_count
            fac.players[player_count] = self
            if len(fac.players) == cfg.exp['main']['players']:
                print 'ready!'
                ready = True
                fac.accept_player = False
        else:
            print 'player rejected'
            accept = False
            reason = cfg.s_msg['server full']

        print 'current players:', len(fac.players)
        print cfg.exp['main']['players']
        print 'was accepted?', accept
        print 'is ready?', ready
        print 'player count?', type(player_count), player_count
        return {'added': accept,
                'reason': reason,
                'ready': ready,
                'player_count': player_count,
                'experiment_pickle': pickle.dumps(cfg.exp)}

    @cmd.ReadyPlayers.responder
    def ready_players(self):
        fac.start_session()
        for p in fac.players.itervalues():
            p.callRemote(cmd.GameReady)
        for p in fac.observers.itervalues():
            p.callRemote(cmd.GameReady)
        return {}

    @cmd.AddAdmin.responder
    def add_admin(self):
        '''admin attempts to connect:
        server kicks previous admin if there is one'''

        if fac.admin is not None:
            print 'kicking previous admin'
            if fac.admin.transport:
                fac.admin.transport.loseConnection()
            fac.admin = None

        self.admin = True
        fac.admin = self
        experiment_pickle = pickle.dumps(cfg.exp)
        return {'experiment_pickle': pickle.dumps(cfg.exp),
                'group': fac.group}

    @cmd.GetModConfig.responder
    def get_mod_config(self, mod_config):
        fac.set_time()
        print 'mod config received!'
        mod_config = pickle.loads(mod_config)
        print 'mod_config:', mod_config
        fac.get_mod_config(mod_config)
        # print mod_config
        return {}

    @cmd.ForceUpdateConfig.responder
    def force_update_config(self):
        fac.update_config()
        return {}

    # MAIN actions

    @cmd.PointPress.responder
    def point_press(self):
        fac.point_press(self.client_count)
        # fac.set_time()
        #
        # fac.points[self.client_count] += 1
        #
        # for p in fac.get_players_and_observer():
        #     p.callRemote(cmd.AddPoint,
        #                     player=self.client_count,
        #                     points=fac.points)
        return {}

    # @cmd.SetButtonHover.responder
    # def set_button_hover(self, button, forced):
    #     print 'got to set button hover responder. forced =', forced
    #     fac.set_time()
    #     for p in fac.get_players_and_observer():
    #         p.callRemote(cmd.SetButtonHovered,
    #                      button=button,
    #                      forced=forced).addErrback(bailout)
    #     if not forced:
    #         fac.record_set_button_hover(button, self.client_count)
    #     return {}
    #
    # @cmd.SetButtonHoverLeave.responder
    # def set_button_hover_leave(self, button, forced):
    #     fac.set_time()
    #     for p in fac.get_players_and_observer():
    #         p.callRemote(cmd.SetButtonHoverLeft,
    #                      button=button,
    #                      forced=forced).addErrback(bailout)
    #     return {}
    #
    # @cmd.SetButtonPress.responder
    # def set_button_press(self, button):
    #     fac.set_time()
    #     for p in fac.get_players_and_observer():
    #         p.callRemote(cmd.SetButtonPressed,
    #                      button=button).addErrback(bailout)
    #     fac.record_set_button_press(button, self.client_count)
    #     return {}
    #
    # @cmd.ColorButtonHover.responder
    # def color_button_hover(self, button, forced):
    #     fac.set_time()
    #     for p in fac.get_players_and_observer():
    #         p.callRemote(cmd.ColorButtonHovered,
    #                      button=button,
    #                      forced=forced).addErrback(bailout)
    #     if not forced:
    #         fac.record_color_button_hover(button, self.client_count)
    #     return {}
    #
    # @cmd.ColorButtonHoverLeave.responder
    # def color_button_hover_leave(self, button, forced):
    #     fac.set_time()
    #     for p in fac.get_players_and_observer():
    #         p.callRemote(cmd.ColorButtonHoverLeft,
    #                      button=button,
    #                      forced=forced).addErrback(bailout)
    #     return {}
    #
    # @cmd.ColorButtonPress.responder
    # def color_button_press(self, button):
    #     fac.set_time()
    #     for p in fac.get_players_and_observer():
    #         p.callRemote(cmd.ColorButtonPressed,
    #                      button=button).addErrback(bailout)
    #     fac.record_color_button_press(button, self.client_count)
    #     return {}
    #
    #
    # @cmd.SizeButtonHover.responder
    # def size_button_hover(self, button, forced):
    #     fac.set_time()
    #     for p in fac.get_players_and_observer():
    #         p.callRemote(cmd.SizeButtonHovered,
    #                      button=button,
    #                      forced=forced).addErrback(bailout)
    #     if not forced:
    #         fac.record_size_button_hover(button, self.client_count)
    #     return {}
    #
    # @cmd.SizeButtonHoverLeave.responder
    # def size_button_hover_leave(self, button, forced):
    #     fac.set_time()
    #     for p in fac.get_players_and_observer():
    #         p.callRemote(cmd.SizeButtonHoverLeft,
    #                      button=button,
    #                      forced=forced).addErrback(bailout)
    #     return {}
    #
    # @cmd.SizeButtonPress.responder
    # def color_button_press(self, button):
    #     fac.set_time()
    #     for p in fac.get_players_and_observer():
    #         p.callRemote(cmd.SizeButtonPressed,
    #                      button=button).addErrback(bailout)
    #     fac.record_size_button_press(button, self.client_count)
    #     return {}
    #
    #
    # @cmd.ShapeButtonHover.responder
    # def shape_button_hover(self, button, forced):
    #     fac.set_time()
    #     for p in fac.get_players_and_observer():
    #         p.callRemote(cmd.ShapeButtonHovered,
    #                      button=button,
    #                      forced=forced).addErrback(bailout)
    #     if not forced:
    #         fac.record_shape_button_hover(button, self.client_count)
    #     return {}
    #
    # @cmd.ShapeButtonHoverLeave.responder
    # def shape_button_hover_leave(self, button, forced):
    #     fac.set_time()
    #     for p in fac.get_players_and_observer():
    #         p.callRemote(cmd.ShapeButtonHoverLeft,
    #                      button=button,
    #                      forced=forced).addErrback(bailout)
    #     return {}
    #
    # @cmd.ShapeButtonPress.responder
    # def color_button_press(self, button):
    #     fac.set_time()
    #     for p in fac.get_players_and_observer():
    #         p.callRemote(cmd.ShapeButtonPressed,
    #                      button=button).addErrback(bailout)
    #     fac.record_shape_button_press(button, self.client_count)
    #     return {}
    #
    # @cmd.CompositeButtonPress.responder
    # def composite_button_press(self):
    #     fac.set_time()
    #     for p in fac.get_players_and_observer():
    #         p.callRemote(cmd.CompositeButtonPressed).addErrback(bailout)
    #     # TODO: check stability, and schedule next choice
    #     fac.choice_made(self.client_count)
    #
    #     return {}


class SymbaductFactory(Factory):
    '''A factory that creates and holds data and protocol instances.'''
    protocol = Protocol

    # starting

    def __init__(self, group):
        self.mod_config = {}  # configs modified by admin
        self.admin = None
        self.group = group
        self.session_started = False
        self.accept_player = True
        self.players = {}
        self.observers = {}

        # observer status
        self.obs_in = False

        self.delay_calls = {}

        # experiment variables

        self.points = [0, 0]
        self.count_click = [0, 0]
        # options: ratio, interval, (?)
        self.schedule = ['interval', 'ratio']
        self.ratio = [5, 5]
        self.interval = [3.0, 3.0]

        # self.active_set = 'color'
        # self.active_color = 1
        # self.active_shape = 1
        # self.active_size = 1
        # self.n_correct = 0
        # self.points = 0
        # self.total_points = 0
        #
        # self.reset_color = self.active_color
        # self.reset_shape = self.active_shape
        # self.reset_size = self.active_size

        # time variables
        self.hour = '-'.join([str(x) for x in time.localtime()[:4]])
        self.time_started = time.time()
        self.now = 0
        self.time_cycle = self.now
        self.event = 0
        self.previous_event = self.event
        self.time_press = [0, 0]
        self.time_previous_press = [0, 0]
        self.time_previous_point_press = [0, 0]
        self.time_point_press = [0, 0]
        self.time_schedule = [0, 0]
        # self.time_start_choice = 0
        # self.time_choice = 0

        # end variables
        self.end = False
        self.end_reason = ''

        # observer variables
        # self.percent_correct = 0.0
        # self.consec_correct = 0

        # to be defined @ create output
        self.output_path = ''
        self.line = {}

        self.create_output()

    def set_time(self, event=True):
        self.now = time.time() - self.time_started
        self.hour = '-'.join([str(x) for x in time.localtime()[:4]])
        if event:
            self.previous_event = self.event
            self.event = self.now

    def start_session(self):
        self.time_started = time.time()
        self.hour = '-'.join([str(x) for x in time.localtime()[:4]])
        self.now = 0
        self.event = 0
        self.previous_event = 0
        self.session_started = True
        if cfg.exp['end_criteria']['use session duration']:
            expire_delay = cfg.exp['durations']['session'] * 60
            self.delay_calls['expire session'] = reactor.callLater(expire_delay, self.expire_session)
        self.record_session_start()

    def create_output(self):
        ''' creates the output file '''
        csv_string = 'grupo-{}.csv'.format(self.group)
        self.output_path = os.path.join(DIR, 'output', csv_string)
        if os.path.exists(self.output_path):
            mode = 'a'
        else:
            mode = 'w'
        output_file = codecs.open(self.output_path, mode, 'iso-8859-1')

        # record_labels

        l = ['hour',
             'event',
             'description',
             'cycle',
             'player',
             'response',
             u't_start',
             't_response',
             u'latency',
             'ref_points',
             'target_points']

        data_string = ';'.join([unicode(x) for x in l]) + u'\n'
        output_file.write(data_string)
        output_file.close()
        self.line = dict(
            hour='',
            event='',
            description='',
            cycle='',
            player='',
            response='',
            t_start='',
            t_response='',
            latency='',
            ref_points='',
            target_points='')

        data = dict(self.line,
                    event=u'start server',
                    hour=self.hour,
                    t_start=0,
                    t_response=0)
        self.record_line(**data)

    def record_line(self, **data):
        d = data
        d_list = [
            d['hour'],
            d['event'],
            d['description'],
            d['cycle'],
            d['player'],
            d['response'],
            d['t_start'],
            d['t_response'],
            d['latency'],
            d['ref_points'],
            d['target_points']]

        data_string = ';'.join([unicode(x) for x in d_list]) + u'\n'

        output_file = codecs.open(self.output_path, 'a', 'iso-8859-1')
        output_file.write(data_string)
        output_file.close()

    def get_mod_config(self, mod_config):
        self.set_time(event=False)
        for k in mod_config.keys():
            if type(mod_config[k]) == dict:
                if k not in self.mod_config.keys():
                    self.mod_config[k] = {}
                self.mod_config[k].update(mod_config[k])
                # for subk in mod_config[k].keys():
                #     self.mod_config[k][subk] = mod_config[k][subk]
            else:
                self.mod_config[k] = mod_config[k]
        if not self.session_started:
            self.update_config()
        else:
            self.record_config_update(changed=False)

    def update_config(self):
        #
        for k in self.mod_config.keys():
            if type(self.mod_config[k]) == dict:
                cfg.exp[k].update(copy.deepcopy(self.mod_config[k]))
                # for subk in self.mod_config[k].keys():
                #     cfg.exp[k][subk] = copy.deepcopy(self.mod_config[k][subk])
            else:
                cfg.exp[k] = copy.deepcopy(self.mod_config[k])
        cfg.exp.write()
        self.record_config_update(changed=True)
        self.mod_config = {}

    def record_config_update(self, changed=False):
        # TODO: fix recording this
        mod = str(self.mod_config)
        mod = mod[1:-1]
        replace = (('{', '['), ('}', ']'), ("'", ''), (',', ' |'))
        for item in replace:
            mod = mod.replace(item[0], item[1])
        event = 'config to change'
        if changed:
            event = 'config changed'
        data = dict(self.line,
                    event=event,
                    hour=self.hour,
                    description=mod)
        self.record_line(**data)

        print 'mod', mod

    # def record_set_button_hover(self, button, player):
    #     print 'got to record set button hover'
    #     data = dict(self.line,
    #                 event='set button hover',
    #                 hour=self.hour,
    #                 description='hover',
    #                 cycle=cfg.exp['save']['cycle'] + 1,
    #                 player=player + 1,
    #                 response=button,
    #                 t_start=n_uni(self.previous_event),
    #                 t_response=n_uni(self.event),
    #                 latency=n_uni(self.event - self.previous_event),
    #                 )
    #     self.record_line(**data)
    #     print data

    def set_time_press(self):
        self.time_previous_press = self.time_press
        self.time_press = self.now

    def point_press(self, player):
        self.set_time()
        self.time_previous_press[player] = self.time_press[player]
        self.time_press[player] = self.now
        self.time_previous_point_press[player] = self.time_point_press[player]
        self.time_point_press[player] = self.now

        add_point = False

        schedule = self.schedule[player]
        if schedule == 'ratio':

            self.count_click[player] += 1

            if self.count_click[player] == self.ratio[player]:
                self.count_click[player] = 0
                add_point = True

        elif schedule == 'interval':
            if self.now - self.time_schedule[player] >= self.interval[player]:
                self.time_schedule[player] = self.now
                add_point = True

        if add_point:
            self.add_point(player)

    def add_point(self, player):
        self.points[player] += 1
        for p in self.get_players_and_observer():
            p.callRemote(cmd.AddPoint,
                         player=player,
                         points=self.points)

    #
    # def record_choice(self, player): #CHOICE
    #     print 'got to record choice'
    #     self.set_time_press()
    #     self.time_start_choice = self.time_choice
    #     self.time_choice = self.now
    #     data = dict(self.line,
    #                 event='choice',
    #                 hour=self.hour,
    #                 description='composite press',
    #                 cycle=cfg.exp['save']['cycle'] + 1,
    #                 player=player + 1,
    #                 t_start=n_uni(self.time_start_choice),
    #                 t_response=n_uni(self.time_choice),
    #                 latency=n_uni(self.time_choice - self.time_start_choice),
    #                 color=self.active_color,
    #                 shape=self.active_shape,
    #                 size=self.active_size,
    #                 n_correct=self.n_correct,
    #                 points=self.points,
    #                 total=self.total_points,
    #                 )
    #     self.record_line(**data)
    #     print data

    # def record_start_choice(self): #CHOICE
    #     print 'got to record choice'
    #     data = dict(self.line,
    #                 event='start choice',
    #                 hour=self.hour,
    #                 description='',
    #                 cycle=cfg.exp['save']['cycle'] + 1,
    #                 t_start=n_uni(self.now),
    #                 color=self.active_color,
    #                 shape=self.active_shape,
    #                 size=self.active_size,
    #                 total=self.total_points,
    #                 )
    #     self.record_line(**data)
    #     print data

    #
    # def choice_made(self, player):
    # self.n_correct = 0
    # if cfg.exp['valid_colors']['color {}'.format(self.active_color)]:
    #     self.n_correct += 1
    # if cfg.exp['valid_shapes']['shape {}'.format(self.active_shape)]:
    #     self.n_correct += 1
    # if cfg.exp['valid_sizes']['size {}'.format(self.active_size)]:
    #     self.n_correct += 1
    # self.points = cfg.exp['game_points']['{} correct'.format(self.n_correct)]
    # # self.total_points += self.points
    #
    #
    # self.record_choice(player)
    # cfg.exp['save']['cycle'] += 1
    # if self.n_correct >= cfg.exp['performance_criteria']['corrects required']:
    #     cfg.exp['save']['window results'].append(True)
    # else:
    #     cfg.exp['save']['window results'].append(False)
    # window_size = cfg.exp['performance_criteria']['window size']
    # cfg.exp['save']['window results'] = cfg.exp['save']['window results'][-1*window_size:]
    # cfg.exp.write()
    # self.check_end_criteria()
    # self.update_observer()
    # self.update_config()

    # def update_observer(self):
    #     for p in self.get_observer():
    #         p.callRemote(cmd.UpdateObserver,
    #                      cycle=cfg.exp['save']['cycle'],
    #                      percent_correct=self.percent_correct,
    #                      consec_correct=self.consec_correct,
    #                      ).addErrback(bailout)

    # def check_end_criteria(self):
    #     cri = cfg.exp['end_criteria']
    #     win = cfg.exp['save']['window results']
    #     len_win = len(win)
    #     true_count = win.count(True)
    #     # self.percent_correct = float(true_count) / len_win
    #     # self.consec_correct = 0
    #     for i in win[::-1]:
    #         if i:
    #             self.consec_correct += 1
    #         else:
    #             break
    #     cycle = cfg.exp['save']['cycle']
    #     if cycle < cri['min cycles']:
    #         return
    #     if cycle > cri['max cycles']:
    #         self.end = True
    #         self.end_reason += '-max cycles'
    #     if cri['use performance criteria']:
    #         per = cfg.exp['performance_criteria']
    #         if len_win < per['window size']:
    #             return
    #         if float(true_count) / len_win >= per['percent correct']:
    #             consec = per['consecutive correct']
    #             if consec == 0 or win[-1*consec:].count(False) == 0:
    #                 self.end = True
    #                 self.end_reason += '-perf criteria'
    #
    # def start_feedback(self):
    #     for p in self.get_players_and_observer():
    #         p.callRemote(cmd.StartFeedback,
    #                      points=self.points,
    #                      total_points=self.total_points,
    #                      reset_color=self.reset_color,
    #                      reset_shape=self.reset_shape,
    #                      reset_size=self.reset_size,
    #                      ).addErrback(bailout)
    #     self.delay_calls['change points'] = reactor.callLater(cfg.exp['durations']['delay change points'],
    #                                                           self.change_points)
    #     self.delay_calls['restart_choice'] = reactor.callLater(cfg.exp['durations']['feedback'],
    #                                                            self.restart_choice)

    # def restart_choice(self):
    #     if self.end:
    #         self.end_session(self.end_reason)
    #         return
    #     self.set_time()
    #     self.set_time_press()
    #     self.time_choice = self.now
    #     self.active_color = self.reset_color
    #     self.active_shape = self.reset_shape
    #     self.active_size = self.reset_size
    #     self.record_start_choice()
    #     for p in self.get_players_and_observer():
    #         p.callRemote(cmd.RestartChoice).addErrback(bailout)

    # def change_points(self):
    #     for p in self.get_players_and_observer():
    #         p.callRemote(cmd.ChangePoints).addErrback(bailout)

    def expire_session(self):
        if self.end:
            return
        self.end = True
        self.end_reason += '-expired'

        # self.end_session('expired')

    def end_session(self, status='criteria'):
        self.unschedule_all()
        self.set_time()
        for p in self.get_players_and_observer():
            p.callRemote(cmd.EndSession,
                         status=status).addErrback(bailout)
        self.record_end(status)

    def record_end(self, reason):
        data = dict(self.line,
                    event='end session',
                    hour=self.hour,
                    description=reason,
                    cycle=cfg.exp['save']['cycle'] + 1,
                    t_start=n_uni(0),
                    t_response=n_uni(self.now),
                    )
        self.record_line(**data)

    def record_session_start(self):
        data = dict(self.line,
                    event='start session',
                    hour=self.hour,
                    cycle=cfg.exp['save']['cycle'] + 1,
                    t_start=n_uni(0))
        self.record_line(**data)

    #
    def get_players_and_observer(self):
        ps = self.players.values()
        for i in self.observers.values():
            ps.append(i)
        return ps

    def get_observer(self):
        ps = []
        for i in self.observers.values():
            ps.append(i)
        return ps

    def unschedule_all(self):
        '''Unschedule every possible delayed function call.'''
        # callID objects have a cancel method that will cancel the delayed call.
        for call_id in self.delay_calls.values():
            if call_id.active():
                call_id.cancel()


# globals
stout = None
fac = None
# save = None
cfg = Container()


def eg_cancel_program():
    """Shows a dialog informing the program is cancelled."""

    eg.msgbox(cfg.s_msg['cancel program'])
    exit_app()


def exit_app():
    print 'exit_app'
    if stout:
        stout.close()
    sys.exit(0)
    # just in case we just closed a thread or exception was caught we force the exit
    os._exit(1)


def create_dirs():
    # redirect sdtout and stderr to log file
    if not os.path.exists(os.path.join(DIR, 'output', 'log', 'observer')):
        os.mkdir(os.path.join(DIR, 'output', 'log', 'observer'))
    stout = StandOut(logfile=os.path.join(DIR, 'output', 'log', 'observer',
                                          'log%s.txt' % LOCALTIME))


def string_to_bool(some_string):
    result = utostr(some_string)
    return result.lower() in ['true', 'yes', 'sim']


def get_experiment(exp_dir, define_experiment):
    if define_experiment:
        experiment = cfg.server['experiment']
        return experiment
    experiments = [x[:-4] for x in os.listdir(exp_dir) if '.ini' in x]
    # dialog asks for an experiment
    experiment = eg.choicebox(cfg.s_msg['run which experiment'], choices=experiments)
    if experiment is None:
        # user closed choice box
        eg_cancel_program()
    return experiment


def get_group(save_dir, define_group):
    if define_group:
        group = cfg.server['group']
        return group
    # load configs
    groups = [x for x in os.listdir(save_dir) if '.' not in x]
    add_new = cfg.s_msg['create new group']
    groups.append(add_new)

    # dialog asks for a group
    group = eg.choicebox(cfg.s_msg['run which group'], choices=groups)
    if group is None:
        # user closed choice box
        eg_cancel_program()
    elif group == add_new:
        # user chose to add a new subject
        group = ''
        while group == '':
            group = eg.enterbox(msg=cfg.s_msg['type group name'],
                                title=cfg.s_msg['new group'],
                                default='',
                                strip=True)
            if group == '':
                continue
            elif group is None:
                eg_cancel_program()
            group = utostr(group)
            group = group.lower()
            if group in groups:
                eg.msgbox(cfg.s_msg['group exists'].format(group))
                group = ''
                continue
    return group


def main():
    global fac
    global stout
    # CREATE DIRS AND STOUT

    # redirect sdtout and stderr to log file
    if not os.path.exists(os.path.join(DIR, 'output', 'log', 'server')):
        os.mkdir(os.path.join(DIR, 'output', 'log', 'server'))

    stout = StandOut(logfile=os.path.join(DIR, 'output', 'log', 'server',
                                          'log%s.txt' % LOCALTIME))

    cfg_dir = os.path.join(DIR, 'config')
    save_dir = os.path.join(cfg_dir, 'saved')
    exp_dir = os.path.join(cfg_dir, 'experiments')

    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
    spec_dir = os.path.join(cfg_dir, 'spec')
    lang_dir = os.path.join(cfg_dir, 'lang', LANG)

    # server messages config
    cfg.s_msg = ConfigObj(infile=os.path.join(lang_dir, 'server_messages.ini'),
                          configspec=os.path.join(spec_dir, 'spec_server_messages.ini'),
                          encoding='UTF8')

    # load server config

    cfg.server = ConfigObj(infile=os.path.join(cfg_dir, 'server.ini'),
                           configspec=os.path.join(spec_dir, 'spec_server.ini'),
                           encoding='UTF8')
    validate_config(cfg.server)

    define_group = string_to_bool(cfg.server['define group'])
    group = get_group(save_dir, define_group)

    save_dir = os.path.join(save_dir, group)
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)

    save_dir_files = [x for x in os.listdir(save_dir) if '.ini' in x]

    experiment_filename = group + '_experiment.ini'
    contains_experiment = experiment_filename in save_dir_files

    if contains_experiment:
        cfg.exp = ConfigObj(infile=os.path.join(save_dir, experiment_filename),
                            configspec=os.path.join(spec_dir, 'spec_experiment.ini'))
        validate_config(cfg.exp)

    else:
        define_experiment = string_to_bool(cfg.server['define experiment'])
        experiment = get_experiment(exp_dir, define_experiment)
        cfg.exp = ConfigObj(infile=os.path.join(exp_dir, experiment + '.ini'),
                            configspec=os.path.join(spec_dir, 'spec_experiment.ini'))

        # validating but PRESERVING comments (set_copy=True also copies spec comments)
        pre_copy_comments = copy.deepcopy(cfg.exp.comments)
        pre_copy_final_comment = copy.deepcopy(cfg.exp.final_comment)
        validate_config(cfg.exp, set_copy=True)
        cfg.exp.comments = pre_copy_comments
        cfg.exp.final_comment = pre_copy_final_comment

        cfg.exp.filename = os.path.join(save_dir, experiment_filename)
        cfg.exp.initial_comment = ['# experiment: {}\n# group: {}'.format(experiment, group), ' ']

        cfg.exp.write()

    fac = SymbaductFactory(utostr(group))
    log.startLogging(sys.stdout)
    reactor.listenTCP(PORT, fac)
    reactor.run()


if __name__ == "__main__":
    import traceback

    try:
        main()
    except:
        traceback.print_exc()
        if stout:
            stout.close()
