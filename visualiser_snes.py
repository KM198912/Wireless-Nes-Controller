"""Simple NES button visualiser for direct sniffer output.

This is a trimmed‑down version of the main visualiser that expects a serial
line containing an 8‑bit state in hex (e.g. "0x3F" or just "3F").  It's
handy when you're tapping the raw controller signals with an ESP32/Arduino
and printing the value rather than using the full receiver firmware.

The GUI and configuration dialog are identical to ``visualiser.py``; only the
reader thread changes.
"""

import serial, threading
import serial.tools.list_ports
from tkinter import *
from tkinter import messagebox
from tkinter import Toplevel
from PIL import Image, ImageTk
import xml.etree.ElementTree as ET
import os
from queue import Queue
import configparser

# configuration file name and defaults
CFGFILE = 'visualiser.ini'
config = configparser.ConfigParser()
config.read(CFGFILE)
PORT = config.get('serial', 'port', fallback='COM6')
BAUD = config.getint('serial', 'baud', fallback=115200)

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

# GUI code copied from visualiser.py
_ROOT = None

class PadViewer(Toplevel):
    def __init__(self, parent=None):
        global _ROOT
        if _ROOT is None:
            _ROOT = Tk()
            _ROOT.withdraw()
        super().__init__(parent or _ROOT)
        self.title("NES Sniffer")
        self.configure(bg='lime')
        self.queue = Queue()
        self.after(5, self.process_queue)

        skin_dir = os.getcwd()
        tree = ET.parse(os.path.join(skin_dir, "skin.xml"))
        root = tree.getroot()
        bgnode = root.find('background')
        bgpath = os.path.join(skin_dir, bgnode.get('image'))
        pil_img = Image.open(bgpath).convert('RGBA')
        pixels = pil_img.getdata()
        new_pixels = []
        for r, g, b, a in pixels:
            if r < 20 and g < 20 and b < 20:
                new_pixels.append((255,255,255,0))
            else:
                new_pixels.append((r,g,b,a))
        pil_img.putdata(new_pixels)
        bgimg = ImageTk.PhotoImage(pil_img)
        w, h = bgimg.width(), bgimg.height()
        self.pad = 10
        self.geometry(f"{w+self.pad}x{h+self.pad}")

        self.canvas = Canvas(self, width=w+self.pad, height=h+self.pad, bg=self['bg'], highlightthickness=0)
        self.canvas.pack()
        self.canvas.create_image(self.pad//2, self.pad//2, image=bgimg, anchor='nw')
        self.bgimg = bgimg

        self.rects = {}
        for btn in root.findall('button'):
            name = btn.get('name').upper()
            x = int(btn.get('x')) + self.pad//2
            y = int(btn.get('y')) + self.pad//2
            w = int(btn.get('width'))
            h = int(btn.get('height'))
            item = self.canvas.create_oval(x, y, x+w, y+h, fill='', outline='')
            self.rects[name] = item

    def set_state(self, byte):
        for name, mask in BTN.items():
            if byte & mask:
                self.canvas.itemconfig(self.rects[name], fill='red', outline='red')
            else:
                self.canvas.itemconfig(self.rects[name], fill='', outline='')

    def process_queue(self):
        while not self.queue.empty():
            state = self.queue.get()
            self.set_state(state)
        self.after(5, self.process_queue)

# reader for sniffer output

def reader_thread(viewer):
    with serial.Serial(PORT, BAUD, timeout=1) as ser:
        while True:
            line = ser.readline().decode('ascii', errors='ignore').strip()
            if not line:
                continue
            # extract hex number if present
            if '0x' in line:
                try:
                    state = int(line[line.find('0x'):], 16)
                except ValueError:
                    continue
            else:
                try:
                    state = int(line, 16)
                except ValueError:
                    continue
            viewer.set_state(state)

# config helpers copied from visualiser.py

def save_config(port, baud):
    cfg = configparser.ConfigParser()
    cfg['serial'] = {'port': port, 'baud': str(baud)}
    with open(CFGFILE, 'w') as f:
        cfg.write(f)


def show_config_dialog():
    global _ROOT
    if _ROOT is None:
        _ROOT = Tk()
        _ROOT.withdraw()

    result = {'port': PORT, 'baud': BAUD, 'cancel': False}
    dlg = Toplevel(_ROOT)
    dlg.title('Serial Settings')
    Label(dlg, text='COM Port:').grid(row=0, column=0, sticky='w')
    port_var = StringVar(value=PORT)
    Entry(dlg, textvariable=port_var).grid(row=0, column=1)
    Label(dlg, text='Baud:').grid(row=1, column=0, sticky='w')
    baud_var = StringVar(value=str(BAUD))
    Entry(dlg, textvariable=baud_var).grid(row=1, column=1)

    def apply():
        try:
            baud_val = int(baud_var.get())
        except ValueError:
            baud_val = 115200
        result['port'] = port_var.get()
        result['baud'] = baud_val
        save_config(result['port'], result['baud'])
        dlg.destroy()

    def cancel():
        result['cancel'] = True
        dlg.destroy()

    Button(dlg, text='Go', command=apply).grid(row=2, column=0)
    Button(dlg, text='Cancel', command=cancel).grid(row=2, column=1)
    dlg.protocol("WM_DELETE_WINDOW", cancel)
    dlg.transient(_ROOT)
    dlg.grab_set()
    _ROOT.wait_window(dlg)
    return result

if __name__ == '__main__':
    while True:
        res = show_config_dialog()
        if res.get('cancel'):
            import sys
            sys.exit(0)
        PORT = res['port']
        BAUD = res['baud']
        if any(p.device == PORT for p in serial.tools.list_ports.comports()):
            break
        messagebox.showerror("Port not found", f"Selected serial port '{PORT}' does not exist.")

    v = PadViewer()
    t = threading.Thread(target=reader_thread, args=(v,), daemon=True)
    t.start()
    v.mainloop()
