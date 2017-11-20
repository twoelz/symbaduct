from kivy.graphics.texture import Texture
from kivy.graphics import Rectangle
from kivy.uix.widget import Widget
from kivy.app import App
 
 
class RadialGradient(App):
    def build(self):
        w = Widget()
        center_color = 200, 200, 0
        border_color = 0, 0, 0
 
        size = (64, 64)
        tex = Texture.create(size=size)
 
        sx_2 = size[0] / 2
        sy_2 = size[1] / 2
 
        buf = ''
        for x in xrange(-sx_2, sx_2):
            for y in xrange(-sy_2, sy_2):
                a = x / (1.0 * sx_2)
                b = y / (1.0 * sy_2)
                d = (a ** 2 + b ** 2) ** .5
 
                for c in (0, 1, 2):
                    buf += chr(max(0,
                                   min(255,
                                       int(center_color[c] * (1 - d)) +
                                       int(border_color[c] * d))))
 
        tex.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
 
        with w.canvas:
            Rectangle(texture=tex, size=(1920, 1080))
        return w
 
 
RadialGradient().run()