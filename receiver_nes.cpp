#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include <BLEClient.h>

// BLE service/characteristic UUIDs must match the controller firmware
#define SERVICE_UUID "12345678-1234-1234-1234-1234567890ab"
#define CHAR_UUID    "abcdefab-1234-5678-1234-abcdefabcdef"

volatile uint8_t currentState = 0;
// pending state from network; only copied to shiftReg on latch
volatile uint8_t pendingState = 0;
// if we receive a zero packet we defer clearing until next latch
volatile bool releasePending = false;

// BLE globals
BLEScan* pBLEScan = nullptr;
BLEClient* pClient = nullptr;
BLERemoteCharacteristic* pRemoteChar = nullptr;
volatile bool linkConnected = false;

// forward declarations for functions used by callbacks
uint8_t translateState(uint8_t net);
void setLinkLed(bool on);

// notification handler from controller
static uint8_t lastRaw = 0xFF;
static void notifyCallback(
    BLERemoteCharacteristic* /*chr*/,
    uint8_t* pData,
    size_t length,
    bool /*isNotify*/
) {
    if (length != 1) return;
    uint8_t raw = pData[0];
    uint8_t mapped = translateState(raw);

    // update debug output on change
#if DEBUG_LOG
    if (raw != lastRaw) {
        Serial.printf("raw=%02X ", raw);
        Serial.printf("mapped=%02X", mapped);
        if (mapped == BTN_A)      Serial.print("  [A]");
        else if (mapped == BTN_B) Serial.print("  [B]");
        else if (mapped == BTN_SELECT) Serial.print("  [SELECT]");
        else if (mapped == BTN_START) Serial.print("  [START]");
        else if (mapped == BTN_UP) Serial.print("  [UP]");
        else if (mapped == BTN_DOWN) Serial.print("  [DOWN]");
        else if (mapped == BTN_LEFT) Serial.print("  [LEFT]");
        else if (mapped == BTN_RIGHT) Serial.print("  [RIGHT]");
        Serial.write('\n');
        lastRaw = raw;
    }
#endif

    // always update currentState for loop visualizer
    currentState = mapped;

    if (mapped != 0) {
        pendingState = mapped;
        releasePending = false;
    } else {
        pendingState = 0;      // clear immediately
        releasePending = true; // keep this as a safety net
    }
}

// client connection/disconnect callbacks
class ClientCallbacks : public BLEClientCallbacks {
    void onConnect(BLEClient* /*c*/) override {
        Serial.println("client callback: connected");
        setLinkLed(true);
        linkConnected = true;
    }
    void onDisconnect(BLEClient* /*c*/) override {
        Serial.println("client callback: disconnected");
        setLinkLed(false);
        linkConnected = false;
        // restart scanning immediately; start() is safe even if already
        // running and BLEScan doesn't provide an isScanning() method.
        if (pBLEScan) {
            pBLEScan->start(0, nullptr, false);
        }
    }
};

// scan callback: when controller advertises, remember address and stop scan
static bool pendingConnect = false;
static BLEAddress pendingAddress = BLEAddress("");  // empty initially
class AdvertisedDeviceCallbacks : public BLEAdvertisedDeviceCallbacks {
    void onResult(BLEAdvertisedDevice advertisedDevice) override {
        if (advertisedDevice.haveServiceUUID() &&
            advertisedDevice.isAdvertisingService(BLEUUID(SERVICE_UUID))) {
            Serial.println("found controller, will connect shortly");
            // save address and stop scanning; actual connect happens in loop
            pendingAddress = advertisedDevice.getAddress();
            pendingConnect = true;
            pBLEScan->stop();
        }
    }
};

// connection flag and LED pin
const uint8_t LED_PIN = 2; // blue on devkit

void setLinkLed(bool on) {
    linkConnected = on;
    digitalWrite(LED_PIN, on ? HIGH : LOW);
}

// comment out the next line to disable serial visualizer output
#define SERIAL_VISUALIZER 1
// comment out the next line to disable raw/mapped debug prints
#define DEBUG_LOG 1
// (we can have both enabled; visualiser output is independent of debug logs)
#define BTN_A      (1 << 0)
#define BTN_B      (1 << 1)
#define BTN_SELECT (1 << 2)
#define BTN_START  (1 << 3)
#define BTN_UP     (1 << 4)
#define BTN_DOWN   (1 << 5)
#define BTN_LEFT   (1 << 6)
#define BTN_RIGHT  (1 << 7)
#define PIN_CLOCK 21   // green wire (NES -> ESP input)
#define PIN_LATCH 22   // black wire (NES -> ESP input)
#define PIN_DATA  23   // yellow wire (ESP -> NES output)
#define PIN_DATA_OUT 23 // same as data pin, but set as output

