#!/usr/bin/env python
# -*- coding: UTF-8 -*-

'''
Lineages

Admin
'''

# Copyright (c) 2017 Thomas Anatol da Rocha Woelz
# All rights reserved.
# BSD type license: check doc folder for details

__version__ = '0.0.1'
__docformat__ = 'restructuredtext'
__author__ = 'Thomas Anatol da Rocha Woelz'

import os
import sys
import os
import codecs

# import random
# import csv
# import time
import copy
import cPickle as pickle
from time import time
from collections import OrderedDict



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


# stout = StandOut('log.txt')

# kivy won't log info about it if os.environ has this keyword
# value is irrelevant. comment out to allow it.
# kivy logs go in a file inside kivy_home
# os.environ['KIVY_NO_FILELOG'] = '1'

# kivy won't print messages to console if os.environ has this keyword
# value is irrelevant, comment out to allow it.
os.environ['KIVY_NO_CONSOLELOG'] = '1'

from kivy.config import Config

Config.set('graphics', 'fullscreen', 0)
Config.set('graphics', 'position', 'custom')
Config.set('graphics', 'top', 0)
Config.set('graphics', 'left', 0)
Config.set('graphics', 'height', 1000)
Config.set('graphics', 'width', 300)
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

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.switch import Switch
from kivy.uix.textinput import TextInput
from kivy.uix.accordion import Accordion
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock


# font for symbols
UNICODE_FONT = './res/fonts/arial.ttf'

# TODO: load without server
# TODO: allow "offline" editing of starting experiments (including default template)
# TODO: connect button (not allow further editing of offline starting experiments)


class Container(object):
    pass


def load_cfg():
    cfg_dir = os.path.join(DIR, 'config')
    spec_dir = os.path.join(cfg_dir, 'spec')
    lang_dir = os.path.join(cfg_dir, 'lang', LANG)

    # cfg.widgets_text = ConfigObj(infile=os.path.join(lang_dir, 'widgets_text.ini'),
    #                              configspec=os.path.join(spec_dir, 'spec_widgets_text.ini'),
    #                              encoding='UTF8')
    # validate_config(cfg.widgets_text)

    # TODO: check if needed
    cfg.adm = ConfigObj(infile=os.path.join(cfg_dir, 'admin.ini'),
                        configspec=os.path.join(spec_dir, 'spec_admin.ini'))
    validate_config(cfg.adm)

    print 'adm test variable:', cfg.adm['options']['test variable']

class BareButton(ButtonBehavior, Label):
    '''
    "Bare" Button should look like a regular Label, but behave like a button.
    '''

class BoxLayoutItem(BoxLayout):
    def __init__(self, section, item_name, item_value):
        super(BoxLayoutItem, self).__init__()
        self.section = section
        self.item_name = item_name
        self.server_value = item_value
        self.different = False
        self.item_label = BareButton(text=item_name)
        self.item_label_pressed = None
        self.add_widget(self.item_label)
        self.item_label.bind(on_press=self.on_item_label_press)

    def changed_value(self, value):
        if not value == self.server_value:
            self.set_mod(value)
            self.item_label.color = [1, 0, 0, 1]
            if not self.different:
                self.different = True
                self.section_changes(+1)
        else:
            self.clear_mod()
            if self.different:
                self.restore_section_and_item_color()
        App.get_running_app().check_send_button()

    def set_mod(self, value):
        if self.section not in cfg.mod.keys():
            cfg.mod[self.section] = {}
        cfg.mod[self.section][self.item_name] = value
        print "cfg.mod", cfg.mod

    def clear_mod(self):
        if self.section not in cfg.mod.keys():
            return
        if self.item_name in cfg.mod[self.section].keys():
            cfg.mod[self.section].pop(self.item_name)
        if cfg.mod[self.section] == {}:
            cfg.mod.pop(self.section)
        print "cfg.mod", cfg.mod

    def restore_section_and_item_color(self):
        self.item_label.color = [1, 1, 1, 1]
        if self.different:
            self.section_changes(-1)
            self.different = False

    def restore_item_value(self):
        # must be overwritten by subclasses
        pass

    def section_changes(self, value):
        run_app = App.get_running_app()
        accordion_section = run_app.accordion_sections[self.section]
        changed_before = accordion_section.changed
        changed_after = changed_before + value
        accordion_section.changed = changed_after
        current_title = accordion_section.title
        if ' [' in current_title:
            base_title = current_title.partition(' [')[0]
        else:
            base_title = current_title
        if changed_after > 0:
            current_title = "{} [{}]".format(base_title, changed_after)
        else:
            current_title = base_title
        accordion_section.title = current_title

    def on_item_label_press(self, value):
        if not self.item_label_pressed:
            self.item_label_pressed = time()
            return
        now = time()
        delay = now - self.item_label_pressed
        self.item_label_pressed = now
        if delay > 0.4:
            return
        self.undo_item_change()

    def restore_all(self):
        self.restore_section_and_item_color()
        self.restore_item_value()

    def undo_item_change(self):
        self.restore_all()
        self.clear_mod()
        App.get_running_app().check_send_button()

