'''
Created on 27/11/2010

@author: thomas
'''

import os
from behavan import app
from behavan.app import my, folder, options, net_options, Container
from behavan.convert import utostr #@UnresolvedImport

import pyglet
from pyglet.window import key
pyglet.options['debug_gl'] = False
from pyglet.clock import schedule_once
from cocos.director import director
from cocos.scene import Scene
from cocos.layer import Layer, ColorLayer
from cocos.text import RichLabel

from layers import MessageLayer, SmallColorLayer, center_label #@UnresolvedImport

#from configobj.configobj import ConfigObj
#from configobj.configobj import flatten_errors
#from configobj.validate import Validator

#__all__ = ['CocosExperiment', 'CocosController', 'GUIBase', 'MessageLayerStyled', 'lr', 'DPI']

# constant
DPI = 96

# anonymous class instance to hold layers
#lr = type('lr', (object, ), {})()
lr = Container()

def play(sound):
    my.sound[sound].play()

class CocosExperiment(app.ExperimentBase):
    def __init__(self):
#        my.debug = False
#        debug_path = os.path.join(folder.main, 'debug.ini')
#        if os.path.exists(debug_path):
#            my.debug = ConfigObj(infile=debug_path)      
        super(CocosExperiment, self).__init__()
        self.create_layers()
        
        # only make window small after all layers were created, to avoid layout errors
        if my.debug:
            if my.debug['smallwindow'] != 1.0 and not director.window.fullscreen:
                self.scaled_resize = True
                director.window.push_handlers(
                    on_resize=director.scaled_resize_window)
                width = int(my.window['width'] * my.debug['smallwindow'])
                height = int(my.window['height'] * my.debug['smallwindow'])
                director.window.set_size(width, height)
        
        
    def create_layers(self):
        '''Creates scene layers.'''
        # layers
        lr.back = ColorLayer(*my.layout['color']['back window'])
        lr.instruction = MessageLayerStyled('instruction')
        lr.end = MessageEnd()
        lr.gui = GUIBase()

    def set_resources(self):
        self.add_resources()
        if options.use_sounds:
            self.set_sounds()
        else: # no sound
            global play
            play = lambda sound:None
        
    def add_resources(self):
        pyglet.resource.path.append(os.path.join(folder.res, 'sounds'))
        pyglet.resource.path.append(os.path.join(folder.res, 'images'))
        pyglet.resource.reindex()
        pyglet.font.add_directory(os.path.join(folder.res, 'fonts'))
        
    def set_sounds(self):
        sound_keys = my.expcfg['sound'].keys()
        sound_values = my.expcfg['sound'].values()
        sound_list = [pyglet.resource.media(
                          sound, streaming=False)
                          for sound in sound_values]
        my.sound = dict((k, v) for k, v in zip(sound_keys, sound_list))
        
        # TODO: add sounds later for cocosclient?
        
    def set_window(self):
        
        self.set_draw_area()
        self.set_text_styles()
        self.set_stimuli_dimensions()
        
    def set_draw_area(self):
        '''Sets up drawing area based on current state and config.'''
        print 'set_draw_area (bacocos gui)'
        
        # TODO: x_ add options to scale up the scene, and to create small window.

        # window / screen status
        my.window['height'] = my.guicfg['height']
        my.window['width'] = my.guicfg['width']
        my.window['proportion'] = my.window['width'] / float(my.window['height'])
        my.window['reduction'] = my.guicfg['reduce window to']
    
