#! /usr/bin/env python
# -*- coding: UTF-8 -*-

# ----------------------------------------------------------------------------
# woelzlayers.py
# Copyright (c) 2009 Thomas Anatol da Rocha Woelz
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
#  * Neither the name of woelzlayers.py nor the names of its
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

# cocos2d main developers (as of 2008) are:
# Daniel Moisset, Ricardo Quesada, Rayentray Tappa, Lucio Torre
# All rights reserved.

'''Custom cocos2d layers.

Based on cocos2d native layers, but changed for common use in various
projects.

'''

__all__ = ['SmallColorLayer', 'RectTextWidget', 'Score', 'Button', \
           'ImageButton', 'MessageLayer', 'rect_position', \
           'rect_with_border_position', 'center_label']
__version__ = '1.0.0'
__docformat__ = 'restructuredtext'

import copy

# dependencies are not added to sys.path because it should have been 
# done from the running script already 

import pyglet
from pyglet import gl
from pyglet.clock import schedule_once

from cocos.director import director
from cocos.layer import Layer, ColorLayer
from cocos.text import Label, RichLabel
from cocos.actions import ScaleTo # actions may be overkill (slow) for very short/fast animations
from cocos.sprite import *

# basic layout functions

def rect_position(x, y, width, height):
    '''Returns vertex positions for drawing a rectangle.'''

    return (x, y,
            x + width, y,
            x + width, y + height,
            x, y + height)


def rect_with_border_position(x, y, width, height, thick):
    '''Returns vertex positions for drawing a rectangle with borders.'''
    return (x + thick, y + thick,
            x + width - thick, y + thick,
            x + width - thick, y + height - thick,
            x + thick, y + height - thick,
            x, y,
            x + width, y,
            x + width, y + thick,
            x, y + thick,
            x, y + height - thick,
            x + width, y + height - thick,
            x + width, y + height,
            x, y + height,
            x, y + thick,
            x + thick, y + thick,
            x + thick, y + height - thick,
            x, y + height - thick,
            x + width - thick, y + thick,
            x + width, y + thick,
            x + width, y + height - thick,
            x + width - thick, y + height - thick)
    
def anchor(img, pos = ()):
    '''
    Add anchors for an image on given (x, y) position.

    Image anchors uses the API of "pyglet.resource.image".
    '''

    if pos == ():
        img.anchor_x = img.width / 2
        img.anchor_y = img.height / 2
    else:
        img.anchor_x, img.anchor_y = pos
    return img


# cocos2d transformation functions

def center_label(label, align='center', content_valign='center'):
    '''centers a cocos2d multi-line label'''
    label.element.document.set_style(0,
                                len(label.element.text),
                                dict(align=align))
    label.element.content_valign = content_valign

# Layer classes (widgets, etc)

class SmallColorLayer(Layer):
    """Creates a layer of a certain color and dimensions.
    The color shall be specified in the format (r,g,b,a).
    The dimensions should be a dictionary containing width, height, x and y.
    """

    def __init__(self, *color, **dimensions):
        super(SmallColorLayer, self).__init__()
        self._batch = pyglet.graphics.Batch()
        self._rgb = color[:3]
        self._opacity = color[3]

        self.w = dimensions['width']
        self.h = dimensions['height']
        self.transform_anchor_x = self.w / 2
        self.transform_anchor_y = self.h / 2
        self.x = dimensions['x']
        self.y = dimensions['y']

        self._vertex_list = self._batch.add(4, gl.GL_QUADS, None,
            ('v2i', (0, 0, 0, self.h, self.w, self.h, self.w, 0)),
            'c4B')

        self._update_color()

    def draw(self):
        super(SmallColorLayer, self).draw()
        gl.glPushMatrix()
        self.transform()
        self._batch.draw()
        gl.glPopMatrix()

    def _update_color(self):
        r, g, b = self._rgb
        self._vertex_list.colors[:] = [r, g, b, int(self._opacity)] * 4

    def _set_opacity(self, opacity):
        self._opacity = opacity
        self._update_color()

    opacity = property(lambda self: self._opacity, _set_opacity,
                       doc='''Blend opacity.

    This property sets the alpha component of the colour of the layer's
    vertices.  This allows the layer to be drawn with fractional opacity,
    blending with the background.

    An opacity of 255 (the default) has no effect.  An opacity of 128 will
    make the sprite appear translucent.

    :type: int
    ''')

    def _set_color(self, rgb):
        self._rgb = map(int, rgb)
        self._update_color()

    color = property(lambda self: self._rgb, _set_color,
                       doc='''Blend color.

    This property sets the color of the layer's vertices. This allows the
    layer to be drawn with a color tint.

    The color is specified as an RGB tuple of integers ``(red, green, blue)``.
    Each color component must be in the range 0 (dark) to 255 (saturated).

    :type: (int, int, int)
    ''')