class BoxLayoutItemBoolean(BoxLayoutItem):
    def __init__(self, section, item_name, item_value):
        super(BoxLayoutItemBoolean, self).__init__(section, item_name, item_value)

        self.item_value = Switch(active=item_value)
        self.add_widget(self.item_value)
        self.item_value.bind(active=self.item_activated)

    def item_activated(self, *args):
        self.changed_value(args[1])

    def restore_item_value(self):
        self.item_value.active = self.server_value

class BoxLayoutItemString(BoxLayoutItem):
    def __init__(self, section, item_name, item_value, min_value, max_value):
        super(BoxLayoutItemString, self).__init__(section, item_name, item_value)
        self.item_value = TextInput(text=item_value, multiline=False)
        self.add_widget(self.item_value)
        self.item_value.bind(on_text_validate=self.validated_text)

        self.min_value = min_value
        self.max_value = max_value
        self.last_valid_item_value = self.item_value.text

    def validated_text(self, value):
        value = value.text
        len_value = len(value)
        accept_value = True
        if self.min_value is not None and self.min_value > len_value:
            accept_value = False
        if self.max_value is not None and self.max_value < len_value:
            accept_value = False
        if accept_value:
            self.changed_value(value)
            self.last_valid_item_value = value
        else:
            self.item_value.text = self.last_valid_item_value

    def restore_item_value(self):
        self.item_value.text = self.server_value

# class BoxLayoutIntegerChooser(BoxLayout):
#     def __init__(self, value, min, max):
#         super(BoxLayoutIntegerChooser, self).__init__()
#         if min:
#             print 'min =', min()
#         if max:
#             print 'max =', max()

class BoxLayoutItemOption(BoxLayoutItem):
    def __init__(self, section, item_name, item_value, options):
        super(BoxLayoutItemOption, self).__init__(section, item_name, item_value)

        self.item_value = Spinner(text=item_value, values=options)
        self.add_widget(self.item_value)
        self.item_value.bind(text=self.choice_made)

    def choice_made(self, *args):
        self.changed_value(self.item_value.text)

    # def validated_text(self, value):
    #     value = value.text
    #     print 'value: {}'.format(value)
    #     self.changed_value(value)

    def restore_item_value(self):
        self.item_value.text = self.server_value

