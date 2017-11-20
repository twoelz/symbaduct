'''
radial gradient in glsl
'''
from kivy.app import App
from kivy.graphics import RenderContext, Rectangle
from kivy.uix.widget import Widget
from kivy.properties import ListProperty
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.uix.gridlayout import GridLayout
from random import random
 
HEADER = '''
#ifdef GL_ES
precision highp float;
#endif

/* Outputs from the vertex shader */
varying vec4 frag_color;
varying vec2 tex_coord0;

/* uniform texture samplers */
uniform sampler2D texture0;
'''
 
GLSL = HEADER + '''
#line 1
uniform vec2 pos;
uniform vec2 size;
uniform vec2 gradient_center;
uniform vec4 gradient_color1;
uniform vec4 gradient_color2;

void main(void){
    gl_FragColor = mix(
        gradient_color1,
        gradient_color2,
        distance(
            vec2(
                (gl_FragCoord.x - pos.x) / size.x,
                (gl_FragCoord.y - pos.y) / size.y),
            gradient_center));
}
'''
 
 
class Radial(Widget):
    gradient_center = ListProperty([.5, .5])
    gradient_color1 = ListProperty([1.0, 1.0, 0.0, 1.0])
    gradient_color2 = ListProperty([0.0, 0.0, 1.0, 1.0])
 
    def __init__(self, **kw):
        self.canvas = RenderContext(
            #use_parent_modelview=True,
            use_parent_projection=True
            )
 
        super(Radial, self).__init__(**kw)
 
        #Clock.schedule_interval(self.update_canvas, 0)
        Clock.schedule_once(self.set_fs, 0)
        self.animate()
        with self.canvas:
            self.rect = Rectangle(pos=self.pos, size=self.size)
 
    def animate(self, *args):
        a = Animation(
            gradient_center=[random(), random()],
            gradient_color1=[random(), random(), random(), random()],
            gradient_color2=[random(), random(), random(), random()],
            d=random())
        a.bind(on_complete=self.animate)
        a.start(self)
 
    def set_fs(self, *args):
        self.canvas['pos'] = map(float, self.pos)
        self.canvas['size'] = map(float, self.size)
        self.canvas['gradient_color1'] = list(self.gradient_color1)
        self.canvas['gradient_color2'] = list(self.gradient_color2)
        self.canvas['gradient_center'] = list(self.gradient_center)
        self.canvas.shader.fs = GLSL
 
    def on_pos(self, *args):
        self.rect.pos = self.pos
        self.canvas['pos'] = map(float, self.pos)
 
    def on_size(self, *args):
        self.rect.size = self.size
        self.canvas['size'] = map(float, self.size)
 
    def on_gradient_color1(self, *args):
        self.canvas['gradient_color1'] = list(self.gradient_color1)
 
    def on_gradient_color2(self, *args):
        self.canvas['gradient_color2'] = list(self.gradient_color2)
 
    def on_gradient_center(self, *args):
        self.canvas['gradient_center'] = list(self.gradient_center)
 
 
class RadialApp(App):
    def build(self):
        root = GridLayout(cols=20)
        for i in range(400):
            root.add_widget(Radial())
        return root
 
 
if __name__ == '__main__':
    RadialApp().run()