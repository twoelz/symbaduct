#!/usr/bin/env python
# -*- coding: UTF-8 -*-

'''
Symbaduct

Client
'''

# symbaduct client
# Copyright (c) 2017 Thomas Anatol da Rocha Woelz
# All rights reserved.
# BSD type license: check doc folder for details

__version__ = '0.0.1'
__docformat__ = 'restructuredtext'
__author__ = 'Thomas Anatol da Rocha Woelz'

import sys
import os
import codecs
import cPickle as pickle

import random
# import csv
# import time
# import copy

# set local path constants
DIR = os.path.abspath(os.path.dirname(__file__))
RESDIR = os.path.join(DIR, 'res')
sys.path.insert(0, os.path.join(RESDIR, 'scripts'))
for dependency_folder in ['standout',
                          'configobj',
                          'amptypes',  # TODO: REMOVE IF NOT USED
                          'configobj']:
    sys.path.insert(0, os.path.abspath(os.path.join(RESDIR,
                                                    'scripts',
                                                    'dependencies',
                                                    dependency_folder)))


from standout import StandOut
from configobj import ConfigObj
from configobj import flatten_errors
from validate import Validator
from validate import ValidateError
from convert import utostr
from convert import print_u
from convert import n_uni

from common_code import is_valid_ip
from common_code import validate_config
from common_code import shared
from common_code import HOST
from common_code import PORT
from common_code import MAX_PORT
from common_code import LOCALTIME
from common_code import LANG
from common_code import DECIMAL_SEPARATOR
from common_code import CSV_SEPARATOR

#custom kivy extension in scripts folder
from hoverbehavior import HoverBehavior


# stout = StandOut('log.txt')

# kivy won't log info about it if os.environ has this keyword
# value is irrelevant. comment out to allow it.
# kivy logs go in a file inside kivy_home
# os.environ['KIVY_NO_FILELOG'] = '1'

# kivy won't print messages to console if os.environ has this keyword
# value is irrelevant, comment out to allow it.
# os.environ['KIVY_NO_CONSOLELOG'] = '1'


win_cfg = ConfigObj(infile=os.path.join(DIR, 'config', 'window.ini'),
                    configspec=os.path.join(DIR, 'config', 'spec',
                                           'spec_window.ini'))
validate_config(win_cfg)


USE_FULLSCREEN = win_cfg['use fullscreen']

WIN_HEIGHT = win_cfg['window']['height']
WIN_WIDTH = win_cfg['window']['width']

# TODO: REMOVE THIS IF FIGURE OUT HOW TO GET THIS
FULL_HEIGHT = win_cfg['fullscreen']['height']
FULL_WIDTH = win_cfg['fullscreen']['width']

BACKGROUND_COLOR = tuple(win_cfg['background color'])
FEEDBACK_BACKGROUND_COLOR = tuple(win_cfg['feedback background color'])

from kivy.config import Config

# disallow resize
# Config.set('graphics','resizable',0)

Config.set('graphics', 'height', WIN_HEIGHT)
Config.set('graphics', 'width', WIN_WIDTH)

if USE_FULLSCREEN:
    Config.set('graphics', 'fullscreen', 'auto')
else:
    Config.set('graphics', 'fullscreen', 0)

Config.set('kivy', 'exit_on_escape', False)
# multitouch disabled (removes red dots when using right-clicked mouse)
Config.set('input', 'mouse', 'mouse,disable_multitouch')

# Config.set('kivy', 'log_level', 'info')
# Config.set('kivy', 'log_enable', '0')

# install_twisted_rector must be called before importing the reactor
from kivy.support import install_twisted_reactor

install_twisted_reactor()

# TODO: consider using uninstall_twisted_reactor after stopping the client

# network modules (twisted)
from twisted.internet import reactor
from twisted.internet import task
from twisted.internet import defer
from twisted.internet.protocol import _InstanceFactory
from twisted.protocols import amp
from twisted.python import log

# my scripts
import mycmd as cmd


