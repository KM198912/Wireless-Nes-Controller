# NES Wireless Controller

**Turn your original 1980s NES pad wireless – without cutting it open.**

When my internet went down one evening and Steam was useless, I dug out my
old NES.  While looking for the cartridge, I also found two ESP32 boards and
a crazy thought hit me: what if the controller itself could go wireless *and*
stay completely stock?  A quick trip to the interwebs later I had an
extension cord in the mail, I cut it in half, wired each half to an ESP, and
just like that the project was born.

The ESPs live in a little dongle between the controller and the console, so
your vintage pad remains untouched.  I’m sharing the code and design here
because it was fun to build and I think other retro gamers will enjoy it too.

---

## What you need

* 2× ESP32 development boards (any flavour will do)  
* A NES extension cable (the long one between pad and console)  
* Female jumper wires, heat‑shrink and optional hot glue.  (If you
  really want to go all‑in you can solder the leads directly to the ESP32 or
  even design a little PCB with the connector built in – for example you can grab the connector from Europe with faster shipping at [Zedlabz](https://www.zedlabz.com/products/controller-connector-port-for-nintendo-nes-console-7-pin-90-degree-replacement-2-pack-black-zedlabz?srsltid=AfmBOorLNYLtyGLcgUVKGPlg8VS46CnAKE-XDuBqMxV1WkUjW-lOKhSV) )
* A multimeter for tracing the four signal lines  
* An original NES controller and a working NES console  

---

## Wiring & setup

Cut the extension cable in half.  On the controller end identify the
following wires with your meter:

* **VCC** (+5 V from the console)
* **GND**
* **CLOCK**
* **LATCH**
* **DATA**

The controller is tolerant of 3.3 V, so feed the +5 V line into the ESP32’s
`3V3` or `5V` input pin.  Tie the other four signals to any free GPIOs – the
example code uses pins 21, 22 and 23, but you can remap them by editing the
`#define` values in the `.cpp` files.

Then create two separate PlatformIO/Arduino projects: one for the
**controller side** (the sketch is provided as `sender_controller.cpp`), and
one for the **console side** (`receiver_nes.cpp`).  Copy each file into its
own project directory and save it there as `main.cpp` before building.
Flash the appropriate sketch to each ESP32 and power them up.

> **Important:** on the **receiver/console** end you **must not** wire the
> VCC line from the cable to the ESP32.  The console provides 5 V and if
> that is fed into the development board it will destroy the chip.  Only
> connect GND, CLOCK, LATCH and DATA on the receiver side; power the ESP32
> separately (USB, battery, etc.).

![pinout](assets/pinout.jpg)

---

## Visualiser (bonus)

When I stream on Twitch I like to show my button presses.  That’s what
`visualiser.py` does – it reads the serial output from the receiver ESP and
renders a little NES skin with blobs for the pressed buttons.  The script
validates the serial port and baud rate you enter and lets you cancel
before the main window opens.  Make sure the receiver is configured to use
the same baud rate (for example 9600 or 115200); if it doesn’t, the
visualiser simply won’t receive the expected bytes and the pad will remain
blank rather than updating.
Once a real port is selected the GUI runs on
Windows, Linux, macOS, etc.  It’s basically a cross‑platform remake of
NintendoSpy.

* Included are a `visualiser.bat` and `.sh` file for cross‑platform launch
  on Linux/Mac make sure to `chmod +x` the `.sh` file
* The launcher scripts will check for Python 3 and the required modules,
  and notify you if something is missing

![visualiser](assets/visualiser.png)

---

Have fun soldering – and if you print a little NES‑style case for the dongle,
set of stylus, or RGB LEDs, I’d love to see pictures!  This project is meant
to be a playful hack, not a serious commercial product, so feel free to
modify and share.

## Fun facts

* The original prototype used AP mode and UDP between the two boards.  It
  worked… except for a bizarre bug where pressing **Right** on the D‑pad
  sometimes produced a phantom **A** press.  After a few hours of chasing
  ghosts I rewrote the link over BLE and the problem vanished.
* I built the adapter as a cable‑cut dongle deliberately so the controller
  itself stays untouched – just plug it in like a normal extension and the
  wireless circuitry is entirely external.
* I already have an SNES about to receive a similar treatment – I’d like to
build a dongle for it too.  Off‑the‑shelf wireless pads and cheap China
clones exist, as well as bespoke ‘8bitdo’ controllers, but none of them
feel quite right in hand like the original.  Adding the built‑in visualiser
could be a neat touch for streamers too.
* **Bonus bonus!**  You could modify the Receiver sketch to read from an
SD‑card module and feed it a TAS (tool‑assisted‑speedrun) file – suddenly
your setup doubles as a TAS console verifier.


## License
* No License, go and have fun, all i ask, spread the word, keep the NES alive, and tell people where to find this repo if they ask!
* And dont slap your own License on it!