class RectWidget(Layer):
    ''' Basic rectangular widget '''
    # requires 2 functions:
    # rect_position()
    # rect_with_border_position()
    def __init__(self,
                x=0,
                y=0,
                width=150,
                height=60,
                background_color= (0, 180, 0, 127),
                border_type ='quad', # options: 'line', 'quad' or None
                border_color = (255, 255, 255, 204),
                border_proportion = 0.2,
                widget_visible = True,
                *a, **kw):

        super(RectWidget, self).__init__()

        # store attributes
        self.widget_x = x
        self.widget_y = y
        self.widget_width = width
        self.widget_height = height
        self.background_color = background_color
        self.border_type = border_type
        self.border_color = border_color
        self.border_thick = self.get_border_thick(
                                            width, height, border_proportion)
        self.widget_visible = widget_visible

        # center anchors
        self.transform_anchor_x = x + width/2
        self.transform_anchor_y = y + height/2

        # batch to accelerate widget drawing
        self.widget_batch = pyglet.graphics.Batch()
        
        #TODO: try to remove border_batch later!
        # added this just because I couldn't draw a line correctly (rect_widget overwrites the lower and leftmost line).
        self.border_batch = pyglet.graphics.Batch()

        # rect drawing stuff
        self.vertex_position = self.get_vertex_position(
                                        x,
                                        y,
                                        width,
                                        height,
                                        self.border_thick)
        self.vertex_colors = self.get_vertex_color(
                                        background_color,
                                        border_color)

        # border drawing stuff
        self.border_colors = None
        if border_type == 'line':
            self.border_colors = border_color * 4

        # drawing attributes start empty
        self.vertex = None
        self.button_border = None

        if self.widget_visible:
            self.show_widget()

    def show_widget(self):
        
        # add rect batch
        self.vertex = self.widget_batch.add(
                self.get_vertex_size(),
                gl.GL_QUADS,
                None,
                ('v2i', self.vertex_position),
                ('c4B', self.vertex_colors))

        # add border batch (if needed)
        if self.border_type == 'line':
            self.border = self.border_batch.add(
                    4,
                    gl.GL_LINE_LOOP,
                    None,
                    ('v2i', rect_position(
                        self.widget_x, self.widget_y,
                        self.widget_width, self.widget_height)),
                    ('c4B', self.border_colors))
        else:
            self.border = object()
        self.widget_visible = True

    def clear_batch(self):
        '''Clears drawing elements from widget batch.'''

        if not self.vertex == None:
            self.vertex.delete()
            self.vertex = None
        if self.border_type == 'line' and not self.button_border == None:
            self.border.delete()
            self.border = None
        self.widget_visible = False

    def get_vertex_position(self, x, y, width, height, border_thick):
        if self.border_type == 'quad':
            return rect_with_border_position(x, y,
                                            width, height,
                                            border_thick)
        else:
            return rect_position(x, y, width, height)

    def get_vertex_color(self, background_color, border_color):
        if self.border_type == 'quad':
            return background_color * 4 + border_color * 16
        else:
            return background_color * 4

    def get_vertex_size(self):
        if self.border_type == 'quad':
            return 20
        else:
            return 4

    def get_border_thick(self, width, height, border_proportion):
        x_thick = max(1, int((width * border_proportion) / 2.))
        y_thick = max(1, int((height * border_proportion) / 2.))
        return min(x_thick, y_thick)

    def draw(self):
        super(RectWidget, self).draw()
        gl.glPushMatrix()
        self.transform()
        self.widget_batch.draw()
        # TODO: try to remove border batch later, see reason above!
        self.border_batch.draw()
        gl.glPopMatrix()
    