from kivy.app import App
from kivy.lang import Builder
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.screenmanager import Screen
from kivy.uix.screenmanager import SlideTransition
from kivy.utils import platform
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.properties import ObjectProperty
from kivy.properties import NumericProperty
from kivy.properties import DictProperty
from kivy.core.audio import SoundLoader

from kivy.animation import Animation

# from kivy.graphics.texture import Texture
# from kivy.graphics.svg import Svg



# import Window must be done after configs are set
from kivy.core.window import Window

# Window.clearcolor = BACKGROUND_COLOR


# set environment variables here
os.environ["DECIMAL_SEPARATOR"] = DECIMAL_SEPARATOR
os.environ["CSV_SEPARATOR"] = CSV_SEPARATOR


def fix_window_size():
    if Window.fullscreen:
        pass
    elif Window.size[0] < WIN_WIDTH or Window.size[1] < WIN_HEIGHT:
        Window.size = WIN_WIDTH, WIN_HEIGHT

    if USE_FULLSCREEN:
        Window.fullscreen = 'auto'

def exit_app():
    App.get_running_app().stop()

class Container(object):
    pass

class TextInputIP(TextInput):
    acceptable_chars = list(str(x) for x in xrange(10)) + ['.', ]

    def insert_text(self, substring, from_undo=False):
        substring = utostr(substring)
        text = utostr(self.text)
        len_text = len(text)
        if len_text >= 15:
            substring = ''
        else:
            substring = ''.join(c for c in utostr(substring)
                                if c in self.acceptable_chars)[:15]
            while substring and len_text + len(substring) > 15:
                substring = substring[:-1]
            while substring and text.count('.') + substring.count('.') > 3:
                substring = substring[:-1]
        return super(TextInputIP, self).insert_text(substring,
                                                    from_undo=from_undo)


class TextInputPORT(TextInput):
    acceptable_chars = list(str(x) for x in xrange(10))
    max_value = MAX_PORT
    def insert_text(self, substring, from_undo=False):
        text = utostr(self.text)
        len_text = len(text)
        if len_text >= 5:
            substring = ''
        else:
            substring = ''.join(c for c in utostr(substring)
                                if c in self.acceptable_chars)[:5-len_text]
            while substring and len_text + len(substring) > 5:
                substring = substring[:-1]
            cursor_index = int(self.cursor[0])
            text_before = text[:cursor_index]
            text_after = text[cursor_index:]
            while substring and int(text_before + substring
                                    + text_after) > self.max_value:
                substring = substring[:-1]
        return super(TextInputPORT, self).insert_text(substring,
                                                      from_undo=from_undo)

class ScreenConnect(Screen):

    # avoid garbage collection of removable rows
    row_ip = ObjectProperty(None)
    row_port = ObjectProperty(None)

    def __init__(self, **kw):
        super(ScreenConnect, self).__init__(**kw)
        self.ip_port_removed = False
        if 'hide_ip_port' in sys.argv \
                or 'hide_ip' in sys.argv \
                or cfg.client['options']['hide ip and port']:
            self.remove_ip_port()

    def remove_ip_port(self):
        for ip_port_row in [self.row_ip,
                            self.row_port]:
            self.ids.grid_conn.remove_widget(ip_port_row)
        self.ip_port_removed = True

    def add_ip_port(self):

        bottom_rows = [self.ids.row_connect,
                       self.ids.label_conn_error]
        ip_port_rows = [self.row_ip,
                        self.row_port]
        for bottom_row in bottom_rows:
            self.ids.grid_conn.remove_widget(bottom_row)
        for ip_port_row in ip_port_rows:
            self.ids.grid_conn.add_widget(ip_port_row)
        for bottom_row in bottom_rows:
            self.ids.grid_conn.add_widget(bottom_row)
        self.ip_port_removed = False

    def toggle_show_ip_port(self):
        if self.ip_port_removed:
            self.add_ip_port()
        else:
            self.remove_ip_port()

    def connect_button_press(self):
        self.ids.label_conn_error.text = ''
        self.ids.label_conn_message.text = 'Conectando...'
        self.ids.button_connect.disabled = True
        Clock.schedule_once(App.get_running_app().try_to_connect, 0.01)

    def reset_layout(self, *args):
        self.ids.label_conn_message.text = 'Bem Vindo!'
        self.ids.button_connect.disabled = False

    def print_error(self, error):
        self.ids.label_conn_error.text = error

    def on_click_printed_error(self, touch):
        Clipboard.put(str(self.ids.label_conn_error.text), 'UTF8_STRING')
        if touch.is_double_tap:
            self.ids.label_conn_error.text = ''