#        caption = my.s_msg['research']

        # screen settings
        display = pyglet.window.get_platform().get_default_display()
        screens = display.get_screens()
        screen = screens[0]

        if screen.width < my.window['width'] or screen.height < my.window['height']:
            my.guicfg['fullscreen'] = True
            if my.guicfg['reject smaller screen'] \
            or not my.guicfg['use screen resolution']:
                msg = my.s_msg['screen smaller than window']
                error = utostr(msg)
                raise Exception(error)
            print '''Screen is smaller than configured window.
            Screen resolution was adjusted.
            This may affect visualization.'''
        
        caption = my.s_msg['research']
        if net_options.client:
            caption = 'client'
        if net_options.observer:
            caption = 'observer'
        # TODO: z_ use translations here for captions!

        # main options, it may change        
        director_init = dict(caption=caption,
                         fullscreen=False,
                         resizable=my.guicfg['resizable'])
        
                        # TODO: allow resizable somehow?
                        # TODO: custom captions: 'observer', 'client'
        
        if (my.guicfg['use screen resolution']
        or my.guicfg['fullscreen']):
            my.window['height'] = screen.height
            my.window['width'] = screen.width
            director_init = dict(director_init,
                                 fullscreen=True)

        elif screen.width == my.window['width'] and screen.height == my.window['height']:
            director_init = dict(director_init, 
                                 fullscreen=True)
        else:
            director_init = dict(director_init,
                                 width=my.window['width'],
                                 height=my.window['height'])
        if my.guicfg['align pixels']:
            director_init['do_not_scale'] = True

        # prepare director
        director.init(**director_init)

        proportion = my.window['width'] / float(my.window['height'])
        equal_proportion = False
        if proportion == my.window['proportion']:
            equal_proportion = True
        if my.guicfg['use screen resolution']:
            if equal_proportion:
                my.window['draw width'] = my.window['width']
                my.window['draw height'] = my.window['height']
            elif proportion < my.window['proportion']:
                my.window['draw height'] = int(my.window['width'] / my.window['proportion'])
                my.window['draw width'] = my.window['width']
            else:
                my.window['draw width'] = int(my.window['height'] * my.window['proportion'])
                my.window['draw height'] = my.window['height']
        else:
            my.window['draw width'] = my.guicfg['width']
            my.window['draw height'] = my.guicfg['height']

        my.window['width hint'] = (my.window['width'] - my.window['draw width']) / 2
        my.window['height hint'] = (my.window['height'] - my.window['draw height']) / 2

        # careful, using pyglet variables that may change (underlined)
        # TODO: z_ check cocos methods here
        if director.window.fullscreen:
            if (my.window['width'] > my.guicfg['width']
            and my.window['height'] > my.guicfg['height']
            and equal_proportion):
                default_width = my.guicfg['width']
                default_height = my.guicfg['height']
            else:
                default_width = int(my.window['width'] * my.window['reduction'])
                default_height = int(my.window['height'] * my.window['reduction'])
        else:
            default_width = my.window['width']
            default_height = my.window['height']
        
        if my.debug:
            if my.debug['smallwindow'] != 1:
                default_width = int(default_width * my.debug['smallwindow'])
                default_height = int(default_height * my.debug['smallwindow'])

        director.window._default_width = default_width
        director.window._default_height = default_height
        director.window._windowed_size = (default_width,
                                          default_height)

#        if my.guicfg['fullscreen'] != director.window.fullscreen:
#            director.window.set_fullscreen(not director.window.fullscreen)
                    
        # flag for scale resize (set to True after the first resize)
        self.scaled_resize = False

        director.show_FPS = my.guicfg['show FPS']

    def set_text_styles(self):
        '''Sets up text styles.'''

        my.text_style = dict()

        my.text_style['single line'] = dict(
           font_name=my.layout['font']['sans'],
           font_size=my.layout['font']['default size'],
           color = (0, 0, 0, 255),
           x=my.window['width'] / 2,
           y=my.window['height'] / 2,
           anchor_x='center',
           anchor_y='center',
           halign='center',
           multiline=False,
           dpi=DPI)

        my.text_style['multi line'] = dict(
            my.text_style['single line'],
            width=int(5 * my.window['draw width'] / 6.),
            height=my.window['draw height'],
            multiline=True)

        my.text_style['error'] = dict(
            my.text_style['multi line'],
            font_size=int(my.layout['font']['default size'] / 2))
    
    def set_stimuli_dimensions(self):
        my.stim = {}

    def set_handlers(self):
        
        # keyboard settings
        self.print_key = my.guicfg['print key']
        self.set_keyboard_exclusivity()

        # push key event handlers to the application
        director.window.push_handlers(on_key_press = self.on_key_press)
        
        # disable window deactivation that exits fullscreen
        director.window.push_handlers(on_deactivate = self.on_deactivate)

    def on_deactivate(self):
        """The window was deactivated, get out of fullscreen if there."""
        return True

    def unschedule_all(self):
        '''Unschedule every possible scheduled function.'''

        for func in my.schedule_funcs:
            pyglet.clock.unschedule(func)

    # events
    def on_key_press(self, symbol, modifiers):
        if symbol == key.ESCAPE:
            if modifiers & key.MOD_SHIFT:
                self.cocos_app_exit()
            return True
        if symbol == key.F and (modifiers & key.MOD_ACCEL):
            # TODO: z_ check methods of newer cocos here
            if not self.scaled_resize:
                director.window.push_handlers(
                    on_resize=director.scaled_resize_window)
