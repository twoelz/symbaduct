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

os.environ["DECIMAL_SEPARATOR"] = DECIMAL_SEPARATOR
os.environ["CSV_SEPARATOR"] = CSV_SEPARATOR

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


def text_to_list(text):
    text = text.replace(' ', '')
    return text.split(',')


class Protocol(amp.AMP):
    def __init__(self, *args, **kwargs):
        super(Protocol, self).__init__(*args, **kwargs)
        self.admin = False
        self.observer = False
        self.client_count = None

    def initialize(self):
        pass

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
            # if len(fac.players) < cfg.exp['main']['players']:
            if len(fac.players) < 2:
                fac.accept_player = True
            # TODO: reset stuff here (or call method for it)
            for p in fac.players.itervalues():
                p.callRemote(cmd.PlayerLeft)
            for p in fac.observers.itervalues():
                p.callRemote(cmd.PlayerLeft)

                # if fac.experiment
                # check if observer left

    # command methods

    @cmd.AddClient.responder
    def add_client(self, observer):
        '''client attempts to connect: server allows it if there is
           a free spot'''
        fac.set_time()
        accept = True
        ready = False
        reason = ''
        player_count = 0

        if observer:
            while player_count in fac.observers.keys():
                player_count += 1
            self.client_count = player_count
            fac.observers[player_count] = self
            fac.obs_in = True
            self.observer = True

        # elif fac.accept_player and len(fac.players) < cfg.exp['main']['players']:
        elif fac.accept_player and len(fac.players) < 2:
            while player_count in fac.players.keys():
                player_count += 1
            self.client_count = player_count
            fac.players[player_count] = self

            # if len(fac.players) == cfg.exp['main']['players']:
            if len(fac.players) == 2:
                ready = True
                fac.accept_player = False
        else:
            print 'player rejected'
            accept = False
            reason = cfg.s_msg['server full']

        return {'added': accept,
                'reason': reason,
                'ready': ready,
                'player_count': player_count,
                'experiment_pickle': pickle.dumps(cfg.exp),
                'conditions_pickle': pickle.dumps(cfg.conds)}

    @cmd.ReadyPlayers.responder
    def ready_players(self):
        if fac.session_started:
            return {}
        for p in fac.get_players_and_observer():
            p.callRemote(cmd.GameReady)

        fac.start_session()

        return {}

    @cmd.RequestInstructionEnd.responder
    def request_instruction_end(self):
        for p in fac.get_players_and_observer():
            p.callRemote(cmd.InstructionEnd)
        fac.reset_time_variables()
        fac.start_time_limit()
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
        return {}

    @cmd.NClick.responder
    def n_click(self):
        fac.fn_click(self.client_count, 'n')
        return {}

    @cmd.FClick.responder
    def f_click(self):
        fac.fn_click(self.client_count, 'f')
        return {}


    # ADMIN METHODS

    @cmd.ForceGameReady.responder
    def force_game_ready(self):
        if len(fac.players):
            self.ready_players()
        return {}

    @cmd.ForcePause.responder
    def force_pause(self):
        fac.pause_session()
        return {}

    @cmd.ForceUnPause.responder
    def force_unpause(self):
        fac.unpause_session()
        return {}

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
        self.all_click = 0
        self.ref_click = 0
        self.adj_click = 0
        self.all_press = 0
        self.ref_press = 0
        self.adj_press = 0
        self.ref_fn_click = 0
        self.adj_fn_click = 0

        self.ref_fn_lock_click = 0
        self.adj_fn_lock_click = 0

        self.points = [0, 0]
        self.count_ratio_click = [0, 0]
        self.conditions = text_to_list(cfg.exp['conditions']['conditions'])
        self.ref_schedule = []
        self.adj_schedule = []
        self.point_counter = 0
        self.fn_invert = False
        self.fn_invert_counter = 0
        # fn_status: 0 = lower, 2 = higher, 1 = default/middle
        self.fn_status = 1

        # frequencies by condition and local (10 ultimas)
        self.freq_cond = 0
        self.freq_local = 0

        # latencies by condition and
        self.latency_cond = 0
        self.latency_local = []

        # lists for multiple schedule settings
        self.mult_sched = []

        self.fn_reduce_change = 0
        self.fn_increase_change = 0  # not doing anything with it
        self.fn_total_change = 0

        self.fn_reduce_lock_change = 0
        self.fn_increase_lock_change = 0  # not doing anything with it
        self.fn_total_lock_change = 0

        self.fn_percent_reduce = 'N/A'

        self.fn_trial = 0
        self.fn_trials = []

        self.fn_setup = None
        # fn_setup = None means first choice lowers
        # fn_setup = 1 means f lowers, n raises
        # fn_setup = 0 means f raises, n lowers

        # STATUSES
        self.condition_name = ''
        self.condition_ended = False
        self.paused = False
        self.condition_expired = False
        self.stay_in_condition = False
        self.do_not_update_observer = False
        self.fn_lock = True


        # options: ratio, interval, (?)
        self.schedule = ['', ''] # interval or ratio
        self.ratio = ['', ''] # integers
        self.interval = ['', ''] # floats

        # time variables
        self.hour = '-'.join([str(x) for x in time.localtime()[:4]])
        self.time_started = time.time()
        self.now = 0

        self.time_condition = 0

        self.time_press = [0, 0]
        self.time_previous_press = [0, 0]
        self.time_fn_click = [0, 0]
        self.time_previous_fn_click = [0, 0]

        self.time_condition = [0, 0]

        # self.time_schedule = [0, 0]

        self.time_previous_add_point = [0, 0]
        self.time_add_point = [0, 0]

        self.override_time_previous_add_point = [0, 0]

        # # end variables
        # self.end = False
        # self.end_reason = ''

        # to be defined @ create output
        self.output_path = ''
        self.line = {}

        self.create_output()

    def set_time(self):
        self.now = time.time() - self.time_started
        self.hour = '-'.join([str(x) for x in time.localtime()[:4]])

    def reset_time_variables(self):
        self.set_time()
        now = self.now
        self.time_press = [now, now]
        self.time_previous_press = [now, now]
        self.time_fn_click = [now, now]
        self.time_previous_fn_click = [now, now]
        self.time_previous_add_point = [now, now]
        self.time_add_point = [now, now]

    def start_session(self):
        self.time_started = time.time()
        self.hour = '-'.join([str(x) for x in time.localtime()[:4]])
        self.now = 0
        self.session_started = True
        self.record_session_start()
        self.start_condition()

    def start_condition(self):
        self.reset_time_variables()
        self.time_condition = self.now

        if self.check_end_experiment():
            return

        self.condition_name = self.conditions[cfg.exp['save']['condition'] - 1]
        cfg.cond = cfg.conds[self.condition_name].dict()
        self.ref_schedule = text_to_list(cfg.cond['ref schedules'])
        self.adj_schedule = text_to_list(cfg.cond['adj schedules'])

        self.ref_back = text_to_list(cfg.cond['ref back'])
        self.adj_back = text_to_list(cfg.cond['adj back'])

        self.point_counter = 0

        self.all_click = 0
        self.ref_click = 0
        self.adj_click = 0
        self.all_press = 0
        self.ref_press = 0
        self.adj_press = 0

        self.ref_fn_click = 0
        self.adj_fn_click = 0

        self.ref_fn_lock_click = 0
        self.adj_fn_lock_click = 0

        self.freq_cond = 0
        self.freq_local = 0

        self.latency_cond = 0
        self.latency_local = []

        self.fn_reduce_change = 0
        self.fn_increase_change = 0
        self.fn_total_change = 0

        self.fn_reduce_lock_change = 0
        self.fn_increase_lock_change = 0
        self.fn_total_lock_change = 0

        self.fn_percent_reduce = 'N/A'

        self.fn_trial = 0
        self.fn_trials = []
        self.fn_lock = True

        self.record_condition_start()

        self.fix_condition_settings()

        self.start_part()

        if cfg.cond['use instruction']:
            for p in self.get_observer():
                p.callRemote(cmd.InfoInstruction)



    def check_end_experiment(self):
        '''returns True if ended'''

        if cfg.exp['save']['condition'] > len(self.conditions):
            self.end_experiment()
            return True
        return False

    def end_experiment(self):
        self.unschedule_all()
        cfg.exp['save']['game over'] = True
        cfg.exp.write()
        for p in self.get_players_and_observer():
            p.callRemote(cmd.EndExperiment).addErrback(bailout)

    def pause_session(self):
        self.set_time()
        if self.paused:
            return
        self.paused = True
        self.record_pause()
        for p in self.get_players_and_observer():
            p.callRemote(cmd.PauseSession).addErrback(bailout)

    def unpause_session(self):
        if not self.paused:
            return
        self.set_time()
        self.paused = False
        self.record_unpause()
        for p in self.get_players_and_observer():
            p.callRemote(cmd.UnPauseSession).addErrback(bailout)

        if self.condition_ended:
            self.start_condition()

    def start_part(self):

        self.set_time()
        self.fn_setup = None
        if 'fn' in cfg.cond['type']:
            self.fn_lock = False

        self.schedule = ['', '']

        part = self.get_part()

        # SETUP REF SCHED
        ref_sched = self.ref_schedule[:]

        if cfg.cond['type'] == 'sequence':
            ref_sched = ref_sched[part-1]
        elif cfg.cond['type'] == 'fn-self':
            ref_sched = ref_sched[1]
        elif cfg.cond['type'] == 'fn-target':
            ref_sched = ref_sched[0]
        elif cfg.cond['type'] == 'mult':
            self.start_mult_sched()
            ref_sched = ref_sched[0]
            self.fn_status = 0
        else:
            raise Exception('condition type unknown')

        if 'FR' in ref_sched:
            self.schedule[0] = 'ratio'
            self.ratio[0] = int(ref_sched.replace('FR', ''))
        elif 'FI' in ref_sched:
            self.schedule[0] = 'interval'
            self.interval[0] = float(ref_sched.replace('FI', ''))
        else:
            raise Exception('invalid schedule configuration for Ref')

        if cfg.cond['show adj']:

            adj_sched = self.adj_schedule[:]
            if cfg.cond['type'] in ['sequence', 'fn-self', 'mult']:
                adj_sched = adj_sched[0]
            elif cfg.cond['type'] == 'fn-target':
                adj_sched = adj_sched[1]
            else:
                raise Exception('condition type unknown')

            if 'FR' in adj_sched:
                self.schedule[1] = 'ratio'
                self.ratio[1] = int(adj_sched.replace('FR', ''))
            elif 'FI' in ref_sched:
                self.schedule[1] = 'interval'
                self.interval[1] = float(adj_sched.replace('FI', ''))
            else:
                raise Exception('invalid schedule configuration for Adj')

        self.fix_trial_settings()

        self.update_observer()

    def start_mult_sched(self):
        self.mult_sched = []
        ref_sched = self.ref_schedule[:]
        len_sched = len(ref_sched)
        range_sched = range(len_sched)
        for i in range_sched:
            self.mult_sched.append(i)
        for j in xrange(1000):
            random.shuffle(range_sched)
            while range_sched[0] == self.mult_sched[-1]:
                random.shuffle(range_sched)
            for i in range_sched:
                self.mult_sched.append(i)

    def end_part(self):
        self.fn_lock = True
        self.count_ratio_click = [0, 0]
        part = cfg.exp['save']['part']
        if part >= cfg.cond['parts']:
            self.end_condition()
        else:
            cfg.exp['save']['part'] += 1
            self.start_part()

    def expire_condition(self):
        print 'CONDITION EXPIRED'
        self.condition_expired = True

        self.update_observer()

        self.end_condition()

    def end_condition(self):

        if 'time limit' in self.delay_calls.values() and self.delay_calls['time limit'].active():
            self.delay_calls['time limit'].cancel()

        self.check_condition_move()

        self.update_observer()
        self.do_not_update_observer = True

        self.record_condition_end()

        cfg.exp['save']['part'] = 1
        cfg.exp.write()

        if self.check_end_experiment():
            return

        if cfg.cond['pause']:
            self.condition_ended = True
            self.pause_session()
        else:
            self.condition_ended = False
            self.start_condition()

    def check_condition_move(self):
        self.stay_in_condition = True

        # TODO: check if expired condition always keep person in condition (currenty: yes)
        if self.condition_expired:
            return

        if cfg.cond['stay based on fn change']:
            if self.fn_total_change == 0:
                # stay in condition (no change made)
                return
            if float(self.fn_reduce_change) / float(self.fn_total_change) <= cfg.cond['min reduce fn change']:
                # stay in condition (equal or less then minimum reduce change)
                return
        if cfg.cond['stay based on fn extinction']:
            min_ext = cfg.cond['min fn extinction trials']
            if sum(self.fn_trials[-1*min_ext:]) > 0:
                return
            ext_window = cfg.cond['fn extinction trials window']
            ext_window = self.fn_trials[-1*ext_window:]
            if sum(ext_window) / float(len(ext_window)) > 1.0 - cfg.cond['percentage fn extinction trials']:
                return
        # move on
        cfg.exp['save']['condition'] += 1
        cfg.exp.write()

        self.stay_in_condition = False

    def fix_condition_settings(self):
        for p in self.get_players_and_observer():
            p.callRemote(cmd.ShowAdj,
                         show=cfg.cond['show adj']).addErrback(bailout)
        if cfg.cond['use instruction']:
            instruction = cfg.cond['instruction']
            for p in self.get_players_and_observer():
                p.callRemote(cmd.ShowInstruction,
                             ref=pickle.dumps(cfg.instructions[instruction]['ref']),
                             target=pickle.dumps(cfg.instructions[instruction]['target'])).addErrback(bailout)
        else:
            self.start_time_limit()

    def fix_trial_settings(self, fix_schedule=False):

        if fix_schedule:
            self.fix_schedule()

        self.fix_ref_color()
        if cfg.cond['show adj']:
            self.fix_adj_color()

    def start_time_limit(self):
        time_limit = cfg.cond['time limit'] * 60
        self.delay_calls['time limit'] = reactor.callLater(time_limit, self.expire_condition)

    def fix_schedule(self):
        # only used by fn conditions

        if 'self' in cfg.cond['type'] or cfg.cond['type'] == 'mult':
            change_index = 0
            sched = self.ref_schedule[:]
        else:
            change_index = 1
            sched = self.adj_schedule[:]

        # get specific now
        sched = sched[self.fn_status]

        if 'FR' in sched:
            self.schedule[change_index] = 'ratio'
            self.ratio[change_index] = int(sched.replace('FR', ''))
        elif 'FI' in sched:
            self.schedule[change_index] = 'interval'
            self.interval[change_index] = float(sched.replace('FI', ''))


    def get_part(self):
        part = cfg.exp['save']['part']
        # if part is larger than parts, set last part
        if part > cfg.cond['parts']:
            part = cfg.cont['parts']
        return part

    def fix_ref_color(self):
        def get_color_index(): # chose part or fn status
            if cfg.cond['type'] in ['fn-self', 'mult']:
                return self.fn_status
            elif cfg.cond['type'] == 'fn-target':
                return 0
            elif cfg.cond['type'] == 'sequence':
                return cfg.exp['save']['part'] - 1

        ref_back = self.ref_back[:]

        if len(ref_back) == 1:
            ref_back = ref_back[0]
        else:
            ref_back = ref_back[get_color_index()]
        if not ref_back == '':
            ref_back = cfg.exp['colors'][ref_back]

        for p in self.get_players_and_observer():
            p.callRemote(cmd.RefBack,
                         ref_back_pickle=pickle.dumps(ref_back)).addErrback(bailout)

    def fix_adj_color(self):

        adj_back = self.adj_back[:]

        if len(adj_back) == 1:
            adj_back = adj_back[0]
        else:
            adj_back = adj_back[self.fn_status]
        if not adj_back == '':
            adj_back = cfg.exp['colors'][adj_back]

        for p in self.get_players_and_observer():
            p.callRemote(cmd.AdjBack,
                         adj_back_pickle=pickle.dumps(adj_back)).addErrback(bailout)

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
             'condition',
             'name',
             'event',
             'player',
             'description',
             'all_click',
             'ref_click',
             'adj_click',
             'all_press',
             'ref_press',
             'adj_press',
             'freq_cond',
             'freq_local',
             'ref_fn_click',
             'adj_fn_click',
             'ref_fn_lock_click',
             'adj_fn_lock_click',
             'response',
             'ref_sched',
             'ref_sched_val',
             'adj_sched',
             'adj_sched_val',
             'fn_total',
             'fn_reduce',
             'fn_total_locked',
             'fn_reduce_locked',
             'fn_setup',
             'fn_direction',
             'fn_status',
             'fn_trials',
             'fn_percent_reduce',
             u't_start',
             't_response',
             u'latency',
             'ref_points',
             'adj_points']

        data_string = ';'.join([unicode(x) for x in l]) + u'\n'
        output_file.write(data_string)
        output_file.close()
        self.line = dict(
            hour='',
            condition='',
            name='',
            event='',
            player='',
            description='',
            all_click='',
            ref_click='',
            adj_click='',
            all_press='',
            ref_press='',
            adj_press='',
            freq_cond='',
            freq_local='',
            ref_fn_click='',
            adj_fn_click='',
            ref_fn_lock_click='',
            adj_fn_lock_click='',
            response='',
            ref_sched='',
            ref_sched_val='',
            adj_sched='',
            adj_sched_val='',
            fn_total='',
            fn_reduce='',
            fn_total_locked='',
            fn_reduce_locked='',
            fn_setup='',
            fn_direction='',
            fn_status='',
            fn_trials='',
            fn_percent_reduce='',
            t_start='',
            t_response='',
            latency='',
            ref_points='',
            adj_points='')

    def record_line(self, **data):
        d = data
        d_list = [
            d['hour'],
            d['condition'],
            d['name'],
            d['event'],
            d['player'],
            d['description'],
            d['all_click'],
            d['ref_click'],
            d['adj_click'],
            d['all_press'],
            d['ref_press'],
            d['adj_press'],
            d['freq_cond'],
            d['freq_local'],
            d['ref_fn_click'],
            d['adj_fn_click'],
            d['ref_fn_lock_click'],
            d['adj_fn_lock_click'],
            d['response'],
            d['ref_sched'],
            d['ref_sched_val'],
            d['adj_sched'],
            d['adj_sched_val'],
            d['fn_total'],
            d['fn_reduce'],
            d['fn_total_locked'],
            d['fn_reduce_locked'],
            d['fn_setup'],
            d['fn_direction'],
            d['fn_status'],
            d['fn_trials'],
            d['fn_percent_reduce'],
            d['t_start'],
            d['t_response'],
            d['latency'],
            d['ref_points'],
            d['adj_points']]

        data_string = ';'.join([unicode(x) for x in d_list]) + u'\n'

        output_file = codecs.open(self.output_path, 'a', 'iso-8859-1')
        output_file.write(data_string)
        output_file.close()

    def get_mod_config(self, mod_config):
        self.set_time()
        for k in mod_config.keys():
            if type(mod_config[k]) == dict:
                if k not in self.mod_config.keys():
                    self.mod_config[k] = {}
                self.mod_config[k].update(mod_config[k])
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

    def point_press(self, player):
        self.set_time()
        self.time_press[player] = self.now
        self.all_click += 1
        self.all_press += 1
        if player == 0:
            self.ref_click += 1
            self.ref_press += 1

        else:
            self.adj_click += 1
            self.adj_press += 1
        add_point = False

        schedule = self.schedule[player]

        if schedule == 'ratio':
            self.count_ratio_click[player] += 1
            if self.count_ratio_click[player] >= self.ratio[player]:
                self.count_ratio_click[player] = 0
                add_point = True

        elif schedule == 'interval':
            previous_time = 0
            if self.override_time_previous_add_point[player] != 0:
                previous_time = self.override_time_previous_add_point[player]
            else:
                previous_time = self.time_previous_add_point[player]

            if self.now - previous_time >= self.interval[player]:
                add_point = True

        self.record_press(player)

        if add_point:
            self.add_point(player)

        self.time_previous_press[player] = self.now
        if self.do_not_update_observer:
            self.do_not_update_observer = False
        else:
            self.update_observer()

    def update_observer(self):

        if self.fn_percent_reduce == 'N/A':
            fn_percent_reduce = unicode(self.fn_percent_reduce)
        else:
            fn_percent_reduce = n_uni(self.fn_percent_reduce)

        condition = unicode(cfg.exp['save']['condition'])
        if self.condition_expired:
            condition += u' EXPIRED!!!'
        elif self.stay_in_condition:
            condition += u' STAY!!!'

        ref_sched = self.schedule[0]
        adj_sched = self.schedule[1]
        ref_sched_val = ''
        adj_sched_val = ''

        if ref_sched == 'ratio':
            ref_sched_val = self.ratio[0]
        elif ref_sched == 'interval':
            ref_sched_val = self.interval[0]

        if adj_sched == 'ratio':
            adj_sched_val = self.ratio[1]
        elif adj_sched == 'interval':
            adj_sched_val = self.interval[1]

        ref_sched = unicode(ref_sched) + unicode(ref_sched_val)
        adj_sched = unicode(adj_sched) + unicode(adj_sched_val)

        data_list = [u'condition: ' + condition,
                    u'name: ' + unicode(self.condition_name),
                    u'time: ' + n_uni(self.now),
                    u'ref_press: ' + unicode(self.ref_press),
                    u'adj_press: ' + unicode(self.adj_press),
                    u'freq_cond: ' + n_uni(self.freq_cond),
                    u'freq_local: ' + n_uni(self.freq_local),
                    u'ref_sched: ' + ref_sched,
                    u'adj sched: ' + adj_sched,
                    u'ref_fn_click: ' + unicode(self.ref_fn_click),
                    # u'adj_fn_click: ' + unicode(self.adj_fn_click),

                    u'ref_fn_lock_click: ' + unicode(self.ref_fn_lock_click),
                    u'adj_fn_lock_click: ' + unicode(self.adj_fn_lock_click),

                    u'fn_status: ' + unicode(self.fn_status),
                    u'fn_trials: ' + unicode(self.fn_trials[-18:]),
                    u'fn_percent_reduce: ' + fn_percent_reduce,

                    u'fn_total:' + unicode(self.fn_total_change),
                    u'fn_reduce: ' + unicode(self.fn_reduce_change),

                    u'fn_total_lock:' + unicode(self.fn_total_lock_change),
                    u'fn_reduce_lock: ' + unicode(self.fn_reduce_lock_change),

                    u'ref_points: ' + unicode(self.points[0]),
                    u'adj_points: ' + unicode(self.points[1])]
        info = u'\n'.join([unicode(x) for x in data_list])
        for p in self.get_observer():
            p.callRemote(cmd.UpdateObserver,
                         info=info)

    # def locked_fn_click(self, player, fn):
    #     # TODO: RECORD STUFF AND SEND TO OBSERVER
    #     pass

    def fn_click(self, player, fn):
        self.set_time()

        self.time_fn_click[player] = self.now
        self.all_click += 1
        if player == 0:
            self.ref_click += 1
            if self.fn_lock:
                self.ref_fn_lock_click +=1
            else:
                self.ref_fn_click += 1
        else:
            self.adj_click += 1
            self.adj_fn_lock_click += 1  # always locked

        fn_setup = ''
        fn_direction = ''
        new_fn_status = ''
        record_locked = False

        # if self.fn_lock:
        #     self.locked_fn_click(player, fn)
        #     return

        if player > 0:
            record_locked = True

        elif 'fn' in cfg.cond['type']:
            if self.fn_lock:
                record_locked = True

            if not self.fn_lock:
                self.fn_trial = 1
                if self.fn_setup is None:
                    if fn == 'f':
                        self.fn_setup = 1
                    else:
                        self.fn_setup = 0
                fn_setup = self.fn_setup
            else:  # locked
                if fn == 'f':
                    fn_setup = 1
                else:
                    fn_setup = 0

            if self.fn_invert:
                fn_setup = 1 - fn_setup

            if fn == 'f' and fn_setup == 1 \
                or fn == 'n' and fn_setup == 0:  # lowers
                fn_direction = 0
                if not self.fn_lock:
                    self.fn_reduce_change += 1
                    # fn_status: 0 = lower, 2 = higher, 1 = default/middle
                    new_fn_status = max(self.fn_status - 1, 0)
                else:
                    self.fn_reduce_lock_change += 1
            else:  # raises
                fn_direction = 1
                if not self.fn_lock:
                    self.fn_increase_change += 1
                    new_fn_status = min(self.fn_status + 1, 2)
                else:
                    self.fn_increase_lock_change += 1

            if not self.fn_lock:
                self.fn_total_change += 1
                self.fn_percent_reduce = (float(self.fn_reduce_change) / float(self.fn_total_change)) * 100
                self.record_fn_click(player, fn, fn_setup, fn_direction, new_fn_status)

                if new_fn_status != self.fn_status:
                    self.fn_status = new_fn_status
                    self.fix_trial_settings(fix_schedule=True)
                    self.fn_lock = True
            else:
                self.fn_total_lock_change += 1
        if record_locked:
            self.record_locked_fn_click(player, fn, fn_direction)

        self.update_observer()

        self.time_previous_fn_click[player] = self.now

    def change_fn_status(self):
        for p in self.get_players_and_observer():
            p.callRemote(cmd.ChangeFnStatus)

    def add_point(self, player):
        end_part = False
        self.set_time()
        self.time_add_point[player] = self.now
        self.override_time_previous_add_point[player] = 0
        self.points[player] += 1
        for p in self.get_players_and_observer():
            p.callRemote(cmd.AddPoint,
                         player=player,
                         points=self.points)
        if player == 0:
            self.point_counter += 1
            if self.point_counter >= cfg.cond['end after']:
                self.point_counter = 0
                end_part = True

            elif cfg.cond['type'] == 'mult':
                self.fn_status = self.mult_sched[self.point_counter]
                self.fix_trial_settings(fix_schedule=True)
        if 'fn' in cfg.cond['type']:
            if player == 1 and 'target' in cfg.cond['type'] or \
                    player == 0 and 'self' in cfg.cond['type']:
                if self.fn_setup is not None:
                    self.fn_invert_counter += 1
                    if cfg.cond['invert fn']:
                        if self.fn_invert_counter >= cfg.cond['invert fn after']:
                            self.fn_invert_counter = 0
                            self.fn_invert = not self.fn_invert
                self.reset_fn_status()
            self.fn_trials.append(self.fn_trial)
            self.fn_trial = 0
        self.record_point(player)
        self.time_previous_add_point[player] = self.now

        if player == 0 and 'fn' in cfg.cond['type'] and cfg.cond['end on extinction']:
            min_ext = cfg.cond['min fn extinction trials']
            if sum(self.fn_trials[-1*min_ext:]) == 0:
                ext_window = cfg.cond['fn extinction trials window']
                if len(self.fn_trials) >= ext_window:
                    ext_window = self.fn_trials[-1*ext_window:]
                    if sum(ext_window) / float(len(ext_window)) <= 1.0 - cfg.cond['percentage fn extinction trials']:
                        end_part = True
        if player == 0 and cfg.cond['ref reset target']:
            self.reset_fn_status()
            self.override_time_previous_add_point[1] = self.now
            self.count_ratio_click[1] = 0

        if end_part:
            self.end_part()

    def reset_fn_status(self):
        self.fn_status = 1
        self.fix_trial_settings(fix_schedule=True)
        self.fn_lock = False

    # def expire_session(self):
    #     if self.end:
    #         return
    #     self.end = True
    #     self.end_reason += '-expired'

        # self.end_session('expired')

    # def end_session(self, status='criteria'):
    #     self.unschedule_all()
    #     self.set_time()
    #     for p in self.get_players_and_observer():
    #         p.callRemote(cmd.EndSession,
    #                      status=status).addErrback(bailout)
    #     self.record_end(status)

    def record_press(self, player):
        t_start = self.time_previous_press[player]
        latency = self.now - t_start

        if player == 0 and self.ref_press > 1:
            self.latency_cond += latency
            self.latency_local.append(latency)
            lat_window = cfg.exp['parameters']['local frequency window']
            self.latency_local = self.latency_local[(-1)*lat_window:]

            self.freq_cond = ((self.ref_press - 1) / self.latency_cond)
            self.freq_local = (len(self.latency_local) / sum(self.latency_local))

        ref_sched = self.schedule[0]
        adj_sched = self.schedule[1]
        ref_sched_val = ''
        adj_sched_val = ''

        if ref_sched == 'ratio':
            ref_sched_val = self.ratio[0]
        elif ref_sched == 'interval':
            ref_sched_val = self.interval[0]

        if adj_sched == 'ratio':
            adj_sched_val = self.ratio[1]
        elif adj_sched == 'interval':
            adj_sched_val = self.interval[1]

        data = dict(self.line,
                    condition=cfg.exp['save']['condition'],
                    name=self.condition_name,
                    event='press',
                    hour=self.hour,
                    all_click=self.all_click,
                    ref_click=self.ref_click,
                    adj_click=self.adj_click,
                    all_press=self.all_press,
                    ref_press=self.ref_press,
                    adj_press=self.adj_press,
                    freq_cond=n_uni(self.freq_cond),
                    freq_local=n_uni(self.freq_local),
                    ref_fn_click=self.ref_fn_click,
                    adj_fn_click=self.adj_fn_click,
                    ref_fn_lock_click=self.ref_fn_lock_click,
                    adj_fn_lock_click=self.adj_fn_lock_click,
                    ref_sched=ref_sched,
                    ref_sched_val=ref_sched_val,
                    adj_sched=adj_sched,
                    adj_sched_val=adj_sched_val,
                    player=player,
                    t_start=n_uni(t_start),
                    t_response=n_uni(self.now),
                    latency=n_uni(latency),
                    ref_points=self.points[0],
                    adj_points=self.points[1]
                    )
        self.record_line(**data)

    def record_point(self, player):

        t_start = self.time_previous_add_point[player]

        if self.fn_percent_reduce == 'N/A':
            fn_percent_reduce = unicode(self.fn_percent_reduce)
        else:
            fn_percent_reduce = n_uni(self.fn_percent_reduce)

        ref_sched = self.schedule[0]
        adj_sched = self.schedule[1]
        ref_sched_val = ''
        adj_sched_val = ''

        if ref_sched == 'ratio':
            ref_sched_val = self.ratio[0]
        elif ref_sched == 'interval':
            ref_sched_val = self.interval[0]

        if adj_sched == 'ratio':
            adj_sched_val = self.ratio[1]
        elif adj_sched == 'interval':
            adj_sched_val = self.interval[1]

        data = dict(self.line,
                    condition=cfg.exp['save']['condition'],
                    name=self.condition_name,
                    event='point',
                    player=player,
                    hour=self.hour,
                    all_click=self.all_click,
                    ref_click=self.ref_click,
                    adj_click=self.adj_click,
                    all_press=self.all_press,
                    ref_press=self.ref_press,
                    adj_press=self.adj_press,
                    freq_cond=n_uni(self.freq_cond),
                    freq_local=n_uni(self.freq_local),
                    ref_fn_click=self.ref_fn_click,
                    adj_fn_click=self.adj_fn_click,
                    ref_fn_lock_click=self.ref_fn_lock_click,
                    adj_fn_lock_click=self.adj_fn_lock_click,
                    ref_sched=ref_sched,
                    ref_sched_val=ref_sched_val,
                    adj_sched=adj_sched,
                    adj_sched_val=adj_sched_val,
                    fn_total=unicode(self.fn_total_change),
                    fn_reduce=unicode(self.fn_reduce_change),
                    fn_total_locked=unicode(self.fn_total_lock_change),
                    fn_reduce_locked=unicode(self.fn_reduce_lock_change),
                    fn_status=unicode(self.fn_status),
                    fn_trials=unicode(sum(self.fn_trials)),
                    fn_percent_reduce=fn_percent_reduce,
                    t_start=n_uni(t_start),
                    t_response=n_uni(self.now),
                    latency=n_uni(self.now - t_start),
                    ref_points=self.points[0],
                    adj_points=self.points[1]
                    )
        self.record_line(**data)

    def record_locked_fn_click(self, player, fn, fn_direction):
        t_start = self.time_previous_fn_click[player]

        ref_sched = self.schedule[0]
        adj_sched = self.schedule[1]
        ref_sched_val = ''
        adj_sched_val = ''

        if ref_sched == 'ratio':
            ref_sched_val = self.ratio[0]
        elif ref_sched == 'interval':
            ref_sched_val = self.interval[0]

        if adj_sched == 'ratio':
            adj_sched_val = self.ratio[1]
        elif adj_sched == 'interval':
            adj_sched_val = self.interval[1]

        data = dict(self.line,
                    condition=cfg.exp['save']['condition'],
                    name=self.condition_name,
                    event='lock_fn_click',
                    player=player,
                    hour=self.hour,
                    all_click=self.all_click,
                    ref_click=self.ref_click,
                    adj_click=self.adj_click,
                    all_press=self.all_press,
                    ref_press=self.ref_press,
                    adj_press=self.adj_press,
                    freq_cond=n_uni(self.freq_cond),
                    freq_local=n_uni(self.freq_local),
                    ref_fn_click=self.ref_fn_click,
                    adj_fn_click=self.adj_fn_click,
                    ref_fn_lock_click=self.ref_fn_lock_click,
                    adj_fn_lock_click=self.adj_fn_lock_click,
                    response=fn,
                    ref_sched=ref_sched,
                    ref_sched_val=ref_sched_val,
                    adj_sched=adj_sched,
                    adj_sched_val=adj_sched_val,
                    fn_direction=fn_direction,
                    fn_trials=unicode(sum(self.fn_trials)),
                    t_start=n_uni(t_start),
                    t_response=n_uni(self.now),
                    latency=n_uni(self.now - t_start),
                    ref_points=self.points[0],
                    adj_points=self.points[1]
                    )
        self.record_line(**data)


    def record_fn_click(self, player, fn, fn_setup, fn_direction, new_fn_status):
        t_start = self.time_previous_fn_click[player]

        if self.fn_percent_reduce == 'N/A':
            fn_percent_reduce = unicode(self.fn_percent_reduce)
        else:
            fn_percent_reduce = n_uni(self.fn_percent_reduce)

        ref_sched = self.schedule[0]
        adj_sched = self.schedule[1]
        ref_sched_val = ''
        adj_sched_val = ''

        if ref_sched == 'ratio':
            ref_sched_val = self.ratio[0]
        elif ref_sched == 'interval':
            ref_sched_val = self.interval[0]

        if adj_sched == 'ratio':
            adj_sched_val = self.ratio[1]
        elif adj_sched == 'interval':
            adj_sched_val = self.interval[1]

        data = dict(self.line,
                    condition=cfg.exp['save']['condition'],
                    name=self.condition_name,
                    event='fn_click',
                    player=player,
                    hour=self.hour,
                    all_click=self.all_click,
                    ref_click=self.ref_click,
                    adj_click=self.adj_click,
                    all_press=self.all_press,
                    ref_press=self.ref_press,
                    adj_press=self.adj_press,
                    freq_cond=n_uni(self.freq_cond),
                    freq_local=n_uni(self.freq_local),
                    ref_fn_click=self.ref_fn_click,
                    adj_fn_click=self.adj_fn_click,
                    ref_fn_lock_click=self.ref_fn_lock_click,
                    adj_fn_lock_click=self.adj_fn_lock_click,
                    response=fn,
                    ref_sched=ref_sched,
                    ref_sched_val=ref_sched_val,
                    adj_sched=adj_sched,
                    adj_sched_val=adj_sched_val,
                    fn_total=unicode(self.fn_total_change),
                    fn_reduce=unicode(self.fn_reduce_change),
                    fn_total_locked=unicode(self.fn_total_lock_change),
                    fn_reduce_locked=unicode(self.fn_reduce_lock_change),
                    fn_setup=fn_setup,
                    fn_direction=fn_direction,
                    fn_status=new_fn_status,
                    fn_trials=unicode(sum(self.fn_trials)),
                    fn_percent_reduce=fn_percent_reduce,
                    t_start=n_uni(t_start),
                    t_response=n_uni(self.now),
                    latency=n_uni(self.now - t_start),
                    ref_points=self.points[0],
                    adj_points=self.points[1]
                    )
        self.record_line(**data)

    # def record_end(self, reason):
    #     data = dict(self.line,
    #                 event='end session',
    #                 hour=self.hour,
    #                 description=reason,
    #                 t_start=n_uni(0),
    #                 t_response=n_uni(self.now),
    #                 )
    #     self.record_line(**data)

    def record_session_start(self):
        data = dict(self.line,
                    event='start session',
                    hour=self.hour,
                    t_start=n_uni(0))
        self.record_line(**data)

    def record_condition_start(self):
        data = dict(self.line,
                    condition=cfg.exp['save']['condition'],
                    name=self.condition_name,
                    event='start condition',
                    hour=self.hour,
                    t_start=n_uni(self.now))
        self.record_line(**data)

    def record_condition_end(self):

        if self.fn_percent_reduce == 'N/A':
            fn_percent_reduce = unicode(self.fn_percent_reduce)
        else:
            fn_percent_reduce = n_uni(self.fn_percent_reduce)

        description = ''
        if self.condition_expired:
            description = 'EXPIRED'
        elif self.stay_in_condition:
            description = 'STAY'

        self.condition_expired = False
        self.stay_in_condition = False

        data = dict(self.line,
                    condition=cfg.exp['save']['condition'],
                    name=self.condition_name,
                    event='end condition',
                    description=description,
                    hour=self.hour,
                    all_click=self.all_click,
                    ref_click=self.ref_click,
                    adj_click=self.adj_click,
                    all_press=self.all_press,
                    ref_press=self.ref_press,
                    adj_press=self.adj_press,
                    freq_cond=self.freq_cond,
                    freq_local=self.freq_local,
                    ref_fn_click=self.ref_fn_click,
                    adj_fn_click=self.adj_fn_click,
                    ref_fn_lock_click=self.ref_fn_lock_click,
                    adj_fn_lock_click=self.adj_fn_lock_click,
                    fn_total=unicode(self.fn_total_change),
                    fn_reduce=unicode(self.fn_reduce_change),
                    fn_total_locked=unicode(self.fn_total_lock_change),
                    fn_reduce_locked=unicode(self.fn_reduce_lock_change),
                    fn_trials=unicode(sum(self.fn_trials)),
                    fn_percent_reduce=fn_percent_reduce,
                    t_start=n_uni(self.time_condition),
                    t_response=n_uni(self.now),
                    latency=n_uni(self.latency_cond),
                    )
        self.record_line(**data)

    def record_pause(self):
        data = dict(self.line,
                    condition=cfg.exp['save']['condition'],
                    name=self.condition_name,
                    event='pause',
                    hour=self.hour,
                    t_start=n_uni(self.now))
        self.record_line(**data)

    def record_unpause(self):
        data = dict(self.line,
                    condition=cfg.exp['save']['condition'],
                    name=self.condition_name,
                    event='unpause',
                    hour=self.hour,
                    t_start=n_uni(self.now))
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
    experiments = [x[:-4] for x in os.listdir(exp_dir) if ('.ini' in x)
                   and ('_conditions' not in x) and ('_instructions' not in x)]
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
    conditions_filename = group + '_conditions.ini'
    instructions_filename = group + '_instructions.ini'
    contains_experiment = experiment_filename in save_dir_files
    contains_conditions = conditions_filename in save_dir_files
    contains_instructions = instructions_filename in save_dir_files

    if contains_experiment and contains_conditions and contains_instructions:
        cfg.exp = ConfigObj(infile=os.path.join(save_dir, experiment_filename),
                            configspec=os.path.join(spec_dir, 'spec_experiment.ini'))
        validate_config(cfg.exp)

        cfg.conds = ConfigObj(infile=os.path.join(save_dir, conditions_filename),
                              configspec=os.path.join(spec_dir, 'spec_conditions.ini'))
        validate_config(cfg.conds)

        cfg.instructions = ConfigObj(infile=os.path.join(save_dir, instructions_filename),
                                     configspec=os.path.join(spec_dir, 'spec_instructions.ini'),
                                     encoding='UTF8')
        validate_config(cfg.instructions)


    else:
        define_experiment = string_to_bool(cfg.server['define experiment'])
        experiment = get_experiment(exp_dir, define_experiment)
        cfg.exp = ConfigObj(infile=os.path.join(exp_dir, experiment + '.ini'),
                            configspec=os.path.join(spec_dir, 'spec_experiment.ini'))

        # EXPERIMENT (validating but PRESERVING comments (set_copy=True also copies spec comments))
        pre_copy_comments = copy.deepcopy(cfg.exp.comments)
        pre_copy_final_comment = copy.deepcopy(cfg.exp.final_comment)
        validate_config(cfg.exp, set_copy=True)
        cfg.exp.comments = pre_copy_comments
        cfg.exp.final_comment = pre_copy_final_comment

        cfg.exp.filename = os.path.join(save_dir, experiment_filename)
        cfg.exp.initial_comment = ['# experiment: {}\n# group: {}'.format(experiment, group), ' ']

        cfg.exp.write()


        # CONDITIONS (validating but PRESERVING comments (set_copy=True also copies spec comments))
        cfg.conds = ConfigObj(infile=os.path.join(exp_dir, experiment + '_conditions.ini'),
                              configspec=os.path.join(spec_dir, 'spec_conditions.ini'))

        pre_copy_comments = copy.deepcopy(cfg.conds.comments)
        pre_copy_final_comment = copy.deepcopy(cfg.conds.final_comment)
        validate_config(cfg.conds, set_copy=True)
        cfg.conds.comments = pre_copy_comments
        cfg.conds.final_comment = pre_copy_final_comment

        cfg.conds.filename = os.path.join(save_dir, conditions_filename)
        cfg.conds.initial_comment = ['# conditions for experiment: {}\n# group: {}'.format(experiment, group), ' ']

        cfg.conds.write()

        # INSTRUCTIONS (validating but PRESERVING comments (set_copy=True also copies spec comments))
        cfg.instructions = ConfigObj(infile=os.path.join(exp_dir, experiment + '_instructions.ini'),
                                     configspec=os.path.join(spec_dir, 'spec_instructions.ini'))

        pre_copy_comments = copy.deepcopy(cfg.instructions.comments)
        pre_copy_final_comment = copy.deepcopy(cfg.instructions.final_comment)
        validate_config(cfg.instructions, set_copy=True)
        cfg.instructions.comments = pre_copy_comments
        cfg.instructions.final_comment = pre_copy_final_comment

        cfg.instructions.filename = os.path.join(save_dir, instructions_filename)
        cfg.instructions.initial_comment = ['# instructions for experiment: {}\n# group: {}'.format(experiment, group), ' ']

        cfg.instructions.write()

    # TEST GAME OVER

    if cfg.exp['save']['game over'] or \
            cfg.exp['save']['condition'] > len(text_to_list(cfg.exp['conditions']['conditions'])):
        cfg.exp['save']['game over'] = True
        cfg.exp.write()
        eg.msgbox('GAME OVER')

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