class ScreenWait(Screen):
    pass

class ScreenGame(Screen):
    r = NumericProperty(BACKGROUND_COLOR[0])
    g = NumericProperty(BACKGROUND_COLOR[1])
    b = NumericProperty(BACKGROUND_COLOR[2])
    a = NumericProperty(BACKGROUND_COLOR[3])
    adj_r = NumericProperty(1.0)
    adj_g = NumericProperty(1.0)
    adj_b = NumericProperty(1.0)
    adj_a = NumericProperty(1.0)
    ref_r = NumericProperty(1.0)
    ref_g = NumericProperty(1.0)
    ref_b = NumericProperty(1.0)
    ref_a = NumericProperty(1.0)
    adj_overlay = NumericProperty(0.0)
    ref_overlay = NumericProperty(0.0)
    ref_coin_size = 1.0
    ref_coin_reduce = True
    ref_coin_count = 5
    ref_coin_started = False


    # events
    update_event = None

    def __init__(self, **kwargs):
        super(ScreenGame, self).__init__(**kwargs)

        if obs:
            self.disable_buttons()

    def coin_anim(self, adj=False):

        if adj:
            ref_coin = self.ids.adj_coin
            plus_label = self.ids.adj_plus
        else:
            ref_coin = self.ids.ref_coin
            plus_label = self.ids.ref_plus

        size_b4 = ref_coin.parent.height
        size_after = size_b4 * 0.5
        ref_coin.width = ref_coin.parent.height * self.ref_coin_size
        ref_coin.height = ref_coin.parent.height * self.ref_coin_size
        anim = Animation(size=(size_after, size_after), t='out_cubic', duration=0.1)
        # anim.bind(on_complete=lambda x, y: app.change_points())
        anim += Animation(size=(size_b4, size_b4), t='out_cubic', duration=0.1)
        anim.start(ref_coin)

        plus_label.text = "+1"

        if not adj:
            play(app.sound['point added'])
        # Clock.schedule_once(self.clear_plus)
        Clock.schedule_once(lambda dt: self.change_points(adj=adj), 0.1)

    def change_points(self, adj=False):
        if adj:
            point_label = self.ids.adj_points
            points = app.adj_points
        else:
            point_label = self.ids.ref_points
            points = app.ref_points

        point_label.text = str(points)

        Clock.schedule_once(lambda dt: self.clear_plus(adj=adj), 0.25)


    def clear_plus(self, adj=False):
        if adj:
            plus_label = self.ids.adj_plus
        else:
            plus_label = self.ids.ref_plus

        plus_label.text = ''


    def disable_buttons(self):
        # obs here: disable all buttons (currently disabled by checking obs)
        pass

    # def add_player_count(self, player_count):
    #     self.ids.label_game_message.text = str(player_count)

    def fix_layout(self):

        # DO STUFF HERE TO SETUP CONDITION
        pass


    # def update(self, dt):
    #
    #     print 'hi'
    #
    #     if self.ref_coin_size <= 0.5:
    #         self.ref_coin_reduce = False
    #
    #     if self.ref_coin_size >= 1.0:
    #         self.ref_coin_reduce = True
    #
    #     if self.ref_coin_reduce:
    #         self.ref_coin_size -= 0.01
    #     else:
    #         self.ref_coin_size += 0.01
    #
    #     print self.ref_coin_size
    #
    #
    #
    #     ref_coin = self.ids.ref_coin
    #
    #     if not self.ref_coin_started:
    #         self.ref_coin_started = True
    #         # ref_coin.mipmap = False
    #
    #     ref_coin.width = ref_coin.parent.height * self.ref_coin_size
    #     ref_coin.height = ref_coin.parent.height * self.ref_coin_size
    #
    #
    #     if self.ref_coin_size >= 1.0:
    #         self.ref_coin_count -= 1
    #         if self.ref_coin_count == 0:
    #             Clock.unschedule(self.update_event)
    #             ref_coin.width = ref_coin.parent.height
    #             ref_coin.height = ref_coin.parent.height
    #             self.ref_coin_started = False
    #             # ref_coin.mipmap = True