#                    on_resize=director.unscaled_resize_window)
            director.window.set_fullscreen(not director.window.fullscreen)
            self.scaled_resize = True
            return True            
        if self.print_key:
            print symbol
        return False
    
    def set_keyboard_exclusivity(self):
        if my.guicfg['exclusive keyboard'] and not my.debug:
            director.window.set_exclusive_keyboard(exclusive=True)
    
    def cocos_app_exit(self):
        if options.use_log:
            my.stout.close()
        pyglet.app.exit()

class CocosController(CocosExperiment):
    '''
    Controls the flow of the experiment.

    It also stores, changes and records data.
    '''

    def __init__(self):
        
        super(CocosController, self).__init__()
#        self.create_layers()
    
    def set_exp_vars(self):
        '''Sets experimental variables.'''
        super(CocosController, self).set_exp_vars()
        
        # section status
        self.session_ended = False
        
    def start_session(self):
        super(CocosController, self).start_session()
        time_limit = my.expcfg['session']['time limit in minutes'] * 60
        schedule_once(self.expire_session_time, time_limit)
        my.schedule_funcs.add(self.expire_session_time)
    
    def start_trial(self):
        self.set_time()
        self.trial_ended = False
        self.time_trial = self.now
        director.replace(Scene(lr.back, lr.gui))
        
    def start_iti(self, *a):
        '''Starts inter-trial interval following feedback'''
        schedule_once(self.start_trial, self.duration_iti)
        if self.session_ended:
            func = self.end_session
        else:
            func = self.start_trial
        schedule_once(func, self.duration_iti)
        director.replace(Scene(lr.back))

    def expire_session_time(self, dt):
        self.unschedule_all()
        self.end_session(self.output_labels['session time ended'])

    def run(self):
        '''Starts the mainloop.'''
        show, start = self.check_start()
        if start:
            self.start_session()
        director.run(show)

    def check_start(self):
        ''' returns starting scene to run according to saved conditions, and returns if session has started '''
        start = False
        show = False
        instruction = False
        if options.use_save:
            if 'concluded' in my.save.keys() and my.save['concluded']:
                lr.end.concluded()
                show = Scene(lr.end)
            elif my.expcfg['main']['use initial instruction']:
                # check if its restarted from previous run
                restarted = False
                status_keys = ['current condition', 'current trial', 'current cycle']
                # experiment moment is usually measured/described by one of these tokens above
                for k in status_keys:
                    if k in my.save.keys():
                        if my.save[k] > 1:
                            restarted = True
                if not restarted:
                    instruction = True
                else:
                    start = True
            else:
                start = True
        elif my.expcfg['main']['use initial instruction']:
            instruction = True
        else:
            start = True
        if instruction:
            show = Scene(lr.back, lr.instruction)
        if start:
            show = self.get_start_scene()
        return (show, start)
    
    def get_start_scene(self):
        return Scene(lr.back)

    def end_session(self, status='', set_time=True):
        if set_time:
            self.set_time()
        self.unschedule_all()
        self.session_ended = True
        if status == 'concluded':
            lr.end.concluded()
        self.record_end(status)
        director.replace(Scene(lr.back, lr.end))
        
class GUIBase(Layer):
    '''GUI template layer.'''

    is_event_handler = True

    def __init__(self, color = (0, 0, 0, 255)):

        # initialize layer
        super(GUIBase, self).__init__()

        # add back color
        back_dim = dict(
            width = my.window['draw width'],
            height = my.window['draw height'],
            x = my.window['width hint'],
            y = my.window['height hint'])
        self.back = SmallColorLayer(*color,
                                    **back_dim)
        self.add(self.back, z=-1)


class MessageLayerStyled(MessageLayer):
    '''Layer with custom message, back color (rgba) and richlabel style.'''

    def __init__(self, text, back_color=None, text_style = 'multi line', rich_text = False):
        text_style = my.text_style[text_style]
        if not rich_text:
            text_style = dict(text_style,
                          bold=True)
        if not back_color:
            back_color = my.layout['color']['back message']

        # initialize layer
        super(MessageLayerStyled, self).__init__(text, text_style, back_color, rich_text)

class MessageEnd(MessageLayerStyled):
    '''Layer with the end message.'''

    is_event_handler = True

    def __init__(self):
        text = my.message['end']
        back_color = my.layout['color']['back end']

        # initialize layer
        super(MessageEnd, self).__init__(text, back_color)
        
        if 'score' in lr.__dict__.keys():
            self.add(lr.score, z=1)

    def concluded(self):
        self.remove(self.label)
        self.label.element.delete()
        del self.label.element
        del self.label
        self.label = RichLabel(**dict(my.text_style['multi line'],
                                      text=my.message['end concluded']))
        center_label(self.label)
        self.add(self.label, z= 1)
        lr.score.score.visible = True


