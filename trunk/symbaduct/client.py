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

# import random
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

# class ScreenGameBackground(RelativeLayout):
#     r = NumericProperty(1.0)
#     g = NumericProperty(1.0)
#     b = NumericProperty(1.0)
#     a = NumericProperty(1.0)

class ScreenGame(Screen):
    r = NumericProperty(BACKGROUND_COLOR[0])
    g = NumericProperty(BACKGROUND_COLOR[1])
    b = NumericProperty(BACKGROUND_COLOR[2])
    a = NumericProperty(BACKGROUND_COLOR[3])
    test_r = NumericProperty(0.5)
    test_g = NumericProperty(1.0)
    test_b = NumericProperty(0.5)
    test_a = NumericProperty(1.0)

    def __init__(self, **kwargs):
        super(ScreenGame, self).__init__(**kwargs)

        # parameter widgets
        # self.color_parameters_layout = ColorParametersLayout()
        # self.shape_parameters_layout = ShapeParametersLayout()
        # self.size_parameters_layout = SizeParametersLayout()
        # self.unbind_color_buttons_hover()
        # self.unbind_shape_buttons_hover()
        # self.unbind_size_buttons_hover()

        if obs:
            self.disable_buttons()

    def disable_buttons(self):
        # obs here: disable all buttons (currently disabled by checking obs)
        pass

    def test_player_count(self, player_count):
        self.ids.label_game_message.text = str(player_count)
        if player_count == 1:
            self.test_r = 1.0
            self.test_g = 0.5
            self.test_b = 0.5
            self.test_a = 1.0


    def set_layout(self, button, initial_fix=False):
        pass

class ScreenPause(Screen):
    pass

class ScreenEnd(Screen):
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

        # elif key == 'right':
        #     if self.current == 'game':
        #         App.get_running_app().press_right()
        #
        #
        # elif key == 'enter':
        #     if self.current == 'game':
        #         App.get_running_app().press_enter()

        return True

    def start_wait_screen(self):
        fix_window_size()
        self.go_to('wait')

        # reset connect screen layout for when we go back to that screen.
        Clock.schedule_once(self.get_screen('connect').reset_layout, 0.2)

    def start_game_screen(self):
        fix_window_size()
        self.go_to('game')

        app = App.get_running_app()
        player_count = app.player_count
        if obs:
            player_count = 'Observer {}'.format(player_count)
        else:
            print player_count
        sm.get_screen('game').test_player_count(player_count)

        # fix game screen almost as soon as it is shown
        # Clock.schedule_once(app.fix_game_layout, 0.1)

        # reset connect screen layout for when we go back to that screen.
        Clock.schedule_once(self.get_screen('connect').reset_layout, 0.2)


    def player_left(self):
        self.get_screen('pause').ids.pause_label.text = 'PAUSE\nPLAYER LEFT'
        self.go_to('pause')

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


# class CompositeButton(Button):
#     def set_image_source(self, shape=1):
#         self.ids.comp_image.source = 'res/images/{}'.format(cfg.exp['shapes'][str(shape)])

# class SetButton(HoverButton):
#     pass
#     # def on_enter(self, *args):
#     #     self.background_normal = '(0.5, 0.5, 0.5. 1.0)'
#     #
#     # def on_leave(self, *args):
#     #     self.background_normal = ''

