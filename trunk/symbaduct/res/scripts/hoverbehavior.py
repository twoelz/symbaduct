"""Hoverable Behaviour (changing when the mouse is on the widget by O. Poyen.
License: LGPL
"""

# Thomas Woelz ADDED bind_hover and unbind_hover methods since removed widgets with HoverBehavior
# wont unbind hoverbehavior when removed. code added at lines 56 to 62

__author__ = 'Olivier POYEN'


from kivy.properties import BooleanProperty, ObjectProperty
from kivy.core.window import Window

class HoverBehavior(object):
    """Hover behavior.

    :Events:
        `on_enter`
            Fired when mouse enter the bbox of the widget.
        `on_leave`
            Fired when the mouse exit the widget 
    """

    hovered = BooleanProperty(False)
    border_point= ObjectProperty(None)
    '''Contains the last relevant point received by the Hoverable. This can
    be used in `on_enter` or `on_leave` in order to know where was dispatched the event.
    '''

    def __init__(self, **kwargs):
        self.register_event_type('on_enter')
        self.register_event_type('on_leave')
        Window.bind(mouse_pos=self.on_mouse_pos)
        super(HoverBehavior, self).__init__(**kwargs)

    def on_mouse_pos(self, *args):
        pos = args[1]
        inside = self.collide_point(*pos)
        if self.hovered == inside:
            #We have already done what was needed
            return
        self.border_point = pos
        self.hovered = inside
        if inside:
            self.dispatch('on_enter')
        else:
            self.dispatch('on_leave')

    def on_enter(self):
        pass

    def on_leave(self):
        pass


    # Methods added by Thomas Woelz (twoelz@gmail.com): unbind_hover and bind_hover
    # to be directly called when widgets with this behavior are removed or re-added
    def unbind_hover(self):
        Window.unbind(mouse_pos=self.on_mouse_pos)

    def bind_hover(self):
        Window.bind(mouse_pos=self.on_mouse_pos)


if __name__=='__main__':
    from kivy.uix.floatlayout import FloatLayout
    from kivy.lang import Builder
    from kivy.uix.label import Label
    from kivy.base import runTouchApp
    class HoverLabel(Label, HoverBehavior):
        def on_enter(self, *args):
            print "You are in, though this point", self.border_point

        def on_leave(self, *args):
            print "You left through this point", self.border_point

    Builder.load_string('''
<HoverLabel>:
    text: "inside" if self.hovered else "outside"
    pos: 200,200
    size_hint: None, None
    size: 100, 30
    canvas.before:
        Color:
            rgb: 1,0,0
        Rectangle:
            size: self.size
            pos: self.pos
    ''')
    fl = FloatLayout()
    fl.add_widget(HoverLabel())
    runTouchApp(fl)