class RectTextWidget(RectWidget):
    ''' Basic rectangular widget with rich text '''
    # requires center_label function:
    def __init__(self,
                text_style = {}, # use cocos2d text_style dict
                text = '',
                text_align='center',
                center_label_align='center',
                rich_text = False,
                hint_label_y = 0,
                hint_label_x = 0,
                text_color=(0, 0, 0, 255),
                widget_visible = True,
                *a, **kw):

        super(RectTextWidget, self).__init__(widget_visible=False,
                                             *a, **kw)

        # store attributes
        self.text_style = text_style
        self.text = text
        self.center_label_align = center_label_align 
        self.rich_text = rich_text
        self.hint_label_y = hint_label_y
        self.hint_label_x = hint_label_x
        self.text_color = text_color
        self.widget_visible = widget_visible

        # label drawing stuff
        self.label_x = self.widget_x + self.hint_label_x
        self.label_y = self.widget_y + self.hint_label_y
        if text_align == 'center':
            self.label_x += self.widget_width / 2
            self.label_y += self.widget_height / 2
        elif text_align == 'topleft':
            self.center_label_align='left'
            self.label_y += self.widget_height

        # drawing attributes start empty
        self.label = None

        if self.widget_visible:
            self.show_widget()

    def show_widget(self):
        super(RectTextWidget, self).show_widget()
        self.add_label()

    def clear_batch(self):
        '''Clears drawing elements from widget batch.'''
        super(RectTextWidget, self).clear_batch()
        self.clear_label()

    def add_label(self):
        if self.rich_text:
            label_class = RichLabel
        else:
            label_class = Label
        self.label = label_class(**dict(
                        self.text_style,
                        text = self.text,
                        x = self.label_x,
                        y = self.label_y,
                        color = self.text_color))
        center_label(self.label, self.center_label_align)
        self.add(self.label, z=1)

    def clear_label(self):
        '''Clears the widget's label'''

        if not self.label == None:
            self.remove(self.label)
            self.label.element.delete()
            del self.label.element
            del self.label

    def update_text(self, text):
        '''Changes widget's current text for new text.'''

        self.text = text
        if self.widget_visible:
            if self.rich_text:
                self.clear_label()
                self.add_label()
            else:
                self.label.element.text = self.text

class Score(RectWidget):
    ''' Basic rectangular widget with rich text '''
    # requires center_label function:
    def __init__(self,
                 title_text_style = {}, # use cocos2d text_style dict
                 title_text = '',
                 title_text_color = (0, 0, 0, 255),
                 title_hint_up = 0,
                 value_text_style = {}, # use cocos2d text_style dict
                 value_text = '',
                 value_text_color = (0, 0, 0, 255),
                 value_hint_down = 0,
                 rich_text = False,
                 hint_label_y = 0,
                 hint_label_x = 0,
                 widget_visible = True,
                 *a, **kw):

        super(Score, self).__init__(widget_visible=False,
                                             *a, **kw)

        # store attributes
        self.title_text_style = dict(title_text_style,
                                     anchor_y = 'bottom')
        self.title_text = title_text
        self.title_text_color = title_text_color
        self.title_hint_up = title_hint_up
        self.text_style = dict(value_text_style,
                               anchor_y = 'top')
        self.text = value_text
        self.text_color = value_text_color
        self.value_hint_down = value_hint_down
        self.rich_text = rich_text
        self.hint_label_y = hint_label_y
        self.hint_label_x = hint_label_x

        self.widget_visible = widget_visible

        # label drawing stuff
        self.label_x = self.widget_x + (self.widget_width/2) \
                                                        + self.hint_label_x
        self.label_y = self.widget_y + (self.widget_height/2) \
                                                        + self.hint_label_y

        # drawing attributes start empty
        self.title_label = None
        self.label = None
        
        self.emphasizable = True

        if self.widget_visible:
            self.show_widget()

    def show_widget(self):
        super(Score, self).show_widget()
        self.add_labels()

    def clear_batch(self):
        '''Clears drawing elements from widget batch.'''
        super(RectTextWidget, self).clear_batch()
        self.clear_labels()

    def add_labels(self):
        if self.rich_text:
            label_class = RichLabel
        else:
            label_class = Label
            
        self.title_label = label_class(**dict(
            self.title_text_style,
            text = self.title_text,
            x = self.label_x,
            y = self.label_y + self.title_hint_up,
            color = self.title_text_color))
        self.label = label_class(**dict(
            self.text_style,
            text = self.text,
            x = self.label_x,
            y = self.label_y - self.value_hint_down,
            color = self.text_color))
        for i in [self.title_label, self.label]:
            center_label(i)
            self.add(i, z=1)