# class ParameterButton(HoverButton):
#     pass
#
#
# class SizeButton(ParameterButton):
#     size_var = NumericProperty(1)
#
# class ShapeButton(ParameterButton):
#     shape_var = NumericProperty(1)
#     color_files = DictProperty()
#     def set_image_source(self, shape=1):
#         self.ids.shape_image.source = 'res/images/{}'.format(cfg.exp['shapes'][str(shape)])
#
#     def selected(self):
#         if self.ids.shape_image.color != [0, 0, 0, 1]:
#             self.ids.shape_image.color = [0, 0, 0, 1]
#
#     def unselected(self):
#         if self.ids.shape_image.color != [0.5, 0.5, 0.5, 1]:
#             self.ids.shape_image.color = [0.5, 0.5, 0.5, 1]
#
# class ColorButton(ParameterButton):
#     color_var = NumericProperty(1)


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

    @cmd.GameReady.responder
    def game_ready(self):
        sm.start_game_screen()
        return {}

    @cmd.PlayerLeft.responder
    def player_left(self):
        print 'player has left'

        App.get_running_app().player_left()
        # DO STUFF HERE (PAUSE GAME?)
        return {}
        #
        # @cmd.StartSession.responder
        # def start(self, source):
        #     # DO STUFF TO START HERE
        #     return {}

    @cmd.EndSession.responder
    def end_session(self, status):
        print 'session ended. status:', status
        # TODO: block game

        sm.session_end(status)
        return {}

    # @cmd.StartFeedback.responder
    # def start_feedback(self, points, total_points, reset_color, reset_shape, reset_size):
    #     App.get_running_app().start_feedback(points, total_points, reset_color, reset_shape, reset_size)
    #     return {}
    #
    # @cmd.RestartChoice.responder
    # def restart_choice(self):
    #     App.get_running_app().restart_choice()
    #     return {}
    #
    # @cmd.UpdateObserver.responder
    # def update_observer(self, cycle, percent_correct, consec_correct):
    #     App.get_running_app().update_observer(cycle, percent_correct, consec_correct)
    #     return {}
    #
    # @cmd.ChangePoints.responder
    # def change_points(self):
    #     App.get_running_app().change_points()
    #     return {}
    #
    # def set_button_hover(self, button, forced):
    #     self.callRemote(cmd.SetButtonHover,
    #                     button=button,
    #                     forced=forced)
    #
    # @cmd.SetButtonHovered.responder
    # def set_button_hovered(self, button, forced):
    #     App.get_running_app().set_button_hovered(button, forced)
    #     return {}
    #
    # def set_button_hover_leave(self, button, forced):
    #     self.callRemote(cmd.SetButtonHoverLeave,
    #                     button=button,
    #                     forced=forced)
    #
    # @cmd.SetButtonHoverLeft.responder
    # def set_button_hover_left(self, button, forced):
    #     App.get_running_app().set_button_hover_left(button, forced)
    #     return {}
    #
    # def set_button_press(self, button):
    #     self.callRemote(cmd.SetButtonPress,
    #                     button=button)
    #
    # @cmd.SetButtonPressed.responder
    # def set_button_pressed(self, button):
    #     App.get_running_app().set_button_pressed(button)
    #     return{}
    #
    # def color_button_hover(self, button, forced):
    #     self.callRemote(cmd.ColorButtonHover,
    #                     button=button,
    #                     forced=forced)
    #
    # @cmd.ColorButtonHovered.responder
    # def color_button_hovered(self, button, forced):
    #     App.get_running_app().color_button_hovered(button, forced)
    #     return {}
    #
    # def color_button_hover_leave(self, button, forced):
    #     self.callRemote(cmd.ColorButtonHoverLeave,
    #                     button=button,
    #                     forced=forced)
    #
    # @cmd.ColorButtonHoverLeft.responder
    # def color_button_hover_left(self, button, forced):
    #     App.get_running_app().color_button_hover_left(button, forced)
    #     return {}
    #
    # def color_button_press(self, button):
    #     self.callRemote(cmd.ColorButtonPress,
    #                     button=button)
    #
    # @cmd.ColorButtonPressed.responder
    # def color_button_pressed(self, button):
    #     App.get_running_app().color_button_pressed(button)
    #     return{}
    #
    # def size_button_hover(self, button, forced):
    #     self.callRemote(cmd.SizeButtonHover,
    #                     button=button,
    #                     forced=forced)
    #
    # @cmd.SizeButtonHovered.responder
    # def size_button_hovered(self, button, forced):
    #     App.get_running_app().size_button_hovered(button, forced)
    #     return {}
    #
    # def size_button_hover_leave(self, button, forced):
    #     self.callRemote(cmd.SizeButtonHoverLeave,
    #                     button=button,
    #                     forced=forced)
    #
    # @cmd.SizeButtonHoverLeft.responder
    # def size_button_hover_left(self, button, forced):
    #     App.get_running_app().size_button_hover_left(button, forced)
    #     return {}
    #
    # def size_button_press(self, button):
    #     self.callRemote(cmd.SizeButtonPress,
    #                     button=button)
    #
    # @cmd.SizeButtonPressed.responder
    # def size_button_pressed(self, button):
    #     App.get_running_app().size_button_pressed(button)
    #     return{}
    #
    # def shape_button_hover(self, button, forced):
    #     self.callRemote(cmd.ShapeButtonHover,
    #                     button=button,
    #                     forced=forced)
    #
    # @cmd.ShapeButtonHovered.responder
    # def shape_button_hovered(self, button, forced):
    #     App.get_running_app().shape_button_hovered(button, forced)
    #     return {}
    #
    # def shape_button_hover_leave(self, button, forced):
    #     self.callRemote(cmd.ShapeButtonHoverLeave,
    #                     button=button,
    #                     forced=forced)
    #
    # @cmd.ShapeButtonHoverLeft.responder
    # def shape_button_hover_left(self, button, forced):
    #     App.get_running_app().shape_button_hover_left(button, forced)
    #     return {}
    #
    # def shape_button_press(self, button):
    #     self.callRemote(cmd.ShapeButtonPress,
    #                     button=button)
    #
    # @cmd.ShapeButtonPressed.responder
    # def shape_button_pressed(self, button):
    #     App.get_running_app().shape_button_pressed(button)
    #     return{}
    #
    # def composite_button_press(self):
    #     self.callRemote(cmd.CompositeButtonPress)
    #
    # @cmd.CompositeButtonPressed.responder
    # def composite_button_pressed(self):
    #     App.get_running_app().composite_button_pressed()
    #     return {}

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
    # active_set = 'color'
    # active_color = 1
    # active_shape = 1
    # active_size = 1
    # reset_color = 1
    # reset_shape = 1
    # reset_size = 1

    freeze = False
    sound = {}
    total_points = 0
    points_added = False

    observer_message = u''

    def build(self):
        global sm
        sm = ScreenManagerMain(transition=SlideTransition())
        sm.add_widget(ScreenConnect(name='connect'))
        sm.add_widget(ScreenWait(name='wait'))
        sm.add_widget(ScreenGame(name='game'))
        sm.add_widget(ScreenPause(name='pause'))
        sm.add_widget(ScreenEnd(name='end'))

        self.sound['point added'] = SoundLoader.load('res/sounds/smw_coin.wav')
        self.sound['point change'] = SoundLoader.load('res/sounds/coinshake.wav')
        self.sound['start choice'] = SoundLoader.load('res/sounds/swosh.wav')
        self.sound['button press'] = SoundLoader.load('res/sounds/button.wav')

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
    #     active_shape = getattr(gm.shape_parameters_layout.ids, 'shape_{}'.format(self.active_shape))
    #     active_shape.selected()
    #
    #     composite_button = gm.ids.composite_button
    #
    #     min_size = min(composite_button.parent.height / 7 * self.active_size,
    #                    composite_button.parent.width / 7 * self.active_size)
    #     composite_button.height = min_size
    #     composite_button.width = min_size
    #
    #     composite_button.set_image_source(self.active_shape)
    #     composite_button.ids.comp_image.color = cfg.exp['colors'][str(self.active_color)]
    #
    #     # TODO: get from score
    #     gm.ids.point_label.text = '0'
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
        if added:
            cfg.exp = pickle.loads(result['experiment_pickle'])
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



    def bailout(self, reason):
        reason.printTraceback()
        if stout:
            stout.close()
        self.stop()

    # def set_button_hover(self, button, forced=False):
    #     if obs or self.freeze:
    #         return
    #     fac.client.set_button_hover(button, forced)
    #     # self.set_button_hovered(button, forced)
    #
    # def set_button_hovered(self, button, forced=False):
    #     if forced:
    #         pass
    #     elif self.active_set == button:
    #         return
    #
    #     button_widget = getattr(sm.get_screen('game').ids, 'set_{}'.format(button))
    #     button_widget.size = button_widget.parent.size
    #
    #     if not self.active_set == button:
    #         self.set_button_hover_leave(self.active_set)
    #
    # def set_button_hover_leave(self, button, forced=False):
    #     if obs or self.freeze:
    #         return
    #     fac.client.set_button_hover_leave(button, forced)
    #
    # def set_button_hover_left(self, button, forced=False):
    #     if forced:
    #         pass
    #     elif self.active_set == button:
    #         return
    #
    #     button_widget = getattr(sm.get_screen('game').ids, 'set_{}'.format(button))
    #     smaller = win_cfg['game layout']['set buttons smaller']
    #
    #     button_widget.width = int(button_widget.parent.width * smaller)
    #     button_widget.height = int(button_widget.parent.height * smaller)
    #
    #     self.set_button_hover(self.active_set, forced=True)
    #
    # def set_button_press(self, button):
    #     if obs or self.freeze:
    #         return
    #     fac.client.set_button_press(button)
    #     # self.set_button_pressed(button)
    #
    # def set_button_pressed(self, button):
    #     if self.active_set == button:
    #         return
    #     self.sound['button press'].play()
    #     previous = self.active_set
    #     self.active_set = button
    #     self.set_button_hover_leave(previous, forced=True)
    #     self.set_layout()
    #
    # def color_button_hover(self, button, forced=False):
    #     if obs or self.freeze:
    #         return
    #     fac.client.color_button_hover(button, forced)
    #
    # def color_button_hovered(self, button, forced):
    #     if forced:
    #         pass
    #     elif self.active_color == button:
    #         return
    #
    #     lay = sm.get_screen('game').color_parameters_layout
    #
    #     smaller = win_cfg['game layout']['set buttons smaller']
    #     for i in xrange(1, 8):
    #         if not i == int(button) and not i == self.active_color:
    #             other_button_widget = getattr(lay.ids, 'color_{}'.format(i))
    #             other_button_widget.width = int(other_button_widget.parent.height * smaller)
    #             other_button_widget.height = int(other_button_widget.parent.height * smaller)
    #
    #     button_widget = getattr(lay.ids, 'color_{}'.format(button))
    #     button_widget.width = button_widget.parent.height
    #     button_widget.height = button_widget.parent.height
    #
    # def color_button_hover_leave(self, button, forced=False):
    #     if obs or self.freeze:
    #         return
    #     fac.client.color_button_hover_left(button, forced)
    #
    # def color_button_hover_left(self, button, forced):
    #     if forced:
    #         pass
    #     elif self.active_color == button:
    #         return
    #
    #     lay = sm.get_screen('game').color_parameters_layout
    #
    #     button_widget = getattr(lay.ids, 'color_{}'.format(button))
    #
    #     smaller = win_cfg['game layout']['set buttons smaller']
    #     button_widget.width = int(button_widget.parent.height * smaller)
    #     button_widget.height = int(button_widget.parent.height * smaller)
    #
    #     self.color_button_hovered(self.active_color, forced=True)
    #
    # def color_button_press(self, button):
    #     if obs or self.freeze:
    #         return
    #     # self.color_button_pressed(button)
    #     fac.client.color_button_press(button)
    #
    # def color_button_pressed(self, button, silence=False):
    #     if self.active_color == button:
    #         return
    #     previous = self.active_color
    #     self.active_color = button
    #     self.color_button_hover_left(previous, forced=True)
    #     sm.get_screen('game').ids.composite_button.ids.comp_image.color = cfg.exp['colors'][str(button)]
    #     if not silence:
    #         self.sound['button press'].play()
    #
    # def size_button_hover(self, button, forced=False):
    #     if obs or self.freeze:
    #         return
    #     fac.client.size_button_hover(button, forced)
    #
    # def size_button_hovered(self, button, forced):
    #     if forced:
    #         pass
    #     elif self.active_size == button:
    #         return
    #
    #     lay = sm.get_screen('game').size_parameters_layout
    #     for i in xrange(1, 8):
    #         if not i == int(button) and not i == self.active_size:
    #             other_button_widget = getattr(lay.ids, 'size_{}'.format(i))
    #             other_button_widget.background_color = 1, 1, 1, 0.7
    #
    #     button_widget = getattr(sm.get_screen('game').size_parameters_layout.ids, 'size_{}'.format(button))
    #     button_widget.background_color = 0.5, 0.5, 0.5, 1
    #
    # def size_button_hover_leave(self, button, forced=False):
    #     if obs or self.freeze:
    #         return
    #     fac.client.size_button_hover_leave(button, forced)
    #
    # def size_button_hover_left(self, button, forced):
    #     if forced:
    #         pass
    #     elif self.active_size == button:
    #         return
    #
    #     button_widget = getattr(sm.get_screen('game').size_parameters_layout.ids, 'size_{}'.format(button))
    #     button_widget.background_color = 1, 1, 1, 0.7
    #
    #     self.size_button_hovered(self.active_size, forced=True)
    #
    # def size_button_press(self, button):
    #     if obs or self.freeze:
    #         return
    #     fac.client.size_button_press(button)
    #
    # def size_button_pressed(self, button, silence=False):
    #
    #     if self.active_size == button:
    #         return
    #     previous = self.active_size
    #     self.active_size = button
    #     self.size_button_hover_left(previous, forced=True)
    #
    #     composite_button = sm.get_screen('game').ids.composite_button
    #
    #     min_size = min(composite_button.parent.height / 7 * button,
    #                    composite_button.parent.width / 7 * button)
    #     composite_button.height = min_size
    #     composite_button.width = min_size
    #     if not silence:
    #         self.sound['button press'].play()
    #
    # def shape_button_hover(self, button, forced=False):
    #     if obs or self.freeze:
    #         return
    #     fac.client.shape_button_hover(button, forced)
    #
    # def shape_button_hovered(self, button, forced):
    #     if forced:
    #         pass
    #     elif self.active_shape == button:
    #         return
    #
    #     lay = sm.get_screen('game').shape_parameters_layout
    #
    #     smaller = win_cfg['game layout']['set buttons smaller']
    #     for i in xrange(1, 8):
    #         if not i == int(button) and not i == self.active_shape:
    #             other_button_widget = getattr(lay.ids, 'shape_{}'.format(i))
    #             other_button_widget.width = int(other_button_widget.parent.height * smaller)
    #             other_button_widget.height = int(other_button_widget.parent.height * smaller)
    #
    #     button_widget = getattr(sm.get_screen('game').shape_parameters_layout.ids, 'shape_{}'.format(button))
    #     button_widget.width = button_widget.parent.height
    #     button_widget.height = button_widget.parent.height
    #
    #     # if not self.active_shape == button:
    #     #     self.shape_button_hover_leave(self.active_shape)
    #
    # def shape_button_hover_leave(self, button, forced=False):
    #     if obs or self.freeze:
    #         return
    #     fac.client.shape_button_hover_leave(button, forced)
    #
    # def shape_button_hover_left(self, button, forced):
    #     if forced:
    #         pass
    #     elif self.active_shape == button:
    #         return
    #
    #     button_widget = getattr(sm.get_screen('game').shape_parameters_layout.ids, 'shape_{}'.format(button))
    #
    #     smaller = win_cfg['game layout']['set buttons smaller']
    #     button_widget.width = int(button_widget.parent.height * smaller)
    #     button_widget.height = int(button_widget.parent.height * smaller)
    #
    #     self.shape_button_hovered(self.active_shape, forced=True)
    #
    # def shape_button_press(self, button):
    #     if obs or self.freeze:
    #         return
    #     fac.client.shape_button_press(button)
    #
    # def shape_button_pressed(self, button, silence=False):
    #
    #     if self.active_shape == button:
    #         return
    #     previous = self.active_shape
    #     self.active_shape = button
    #     self.shape_button_hover_left(previous, forced=True)
    #     sm.get_screen('game').ids.composite_button.set_image_source(self.active_shape)
    #     for button in xrange(1, 8):
    #         button_widget = getattr(sm.get_screen('game').shape_parameters_layout.ids, 'shape_{}'.format(button))
    #         if button == self.active_shape:
    #             button_widget.selected()
    #         else:
    #             button_widget.unselected()
    #     if not silence:
    #         self.sound['button press'].play()
    #
    # def composite_button_press(self):
    #     if obs or self.freeze:
    #         return
    #     self.freeze = True
    #     fac.client.composite_button_press()
    #
    # def composite_button_pressed(self):
    #     print 'composite was pressed'
    #     self.set_freeze(True)
    #     sm.get_screen('game').ids.composite_button.background_down = ''
    #     self.sound['button press'].play()

    def set_freeze(self, freeze=True):
        # gm = sm.get_screen('game')
        if freeze:
            self.freeze = True
            # gm.r, gm.g, gm.b, gm.a = FEEDBACK_BACKGROUND_COLOR
            # sm.get_screen('game').ids.composite_button.background_down = \
            #     'res/images/transparent.png'
        else:
            self.freeze = False
            # gm.r, gm.g, gm.b, gm.a = BACKGROUND_COLOR
            # sm.get_screen('game').ids.composite_button.background_down = \
            #     'res/images/30gray.png'

    # def start_feedback(self, points, total_points, reset_color, reset_shape, reset_size):
    #     self.total_points = total_points # to update later
    #     self.reset_color = reset_color
    #     self.reset_shape = reset_shape
    #     self.reset_size = reset_size
    #     if points > 0:
    #         self.points_added = True
    #     else:
    #         self.points_added = False
    #
    #     gm = sm.get_screen('game')
    #
    #     if self.points_added:
    #         gm.ids.add_point_label.text = '+ {}'.format(points)
    #         self.sound['point added'].play()
    #     else:
    #         gm.ids.add_point_label.text = '{}'.format(points)

    # def restart_choice(self):
    #     self.set_freeze(False)
    #     self.sound['start choice'].play()
    #     self.color_button_pressed(self.reset_color, silence=True)
    #     self.shape_button_pressed(self.reset_shape, silence=True)
    #     self.size_button_pressed(self.reset_size, silence=True)

    def update_observer(self, cycle, percent_correct, consec_correct):
        self.observer_message = u'cycle: {}\npercent: {}\nconsec: {}'.format(cycle, percent_correct, consec_correct)
        gm = sm.get_screen('game')
        gm.ids.label_game_message.text = self.observer_message

    def change_points(self):
        gm = sm.get_screen('game')
        gm.ids.point_label.text = '{}'.format(self.total_points)
        gm.ids.add_point_label.text = ''
        if self.points_added:
            self.sound['point change'].play()
    #
    # def press_right(self):
    #     self.pressed_right()
    #
    # def pressed_right(self):
    #     if self.active_set == 'color':
    #         self.set_button_press('shape')
    #     elif self.active_set == 'shape':
    #         self.set_button_press('size')
    #     elif self.active_set == 'size':
    #         pass
    #
    # def press_left(self):
    #     self.pressed_left()
    #
    # def pressed_left(self):
    #     if self.active_set == 'color':
    #         pass
    #     elif self.active_set == 'shape':
    #         self.set_button_press('color')
    #     elif self.active_set == 'size':
    #         self.set_button_press('shape')
    #
    # def press_up(self):
    #     self.pressed_up()
    #
    # def pressed_up(self):
    #     if self.active_set == 'color':
    #         self.press_up_color()
    #     elif self.active_set == 'shape':
    #         self.press_up_shape()
    #     elif self.active_set == 'size':
    #         self.press_up_size()
    #
    # def press_down(self):
    #     self.pressed_down()
    #
    # def pressed_down(self):
    #     if self.active_set == 'color':
    #         self.press_down_color()
    #     elif self.active_set == 'shape':
    #         self.press_down_shape()
    #     elif self.active_set == 'size':
    #         self.press_down_size()
    #
    # def press_up_color(self):
    #     self.pressed_up_color()
    #
    # def pressed_up_color(self):
    #     if self.active_color == 1:
    #         return
    #     self.color_button_press(self.active_color - 1)
    #
    # def press_down_color(self):
    #     self.pressed_down_color()
    #
    # def pressed_down_color(self):
    #     if self.active_color == 7:
    #         return
    #     self.color_button_press(self.active_color + 1)
    #
    # def press_up_shape(self):
    #     self.pressed_up_shape()
    #
    # def pressed_up_shape(self):
    #     if self.active_shape == 1:
    #         return
    #     self.shape_button_press(self.active_shape - 1)
    #
    # def press_down_shape(self):
    #     self.pressed_down_shape()
    #
    # def pressed_down_shape(self):
    #     if self.active_shape == 7:
    #         return
    #     self.shape_button_press(self.active_shape + 1)
    #
    # def press_up_size(self):
    #     self.pressed_up_size()
    #
    # def pressed_up_size(self):
    #     if self.active_size == 1:
    #         return
    #     self.size_button_press(self.active_size - 1)
    #
    # def press_down_size(self):
    #     self.pressed_down_size()
    #
    # def pressed_down_size(self):
    #     if self.active_size == 7:
    #         return
    #     self.size_button_press(self.active_size + 1)

    def press_enter(self):
        self.pressed_enter()

    def pressed_enter(self):
        self.composite_button_press()

    def set_layout(self, initial_fix=False):
        sm.get_screen('game').set_layout(self.active_set, initial_fix)

    # def fix_color_layout(self, *args):
    #     passs
    #     # fixes to color layout
    #     self.color_button_hover(self.active_color, forced=True)
    #     # sm.get_screen('game').ids.comp_image.color = cfg.exp['colors'][str(self.active_color)]

    # def fix_size_layout(self, *args):
    #     # fixes to color layout
    #     self.size_button_hover(self.active_size, forced=True)
    #
    # def fix_shape_layout(self, *args):
    #     self.shape_button_hover(self.active_shape, forced=True)
    #     for button in xrange(1, 8):
    #         button_widget = getattr(sm.get_screen('game').shape_parameters_layout.ids, 'shape_{}'.format(button))
    #         button_widget.set_image_source(button)




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