class BoxLayoutItemInteger(BoxLayoutItem):
    def __init__(self, section, item_name, item_value, min_value, max_value):
        super(BoxLayoutItemInteger, self).__init__(section, item_name, item_value)

        self.item_value = TextInput(text=str(item_value), multiline=False)

        # TODO: this input_filter won't allow typing negative numbers
        # the input filter can be a callable, that way we could allow negatives
        self.item_value.input_filter = 'int'

        self.min_value = min_value
        self.max_value = max_value
        self.last_valid_item_value = self.item_value.text

        value_changer = BoxLayout(orientation='vertical',
                                  size_hint_x=None,
                                  width='15dp')
        button_plus = Button(text=u'\u25b2', font_name=UNICODE_FONT)
        button_plus.bind(on_press=self.on_plus_press)
        # button_plus.font_size = '5sp'
        spacer = Widget(size_hint_y=None,
                        height=1)
        button_minus = Button(text=u'\u25BC', font_name=UNICODE_FONT)
        button_minus.bind(on_press=self.on_minus_press)
        value_changer.add_widget(button_plus)
        value_changer.add_widget(spacer)
        value_changer.add_widget(button_minus)
        self.number_chooser = BoxLayout()

        for item in [self.item_value, value_changer]:
            self.number_chooser.add_widget(item)
        self.add_widget(self.number_chooser)

        self.item_value.bind(on_text_validate=self.validated_text)


    def on_plus_press(self, *args, **kwargs):
        new_value = int(self.item_value.text) + 1
        self.process_new_value_button_press(new_value, "plus")

    def on_minus_press(self, *args, **kwargs):
        new_value = int(self.item_value.text) - 1
        self.process_new_value_button_press(new_value, "minus")

    def check_new_value(self, new_value):
        if self.min_value is not None and (new_value < self.min_value) or \
           self.max_value is not None and (new_value > self.max_value):
            return False
        return True

    def process_new_value_button_press(self, new_value, button_type):
        if not self.check_new_value(new_value):
            if button_type == "plus":
                new_value = self.max_value
            else:
                new_value = self.min_value
            if self.last_valid_item_value == str(new_value):
                return
        self.item_value.text = str(new_value)
        self.last_valid_item_value = self.item_value.text
        self.changed_value(new_value)

    def validated_text(self, value):
        new_value = int(value.text)
        if not self.check_new_value(new_value):
            if new_value > self.max_value:
                new_value = self.max_value
            else:
                new_value = self.min_value
            self.item_value.text = str(new_value)
            if self.last_valid_item_value == self.item_value.text:
                return
        self.last_valid_item_value = self.item_value.text
        self.changed_value(new_value)

    def restore_item_value(self):
        self.item_value.text = str(self.server_value)
        self.last_valid_item_value = self.item_value.text

class BoxLayoutItemFloat(BoxLayoutItem):
    def __init__(self, section, item_name, item_value, min_value, max_value):
        super(BoxLayoutItemFloat, self).__init__(section, item_name, item_value)

        self.item_value = TextInput(text=str(item_value), multiline=False)

        # TODO: this input_filter won't allow typing negative numbers
        # the input filter can be a callable, that way we could allow negatives
        self.item_value.input_filter = 'float'

        self.min_value = min_value
        self.max_value = max_value
        self.last_valid_item_value = self.item_value.text

        value_changer = BoxLayout(orientation='vertical',
                                  size_hint_x=None,
                                  width='15dp')
        button_plus = Button(text=u'\u25b2', font_name=UNICODE_FONT)
        button_plus.bind(on_press=self.on_plus_press)
        # button_plus.font_size = '5sp'
        spacer = Widget(size_hint_y=None,
                        height=1)
        button_minus = Button(text=u'\u25BC', font_name=UNICODE_FONT)
        button_minus.bind(on_press=self.on_minus_press)
        value_changer.add_widget(button_plus)
        value_changer.add_widget(spacer)
        value_changer.add_widget(button_minus)
        self.number_chooser = BoxLayout()

        for item in [self.item_value, value_changer]:
            self.number_chooser.add_widget(item)
        self.add_widget(self.number_chooser)

        self.item_value.bind(on_text_validate=self.validated_text)


    def on_plus_press(self, *args, **kwargs):
        new_value = float(self.item_value.text) + 1.0
        self.process_new_value_button_press(new_value, "plus")

    def on_minus_press(self, *args, **kwargs):
        new_value = float(self.item_value.text) - 1.0
        self.process_new_value_button_press(new_value, "minus")

    def check_new_value(self, new_value):
        if self.min_value is not None and (new_value < self.min_value) or \
           self.max_value is not None and (new_value > self.max_value):
            return False
        return True

    def process_new_value_button_press(self, new_value, button_type):
        if not self.check_new_value(new_value):
            if button_type == "plus":
                new_value = self.max_value
            else:
                new_value = self.min_value
            if self.last_valid_item_value == str(new_value):
                return
        self.item_value.text = str(new_value)
        self.last_valid_item_value = self.item_value.text
        self.changed_value(new_value)

    def validated_text(self, value):
        new_value = float(value.text)
        if not self.check_new_value(new_value):
            if new_value > self.max_value:
                new_value = self.max_value
            else:
                new_value = self.min_value
            self.item_value.text = str(new_value)
            if self.last_valid_item_value == self.item_value.text:
                return
        self.last_valid_item_value = self.item_value.text
        self.changed_value(new_value)

    def restore_item_value(self):
        self.item_value.text = str(self.server_value)
        self.last_valid_item_value = self.item_value.text