class ScreenPause(Screen):
    pass

class ScreenEnd(Screen):
    pass

class ScreenInstruction(Screen):
    pass

class ScreenManagerMain(ScreenManager):
    def __init__(self, **kwargs):
        super(ScreenManagerMain, self).__init__(**kwargs)
        # self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard = Window.request_keyboard(lambda: None, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

    def go_to(self, screen_name, direction='left'):
        self.transition.direction = direction
        self.current = screen_name


    # I had to remove or TextInput would force the keyboard to unbind
    # def _keyboard_closed(self):
    # self._keyboard.unbind(on_key_down=self._on_keyboard_down)
    #     self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        key = keycode[1]
        if key == 's' and modifiers == ['ctrl']:  # control-s (screenshot)
            i = 0
            path = None
            name = 'screenshot{:03d}.png'
            while True:
                i += 1
                path = os.path.join(os.getcwd(), name.format(i))
                if not os.path.exists(path):
                    name = name.format(i)
                    break
            self.export_to_png(name)

        # control-r (rotate)
        elif key == 'r' and modifiers == ['ctrl']:
            Window.rotation += 90
        # control-t (toggle portrait/landscape)
        elif key == 't' and modifiers == ['ctrl']:
            if platform in ('win', 'linux', 'macosx'):
                Window.rotation = 0
                w, h = Window.size
                w, h = h, w
                Window.size = (w, h)
        # control-w (windowed)
        elif key == 'w' and modifiers == ['ctrl']:
            Window.fullscreen = False
            Window.size = (WIN_WIDTH, WIN_HEIGHT)

        # control-f (fullscreen)
        elif key == 'f' and modifiers == ['ctrl']:
            Window.size = (FULL_WIDTH, FULL_HEIGHT)
            Window.fullscreen = 'auto'

        # shift-escape exits app
        elif key == 'escape' and 'shift' in modifiers:
            exit_app()

        # specific cases for this particular app below
        elif key == 'i' and modifiers == ['ctrl'] \
                and self.current == 'connect':
            self.get_screen('connect').toggle_show_ip_port()

        elif key == 'enter' and modifiers == ['ctrl'] \
                and self.current == 'connect':
            self.get_screen('connect').connect_button_press()

        elif key == 'backspace' and modifiers == ['ctrl'] \
                and not self.current == 'connect':
            App.get_running_app().disconnect_client()

        # GAME COMMANDS

        elif obs: # break all below key inputs from observer
            return True

        elif key == 'spacebar' and self.current == 'instruction':
            app.instruction_press()

        return True

    def start_wait_screen(self):
        fix_window_size()
        self.go_to('wait')

        # reset connect screen layout for when we go back to that screen.
        Clock.schedule_once(self.get_screen('connect').reset_layout, 0.2)

    def start_game_screen(self):
        fix_window_size()
        self.go_to('game')

        player_count = app.player_count
        if obs:
            player_count = 'Observer {}'.format(player_count)
        else:
            print player_count

        game_screen = sm.get_screen('game')

        # # TODO: REMOVE ME LATER
        # game_screen.add_player_count(player_count)

        game_screen.fix_layout()



        # fix game screen almost as soon as it is shown
        # Clock.schedule_once(app.fix_game_layout, 0.1)

        # reset connect screen layout for when we go back to that screen.
        Clock.schedule_once(self.get_screen('connect').reset_layout, 0.2)



    def player_left(self):
        self.get_screen('pause').ids.pause_label.text = 'PAUSA\nPARTICIPANTE SAIU'
        self.go_to('pause')

    def session_pause(self):
        self.get_screen('pause').ids.pause_label.text = 'PAUSA\nAVISE O EXPERIMENTADOR'
        self.go_to('pause')

    def session_unpause(self):
        self.go_to('game')

    def session_end(self, status):
        end_text = u'Sessão encerrada:\n\naguarde o pesquisador'
        if obs:
            end_text += u'\n\n{}\n{}'.format(status, App.get_running_app().observer_message)
        self.get_screen('end').ids.end_label.text = end_text
        self.go_to('end')

