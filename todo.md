## Rev 1.0 Todo

* Instead of using Jumper Cables and Heatshrink, order PCB from design in [Assets](assets/esp32-controller.zip)
* Use External LED for connection Status
* Use a USB-C charging circuit and 3.7V Battery for true Wireless Experience
* Switch to a smaller footprint ESP32 (maybe a ESP32 D1 Mini?)  
* Add a Powerswitch to turn off the Controller when battery powered. (could either be on the positive wire of the battery, or a PCB Redesign, but most likely the redesign will be in Rev 2.0, maybe even a 3 position slider switch, 3 positions: 1: USB Power, 2: OFF, 3: Battery power)
* 3D print a Case for Controller part
* Use a breakout board for receiver part, and print case for it
## Rev 2.0 Ideas

* Add a low power Timer circuit, when switch powered on, that shuts power to the ESP after a set time (3 minutes?) of no input
* Maybe add a Wireless option with a Webinterface to configure timeout or turn timeout off, remap buttons? (maybe someone wants to swap the A+B buttons in mario?)
* PCB Redesign for smaller footprint