class AccordionAdmin(Accordion):
    pass

class AdminApp(App):
    # sections = {}
    # accordion_sections = {}
    sections = OrderedDict()
    accordion_sections = OrderedDict()

    item_tree = {}
    kv_directory = 'res/scripts/kv'

    def on_start(self):
        super(AdminApp, self).on_start()

        # self.sections = {'main': self.root.ids.main,
        #                  'testing': self.root.ids.testing,
        #                  'game_points': self.root.ids.game_points,
        #                  'valid_colors': self.root.ids.valid_colors,
        #                  'valid_shapes': self.root.ids.valid_shapes,
        #                  'valid_sizes': self.root.ids.valid_sizes}

        self.sections = OrderedDict()
        self.sections['main'] = self.root.ids.main
        self.sections['save'] = self.root.ids.save
        self.sections['save'] = self.root.ids.save
        self.sections['end_criteria'] = self.root.ids.end_criteria
        self.sections['performance_criteria'] = self.root.ids.performance_criteria
        self.sections['game_points'] = self.root.ids.game_points
        self.sections['valid_colors'] = self.root.ids.valid_colors
        self.sections['valid_shapes'] = self.root.ids.valid_shapes
        self.sections['valid_sizes'] = self.root.ids.valid_sizes

        self.accordion_sections = OrderedDict()
        self.accordion_sections['main'] = self.root.ids.main_accordion
        self.accordion_sections['save'] = self.root.ids.save_accordion
        self.accordion_sections['end_criteria'] = self.root.ids.end_criteria_accordion
        self.accordion_sections['performance_criteria'] = self.root.ids.performance_criteria_accordion
        self.accordion_sections['game_points'] = self.root.ids.game_points_accordion
        self.accordion_sections['valid_colors'] = self.root.ids.valid_colors_accordion
        self.accordion_sections['valid_shapes'] = self.root.ids.valid_colors_accordion
        self.accordion_sections['valid_sizes'] = self.root.ids.valid_colors_accordion

        cfg.mod = {}

        self.try_to_connect()

    # CONNECT SCREEN METHODS

    def try_to_connect(self, reason=False, force_localhost=False, *args, **kwargs):
        current_host = HOST
        print 'force_localhost', force_localhost
        if force_localhost:
            current_host = '127.0.0.1'
        print 'current host =', current_host
        global fac
        valid_ip = is_valid_ip(current_host)
        valid_port = bool(0 <= PORT <= MAX_PORT)
        if not valid_ip or not valid_port:
            if not valid_ip and not valid_port:
                print 'PORT {} and IP {} not valid'.format(PORT, current_host)
            elif not valid_ip:
                print 'IP {} not valid'.format(current_host)
            else:
                print 'PORT {} not valid'.format(PORT)
            return

        deferred = defer.Deferred()
        fac = AdminFactory(reactor, AdminAMP(), deferred)

        def got_protocol(p):
            print 'GOT PROTOCOL!'
            # global fac
            p.callRemote(cmd.AddAdmin).addCallback(self.get_experiment_pickle)
            fac.add_admin_protocol(p)

        reactor.connectTCP(current_host, PORT, fac, timeout=3)

        deferred.addCallback(got_protocol)
        # deferred.addErrback(self.cant_connect_error)
        if not str(current_host) == '172.0.0.1':
            deferred.addErrback(self.try_to_connect, force_localhost=True)
        else:
            deferred.addErrback(self.cant_connect_error)

    def cant_connect_error(self, reason):
        print 'cannot connect: ' + repr(reason)

    def bailout(self, reason):
        print 'bailout reason:', reason
        reason.printTraceback()
        if stout:
            stout.close()
        self.stop()

    def get_experiment_pickle(self, result):
        cfg.exp = pickle.loads(result['experiment_pickle'])
        experiment_name = ""
        initial_comment = cfg.exp.initial_comment[0]
        if initial_comment.startswith('# experiment:'):
            experiment_name = initial_comment[13:].strip()
        self.root.ids.admin_info.text = u"G: {}  E: {}".format(result['group'], experiment_name)

        # self.root.ids.send_mod_config.bind(on_press=self.send_mod_config)

        print 'about to load experiment to gui'
        self.load_experiment_to_gui()

    def check_send_button(self):
        empty_mod = (cfg.mod == {})
        if empty_mod and not self.root.ids.send_mod_config.disabled:
            self.root.ids.send_mod_config.disabled = True
        elif not empty_mod and self.root.ids.send_mod_config.disabled:
            self.root.ids.send_mod_config.disabled = False

    def send_mod_config(self, *args):
        fac.p.send_mod_config()

    def force_update_config(self, *args):
        empty_mod = (cfg.mod == {})
        if empty_mod:
            pass
        else:
            self.send_mod_config()
        fac.p.force_update_config()
        self.check_send_button()
        print 'force update'

    def mod_config_received(self):
        for k in cfg.mod.iterkeys():
            if type(cfg.mod[k]) == dict:
                cfg.exp[k].update(copy.deepcopy(cfg.mod[k]))
                for subk in cfg.mod[k].iterkeys():
                    self.item_tree[k][subk].server_value = copy.deepcopy(
                        cfg.exp[k][subk])
                    self.item_tree[k][subk].restore_all()
            else:
                cfg.exp[k] = copy.deepcopy(cfg.mod[k])
        cfg.mod = {}
        self.root.ids.send_mod_config.disabled = True

    def load_experiment_to_gui(self):
        self.item_tree = {}
        for section in self.sections.iterkeys():
            self.item_tree[section] = {}
            for section_item in cfg.exp[section].iterkeys():
                spec_item = cfg.exp.configspec[section][section_item]
                item_value = cfg.exp[section][section_item]
                item = None
                item_args = (section, section_item, item_value, spec_item)
                if spec_item.startswith('integer'):
                    item = self.get_item_integer(*item_args)
                elif spec_item.startswith('string'):
                    item = self.get_item_string(*item_args)
                elif spec_item.startswith('boolean'):
                    item = self.get_item_boolean(*item_args)
                elif spec_item.startswith('option'):
                    item = self.get_item_option(*item_args)
                elif spec_item.startswith('float'):
                    item = self.get_item_float(*item_args)
                if item is not None:
                    self.sections[section].add_widget(item)
                    self.item_tree[section][section_item] = item

    def get_int_from_spec(self, value, spec_item):
        if value not in spec_item:
            return None
        sep = '{}='.format(value)
        if sep not in spec_item:
            sep = '{} ='.format(value)
            if sep not in spec_item:
                return None
        text = spec_item.partition(sep)[2]
        seps = [' ', ',', ')']
        for sep in seps:
            if sep in text:
                text = text.partition(sep)[0]
        if text.count('-') > 1:
            return None
        if text.isdigit() or (text.startswith('-') and text[1:].isdigit()):
            return int(text)
        return None

    def get_float_from_spec(self, value, spec_item):
        if value not in spec_item:
            return None
        sep = '{}='.format(value)
        if sep not in spec_item:
            sep = '{} ='.format(value)
            if sep not in spec_item:
                return None
        text = spec_item.partition(sep)[2]
        seps = [' ', ',', ')']
        for sep in seps:
            if sep in text:
                text = text.partition(sep)[0]
        if text.count('.') > 1:
            return None

        if text.replace('.', '').isdigit() or \
                (text.startswith('-') and text[1:].replace('.', '').isdigit()):
            return float(text)
        return None

    def get_item_integer(self, section, section_item, item_value, spec_item):
        min_value = self.get_int_from_spec('min', spec_item)
        max_value = self.get_int_from_spec('max', spec_item)

        return BoxLayoutItemInteger(section, section_item, item_value, min_value, max_value)

    def get_item_string(self, section, section_item, item_value, spec_item):
        min_value = self.get_int_from_spec('min', spec_item)
        max_value = self.get_int_from_spec('max', spec_item)
        return BoxLayoutItemString(section, section_item, item_value, min_value, max_value)

    def get_item_boolean(self, section, section_item, item_value, spec_item):
        return BoxLayoutItemBoolean(section, section_item, item_value)

    def get_item_option(self, section, section_item, item_value, spec_item):
        spec_item = spec_item.partition('option')[2]
        spec_item = spec_item.replace('=', '')
        spec_item = spec_item.replace('default', '')
        options = list(eval(spec_item))
        if options.count(options[-1]) > 1:
            options = options[:-1]
        return BoxLayoutItemOption(section, section_item, item_value, options)

    def get_item_float(self, section, section_item, item_value, spec_item):
        min_value = self.get_float_from_spec('min', spec_item)
        max_value = self.get_float_from_spec('max', spec_item)
        return BoxLayoutItemFloat(section, section_item, item_value, min_value, max_value)