class HoverLabel(Label, HoverBehavior):
    def on_enter(self, *args):
        pass
        # print "You are in, though this point", self.border_point

    def on_leave(self, *args):
        pass
        # print "You left through this point", self.border_point

class HoverButton(Button, HoverBehavior):
    def on_enter(self, *args):
        pass
        # print "You are in, though this point", self.border_point

    def on_leave(self, *args):
        pass
        # print "You left through this point", self.border_point

class ClientAMP(amp.AMP):
    """
    Client with a customized Assynchronous Messaging Protocol.
    Enables client-server communication.
    """

    def __init__(self):
        super(ClientAMP, self).__init__()

    # AMP methods
    def makeConnection(self, transport):
        """overrides default TCP delay with no delay"""
        if not transport.getTcpNoDelay():
            transport.setTcpNoDelay(True)
        super(ClientAMP, self).makeConnection(transport)

    def connectionLost(self, reason):
        App.get_running_app().connection_error(reason,
                                               print_error='Connection lost: '
                                                           + repr(reason))
        super(ClientAMP, self).connectionLost(reason)

        # TODO: maybe explore using AMP.connectionLost to display a message!

    def disconnect_player(self, reason):
        print 'disconnecting player', repr(reason)

    def ready_players(self):
        self.callRemote(cmd.ReadyPlayers).addErrback(self.disconnect_player)

    def request_instruction_end(self):
        self.callRemote(cmd.RequestInstructionEnd)

    @cmd.GameReady.responder
    def game_ready(self):
        sm.start_game_screen()
        return {}

    @cmd.InstructionEnd.responder
    def instruction_end(self):
        app.instruction_end()
        return {}

    @cmd.PlayerLeft.responder
    def player_left(self):
        print 'player has left'

        app.player_left()
        # DO STUFF HERE (PAUSE GAME?)
        return {}

    @cmd.PauseSession.responder
    def pause_session(self):
        print 'pause'

        app.session_pause()
        # DO STUFF HERE (PAUSE GAME?)
        return {}

    @cmd.UnPauseSession.responder
    def unpause_session(self):
        print 'unpause'

        app.session_unpause()
        # DO STUFF HERE (PAUSE GAME?)
        return {}

    @cmd.EndSession.responder
    def end_session(self, status):
        print 'session ended. status:', status
        # TODO: block game

        sm.session_end(status)
        return {}

    @cmd.ShowAdj.responder
    def show_adj(self, show):

        app.show_adj(show)
        return {}

    @cmd.ShowInstruction.responder
    def show_instruction(self, ref, target):
        if app.player_count == 0:
            instruction = pickle.loads(ref)
        else:
            instruction = pickle.loads(target)

        app.show_instruction(instruction)
        return {}

    @cmd.RefBack.responder
    def ref_back(self, ref_back_pickle):
        ref_back = pickle.loads(ref_back_pickle)
        app.change_back(ref_back, 0)
        return {}

    @cmd.AdjBack.responder
    def adj_back(self, adj_back_pickle):
        adj_back = pickle.loads(adj_back_pickle)
        app.change_back(adj_back, 1)
        return {}

    @cmd.AddPoint.responder
    def add_point(self, player, points):

        app.add_point(player, points)

        return {}

    def point_press(self):
        self.callRemote(cmd.PointPress)

    def n_press(self):
        self.callRemote(cmd.NPress)

    def f_press(self):
        self.callRemote(cmd.FPress)

