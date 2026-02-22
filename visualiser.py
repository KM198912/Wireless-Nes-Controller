import serial, threading
from tkinter import *
from PIL import Image, ImageTk
import xml.etree.ElementTree as ET
import os
from queue import Queue

PORT = 'COM6'          # change to the receiver’s port
BAUD = 9600          # original firmware uses 115200 (receiver too)

# button bit masks, same as in the ESP code
BTN = {
    'A':      1 << 0,
    'B':      1 << 1,
    'SELECT': 1 << 2,
    'START':  1 << 3,
    'UP':     1 << 4,
    'DOWN':   1 << 5,
    'LEFT':   1 << 6,
    'RIGHT':  1 << 7,
}

class PadViewer(Tk):
    def __init__(self):
        super().__init__()
        self.title("NES Spy")
        self.configure(bg='lime')  # set root window background
        # thread-safe queue for incoming states
        self.queue = Queue()
        # start queue processor
        self.after(5, self.process_queue)

        # load skin xml to position elements
        skin_dir = os.path.join(os.getcwd(), ".")
        tree = ET.parse(os.path.join(skin_dir, "skin.xml"))
        root = tree.getroot()
        bgnode = root.find('background')
        bgpath = os.path.join(skin_dir, bgnode.get('image'))
        # load image, strip solid-black border by making it transparent
        pil_img = Image.open(bgpath).convert('RGBA')
        pixels = pil_img.getdata()
        new_pixels = []
        for r, g, b, a in pixels:
            # treat near-black as transparent
            if r < 20 and g < 20 and b < 20:
                new_pixels.append((255,255,255,0))
            else:
                new_pixels.append((r,g,b,a))
        pil_img.putdata(new_pixels)
        bgimg = ImageTk.PhotoImage(pil_img)
        w, h = bgimg.width(), bgimg.height()
        self.pad = 10            # border thickness (also used for button offset)
        self.geometry(f"{w+self.pad}x{h+self.pad}")

        # create canvas with magenta background, slightly larger than image
        self.canvas = Canvas(self, width=w+self.pad, height=h+self.pad, bg=self['bg'], highlightthickness=0)
        self.canvas.pack()
        # draw background image with offset so border shows
        self.canvas.create_image(self.pad//2, self.pad//2, image=bgimg, anchor='nw')
        self.bgimg = bgimg    # keep reference

        self.rects = {}
        for btn in root.findall('button'):
            name = btn.get('name').upper()
            x = int(btn.get('x')) + self.pad//2
            y = int(btn.get('y')) + self.pad//2
            w = int(btn.get('width'))
            h = int(btn.get('height'))
            if name in ('UP','DOWN','LEFT','RIGHT'):
                # draw simple oval for dpad directions, invisible initially
                item = self.canvas.create_oval(x, y, x+w, y+h, fill='', outline='')
            else:
                # other buttons invisible until pressed
                item = self.canvas.create_oval(x, y, x+w, y+h, fill='', outline='')
            self.rects[name] = item

    def set_state(self, byte):
        for name, mask in BTN.items():
            if byte & mask:
                # show pressed button in red
                self.canvas.itemconfig(self.rects[name], fill='red', outline='red')
            else:
                # hide unpressed button
                self.canvas.itemconfig(self.rects[name], fill='', outline='')

    def process_queue(self):
        while not self.queue.empty():
            state = self.queue.get()
            self.set_state(state)
        self.after(5, self.process_queue)

def reader_thread(viewer):
    with serial.Serial(PORT, BAUD, timeout=1) as ser:
        buf = bytearray()
        while True:
            b = ser.read(1)
            if not b: continue
            if b == b'\n':
                if len(buf) >= 8:
                    # receiver sends one byte per button (0x00 or 0x01), convert back to mask
                    state = 0
                    for i in range(8):
                        if buf[i] != 0:
                            state |= 1 << i
                    viewer.set_state(state)
                buf.clear()
            else:
                buf.append(b[0])

if __name__ == '__main__':
    v = PadViewer()
    t = threading.Thread(target=reader_thread, args=(v,), daemon=True)
    t.start()
    v.mainloop()