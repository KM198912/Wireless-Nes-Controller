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
* Female jumper wires, heat‑shrink and optional hot glue  
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
**controller side** (`sender_controller.cpp`), and one for the **console side**
(`receiver_nes.cpp`) then rename them to main.cpp in their own project folders.
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
renders a little NES skin with blobs for the pressed buttons.  Just adjust
the COM port at the top of the script and run it (it works on Windows,
Linux, etc.).  It’s basically a cross‑platform remake of NintendoSpy.

![visualiser](assets/visualiser.png)

---

Have fun soldering – and if you print a little NES‑style case for the dongle,
set of stylus, or RGB LEDs, I’d love to see pictures!  This project is meant
to be a playful hack, not a serious commercial product, so feel free to
modify and share.