class ClientFactory(_InstanceFactory):
    """Factory used by ClientCreator, using ClientAMP protocol."""

    protocol = ClientAMP

    def __init__(self, some_reactor, instance, deferred):
        _InstanceFactory.__init__(self, some_reactor, instance, deferred)
        self.client = None

    def __repr__(self):
        return "<ClientAMP factory: %r>" % (self.instance,)

    def add_client(self, p):
        self.client = p

    def disconnect_client(self):
        if self.client.transport:
            self.client.transport.loseConnection()
        Clock.schedule_once(self.cleanup_client, 0.00001)
        # self.cleanup_client()

    def cleanup_client(self, *args):
        del self.client
        self.client = None

class ClientApp(App):

    player_count = None

    freeze = False
    sound = {}
    total_points = 0
    points_added = False

    observer_message = u''

    ref_points = 0
    adj_points = 0

    adj = False

    def build(self):
        global sm
        global app
        app = self

        sm = ScreenManagerMain(transition=SlideTransition())
        sm.add_widget(ScreenConnect(name='connect'))
        sm.add_widget(ScreenWait(name='wait'))
        sm.add_widget(ScreenGame(name='game'))
        sm.add_widget(ScreenPause(name='pause'))
        sm.add_widget(ScreenEnd(name='end'))
        sm.add_widget(ScreenInstruction(name='instruction'))

        self.sound['point added'] = [SoundLoader.load('res/sounds/smw_coin.wav') for _ in xrange(5)]
        self.sound['point change'] = [SoundLoader.load('res/sounds/coinshake.wav') for _ in xrange(5)]
        self.sound['start choice'] = [SoundLoader.load('res/sounds/swosh.wav') for _ in xrange(5)]
        self.sound['button press'] = [SoundLoader.load('res/sounds/button.wav') for _ in xrange(5)]

        if obs:
            self.title = 'Observer'
        else:
            self.title = 'Client'

        # Create the screen manager
        return sm

    def on_start(self):
        super(ClientApp, self).on_start()
        if 'autoconnect' in sys.argv \
                or cfg.client['options']['autoconnect']:
            self.try_to_connect()

    # def fix_game_layout(self, *args):
    #
    #     # fixes from experiment config
    #
    #     gm = sm.get_screen('game')
    #
    #     for button in xrange(1, 8):
    #         button_widget = getattr(sm.get_screen('game').color_parameters_layout.ids, 'color_{}'.format(button))
    #         button_widget.background_color = cfg.exp['colors'][str(button)]
    #
    #
    #     # fix game layout
    #
    #     self.set_button_hover(self.active_set, forced=True)
    #     self.set_layout(initial_fix=True)

    # CONNECT SCREEN METHODS

    def try_to_connect(self, *args):
        print 'will try to connect'
        global fac

        # check for invalid HOST/PORT
        if not self.check_valid_ip_port():
            sm.get_screen('connect').reset_layout()
            return

        # logging client into twisted not necessarily a good idea, but possible
        # log stdout using sys.stdout)

        deferred = defer.Deferred()
        fac = ClientFactory(reactor, ClientAMP(), deferred)

        def got_protocol(p):
            print 'got protocol'
            # global fac
            p.callRemote(cmd.AddClient, observer=obs).\
                addCallback(self.add_client_result).\
                addErrback(self.add_client_error)
            fac.add_client(p)

        print 'starting reactor'

        reactor.connectTCP(HOST, PORT, fac, timeout=10)
        deferred.addCallback(got_protocol)
        deferred.addErrback(self.cant_connect_error)

    def add_client_result(self, result):
        added = result['added']
        ready = result['ready']
        player_count = result['player_count']
        self.player_count = player_count
        if self.player_count:
            self.adj = True

        if added:
            # TODO: see if these two are needed at all
            cfg.exp = pickle.loads(result['experiment_pickle'])
            cfg.conds = pickle.loads(result['conditions_pickle'])

            if ready:
                fac.client.ready_players()
            else:
                sm.start_wait_screen()
        else:
            self.disconnect_client(reason=result['reason'])

    def set_host(self, host):
        global HOST
        host = str(host)
        HOST = host
        self.check_valid_ip_port()

    def set_port(self, port):
        global PORT
        if port:
            port = int(port)
        else:
            port = 0
        PORT = port
        self.check_valid_ip_port()

    def save_host(self, host):
        self.set_host(host)
        if is_valid_ip(HOST):
            shared['host'] = HOST
            shared.write()

    def save_port(self, port):
        self.set_port(port)
        if 0 <= PORT <= MAX_PORT:
            shared['port'] = PORT
            shared.write()

    def check_valid_ip_port(self):
        result = False
        valid_ip = is_valid_ip(HOST)
        valid_port = bool(0 <= PORT <= MAX_PORT)
        if valid_ip and valid_port:
            print_error = ''
            result = True
        elif not valid_ip and not valid_port:
            print_error = 'invalid ip and port'
        elif not valid_ip:
            print_error = 'invalid ip'
        else:
            print_error = 'invalid port'
        sm.get_screen('connect').print_error(print_error)
        return result

    # connect error handling methods

    def cant_connect_error(self, reason):
        self.connection_error(reason, print_error='cannot connect: ' + repr(reason))

    def add_client_error(self, reason):
        self.connection_error(reason, print_error='server could not add client: ' + repr(reason))

    def connection_error(self, reason, print_error=None):
        reason.printTraceback()
        if not isinstance(print_error, str):
            print_error = repr(reason)
        sm.get_screen('connect').print_error(print_error)
        sm.go_to('connect', direction='right')


    def disconnect_client(self, clear_error=True, reason=None):
        # do stuff here to actually disconnect
        fac.disconnect_client()
        sm.get_screen('connect').reset_layout()
        sm.go_to('connect', direction='right')

        if reason:
            print_error = reason
        elif clear_error:
            print_error = ''
        else: # do not clear_error
            return
        Clock.schedule_once(lambda x: sm.get_screen('connect').
                            print_error(print_error), 0.1)

    def player_left(self):
        # TODO: unschedule all funcs
        print 'running player_left from app'
        sm.player_left()


    def session_pause(self):
        # TODO: unschedule stuff
        sm.session_pause()

    def session_unpause(self):
        # TODO: reschedule stuff?
        sm.session_unpause()

    def bailout(self, reason):
        reason.printTraceback()
        if stout:
            stout.close()
        self.stop()


    def set_freeze(self, freeze=True):
        if freeze:
            self.freeze = True
        else:
            self.freeze = False

    def update_observer(self, cycle, percent_correct, consec_correct):
        self.observer_message = u'cycle: {}\npercent: {}\nconsec: {}'.format(cycle, percent_correct, consec_correct)
        gm = sm.get_screen('game')
        gm.ids.label_game_message.text = self.observer_message


    def point_press(self):
        fac.client.point_press()

    def n_press(self):
        fac.client.n_press()

    def f_press(self):
        fac.client.f_press()

    def show_adj(self, show):
        gm = sm.get_screen('game')
        if self.adj:
            gm.adj_overlay = 0
            if show:
                gm.ref_overlay = 0
            else:
                gm.ref_overlay = 1
        else:
            gm.ref_overlay = 0
            if show:
                gm.adj_overlay = 0
            else:
                gm.adj_overlay = 1

    def show_instruction(self, instruction):

        print 'GOT TO SHOW INSTRUCTION ON APP'

        sm.get_screen('instruction').ids.instruction_label.text = instruction
        sm.go_to('instruction')

    def instruction_press(self):
        if self.player_count == 0:
            fac.client.request_instruction_end()

    def instruction_end(self):
        # TODO: start timing variables here

        sm.go_to('game')

    def change_back(self, back, player):
        # TO DO: move color changing stuff to game screen
        change_ref = True
        if self.adj:
            if not player:
                change_ref = False
        else:
            if player:
                change_ref = False

        if change_ref:
            self.change_ref_back(back)
        else:
            self.change_adj_back(back)

    @staticmethod
    def change_ref_back(back):
        gm = sm.get_screen('game')
        if back == "":
            # TODO: put appropriate color
            pass
        elif len(back) == 4:
            gm.ref_r = back[0]
            gm.ref_g = back[1]
            gm.ref_b = back[2]
            gm.ref_a = back[3]

    @staticmethod
    def change_adj_back(back):
        gm = sm.get_screen('game')
        if back == "":
            # TODO: put appropriate color
            pass
        elif len(back) == 4:
            gm.adj_r = back[0]
            gm.adj_g = back[1]
            gm.adj_b = back[2]
            gm.adj_a = back[3]



    def add_point(self, player, points):
        adj = False
        if not player == self.player_count:
            adj = True
        else:
            pass
        if self.player_count == 0:
            self.ref_points = points[0]
            self.adj_points = points[1]
        else:
            self.ref_points = points[1]
            self.adj_points = points[0]

        sm.get_screen('game').coin_anim(adj)




    # def set_layout(self, initial_fix=False):
    #     sm.get_screen('game').set_layout(self.active_set, initial_fix)