#        self.title_label.element.content_valign = 'top'
#        self.label.element.content_valign = 'bottom'

    def clear_labels(self):
        '''Clears the widget's label'''

        if not self.label == None:
            self.remove(self.label)
            self.label.element.delete()
            del self.label.element
            del self.label

    def update_text(self, text):
        '''Changes widget's current text for new text.'''

        self.text = text
        if self.widget_visible:
            if self.rich_text:
                self.clear_label()
                self.add_label()
            else:
                self.label.element.text = self.text

    def emphasize(self, duration=0.10):
        if self.emphasizable:
            self.emphasizable = False
            if duration < 0.10:
                duration = 0.10
            half_duration = duration / 2.0
            self.do(ScaleTo(1.2, half_duration) + ScaleTo(1, half_duration))
            schedule_once(self.make_emphasizable, duration)     
            # TODO: figure out why emphasize not smooth
            # implement animation myself without 'actions' maybe? just some 5 frames?

    def make_emphasizable(self, *a):
        self.emphasizable = True

class Button(RectTextWidget):

    is_event_handler = True

    def __init__(self,
                text_charged_color=(127, 0, 0, 255),
                border_charged_color = (127, 0, 0, 255),
                keys = [],
                modifier = 0,
                activate_funcs = [],
                deactivate_funcs = [],
                name = None,
                frozen = False,
                **kw):
        
        super(Button, self).__init__(**kw)

        # store attributes
        self.text_charged_color = text_charged_color
        self.border_charged_color = border_charged_color
        self.keys = keys
        self.modifier = modifier
        self.activate_funcs = activate_funcs
        self.deactivate_funcs = deactivate_funcs
        self.name = name
        self.frozen = frozen

        self.active = False
        self.charged = False

        # rect drawing stuff
        self.vertex_idle_colors = copy.deepcopy(self.vertex_colors)
        self.vertex_charged_colors = self.get_vertex_color(
                                        self.background_color,
                                        self.border_charged_color)

        # border drawing stuff
        self.border_idle_colors = copy.deepcopy(self.border_colors)
        if self.border_type == 'line':
            self.border_charged_colors = border_charged_color * 4
        else:
            self.border_charged_colors = None

        # label drawing stuff
        self.text_idle_color = copy.deepcopy(self.text_color)

        if self.widget_visible:
            self.show_button(show_base_widget = False)

    def show_button(self, show_base_widget = True):
        self.key_down = False
        self.mouse_down = False
        if not self.frozen:
            self.active = True
        if show_base_widget:
            super(Button, self).show_widget()
        self.set_idle()

    def set_idle(self):
        self.charged = False
#        # TODO: changed from market2: no error catching for vertex_colors b4

        try:
            self.vertex.colors = self.vertex_idle_colors
        except AttributeError:
            pass
        try:
            self.border.colors = self.border_idle_colors
        except AttributeError:
            pass