class AdminAMP(amp.AMP):
    """
    Admin with a customized Assynchronous Messaging Protocol.
    Enables client-server communication.
    """

    def __init__(self):
        super(AdminAMP, self).__init__()

    # AMP methods
    def makeConnection(self, transport):
        """overrides default TCP delay with no delay"""
        if not transport.getTcpNoDelay():
            transport.setTcpNoDelay(True)
        super(AdminAMP, self).makeConnection(transport)

    def connectionLost(self, reason):
        super(AdminAMP, self).connectionLost(reason)
        App.get_running_app().bailout(reason)

    def send_mod_config(self):
        self.callRemote(cmd.GetModConfig,
                        mod_config=pickle.dumps(cfg.mod),
                        ).addCallback(self.mod_config_received)

    def force_update_config(self):
        self.callRemote(cmd.ForceUpdateConfig)

    # callback for send_mod_config
    def mod_config_received(self, *args):
        App.get_running_app().mod_config_received()
        # return {}

        # TODO: maybe explore using AMP.connectionLost to display a message!

        # @cmd.PlayerLeft.responder
        # def player_left(self):
        #     # UNSCHEDULE ALL FUNCS
        #     # DO STUFF HERE (PAUSE GAME?)
        #     return {}
        #
        # @cmd.StartSession.responder
        # def start(self, source):
        #     # DO STUFF TO START HERE
        #     return {}

