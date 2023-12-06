#!/usr/bin/env python3

import io
from base64 import standard_b64encode

import requests
from PIL import Image

from textual.app import App
from textual.widgets import Static
from rich import print
from rich.segment import Segment

url = 'https://github.com/textualize/rich/raw/master/imgs/features.png'


class KittyImage:
    def __init__(self, url):
        # download the image, resize and convert to png
        img_response = requests.get(url, stream=True)
        img = Image.open(io.BytesIO(img_response.content))
        self.png = io.BytesIO()
        img.resize(size=(500, 500)).save(self.png, format='png')
        # fill up the buffer using the function from the example
        self.buf = io.BytesIO()
        self.write_chunked(a='T', f=100)
        self.buf.seek(0)
        # generate a Segment for rich to display
        self.segment = Segment(self.buf.read().decode())

    # the following two methods are essentially unchanged from the example in
    # https://sw.kovidgoyal.net/kitty/graphics-protocol/#a-minimal-example
    @staticmethod
    def serialize_gr_command(**cmd):
        payload = cmd.pop('payload', None)
        cmd = ','.join(f'{k}={v}' for k, v in cmd.items())
        ans = []
        w = ans.append
        w(b'\033_G'), w(cmd.encode('ascii'))
        if payload:
            w(b';')
            w(payload)
        w(b'\033\\')
        return b''.join(ans)

    def write_chunked(self, **cmd):
        self.png.seek(0)
        data = standard_b64encode(self.png.read())
        while data:
            chunk, data = data[:4096], data[4096:]
            m = 1 if data else 0
            self.buf.write(self.serialize_gr_command(payload=chunk, m=m, **cmd))
            self.buf.flush()
            cmd.clear()

    def __rich_console__(self, console, options):
        yield self.segment


# small app example
class Img(Static):
    def get_content_width(self, container, viewport):
        return 50

class ImageApp(App):
    def compose(self):
        yield Img(KittyImage(url))


if __name__ == "__main__":
    app = ImageApp()
    app.run()
    img = KittyImage(url)
    print(repr(img))
    print(img)
