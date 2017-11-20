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

Library designed to create behavior analytic experiments
'''

__version__ = '1.0.0'
__docformat__ = 'restructuredtext'

import os
import sys
import time
import codecs
import shutil

class Container(object):
    pass

# overloadable paths to folders
#folder = type('folder', (object, ), {})()
folder = Container()
folder.ba = os.path.abspath(os.path.dirname(__file__))
folder.bacfg = os.path.join(folder.ba, 'config')
folder.baspec = os.path.join(folder.bacfg, 'spec')
folder.dep = os.path.join(folder.ba, 'dependencies')
# these paths below should probably be overloaded in the experiment module!
folder.extra = folder.bacfg
folder.cfg = folder.bacfg
folder.spec = folder.baspec
# main, output, log and resources paths have to be set in the experiment module!
folder.main = None
folder.out = None
folder.log = None
folder.res = None
# these paths will be automatically updated
folder.save = None
folder.cfglang = None
folder.temp = None


options = type('options', (object, ),
               dict(
                    main_lang = 'eng', # must match lang folder name
                    subj_type = 'subj', # options: 'subj' or 'group'
                    check_run_ini = False, # optional run.ini sets subject/group and experiment to run
                    check_lang = False,
                    translate = False,
                    translate_filenames = False,
                    use_save = False,
                    write_save = False,
                    use_output = False,
                    use_log = False,
                    experiment_backup_use = False, # use backup experiment.ini in spec folder
                    experiment_restore_warn = False, # warns user that it was restored
                    use_experiment_folder = False,
                    choose_subject = False,
                    choose_experiment = False,
                    use_subject_folder = False,
                    # TODO: fix subject folder option. 
                    # if using custom subjects (choice or whatever, this HAS to be set True)
                    # would be nice to fix this later to accept subject files in the experiment folder root.
                    
                    use_mod = False,
                    create_mod = False,
                    gui = False,
                    custom_system_messages = False,
                    custom_layout = False,
                    custom_output = False,
                    custom_labels = False,
                    custom_gui = False,
                    use_sounds = False))()

net_options = type('net_options', (object, ),
               dict(
                    use_net = False,
                    server = False,
                    client = False,
                    observer = False,
                    observer_id = 0,
                    admin = False,
                    pyglet_reactor=True,
                    min_clients = 1,
                    max_clients = 4,
                    send_configs = ['regioncfg',
                                    'expcfg',
                                    's_msg',
                                    'net_msg',
                                    'message',
                                    'layout',
                                    'guicfg',
                                    'save']))()

# add them to path
sys.path.insert(0, folder.dep)


from configobj.configobj import ConfigObj
from configobj.configobj import flatten_errors
from configobj.validate import Validator
from configobj.validate import ValidateError #@UnusedImport
from standout.standout import StandOut
#to avoid twisted try to re-import
from configobj import configobj #@UnusedImport 

from convert import utostr
from convert import print_u
from convert import n_uni

# TODO: other modules should import these above directly from convert, no from app

# global constants
LOCALTIME = '%04d-%02d-%02d-%02d-%02d-%02d' %time.localtime()[0:6]
#DPI = 96

def set_line():
    my.line = {}
    for label in my.labels:
        my.line[label] = ''

def set_multiple_labels_per_subject():
    multiple_labels = my.output_cfg['multiple per subject']
    my.labels = []
    my.label_translations = []
    for label in my.basic_labels:
        if label in multiple_labels:
            for i in xrange(1, net_options.max_clients + 1):
                my.labels.append(label + str(i))
                my.label_translations.append(my.output_labels[label] + str(i))
        else:
            my.labels.append(label)
            my.label_translations.append(my.output_labels[label])
    set_line()


def set_simple_labels():
    my.labels = my.basic_labels[:]
    my.label_translations = [my.output_labels[x] for x in my.labels]
    set_line()

class ExperimentBase(object):
    '''Base class for creating experiments'''

    def __init__(self):
        
        if options.gui:                
            self.set_resources()
            self.set_window()
            self.set_handlers()
        self.set_exp_vars()
        if options.use_output:
            self.create_output()
        else:
            self.create_output_mock()
        
    def set_window(self):
        # placeholder for GUI-specific window settings
        pass

    def set_resources(self):
        # placeholder for setting resources and sounds
        pass
        
    def set_handlers(self):
        # placeholder for setting event handlers specific to GUI toolkit
        pass

    def set_exp_vars(self):
        '''Sets experimental variables.'''
        # exp status
        self.session_started = False
        self.session_ended = False

    def start_session(self):
        # time vars
        self.now = 0
        self.time_trial = self.now
        self.hour = '-'.join([str(x) for x in time.localtime()[:4]])
        self.time_started = time.time()
        self.session_started = True
        self.record_event(my.output_labels['session start'])

    def set_time(self):
        self.now = time.time() - self.time_started
        self.hour = '-'.join([str(x) for x in time.localtime()[:4]])

    def create_output(self):

        '''Creates the output file.'''

        if not os.path.exists(folder.out):
            os.mkdir(folder.out)
        csv_string = '{0}_{1}.csv'.format(my.experiment, my.subject)
        my.output_path = os.path.join(folder.out, csv_string)

        if 'multiple per subject' in my.output_cfg.keys():
            set_multiple_labels_per_subject()
        else:
            set_simple_labels()

        self.record_labels()

        hour = '-'.join([str(x) for x in time.localtime()[:5]])
        data = dict(my.line,
                    event = my.output_labels['program start'],
                    hour = hour)
        self.record_line(**data)
        
    def record_labels(self):
        if os.path.exists(my.output_path):
            mode = 'a'
        else:
            mode = 'w'
        output_file = codecs.open(my.output_path, mode, my.encoding)
        data_string = my.CSV_DELIMIT.join(my.label_translations) + u'\n'
        output_file.write(data_string)
        output_file.close()
    
    def create_output_mock(self):
        '''Substitutes output properties and methods to skip recording'''
        class DictMock(dict):
            def __missing__(self, key):
                return None
        my.output_labels = DictMock()
        my.line = DictMock()
        self.record_line = lambda *args, **kwargs:None
        
    def record_line(self, **data):
        '''Records a line of data in the output file.

        It is called by all recording functions.
        '''
        d_list = [data[x] for x in my.labels]
        data_string = my.CSV_DELIMIT.join(
            [unicode(x) for x in d_list]) + u'\n'
        output_file = codecs.open(my.output_path, 'a', my.encoding)
        output_file.write(data_string)
        output_file.close()

    def record_event(self, event='', description=''):
        '''Records some event.'''
        data = dict(
            my.line,
            hour=self.hour,
            event=event,
            description=description,
            t_response=n_uni(self.now))
        self.record_line(**data)
        
    def record_end(self, description=''):
        data = dict(
            my.line,
            hour=self.hour,
            event=my.output_labels['session end'],
            description=description,
            t_response=n_uni(self.now))
        self.record_line(**data)

class PrepareBase(object):
    
#    controller = ControllerBase
    
    def __init__(self):
        # these 2 status properties useful for later creating save file
        self.custom_subject_name = False
        self.custom_experiment_name = False
        my.schedule_funcs = set() # scheduled functions: timers, etc
        self.configure_debug()
        self.create_folders()
        if options.use_log:
            self.start_log()
        self.imports()
        self.configure_lang()
        if options.translate:
            self.configure_translate()
            if options.translate_filenames:
                self.configure_filename_translate()
        self.configure_system_messages()
        self.configure_subject_type()
        self.configure_region()
        self.configure_messages()
        self.configure_gui() # server may load this, to distribute to clients
        self.configure_layout() # same here
        if options.gui:
            self.configure_gui_specific()
        self.configure_defaults()
        self.set_experiment_folder()
        if options.check_run_ini:
            self.check_run_ini()
        if options.choose_experiment:
            self.choose_experiment()
        else:
            self.check_experiment_exists()
        if options.use_save:
            self.create_save_folders()
        if options.choose_subject:
            self.choose_subject()
        if options.use_save:
            self.create_save_file()
        self.load_exp_cfg()
        if net_options.use_net:
            self.configure_network()
        if options.use_output:
            self.configure_output()
        self.cleanup()

    def configure_debug(self):
        my.debug = False
        debug_path = os.path.join(folder.main, 'debug.ini')
        if os.path.exists(debug_path):
            my.debug = ConfigObj(infile=debug_path,
                                 configspec=os.path.join(folder.baspec, 'ba_debug_spec.ini'))
            validate(my.debug)
            
            if my.debug['turn off sound']:
                options.use_sounds = False
            if my.debug['turn off output']:
                options.use_output = False
            if my.debug['turn off save write']:
                options.write_save = False
            if my.debug['turn off log']:
                options.use_log = False
            if my.debug['turn off use mod']:
                options.use_mod = False
            if my.debug['turn off create mod']:
                options.create_mod = False

    def imports(self):
        if options.choose_experiment or options.choose_subject:
            options.use_eg = True
            # easygui used to create tkinter dialogs
            import easygui.easygui as eg
            globals()['eg'] = eg # add to global namespace

        
    def create_folders(self):
        # check if needed paths were set
        if folder.out == None or folder.log == None:
            error = ''
            if folder.out == None:
                error = "output folder wasn't set. "
            if folder.log == None:
                error += "log folder wasn't set."
            raise Exception(error)
        if options.translate:
            import tempfile
            folder.temp = os.path.abspath(os.path.join(tempfile.gettempdir(), 'cocos2dtemp'))
        # create folders if missing
        if options.translate and not os.path.exists(folder.temp):
            os.mkdir(folder.temp)
        if options.use_output and not os.path.exists(folder.out):
            os.mkdir(folder.out)
        if options.use_log and not os.path.exists(folder.log):
            os.mkdir(folder.log)
    
    def start_log(self):
        #redirect sdtout and stderr to log file
        log_string = 'log{0}{{0}}.txt'
        log_source = ''
        if net_options.use_net:
            if net_options.server:
                log_source = 'server'
            elif net_options.client:
                log_source = 'client'
            elif net_options.admin:
                log_source = 'admin'
            elif net_options.observer:
                log_source = 'observer'
        log_string = log_string.format(log_source)
        log_string = log_string.format(LOCALTIME)
        unbuffered=False
        if my.debug:
            if my.debug['force unbuffered log']:
                unbuffered = True
        my.stout = StandOut(logfile=os.path.join(folder.log, log_string),
                            unbuffered=unbuffered)
        
    def configure_output(self):
        output_path = os.path.join(folder.bacfg, 'ba_output.ini')
        output_spec_path = os.path.join(folder.baspec, 'ba_output_spec.ini')
        output_labels_path = os.path.join(folder.balang,'ba_output_labels.ini')
        output_labels_spec_path = os.path.join(folder.baspec, 'ba_output_labels_spec.ini')
        custom_output_labels_path = os.path.join(folder.extralang, 'output_labels.ini')
        ba_output_labels = ConfigObj(infile=output_labels_path,\
                                     configspec=output_labels_spec_path,
                                     encoding = 'UTF8')
        validate(ba_output_labels)
        if options.custom_output:
            output_path = os.path.join(folder.extra, 'output.ini')
            output_spec_path = os.path.join(folder.spec, 'output_spec.ini')
            if os.path.exists(custom_output_labels_path):
                output_labels = ConfigObj(\
                    infile=os.path.join(folder.extralang, 'output_labels.ini'),\
                    configspec=os.path.join(folder.spec, 'output_labels_spec.ini'),
                    encoding = 'UTF8')
                validate(output_labels)
                ba_output_labels.merge(output_labels)
        my.output_labels = ba_output_labels.dict()
        output_cfg = ConfigObj(
            infile=output_path,
            configspec=output_spec_path)
        validate(output_cfg)
        my.output_cfg = output_cfg
        my.encoding = output_cfg['output_encoding']
        my.basic_labels = output_cfg['labels']


    def configure_lang(self):
        lang = options.main_lang
        
        # if no language folder or extra (hidden) folder, use default folders:
        folder.cfglang = folder.cfg
        folder.extralang = folder.extra

        if options.check_lang:
            custom_lang_path = os.path.join(folder.extra, 'lang.ini')
            if os.path.exists(custom_lang_path):
                infile_path = custom_lang_path
            else:
                infile_path = os.path.join(folder.bacfg, 'ba_lang.ini')
            lang = ConfigObj(infile=infile_path)
            lang = lang['lang']
            # set lang folder paths
            folder.cfglang = os.path.join(folder.cfg, lang)
            folder.extralang = os.path.join(folder.extra, lang)
        folder.balang = os.path.join(folder.bacfg, lang)
        my.lang = lang
        # check if lang folder exists            
        error = ''
        if not os.path.exists(folder.balang):
            error += "language not supported by behavan\n"
        elif not os.path.exists(folder.cfglang):
            error += "language config folder doesn't exist"
        elif not os.path.exists(folder.extralang):
            error += "language config for extra (hidden) folder doesn't exist"
        if error:
            print error
            if options.use_eg:
                eg.msgbox(error)
            exit_app()
        
    def configure_translate(self):
        #load and validate section/items translation config
        my.translate = ConfigObj(
            infile=os.path.join(folder.extralang, 'translate.ini'),
            configspec=os.path.join(folder.spec, 'translate_spec.ini'))
        validate(my.translate)
        
    def configure_filename_translate(self):
        # load and validate file translation config
            my.files = ConfigObj(
                infile=os.path.join(folder.extralang, 'files_cfg.ini'),
                configspec=os.path.join(folder.spec, 'files_cfg_spec.ini'))
            validate(my.files)
            
    def configure_system_messages(self):
        #load and validate basic system messages config
        my.s_msg = ConfigObj(infile=os.path.join(folder.balang, 'ba_s_msg.ini'),
            configspec=os.path.join(folder.baspec, 'ba_s_msg_spec.ini'),
            encoding = 'UTF8')
        validate(my.s_msg)
        if options.custom_system_messages:
            self.configure_custom_system_messages()
        my.s_msg = my.s_msg.dict()
    
    def configure_custom_system_messages(self):
        #load and validate custom system messages config
        cs_msg = ConfigObj(infile=os.path.join(folder.extralang, 's_msg.ini'),
            configspec=os.path.join(folder.spec, 's_msg_spec.ini'),
            encoding = 'UTF8')
        validate(cs_msg)
        my.s_msg.merge(cs_msg)
        del cs_msg
          
    def configure_subject_type(self):
        my.subj_type = my.s_msg[options.subj_type]
        
    def configure_defaults(self):
        # set default subject and experiment in case it doesn't get set later
        my.subject = my.subj_type
        my.experiment = 'experiment'
        if options.translate_filenames:
            my.experiment = my.files['experiment']
        
    def configure_region(self):
        # load and validate regional settings
        infile_path = os.path.join(folder.extralang, 'regional.ini')
        if not os.path.exists(infile_path):
            infile_path = os.path.join(folder.balang, 'ba_regional.ini')
        configspec_path = os.path.join(folder.spec, 'regional_spec.ini')
        if not os.path.exists(configspec_path):
            configspec_path = os.path.join(folder.baspec, 'ba_regional_spec.ini')
        regioncfg = ConfigObj(
            infile=infile_path,
            configspec=configspec_path,
            encoding='UTF8')
        validate(regioncfg)
        my.CSV_DELIMIT = regioncfg['csv delimiter']
        my.DECIMAL_SEPARATOR = regioncfg['decimal separator']
        my.regioncfg = regioncfg.dict()
        
    def configure_messages(self):
        message_ini = "message.ini"
        if options.translate_filenames:
            message_ini = my.files['message'] + '.ini'
        message_path = os.path.join(folder.cfglang, message_ini)
        if options.translate and my.lang != 'eng':
            # edit the config files and set the path to the edited versions
            message_path = translate_and_change_path(message_path)        
        # load and validate message
        my.message = ConfigObj(infile=message_path,\
                            configspec=os.path.join(folder.spec, 'message_spec.ini'),\
                            encoding='UTF8')
        validate(my.message)
        my.message = my.message['message'].dict()
#        my.message = my.message.dict()

    def configure_gui(self):
        my.guicfg = ConfigObj(infile=os.path.join(folder.bacfg, 'ba_gui.ini'),
                            configspec=os.path.join(folder.baspec, 'ba_gui_spec.ini'))
        validate(my.guicfg)
        if options.custom_gui:
            custom_guicfg = ConfigObj(infile=os.path.join(folder.extra, 'gui.ini'),
                                      configspec=os.path.join(folder.spec, 'gui_spec.ini'))
            validate(custom_guicfg)
            my.guicfg.merge(custom_guicfg)
        my.guicfg = my.guicfg['gui'].dict()
        if my.debug:
            if my.debug['force resizable']:
                my.guicfg['resizable'] = True
            if my.debug['turn off fullscreen']:
                my.guicfg['fullscreen'] = False
        

    def configure_layout(self):
        my.layout = ConfigObj(infile=os.path.join(folder.bacfg, 'ba_layout.ini'),
                            configspec=os.path.join(folder.baspec, 'ba_layout_spec.ini'))
        validate(my.layout)
        if options.custom_layout:
            layout_ini = "layout.ini"
            if options.translate_filenames:
                layout_ini = my.files['layout'] + '.ini'
            layout_path = os.path.join(folder.cfglang, layout_ini)
            if options.translate and my.lang != 'eng':
                # edit the config files and set the path to the edited versions
                layout_path = translate_and_change_path(layout_path)
            # load and validate layout
            custom_layout = ConfigObj(infile=layout_path,\
                               configspec=os.path.join(folder.spec, 'layout_spec.ini'))
            validate(custom_layout)
            my.layout.merge(custom_layout)
        my.layout = my.layout.dict()
        
    def configure_gui_specific(self):
        # these below can be used later by GUI specific needs
        my.text_style = {}
        my.window = {}
        my.sound = {}
#        my.schedule_funcs = set() # scheduled functions: timers, etc
        # TODO: z_ make these None?
        
    def get_expcfg_folder_name(self, expcfg_folder_name = 'experiments'):
        if options.translate_filenames:
            expcfg_folder_name = my.files[expcfg_folder_name]
        return expcfg_folder_name

    def set_experiment_folder(self):
        # set experiment config folder paths
        if options.use_experiment_folder:
            folder.expcfg = os.path.join(folder.cfglang, self.get_expcfg_folder_name())
        else:
            folder.expcfg = folder.cfglang
            
        # create folders if missing
        if not os.path.exists(folder.expcfg):
            os.mkdir(folder.expcfg)
            
    def check_run_ini(self):
        # checks run.ini in 3 paths: 
        # 1) main folder (where you ran the experiment)
        # 2) config folder (before the language) and
        # 3) config-language folder 
        if os.path.exists(os.path.join(folder.main, 'run.ini')):
            run_path = os.path.join(folder.main, 'run.ini')
        elif os.path.exists(os.path.join(folder.cfg, 'run.ini')):
            run_path = os.path.join(folder.cfg, 'run.ini')
        elif os.path.exists(os.path.join(folder.cfglang, 'run.ini')):
            run_path = os.path.join(folder.cfglang, 'run.ini')
        else:
            return
        # file found: load it (no config spec, its free-form, only strings)
        run = ConfigObj(infile=run_path)
        run_keys = run.keys()
        if 'experiment' in run_keys:
            options.choose_experiment = False
            self.custom_experiment_name = True
            experiment = run['experiment']
            my.experiment = utostr(experiment)       
        subject_keys = ['subject', 'participant', 'group']
        if set(run_keys).intersection(subject_keys):
#            options.choose_subject = False
            for i in run_keys:
                if i in subject_keys:
                    subject = run[i]
                    subject = utostr(subject)                    
                    subject = subject.lower()
                    if subject != 'mod':
                        my.subject = subject
                        self.custom_subject_name = True
                        options.choose_subject = False
                        return

    def get_experiment_backup_paths(self):
        experiment = 'experiment'
        if options.translate_filenames:
            experiment = my.files['experiment']
        filename = experiment + '.ini'
        source = os.path.join(folder.extralang, 'experiment_backup.ini')
        destination = os.path.join(folder.expcfg, filename)
        return (experiment, source, destination)

    def choose_experiment(self):
        ## use dialogs to choose experiment and subject
        s_msg = my.s_msg

        # create dialogs for choosing an experiment
        experiments = [x.replace('.ini', '')
                        for x in os.listdir(folder.expcfg) if '.ini' in x]
        if experiments == [] and not options.experiment_backup_use:
            # no experiments found and not looking for backup
            eg_experiment_not_found()
        elif experiments == [] and options.experiment_backup_use:
            # now no experiment found, but lets check if that backup is there
            experiment, source, destination = self.get_experiment_backup_paths()
            if not os.path.exists(source):
                # no backups found
                eg_experiment_not_found(msg=my.s_msg['no exp nor backup found'])
            # if we are here (still alive) backup was found
            if options.experiment_restore_warn:
                # here we let the user know we just created a new config from the backup
                if eg.ccbox(s_msg['no exp found lets create'], s_msg['confirm']):      
                    shutil.copy(source, destination)
                    eg.msgbox(s_msg['exp created'])
                    # and we exit here
                    exit_app()
                else:
                    # unless the user cancels it all and no file was created
                    eg_cancel_program()
            # here, we just opted to copy the backup without warning. 
            else:
                shutil.copy(source, destination)
                # so now we have the file 'experiment' where it belongs
                experiments = [experiment]
        # dialog asks for an experiment
        experiment = eg.choicebox(s_msg['run which exp'], choices=experiments)
        my.experiment = experiment
        if experiment == None:
            eg.msgbox(s_msg['cancel program'])
            exit_app()
        msg = s_msg['you chose exp'].format(exp=experiment)
        if eg.ccbox(msg, s_msg['confirm']): # show a Continue/Cancel dialog
            pass
        else:
            eg_cancel_program()
        self.custom_experiment_name = True

    def check_experiment_exists(self):
        exp_path = os.path.join(folder.expcfg, my.experiment + '.ini')
        if os.path.exists(exp_path):
            return
        if not options.experiment_backup_use:
            raise Exception(utostr(my.s_msg['no exp found']))
        experiment, source, destination = self.get_experiment_backup_paths()
        if not os.path.exists(source):
            raise Exception(utostr(my.s_msg['no exp nor backup found']))
        my.experiment = experiment
        shutil.copy(source, destination)
    
    def create_save_folders(self):
        save_path = 'saved data'
        if options.translate_filenames:
            save_path = my.files[save_path]
        folder.save = os.path.join(folder.cfglang, save_path)
        if not os.path.exists(folder.save) and options.write_save:
            os.mkdir(folder.save)
        if self.custom_experiment_name:
            folder.save = os.path.join(folder.save, my.experiment)
            if not os.path.exists(folder.save) and options.write_save:
                os.mkdir(folder.save)
    
    def choose_subject(self):        # create dialogs for choosing subject
        s_msg = my.s_msg
        subjects = []
        if options.use_save:
            if not os.path.exists(folder.save):
                subjects = []
            elif options.use_subject_folder:
                subjects = [x for x in os.listdir(folder.save) if not '.' in x]
            else:
                subjects = [x[0:-4] for x in os.listdir(folder.save) if ('.ini' in x and x != 'mod.ini')]
        addnew = s_msg['create new subj'].format(subj=my.subj_type)
        subjects.append(addnew)
    
        # dialog asks for a subject
        subject = eg.choicebox(s_msg['run which subj'].format(subj=my.subj_type), choices=subjects)
        if subject == None:
            # user closed choice box
            eg_cancel_program()
        elif subject == addnew:
            # user chose to add a new subject
            subject = ''
            while subject == '':
                subject = eg.enterbox(msg=s_msg['type subj name'].format(subj=my.subj_type), \
                                      title=s_msg['new subj'].format(subj=my.subj_type), \
                                      default='', \
                                      strip=True)
                if subject == '':
                    continue
                elif subject == None:
                    eg_cancel_program()
                subject = utostr(subject)
                subject = subject.lower()
                if subject in subjects:
                    eg.msgbox(s_msg['subj exists'].format(subj=my.subj_type, chosen_subj=subject))
                    subject = ''
                    continue
                elif subject == 'mod':
                    eg.msgbox(s_msg['subj cant be named mod'].format(subj=my.subj_type))
                    subject = ''
                    continue
    
        # show a Continue/Cancel dialog
        msg = s_msg['you chose subj'].format(subj=my.subj_type, chosen_subj=subject, chosen_exp=my.experiment)
        if eg.ccbox(msg=msg, title = s_msg['confirm']):
            # user chose Continue
            pass
        else:
            # user chose Cancel
            eg_cancel_program()
            
        my.subject = subject
        self.custom_subject_name = True
            
    def create_save_file(self):
        
        save_filename = 'save.ini'
        if self.custom_subject_name:
            save_filename = '{0}.ini'.format(my.subject)
            if options.use_subject_folder:
                folder.save = os.path.join(folder.save, my.subject)
        elif self.custom_experiment_name:
            save_filename = '{0}.ini'.format(my.experiment)
        savepath = os.path.join(folder.save, save_filename)

        if not os.path.exists(folder.save) and options.write_save:
            os.mkdir(folder.save)
        if os.path.exists(savepath):
            # load and validate save file of existing subject
            save = ConfigObj(infile=savepath,
                             configspec=os.path.join(folder.spec, 'save_spec.ini'))
            validate(save)
        else:
            # subject doesn't exist yet: load initial save, validate and save file
            initial_save_path = os.path.join(folder.extralang, 'initial_save.ini')
            if not os.path.exists(initial_save_path):
                initial_save_path = None
            save = ConfigObj(infile=initial_save_path,
                    configspec=os.path.join(folder.spec, 'save_spec.ini'))
            validate(save, set_copy=True)
            save.filename = savepath

            if options.write_save:
                save.write()
        if not options.write_save:
            # make the write function do nothing
            save.write = lambda:None
        my.save = save
    
    def load_exp_cfg(self):
        exp_path = os.path.join(folder.expcfg, my.experiment + '.ini')   
        if my.lang != 'eng' and options.translate:
            exp_path = translate_and_change_path(exp_path)        

        if options.use_save and options.use_mod and os.path.exists(folder.save):
            if 'mod.ini' in os.listdir(folder.save):
                # mod.ini describes overloading config on top of experiment config
                # here we edit the experiment file to use the mod.ini values
        
                mod_path = os.path.join(folder.save, 'mod.ini')
                if options.translate and my.lang != 'eng':
                    mod_path = translate_and_change_path(mod_path)
        
                exp_path = modify_and_change_path(exp_path, mod_path)
            elif options.create_mod:
                f = open(os.path.join(folder.save, 'mod.ini'), "w")
                f.close()
        
        # load and validate experiment
        my.expcfg = ConfigObj(infile=exp_path,
                        configspec=os.path.join(folder.spec, 'experiment_spec.ini'))
        validate(my.expcfg)
        
        # we are keeping my.expcfg as ConfigObj to eventually use its methods for saving

    def configure_network(self):
        my.network = ConfigObj(infile=os.path.join(folder.ba, 'ba_network.ini'),
                        configspec=os.path.join(folder.baspec, 'ba_network_spec.ini'))
        validate(my.network)
        custom_network_ini = os.path.join(folder.main, 'network.ini')
        if os.path.exists(custom_network_ini):
            custom_network = ConfigObj(infile=custom_network_ini,
                        configspec=os.path.join(folder.spec, 'network_spec.ini'))
            validate(custom_network)
            my.network.merge(custom_network)
        
        my.net_msg = ConfigObj(infile=os.path.join(folder.balang, 'ba_net_msg.ini'),
                        configspec=os.path.join(folder.baspec, 'ba_net_msg_spec.ini'),
                        encoding = 'UTF8')
        validate(my.net_msg)
        custom_net_msg_ini = os.path.join(folder.extralang, 'net_msg.ini')
        if os.path.exists(custom_net_msg_ini):
            custom_net_msg = ConfigObj(infile=custom_net_msg_ini,
                        configspec=os.path.join(folder.spec, 'net_msg_spec.ini'),
                        encoding = 'UTF8')
            validate(custom_net_msg)
            my.net_msg.merge(custom_net_msg)

    def cleanup(self):
        
        if options.translate:
            # cleanup temp files
            shutil.rmtree(folder.temp)
        
    def run(self, controller):
        controller().run()

def validate(cfg, set_copy=False):
    '''Validates a ConfigObj instance.

    If errors are found, throws exception and reports errors.
    '''

    validator = Validator()
    res = cfg.validate(validator, preserve_errors = True, copy=set_copy)
    for entry in flatten_errors(cfg, res):
        # each entry is a tuple
        section_list, key, error = entry
        if key is not None:
            section_list.append(key)
        else:
            section_list.append('[missing section]')
        section_string = ', '.join(section_list)
        if error == False:
            error = 'Missing value or section.'
        print section_string, ' = ', error
    if res != True:
        error = '{0} invalido\n'.format(os.path.split(cfg.filename)[1])
        raise Exception(error)


def is_comment_or_empty(text):
    '''Returns True if config text line is empty or a comment.'''

    return text in [u'', []] or text[0] == u'#'


def is_section(text):
    '''Returns True if config text line is a section of the config.'''

    if is_comment_or_empty(text) or text[0] != u'[':
        return False
    return u']' in text


def translate_and_change_path(config_path):
    '''
    Creates an edited config from another and returns a path to itself.

    The new edited config file is saved in a temporary system folder.
    '''

    config_file = codecs.open(config_path, 'r', 'utf-8')
    file_name = '{0}{1}'.format(os.getpid(), os.path.split(config_path)[1])
    temp_path = os.path.join(folder.temp, file_name)
    a_temp_file = codecs.open(temp_path, 'w', 'utf-8')

    # read config and split its lines
    text = config_file.read()
    text = [x.strip() for x in text.splitlines()]

    # shrink it to help parsing
    text = split_config_text_shrink(text)

    # start translating
    section = 'root'
    for i in xrange(len(text)):
        # skip comments and empty lines
        if not is_comment_or_empty(text[i]):
            # translate sections
            if is_section(text[i]):
                for k, v in my.translate['sections'].iteritems():
                    section_trans = u'[{0}]'.format(v)
                    section_orig = u'[{0}]'.format(k)
                    text[i] = text[i].replace(section_trans, section_orig)
                section = text[i].split(u'[')[1].split(u']')[0]
            # or translate items
            elif u'=' in text[i]:
                for k, v in my.translate[section].iteritems():
                    item_v = u'{0}='.format(v)
                    item_k = u'{0}='.format(k)
#                    if item_v in text[i]:
                        
                    # TODO: z_ only replace if thats all there is before the '='
                    text[i] = text[i].replace(item_v, item_k)

    # finish up: restore, put it back toguether, write, close, return new path
    text = split_config_text_restore(text)
    text = u'\n'.join(text)
    a_temp_file.write(text)
    a_temp_file.close()

    return temp_path


def modify_and_change_path(config_path, mod_path):
    '''
    Overloads values from a config to another and returns a new path to it.

    The new edited config file is saved in a temporary system folder.
    '''

    config_file = codecs.open(config_path, 'r', 'utf-8')
    mod_file = codecs.open(mod_path, 'r', 'utf-8')
    file_name = '{0}mod{1}'.format(os.getpid(), os.path.split(config_path)[1])
    temp_path = os.path.join(folder.temp, file_name)
    a_temp_file = codecs.open(temp_path, 'w', 'utf-8')

    # read configs and split the lines
    text = config_file.read()
    text = [x.strip() for x in text.splitlines()]
    mod_text = mod_file.read()
    mod_text = [x.strip() for x in mod_text.splitlines()]

    # shrink both files for parsing first
    text = split_config_text_shrink(text)
    mod_text = split_config_text_shrink(mod_text)

    # list sections and items to change
    section = 'root'
    mod_dict = dict(root = {})
    for i in xrange(len(mod_text)):
        # skip comments and empty lines
        if not is_comment_or_empty(mod_text[i]):
            # get sections
            if is_section(mod_text[i]):
                section = mod_text[i].split(u'[')[1].split(u']')[0]
                mod_dict[section] = {}
            # or get items
            elif u'=' in mod_text[i]:
                k, v = mod_text[i].split(u'=', 1)
                mod_dict[section][k] = v

    # start modifyng
    section = 'root'
    for i in xrange(len(text)):
        # skip non-mod sections
        if section in mod_dict.keys():
            # skip comments and empty lines
            if not is_comment_or_empty(text[i]):
                # get section name
                if is_section(text[i]):
                    section = text[i].split(u'[')[1].split(u']')[0]
                # check if same keys are found, replace value in that case
                elif u'=' in text[i]:
                    k, v = text[i].split(u'=', 1)
                    if k in mod_dict[section].keys():
                        text[i] = text[i].replace(v, mod_dict[section][k])

    # finish up: restore, put it back toguether, write, close, return new path
    text = u'\n'.join(text)
    a_temp_file.write(text)
    a_temp_file.close()

    return temp_path

def split_config_text_shrink(text_list):
    '''
    Shrinks config text lines from a splitted config file.

    Takes a text list and returns the shrunk list.
    '''

    # This helps modifying config files

    for i in xrange(len(text_list)):
        # skip comments and empty lines
        if not is_comment_or_empty(text_list[i]):
            # process sections
            if is_section(text_list[i]):
                while u'[ ' in text_list[i]:
                    text_list[i] = text_list[i].replace(u'[ ', u'[')
                while u' ]' in text_list[i]:
                    text_list[i] = text_list[i].replace(u' ]', u']')
            # or process items
            elif u'=' in text_list[i]:
                while u' =' in text_list[i]:
                    text_list[i] = text_list[i].replace(u' =', u'=')

    return text_list

def split_config_text_restore(text_list):
    '''
    Restores config text lines from a splitted and shrunk config file.

    Takes a text list and returns the restored list.
    '''

    # This is done after modifying config files

    for i in xrange(len(text_list)):
        # skip comments and empty lines
        if not is_comment_or_empty(text_list[i]):
            # process sections
            if is_section(text_list[i]):
                text_list[i] = text_list[i].replace(u'[', u'[ ')
                text_list[i] = text_list[i].replace(u']', u' ]')
            # or process items
            elif u'=' in text_list[i]:
                text_list[i] = text_list[i].replace(u' =', u'=')

    return text_list


def eg_cancel_program():
    '''Shows a dialog informing the program is cancelled.'''

    eg.msgbox(my.s_msg['cancel program'])
    exit_app()
    
def exit_app():
    print 'exit_app'
    if options.use_log:
        my.stout.close()
#    sys.exit(0)
    os._exit(1)
    
def eg_experiment_not_found(msg=''):
    if msg == '':   
        msg = my.s_msg['no exp found']
    print_u(msg)
    eg.msgbox(msg)
    eg_cancel_program()

def main():
    if options.gui:
        from mycocos.cocosgui import CocosController #@UnresolvedImport
    else:
        sys.exit(0)
    PrepareBase()
    controller = CocosController()
    controller.run()

# anonymous class instances for holding global variables
#my = type('my', (object, ), {})()
my = Container()

# Fool py2exe, py2app into including all top-level modules
if False: 
    import easygui as eg # easygui used to create tkinter dialog windows
    import tempfile #@UnusedImport

if __name__ == '__main__':
    main()

# TODO: z_ reimplement translations using the "walk" method of ConfigObj!!!
# TODO: z_ reimplement translations (http://www.voidspace.org.uk/python/configobj.html#walking-a-section)

# TODO: exp folder should be at res/scripts !! (actually no "exp" folder should be required!)
# TODO: docs should have its own folder.