class AdminFactory(_InstanceFactory):
    """Factory used by ClientCreator, using ClientAMP protocol."""

    protocol = AdminAMP

    def __init__(self, some_reactor, instance, deferred):
        _InstanceFactory.__init__(self, some_reactor, instance, deferred)
        self.p = None

    def __repr__(self):
        return "<AdminAMP factory: %r>" % (self.instance,)

    def add_admin_protocol(self, p):
        self.p = p

    # def disconnect_admin(self):
    #     if self.client.transport:
    #         self.client.transport.loseConnection()
    #     Clock.schedule_once(self.cleanup_admin, 0.00001)
    #     # self.cleanup_client()
    #
    # def cleanup_admin(self, *args):
    #     del self.client
    #     self.admin = None

def main():
    # global sm
    global stout

    # CREATE DIRS AND STOUT

    # redirect sdtout and stderr to log file
    if not os.path.exists(os.path.join(DIR, 'output', 'log', 'admin')):
        os.mkdir(os.path.join(DIR, 'output', 'log', 'admin'))
    stout = StandOut(logfile=os.path.join(DIR, 'output', 'log', 'admin',
                                          'log%s.txt' % LOCALTIME))

    load_cfg()



    # KV BUILDERS
    # with codecs.open(os.path.join(RESDIR,
    #                        'scripts',
    #                        'kv',
    #                        'client.kv'), 'r', 'utf-8') as f:
    #     Builder.load_string(f.read().format(**dict(cfg.widgets_text.dict(),
    #                                                input_conn_ip=HOST,
    #                                                input_conn_port=PORT)))
    AdminApp().run()

cfg = Container()
fac = None
stout = False

if __name__ == '__main__':
    import traceback
    # noinspection PyBroadException
    try:
        main()
    except:
        traceback.print_exc()
        if stout:
            stout.close()