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

# keep track of the single root Tk instance that underpins all windows
_ROOT = None

CFGFILE = 'visualiser.ini'

# load or create configuration
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

class PadViewer(Toplevel):
    def __init__(self, parent=None):
        # ensure we have a root to attach to
        global _ROOT
        if _ROOT is None:
            _ROOT = Tk()
            _ROOT.withdraw()
        super().__init__(parent or _ROOT)
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

# helper routines for config

def save_config(port, baud):
    cfg = configparser.ConfigParser()
    cfg['serial'] = {'port': port, 'baud': str(baud)}
    with open(CFGFILE, 'w') as f:
        cfg.write(f)


def show_config_dialog():
    """Display a modal dialog for serial settings.

    Returns a dict with keys 'port', 'baud' and 'cancel'.
    If the user cancels (or closes the window) the 'cancel' flag is True.

    Uses a Toplevel window so we only ever create a single Tk() root.
    """
    global _ROOT
    if _ROOT is None:
        _ROOT = Tk()
        _ROOT.withdraw()          # hide the invisible master window

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
        # user accepted new values
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
    # handle window close as cancel too
    dlg.protocol("WM_DELETE_WINDOW", cancel)

    # make the dialog modal
    dlg.transient(_ROOT)
    dlg.grab_set()
    _ROOT.wait_window(dlg)

    return result


if __name__ == '__main__':
    # keep asking until the user picks a real port or decides to quit
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