def load_cfg():
    cfg_dir = os.path.join(DIR, 'config')
    spec_dir = os.path.join(cfg_dir, 'spec')
    lang_dir = os.path.join(cfg_dir, 'lang', LANG)

    cfg.widgets_text = ConfigObj(infile=os.path.join(lang_dir, 'widgets_text.ini'),
                                 configspec=os.path.join(spec_dir, 'spec_widgets_text.ini'),
                                 encoding='UTF8')
    validate_config(cfg.widgets_text)

    # TODO: check if needed
    cfg.client = ConfigObj(infile=os.path.join(cfg_dir, 'client.ini'),
                           configspec=os.path.join(spec_dir, 'spec_client.ini'))
    validate_config(cfg.client)

def set_obs_on():
    global obs
    obs = True



def main():
    # global sm
    global stout

    # CREATE DIRS AND STOUT
    if obs:
        print "I AM OBS!"
        # redirect sdtout and stderr to log file
        if not os.path.exists(os.path.join(DIR, 'output', 'log', 'observer')):
            os.mkdir(os.path.join(DIR, 'output', 'log', 'observer'))
        stout = StandOut(logfile=os.path.join(DIR, 'output', 'log', 'observer',
                                              'log%s.txt' % LOCALTIME))
    else:  # client
        print "I AM CLIENT!"
        # redirect sdtout and stderr to log file
        if not os.path.exists(os.path.join(DIR, 'output', 'log', 'client')):
            os.mkdir(os.path.join(DIR, 'output', 'log', 'client'))
        stout = StandOut(logfile=os.path.join(DIR, 'output', 'log', 'client',
                                              'log%s.txt' % LOCALTIME))

    load_cfg()

    # KV BUILDERS
    with codecs.open(os.path.join(RESDIR,
                           'scripts',
                           'kv',
                           'client.kv'), 'r', 'utf-8') as f:
        Builder.load_string(f.read().format(**dict(cfg.widgets_text.dict(),
                                                   input_conn_ip=HOST,
                                                   input_conn_port=PORT,
                                                   set_buttons_smaller=win_cfg['game layout']['set buttons smaller'],
                                                   set_buttons_spacing="'{}dp'".format(win_cfg['game layout']['set buttons spacing']),
                                                   # PRESERVE THESE (partial formatting)
                                                   size_var='{size_var}'
                                                   )))
    ClientApp().run()

# globals - alphabetical order
cfg = Container()
fac = None
obs = False
sm = None
stout = False
app = None

play_index = 0


def play(sound):
    global play_index
    sound[play_index].play()
    play_index = (play_index + 1) % 5


# fool inspection
if False:
    stout = StandOut()
    # sm = ScreenManager()

if __name__ == '__main__':
    import traceback
    # noinspection PyBroadException
    try:
        main()
    except:
        traceback.print_exc()
        if stout:
            stout.close()