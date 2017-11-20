'''
Gradients for kivy
Code snippet posted by Tim H. on "kivy users" forum.
https://groups.google.com/forum/#!msg/kivy-users/Go7HINbBtI0/Bs50WN5YxGQJ
post date: 10/09/2014
'''

from kivy.graphics.texture import Texture


class Gradient(object):
    @staticmethod
    def horizontal(rgba_left, rgba_right):
        texture = Texture.create(size=(2, 1), colorfmt="rgba")

        # NEXT 2 LINES ADDED BY THOMAS WOELZ (not Tim H)
        texture.mag_filter = 'linear'
        texture.min_filter = 'linear'

        pixels = rgba_left + rgba_right
        pixels = [chr(int(v * 255)) for v in pixels]
        buf = ''.join(pixels)
        texture.blit_buffer(buf, colorfmt='rgba', bufferfmt='ubyte')
        return texture

    @staticmethod
    def vertical(rgba_top, rgba_bottom):
        texture = Texture.create(size=(1, 2), colorfmt="rgba")

        # NEXT 2 LINES ADDED BY THOMAS WOELZ (not Tim H)
        texture.mag_filter = 'linear'
        texture.min_filter = 'linear'

        pixels = rgba_bottom + rgba_top
        pixels = [chr(int(v * 255)) for v in pixels]
        buf = ''.join(pixels)
        texture.blit_buffer(buf, colorfmt='rgba', bufferfmt='ubyte')
        return texture