// state used by ISRs
volatile uint8_t shiftReg = 0;
volatile uint8_t bitIndex = 0;

// network byte already uses the NES bit order, so just pass it through
uint8_t translateState(uint8_t net) {
    return net;
}

// ISR for strobe rising edge
void IRAM_ATTR latchISR() {
    // use the buffered pending state instead of currentState directly
    shiftReg = pendingState;
    bitIndex = 0;
    digitalWrite(PIN_DATA_OUT, (shiftReg & 1) ? LOW : HIGH);
    if (releasePending) {
        // now that the console has latched the previous value, clear it
        pendingState = 0;
        releasePending = false;
    }
}

// ISR for clock falling edge
void IRAM_ATTR clockISR() {
    if (bitIndex < 7) {
        bitIndex++;
        digitalWrite(PIN_DATA_OUT, (shiftReg & (1 << bitIndex)) ? LOW : HIGH);
        if (bitIndex == 7) {
            // we've just shifted out the last bit; clear shiftReg so a
            // subsequent strobe without a new packet won't resend old data
            shiftReg = 0;
        }
    }
}

// no longer used
void EmulateController(uint8_t) {}

void setup() {
    Serial.begin(9600);          // debug output

    pinMode(LED_PIN, OUTPUT);
    setLinkLed(false);

    // controller pins
    pinMode(PIN_LATCH, INPUT_PULLUP);
    pinMode(PIN_CLOCK, INPUT_PULLUP);
    pinMode(PIN_DATA_OUT, OUTPUT);
    digitalWrite(PIN_DATA_OUT, HIGH); // release bus (open collector behaviour)

    // install interrupts on latch and clock
    attachInterrupt(digitalPinToInterrupt(PIN_LATCH), latchISR, RISING);
    attachInterrupt(digitalPinToInterrupt(PIN_CLOCK), clockISR, FALLING);

    // BLE central initialization and scanning
    BLEDevice::init("");               // no local name needed
    pBLEScan = BLEDevice::getScan();
    pBLEScan->setActiveScan(true);
    pBLEScan->setAdvertisedDeviceCallbacks(new AdvertisedDeviceCallbacks());
    pBLEScan->start(0, nullptr, false); // continuous scan
}



// active loop after migrating to BLE
void loop() {
    // if we were told to connect, do it here instead of inside the callback
    if (pendingConnect) {
        pendingConnect = false;
        Serial.printf("loop: connecting to %s\n", pendingAddress.toString().c_str());
        if (!pClient) {
            pClient = BLEDevice::createClient();
            pClient->setClientCallbacks(new ClientCallbacks());
        }
        if (!pClient->isConnected()) {
            if (pClient->connect(pendingAddress)) {
                Serial.println("loop: connected, discovering service");
                BLERemoteService* svc = pClient->getService(BLEUUID(SERVICE_UUID));
                if (svc) {
                    Serial.println("loop: service found");
                    pRemoteChar = svc->getCharacteristic(BLEUUID(CHAR_UUID));
                    if (pRemoteChar) {
                        Serial.println("loop: characteristic found");
                        if (pRemoteChar->canNotify()) {
                            Serial.println("loop: registering notify");
                            pRemoteChar->registerForNotify(notifyCallback);
                        } else {
                            Serial.println("loop: char cannot notify");
                        }
                    } else {
                        Serial.println("loop: characteristic not found");
                    }
                } else {
                    Serial.println("loop: service not found");
                }
            } else {
                Serial.println("loop: connect() failed");
            }
        }
    }

    // blink LED when not linked
    static unsigned long blinkNext = 0;
    if (!linkConnected) {
        if (millis() >= blinkNext) {
            blinkNext = millis() + 500;
            digitalWrite(LED_PIN, !digitalRead(LED_PIN));
        }
    } else {
        digitalWrite(LED_PIN, HIGH);
    }

    #if SERIAL_VISUALIZER
    // emit eight‑bit state every iteration so the visualiser always gets a
    // complete packet even when no change occurs.  This matches the old UDP
    // behaviour the Python script expects.
    uint8_t mapped = currentState;
    for (int i = 0; i < 8; i++) {
        Serial.write((mapped & (1 << i)) ? 0x01 : 0x00);
    }
    Serial.write('\n');
    #endif
    delay(10); // ~100 Hz update rate
}