#        # TODO: changed from market2: no error catching for label b4
        try:
            if self.label != None:
                self.label.color = self.text_idle_color
        except AttributeError:
            pass

    def set_charged(self):
        self.charged = True
        self.label.color = self.text_charged_color
        self.vertex.colors = self.vertex_charged_colors
        try:
            self.border.colors = self.border_charged_colors
        except AttributeError:
            pass

    def hit_test(self, x, y):
        return (self.widget_x < x < self.widget_x + self.widget_width and
                self.widget_y < y < self.widget_y + self.widget_height)

    def clear_batch(self):
        super(Button, self).clear_batch()
        self.active = False

    def on_mouse_press(self, x, y, button, modifiers):
        x, y = director.get_virtual_coordinates(x, y)
        if self.active and self.hit_test(x, y):
            if not self.charged and not self.key_down:
                self.mouse_down = True
                self.set_charged()
                self.activate()

    def activate(self):
        for func in self.activate_funcs:
            if not func == 'destroy':
                if not self.name == None:
                    func(name=self.name)
                else:
                    func()
        if 'destroy' in self.activate_funcs:
            self.clear_batch()

    def deactivate(self):
        if 'destroy' in self.deactivate_funcs:
            self.clear_batch()
        if 'deactivate' in self.deactivate_funcs:
            self.active = False
        for func in self.deactivate_funcs:
            if not func in ['destroy', 'deactivate']:
                if not self.name == None:
                    func(name=self.name)
                else:
                    func()

    def on_mouse_release(self, x, y, button, modifiers):
        if self.charged and not self.key_down:
            self.mouse_down = False
            self.set_idle()
#        # TODO: changed from market2 was not requiring self.active, but for metamatrix2 produces error
            if self.active:
                self.deactivate()

    def on_key_press(self, symbol, modifiers):
        if self.active:
            press = False
            if not self.charged and not self.mouse_down and \
            not self.key_down and symbol in self.keys:
                if self.modifier > 0:
                    if modifiers & self.modifier:
                        press = True
                else:
                    press = True
            if press:
                self.key_down = True
                self.set_charged()
                self.activate()

    def on_key_release(self, symbol, modifiers):
#        if self.active:
        if self.charged and not self.mouse_down and \
        self.key_down and symbol in self.keys:
            self.key_down = False
            self.set_idle()
            self.deactivate()
            
class HoverButton(Button):
    
    def __init__(self, 
                 hover_on_funcs = [],
                 hover_off_funcs = [],
                 **kw):

        self.hovering = False
        self.hover_on_funcs = hover_on_funcs
        self.hover_off_funcs = hover_off_funcs
        super(HoverButton, self).__init__(**kw)        
            
    def on_mouse_motion(self, x, y, dx, dy):
        if self.active:
            x, y = director.get_virtual_coordinates(x, y)
            if not self.hovering and self.hit_test(x, y):
                self.start_hovering()
            elif self.hovering and not self.hit_test(x, y):
                self.stop_hovering()
                
    def start_hovering(self):
        self.hovering = True
        for func in self.hover_on_funcs:
            if not self.name == None:
                func(name=self.name)
            else:
                func()
   
    def stop_hovering(self):
        self.hovering = False
        for func in self.hover_off_funcs:
            if not self.name == None:
                func(name=self.name)
            else:
                func()
                
class ImageButton(HoverButton):
    
    def __init__(self, 
                 image = None,
                 **kw):
        
        super(ImageButton, self).__init__(**kw)
        
        if image:
            if isinstance(image, str) or isinstance(image, unicode):
                image=pyglet.resource.image(image)
            image_x = self.widget_x + kw['width'] / 2
            image_y = self.widget_y + kw['height'] / 2
            self.sprite = Sprite(image=image,
                                 position = (image_x, image_y))
            self.add(self.sprite, z=1)
        
    def replace_image(self, image):
        if hasattr(self, 'sprite'):
            if isinstance(image, str) or isinstance(image, unicode):
                image=pyglet.resource.image(image)
            self.sprite.image = image
        

#        self.sprite.position = (0, 0)

class MessageLayer(Layer):
    '''layer with back color (rgba) and a message accepting richlabel style'''
    # requires center_label function
    def __init__(self, text = '',
                       text_style = {},
                       back_color = (0, 0, 0, 255),
                       rich_text = False):

        # initialize layer
        super(MessageLayer, self).__init__()

        # add back color
        self.back = ColorLayer(*back_color)
        self.add(self.back, z=-1)

        # add text label
        if rich_text:
            label_class = RichLabel
            text_style = dict(text_style,
                              color=None)
        else:
            label_class = Label
        self.label = label_class(**dict(text_style,
                                    text=text))
        center_label(self.label)
        self.add(self.label, z=1)
